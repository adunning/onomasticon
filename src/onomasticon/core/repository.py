"""TOML-backed persistence for canonical entities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from secrets import choice
import tomllib

from onomasticon.core.entities import (
    AnyEntity,
    Entity,
    EntityType,
    Expression,
    Item,
    Manifestation,
    Organization,
    Person,
    Place,
    Work,
)
from onomasticon.core.identifiers import Identifier
from onomasticon.core.local_ids import LOCAL_IDENTIFIER_LENGTH
from onomasticon.core.statements import (
    Certainty,
    DateValue,
    EntityValue,
    IdentifierValue,
    LanguageTagValue,
    Reference,
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
        return self.loads(path.read_text())

    def dumps(self, entity: AnyEntity) -> str:
        """Serialize one entity to TOML."""
        lines = [f"id = {_quote_string(entity.id)}"]
        entity_type = _entity_type_for(entity)
        if entity_type is not None:
            lines.append(f"entity_type = {_quote_string(entity_type.value)}")
        if entity.redirect is not None:
            lines.append(f"redirect = {_quote_string(entity.redirect)}")
        if entity.note is not None:
            lines.append(f"note = {_quote_string(entity.note)}")
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
        if destination.exists() and not overwrite:
            msg = f"Refusing to overwrite existing entity file: {destination}."
            raise EntityWriteError(msg)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.dumps(entity))
        return destination

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
        case Place():
            return EntityType.PLACE
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
        "entity_type",
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
    entity_type_raw = _optional_string(data, "entity_type")
    identifiers = _parse_identifiers(data.get("identifiers"))
    redirect = _optional_string(data, "redirect")
    note = _optional_string(data, "note")
    statements = _parse_statements(data.get("statements"))

    try:
        entity_type = (
            EntityType(entity_type_raw) if entity_type_raw is not None else None
        )
    except ValueError as exc:
        msg = f"Unknown entity_type: {entity_type_raw}."
        raise EntityValidationError(msg) from exc

    entity_class = _entity_class_for(entity_type)
    return entity_class(
        id=entity_id,
        identifiers=identifiers,
        statements=statements,
        redirect=redirect,
        note=note,
    )


def _entity_class_for(entity_type: EntityType | None) -> type[AnyEntity]:
    match entity_type:
        case EntityType.PERSON:
            return Person
        case EntityType.PLACE:
            return Place
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
        "refs",
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
        key for key in ("entity", "identifier", "text", "lang", "date") if key in data
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
        case _:
            raise AssertionError(value_key)
    return Statement(
        property=_require_string(data, "property"),
        value=value,
        references=_parse_references(data.get("refs")),
        status=_parse_statement_status(data.get("status")),
        certainty=_parse_certainty(data.get("certainty")),
        note=_optional_string(data, "note"),
    )


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


def _dump_reference(reference: Reference) -> str:
    parts = [f"source = {_quote_string(reference.source)}"]
    if reference.record is not None:
        parts.append(f"record = {_quote_string(reference.record)}")
    if reference.locator is not None:
        parts.append(f"locator = {_quote_string(reference.locator)}")
    if reference.note is not None:
        parts.append(f"note = {_quote_string(reference.note)}")
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


def _parse_statement_status(raw: object) -> StatementStatus:
    if raw is None:
        return StatementStatus.ACCEPTED
    try:
        return StatementStatus(_require_raw_string(raw, field_name="status"))
    except ValueError as exc:
        msg = f"Unknown statement status: {raw}."
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


def _require_list(raw: object, *, field_name: str) -> list[object]:
    try:
        return require_list(raw, field_name=field_name)
    except ValueError as exc:
        raise EntityValidationError(str(exc)) from exc


def _quote_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
