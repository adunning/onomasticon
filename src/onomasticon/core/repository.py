"""TOML-backed persistence for canonical entities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from secrets import choice
import tomllib

from onomasticon.core.appellations import Appellation, AppellationPart
from onomasticon.core.entities import (
    AnyEntity,
    Entity,
    EntityType,
    Expression,
    Item,
    Manifestation,
    Organization,
    OrganizationSubtype,
    Person,
    Place,
    PlaceSubtype,
    Work,
    entity_type_for_instance,
)
from onomasticon.core.identifiers import Identifier
from onomasticon.core.local_ids import LOCAL_IDENTIFIER_LENGTH
from onomasticon.core.properties import StatementProperty, allowed_target_entity_types
from onomasticon.core.statements import (
    AscriptionValue,
    Certainty,
    CoordinateValue,
    DateValue,
    EntityValue,
    IdentifierValue,
    LanguageTagValue,
    Qualifier,
    Reference,
    SexValue,
    Statement,
    StatementStatus,
    TextValue,
)
from onomasticon.core.temporal import TemporalValue
from onomasticon.core.validation import (
    optional_string,
    require_list,
    require_non_empty_string,
)

_IDENTIFIER_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"
DEFAULT_ID_MINT_ATTEMPTS = 64


class RepositoryError(Exception):
    """Base class for repository-layer errors."""


class EntityValidationError(RepositoryError, ValueError):
    """Raised when an entity document fails repository validation."""


class IdentifierCollisionError(RepositoryError):
    """Raised when ID minting exhausts its retry budget."""


class EntityWriteError(RepositoryError):
    """Raised when repository write semantics are violated."""


@dataclass(slots=True, frozen=True)
class RepositoryLayout:
    """Path policy for the Git-backed entity repository."""

    root: Path
    entities_directory: str = "entities"

    def entity_path(self, entity_id: str) -> Path:
        """Return the canonical path for one entity file."""
        return self.root / self.entities_directory / f"{entity_id}.toml"

    def entity_exists(self, entity_id: str) -> bool:
        """Return whether the given entity identifier is already present."""
        return self.entity_path(entity_id).exists()


@dataclass(slots=True, frozen=True)
class EntityRepository:
    """Load and serialize canonical entity records."""

    layout: RepositoryLayout

    def loads(self, content: str) -> AnyEntity:
        """Parse one entity from TOML text."""
        try:
            data = _require_table(tomllib.loads(content))
        except tomllib.TOMLDecodeError as exc:
            msg = "Invalid TOML entity document."
            raise EntityValidationError(msg) from exc
        return _entity_from_mapping(data)

    def load(self, path: Path) -> AnyEntity:
        """Load one entity from a TOML file."""
        entity = self.loads(path.read_text())
        self.validate_cross_entity_references(entity)
        return entity

    def dumps(self, entity: AnyEntity) -> str:
        """Serialize one entity to TOML."""
        lines = [f"id = {_quote_string(entity.id)}"]
        entity_type = _entity_type_for(entity)
        if entity_type is not None:
            lines.append(f"type = {_quote_string(entity_type.value)}")
        if entity.redirect is not None:
            lines.append(f"redirect = {_quote_string(entity.redirect)}")
        if entity.note is not None:
            lines.append(f"note = {_quote_string(entity.note)}")
        lines.extend(_dump_appellations(entity.appellations))
        lines.extend(_dump_identifiers(entity.identifiers))
        lines.extend(_dump_statements(entity.statements))
        return "\n".join(lines) + "\n"

    def dump(
        self,
        entity: AnyEntity,
        path: Path | None = None,
        *,
        overwrite: bool = False,
    ) -> Path:
        """Write one entity to disk and return the path used."""
        destination = path or self.layout.entity_path(entity.id)
        expected_name = f"{entity.id}.toml"
        if destination.name != expected_name:
            msg = f"Entity {entity.id} must be written to a file named {expected_name}."
            raise EntityWriteError(msg)
        self.validate_cross_entity_references(entity)
        if destination.exists() and not overwrite:
            msg = f"Refusing to overwrite existing entity file: {destination}."
            raise EntityWriteError(msg)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.dumps(entity))
        return destination

    def validate_cross_entity_references(self, entity: AnyEntity) -> None:
        """Validate repository-level entity references for one entity."""
        for statement in entity.statements:
            match statement.value:
                case EntityValue(entity_id=target_id):
                    self._validate_entity_reference(
                        entity, statement.property, target_id
                    )
                case _:
                    continue

    def _validate_entity_reference(
        self,
        entity: AnyEntity,
        property_name: StatementProperty | str,
        target_id: str,
    ) -> None:
        normalized_property = StatementProperty(property_name)
        target_path = self.layout.entity_path(target_id)
        if not target_path.exists():
            msg = (
                f"Entity {entity.id} references missing entity {target_id!r} "
                f"via property {normalized_property.value!r}."
            )
            raise EntityValidationError(msg)
        target_entity = self.loads(target_path.read_text())
        allowed_types = allowed_target_entity_types(normalized_property)
        if allowed_types is None:
            return
        target_type = entity_type_for_instance(target_entity)
        target_type_value = getattr(target_type, "value", None)
        if target_type_value not in allowed_types:
            allowed = ", ".join(sorted(allowed_types))
            actual = target_type_value or "untyped"
            msg = (
                f"Property {normalized_property.value!r} on entity {entity.id} must point "
                f"to one of [{allowed}], not {actual!r}."
            )
            raise EntityValidationError(msg)

    def mint_id(self, *, max_attempts: int = DEFAULT_ID_MINT_ATTEMPTS) -> str:
        """Mint a new six-character local identifier with collision checking."""
        for _ in range(max_attempts):
            candidate = "".join(
                choice(_IDENTIFIER_ALPHABET) for _ in range(LOCAL_IDENTIFIER_LENGTH)
            )
            if not self.layout.entity_exists(candidate):
                return candidate
        msg = (
            f"Unable to mint a unique entity identifier after {max_attempts} attempts."
        )
        raise IdentifierCollisionError(msg)


def _entity_type_for(entity: AnyEntity) -> EntityType | None:
    match entity:
        case Person():
            return EntityType.PERSON
        case Place(subtype=PlaceSubtype.COUNTRY):
            return EntityType.COUNTRY
        case Place():
            return EntityType.PLACE
        case Organization(subtype=OrganizationSubtype.RELIGIOUS_ORDER):
            return EntityType.RELIGIOUS_ORDER
        case Organization():
            return EntityType.ORGANIZATION
        case Work():
            return EntityType.WORK
        case Expression():
            return EntityType.EXPRESSION
        case Manifestation():
            return EntityType.MANIFESTATION
        case Item():
            return EntityType.ITEM
        case Entity():
            return None


def _entity_from_mapping(data: dict[str, object]) -> AnyEntity:
    allowed_keys = {
        "id",
        "type",
        "appellations",
        "identifiers",
        "statements",
        "redirect",
        "note",
    }
    extra_keys = set(data) - allowed_keys
    if extra_keys:
        extras = ", ".join(sorted(extra_keys))
        msg = f"Unexpected entity fields: {extras}."
        raise EntityValidationError(msg)

    entity_id = _require_string(data, "id")
    entity_type_raw = _optional_string(data, "type")
    appellations = _parse_appellations(data.get("appellations"))
    identifiers = _parse_identifiers(data.get("identifiers"))
    redirect = _optional_string(data, "redirect")
    note = _optional_string(data, "note")
    statements = _parse_statements(data.get("statements"))

    try:
        entity_type = (
            EntityType(entity_type_raw) if entity_type_raw is not None else None
        )
    except ValueError as exc:
        msg = f"Unknown type: {entity_type_raw}."
        raise EntityValidationError(msg) from exc

    entity_class = _entity_class_for(entity_type)
    return entity_class(
        id=entity_id,
        appellations=appellations,
        identifiers=identifiers,
        statements=statements,
        redirect=redirect,
        note=note,
        **_entity_subtype_kwargs(entity_type),
    )


def _entity_class_for(entity_type: EntityType | None) -> type[AnyEntity]:
    match entity_type:
        case EntityType.PERSON:
            return Person
        case EntityType.COUNTRY:
            return Place
        case EntityType.PLACE:
            return Place
        case EntityType.RELIGIOUS_ORDER:
            return Organization
        case EntityType.ORGANIZATION:
            return Organization
        case EntityType.WORK:
            return Work
        case EntityType.EXPRESSION:
            return Expression
        case EntityType.MANIFESTATION:
            return Manifestation
        case EntityType.ITEM:
            return Item
        case None:
            return Entity


def _entity_subtype_kwargs(
    entity_type: EntityType | None,
) -> dict[str, object]:
    match entity_type:
        case EntityType.COUNTRY:
            return {"subtype": PlaceSubtype.COUNTRY}
        case EntityType.RELIGIOUS_ORDER:
            return {"subtype": OrganizationSubtype.RELIGIOUS_ORDER}
        case _:
            return {}


def _parse_identifiers(raw: object) -> tuple[Identifier, ...]:
    if raw is None:
        return ()
    raw_list = _require_list(raw, field_name="identifiers")
    identifiers: list[Identifier] = []
    for item in raw_list:
        data = _require_table(item)
        allowed_keys = {"scheme", "value", "note"}
        extra_keys = set(data) - allowed_keys
        if extra_keys:
            extras = ", ".join(sorted(extra_keys))
            msg = f"Unexpected identifier fields: {extras}."
            raise EntityValidationError(msg)
        identifiers.append(
            Identifier(
                scheme=_require_string(data, "scheme"),
                value=_require_string(data, "value"),
                note=_optional_string(data, "note"),
            )
        )
    return tuple(identifiers)


def _parse_appellations(raw: object) -> tuple[Appellation, ...]:
    if raw is None:
        return ()
    raw_list = _require_list(raw, field_name="appellations")
    appellations: list[Appellation] = []
    for item in raw_list:
        data = _require_table(item)
        allowed_keys = {
            "kind",
            "parts",
            "value",
            "language",
            "script",
            "refs",
            "status",
            "certainty",
            "note",
        }
        extra_keys = set(data) - allowed_keys
        if extra_keys:
            extras = ", ".join(sorted(extra_keys))
            msg = f"Unexpected appellation fields: {extras}."
            raise EntityValidationError(msg)
        try:
            appellations.append(
                Appellation(
                    kind=_require_string(data, "kind"),
                    parts=_parse_appellation_parts(data.get("parts")),
                    value=_optional_string(data, "value"),
                    language=_optional_string(data, "language"),
                    script=_optional_string(data, "script"),
                    references=_parse_references(data.get("refs")),
                    status=_parse_statement_status(data.get("status")),
                    certainty=_parse_certainty(data.get("certainty")),
                    note=_optional_string(data, "note"),
                )
            )
        except ValueError as exc:
            raise EntityValidationError(str(exc)) from exc
    return tuple(appellations)


def _parse_appellation_parts(raw: object) -> tuple[AppellationPart, ...]:
    if raw is None:
        return ()
    raw_list = _require_list(raw, field_name="parts")
    parts: list[AppellationPart] = []
    for item in raw_list:
        data = _require_table(item)
        allowed_keys = {"kind", "value"}
        extra_keys = set(data) - allowed_keys
        if extra_keys:
            extras = ", ".join(sorted(extra_keys))
            msg = f"Unexpected appellation part fields: {extras}."
            raise EntityValidationError(msg)
        try:
            parts.append(
                AppellationPart(
                    kind=_require_string(data, "kind"),
                    value=_require_string(data, "value"),
                )
            )
        except ValueError as exc:
            raise EntityValidationError(str(exc)) from exc
    return tuple(parts)


def _parse_statements(raw: object) -> tuple[Statement, ...]:
    if raw is None:
        return ()
    raw_list = _require_list(raw, field_name="statements")
    return tuple(_statement_from_mapping(_require_table(item)) for item in raw_list)


def _statement_from_mapping(data: dict[str, object]) -> Statement:
    allowed_keys = {
        "property",
        "entity",
        "identifier",
        "text",
        "lang",
        "date",
        "coordinates",
        "sex",
        "ascription",
        "refs",
        "qualifiers",
        "status",
        "certainty",
        "note",
    }
    extra_keys = set(data) - allowed_keys
    if extra_keys:
        extras = ", ".join(sorted(extra_keys))
        msg = f"Unexpected statement fields: {extras}."
        raise EntityValidationError(msg)
    value_keys = [
        key
        for key in (
            "entity",
            "identifier",
            "text",
            "lang",
            "date",
            "coordinates",
            "sex",
            "ascription",
        )
        if key in data
    ]
    if len(value_keys) != 1:
        msg = "Each statement must define exactly one value field."
        raise EntityValidationError(msg)
    value_key = value_keys[0]
    raw_value = data[value_key]
    match value_key:
        case "entity":
            value = EntityValue(_require_raw_string(raw_value, field_name="entity"))
        case "identifier":
            identifier = _require_table(raw_value)
            value = IdentifierValue(
                Identifier(
                    scheme=_require_string(identifier, "scheme"),
                    value=_require_string(identifier, "value"),
                    note=_optional_string(identifier, "note"),
                )
            )
        case "text":
            value = TextValue(_require_raw_string(raw_value, field_name="text"))
        case "lang":
            value = LanguageTagValue(_require_raw_string(raw_value, field_name="lang"))
        case "date":
            value = DateValue(_parse_temporal_value(raw_value))
        case "coordinates":
            value = _parse_coordinate_value(raw_value)
        case "sex":
            try:
                value = SexValue(_require_raw_string(raw_value, field_name="sex"))
            except ValueError as exc:
                raise EntityValidationError(str(exc)) from exc
        case "ascription":
            try:
                value = AscriptionValue(
                    _require_raw_string(raw_value, field_name="ascription")
                )
            except ValueError as exc:
                raise EntityValidationError(str(exc)) from exc
        case _:
            raise AssertionError(value_key)
    return Statement(
        property=_parse_statement_property(data.get("property")),
        value=value,
        references=_parse_references(data.get("refs")),
        qualifiers=_parse_qualifiers(data.get("qualifiers")),
        status=_parse_statement_status(data.get("status")),
        certainty=_parse_certainty(data.get("certainty")),
        note=_optional_string(data, "note"),
    )


def _parse_qualifiers(raw: object) -> tuple[Qualifier, ...]:
    if raw is None:
        return ()
    raw_list = _require_list(raw, field_name="qualifiers")
    return tuple(_qualifier_from_mapping(_require_table(item)) for item in raw_list)


def _qualifier_from_mapping(data: dict[str, object]) -> Qualifier:
    allowed_keys = {
        "property",
        "entity",
        "identifier",
        "text",
        "lang",
        "date",
        "coordinates",
        "sex",
        "ascription",
    }
    extra_keys = set(data) - allowed_keys
    if extra_keys:
        extras = ", ".join(sorted(extra_keys))
        msg = f"Unexpected qualifier fields: {extras}."
        raise EntityValidationError(msg)
    value_keys = [
        key
        for key in (
            "entity",
            "identifier",
            "text",
            "lang",
            "date",
            "coordinates",
            "sex",
            "ascription",
        )
        if key in data
    ]
    if len(value_keys) != 1:
        msg = "Each qualifier must define exactly one value field."
        raise EntityValidationError(msg)
    value_key = value_keys[0]
    raw_value = data[value_key]
    match value_key:
        case "entity":
            value = EntityValue(_require_raw_string(raw_value, field_name="entity"))
        case "identifier":
            identifier = _require_table(raw_value)
            value = IdentifierValue(
                Identifier(
                    scheme=_require_string(identifier, "scheme"),
                    value=_require_string(identifier, "value"),
                    note=_optional_string(identifier, "note"),
                )
            )
        case "text":
            value = TextValue(_require_raw_string(raw_value, field_name="text"))
        case "lang":
            value = LanguageTagValue(_require_raw_string(raw_value, field_name="lang"))
        case "date":
            value = DateValue(_parse_temporal_value(raw_value))
        case "coordinates":
            value = _parse_coordinate_value(raw_value)
        case "sex":
            try:
                value = SexValue(_require_raw_string(raw_value, field_name="sex"))
            except ValueError as exc:
                raise EntityValidationError(str(exc)) from exc
        case "ascription":
            try:
                value = AscriptionValue(
                    _require_raw_string(raw_value, field_name="ascription")
                )
            except ValueError as exc:
                raise EntityValidationError(str(exc)) from exc
        case _:
            raise AssertionError(value_key)
    try:
        return Qualifier(
            property=_require_string(data, "property"),
            value=value,
        )
    except ValueError as exc:
        raise EntityValidationError(str(exc)) from exc


def _parse_references(raw: object) -> tuple[Reference, ...]:
    if raw is None:
        return ()
    raw_list = _require_list(raw, field_name="refs")
    references: list[Reference] = []
    for item in raw_list:
        data = _require_table(item)
        allowed_keys = {"source", "record", "locator", "note"}
        extra_keys = set(data) - allowed_keys
        if extra_keys:
            extras = ", ".join(sorted(extra_keys))
            msg = f"Unexpected reference fields: {extras}."
            raise EntityValidationError(msg)
        references.append(
            Reference(
                source=_require_string(data, "source"),
                record=_optional_string(data, "record"),
                locator=_optional_string(data, "locator"),
                note=_optional_string(data, "note"),
            )
        )
    return tuple(references)


def _dump_statements(statements: tuple[Statement, ...]) -> list[str]:
    lines: list[str] = []
    for statement in statements:
        lines.append("[[statements]]")
        lines.append(f"property = {_quote_string(statement.property)}")
        match statement.value:
            case EntityValue(entity_id=entity_id):
                lines.append(f"entity = {_quote_string(entity_id)}")
            case IdentifierValue(identifier=identifier):
                lines.append(f"identifier = {_dump_inline_identifier(identifier)}")
            case TextValue(text=text):
                lines.append(f"text = {_quote_string(text)}")
            case LanguageTagValue(language_tag=language_tag):
                lines.append(f"lang = {_quote_string(language_tag)}")
            case DateValue(temporal=temporal):
                lines.append(f"date = {_dump_temporal_value(temporal)}")
            case CoordinateValue(latitude=latitude, longitude=longitude):
                lines.append(
                    "coordinates = "
                    f"{{ latitude = {latitude}, longitude = {longitude} }}"
                )
            case SexValue(sex=sex):
                lines.append(f"sex = {_quote_string(sex.value)}")
            case AscriptionValue(ascription=ascription):
                lines.append(f"ascription = {_quote_string(ascription.value)}")
        if statement.note is not None:
            lines.append(f"note = {_quote_string(statement.note)}")
        if statement.status is not StatementStatus.ACCEPTED:
            lines.append(f"status = {_quote_string(statement.status.value)}")
        if statement.certainty is not None:
            lines.append(f"certainty = {_quote_string(statement.certainty.value)}")
        if statement.references:
            refs = ", ".join(
                _dump_reference(reference) for reference in statement.references
            )
            lines.append(f"refs = [{refs}]")
        if statement.qualifiers:
            qualifiers = ", ".join(
                _dump_qualifier(qualifier) for qualifier in statement.qualifiers
            )
            lines.append(f"qualifiers = [{qualifiers}]")
    return lines


def _dump_identifiers(identifiers: tuple[Identifier, ...]) -> list[str]:
    lines: list[str] = []
    for identifier in identifiers:
        lines.append("[[identifiers]]")
        lines.append(f"scheme = {_quote_string(identifier.scheme)}")
        lines.append(f"value = {_quote_string(identifier.value)}")
        if identifier.note is not None:
            lines.append(f"note = {_quote_string(identifier.note)}")
    return lines


def _dump_appellations(appellations: tuple[Appellation, ...]) -> list[str]:
    lines: list[str] = []
    for appellation in appellations:
        lines.append("[[appellations]]")
        kind = getattr(appellation.kind, "value", appellation.kind)
        lines.append(f"kind = {_quote_string(kind)}")
        if appellation.value is not None:
            lines.append(f"value = {_quote_string(appellation.value)}")
        if appellation.language is not None:
            lines.append(f"language = {_quote_string(appellation.language)}")
        if appellation.script is not None:
            lines.append(f"script = {_quote_string(appellation.script)}")
        if appellation.status is not StatementStatus.ACCEPTED:
            lines.append(f"status = {_quote_string(appellation.status.value)}")
        if appellation.certainty is not None:
            lines.append(f"certainty = {_quote_string(appellation.certainty.value)}")
        if appellation.references:
            refs = ", ".join(
                _dump_reference(reference) for reference in appellation.references
            )
            lines.append(f"refs = [{refs}]")
        if appellation.parts:
            for part in appellation.parts:
                lines.append("[[appellations.parts]]")
                part_kind = getattr(part.kind, "value", part.kind)
                lines.append(f"kind = {_quote_string(part_kind)}")
                lines.append(f"value = {_quote_string(part.value)}")
        if appellation.note is not None:
            lines.append(f"note = {_quote_string(appellation.note)}")
    return lines


def _dump_reference(reference: Reference) -> str:
    parts = [f"source = {_quote_string(reference.source)}"]
    if reference.record is not None:
        parts.append(f"record = {_quote_string(reference.record)}")
    if reference.locator is not None:
        parts.append(f"locator = {_quote_string(reference.locator)}")
    if reference.note is not None:
        parts.append(f"note = {_quote_string(reference.note)}")
    return "{ " + ", ".join(parts) + " }"


def _dump_qualifier(qualifier: Qualifier) -> str:
    property_name = getattr(qualifier.property, "value", qualifier.property)
    parts = [f"property = {_quote_string(property_name)}"]
    match qualifier.value:
        case EntityValue(entity_id=entity_id):
            parts.append(f"entity = {_quote_string(entity_id)}")
        case IdentifierValue(identifier=identifier):
            parts.append(f"identifier = {_dump_inline_identifier(identifier)}")
        case TextValue(text=text):
            parts.append(f"text = {_quote_string(text)}")
        case LanguageTagValue(language_tag=language_tag):
            parts.append(f"lang = {_quote_string(language_tag)}")
        case DateValue(temporal=temporal):
            parts.append(f"date = {_dump_temporal_value(temporal)}")
        case CoordinateValue(latitude=latitude, longitude=longitude):
            parts.append(
                f"coordinates = {{ latitude = {latitude}, longitude = {longitude} }}"
            )
        case SexValue(sex=sex):
            parts.append(f"sex = {_quote_string(sex.value)}")
        case AscriptionValue(ascription=ascription):
            parts.append(f"ascription = {_quote_string(ascription.value)}")
    return "{ " + ", ".join(parts) + " }"


def _parse_temporal_value(raw: object) -> TemporalValue:
    if isinstance(raw, str):
        return TemporalValue(raw)
    data = _require_table(raw)
    allowed_keys = {"edtf", "label"}
    extra_keys = set(data) - allowed_keys
    if extra_keys:
        extras = ", ".join(sorted(extra_keys))
        msg = f"Unexpected temporal value fields: {extras}."
        raise EntityValidationError(msg)
    return TemporalValue(
        edtf=_require_string(data, "edtf"),
        label=_optional_string(data, "label"),
    )


def _parse_coordinate_value(raw: object) -> CoordinateValue:
    data = _require_table(raw)
    allowed_keys = {"latitude", "longitude"}
    extra_keys = set(data) - allowed_keys
    if extra_keys:
        extras = ", ".join(sorted(extra_keys))
        msg = f"Unexpected coordinate fields: {extras}."
        raise EntityValidationError(msg)
    try:
        return CoordinateValue(
            latitude=_require_number(data.get("latitude"), field_name="latitude"),
            longitude=_require_number(data.get("longitude"), field_name="longitude"),
        )
    except ValueError as exc:
        raise EntityValidationError(str(exc)) from exc


def _parse_statement_status(raw: object) -> StatementStatus:
    if raw is None:
        return StatementStatus.ACCEPTED
    try:
        return StatementStatus(_require_raw_string(raw, field_name="status"))
    except ValueError as exc:
        msg = f"Unknown statement status: {raw}."
        raise EntityValidationError(msg) from exc


def _parse_statement_property(raw: object) -> StatementProperty:
    try:
        return StatementProperty(_require_raw_string(raw, field_name="property"))
    except ValueError as exc:
        msg = f"Unknown statement property: {raw}."
        raise EntityValidationError(msg) from exc


def _parse_certainty(raw: object) -> Certainty | None:
    if raw is None:
        return None
    try:
        return Certainty(_require_raw_string(raw, field_name="certainty"))
    except ValueError as exc:
        msg = f"Unknown statement certainty: {raw}."
        raise EntityValidationError(msg) from exc


def _dump_temporal_value(temporal: TemporalValue) -> str:
    if temporal.label is None:
        return _quote_string(temporal.edtf)
    parts = [f"edtf = {_quote_string(temporal.edtf)}"]
    parts.append(f"label = {_quote_string(temporal.label)}")
    return "{ " + ", ".join(parts) + " }"


def _dump_inline_identifier(identifier: Identifier) -> str:
    parts = [
        f"scheme = {_quote_string(identifier.scheme)}",
        f"value = {_quote_string(identifier.value)}",
    ]
    if identifier.note is not None:
        parts.append(f"note = {_quote_string(identifier.note)}")
    return "{ " + ", ".join(parts) + " }"


def _require_table(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict):
        msg = "Expected a TOML table."
        raise EntityValidationError(msg)
    table: dict[str, object] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            msg = "Expected a TOML table with string keys."
            raise EntityValidationError(msg)
        table[key] = value
    return table


def _require_string(data: dict[str, object], key: str) -> str:
    return _require_raw_string(data.get(key), field_name=key)


def _optional_string(data: dict[str, object], key: str) -> str | None:
    try:
        return optional_string(data.get(key), field_name=key)
    except ValueError as exc:
        raise EntityValidationError(str(exc)) from exc


def _require_raw_string(raw: object, *, field_name: str) -> str:
    try:
        return require_non_empty_string(raw, field_name=field_name)
    except ValueError as exc:
        raise EntityValidationError(str(exc)) from exc


def _require_number(raw: object, *, field_name: str) -> float:
    if isinstance(raw, bool) or not isinstance(raw, int | float):
        msg = f"{field_name} must be a number."
        raise EntityValidationError(msg)
    return float(raw)


def _require_list(raw: object, *, field_name: str) -> list[object]:
    try:
        return require_list(raw, field_name=field_name)
    except ValueError as exc:
        raise EntityValidationError(str(exc)) from exc


def _quote_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
