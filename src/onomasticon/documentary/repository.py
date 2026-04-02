"""Default TOML adapter for documentary units."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib

from onomasticon.core.documentary import (
    AnyDocumentaryUnit,
    Component,
    ContentItem,
    DocumentaryType,
    Holding,
)
from onomasticon.core.entities import entity_type_for_instance
from onomasticon.core.properties import (
    StatementProperty,
    allowed_target_entity_types,
)
from onomasticon.core.repository import (
    _dump_appellations,
    _dump_identifiers,
    _dump_statements,
    _entity_from_mapping,
    _optional_string,
    _parse_appellations,
    _parse_identifiers,
    _parse_statements,
    _quote_string,
    _require_string,
    _require_table,
    EntityValidationError,
    EntityWriteError,
)
from onomasticon.core.statements import EntityValue


@dataclass(slots=True, frozen=True)
class DocumentaryLayout:
    """Path policy for documentary records."""

    root: Path
    holdings_directory: str = "holdings"
    components_directory: str = "components"
    content_items_directory: str = "content-items"
    entities_directory: str = "entities"

    def holding_path(self, unit_id: str) -> Path:
        """Return the canonical path for one holding file."""
        return self.root / self.holdings_directory / f"{unit_id}.toml"

    def component_path(self, unit_id: str) -> Path:
        """Return the canonical path for one component file."""
        return self.root / self.components_directory / f"{unit_id}.toml"

    def content_item_path(self, unit_id: str) -> Path:
        """Return the canonical path for one content item file."""
        return self.root / self.content_items_directory / f"{unit_id}.toml"

    def entity_path(self, entity_id: str) -> Path:
        """Return the canonical path for one canonical entity file."""
        return self.root / self.entities_directory / f"{entity_id}.toml"


@dataclass(slots=True, frozen=True)
class DocumentaryRepository:
    """Load and serialize documentary units."""

    layout: DocumentaryLayout

    def loads(
        self, content: str, *, documentary_type: DocumentaryType
    ) -> AnyDocumentaryUnit:
        """Parse one documentary unit from TOML text."""
        try:
            data = _require_table(tomllib.loads(content))
        except tomllib.TOMLDecodeError as exc:
            msg = f"Invalid TOML {documentary_type.value} document."
            raise EntityValidationError(msg) from exc
        return _documentary_unit_from_mapping(data, documentary_type=documentary_type)

    def load(self, path: Path) -> AnyDocumentaryUnit:
        """Load one documentary unit from a TOML file."""
        documentary_type = self._documentary_type_for_path(path)
        unit = self.loads(path.read_text(), documentary_type=documentary_type)
        self.validate_references(unit)
        return unit

    def dumps(self, unit: AnyDocumentaryUnit) -> str:
        """Serialize one documentary unit to TOML."""
        lines = [f"id = {_quote_string(unit.id)}"]
        match unit:
            case Holding():
                pass
            case Component(
                holding_id=holding_id, parent_component_id=parent_component_id
            ):
                lines.append(f"holding = {_quote_string(holding_id)}")
                if parent_component_id is not None:
                    lines.append(
                        f"parent_component = {_quote_string(parent_component_id)}"
                    )
            case ContentItem(
                holding_id=holding_id,
                component_id=component_id,
                parent_content_item_id=parent_content_item_id,
            ):
                lines.append(f"holding = {_quote_string(holding_id)}")
                if component_id is not None:
                    lines.append(f"component = {_quote_string(component_id)}")
                if parent_content_item_id is not None:
                    lines.append(
                        f"parent_content_item = {_quote_string(parent_content_item_id)}"
                    )
        if unit.note is not None:
            lines.append(f"note = {_quote_string(unit.note)}")
        lines.extend(_dump_appellations(unit.appellations))
        lines.extend(_dump_identifiers(unit.identifiers))
        lines.extend(_dump_statements(unit.statements))
        return "\n".join(lines) + "\n"

    def dump(
        self,
        unit: AnyDocumentaryUnit,
        path: Path | None = None,
        *,
        overwrite: bool = False,
    ) -> Path:
        """Write one documentary unit to disk and return the path used."""
        destination = path or self._path_for_unit(unit)
        expected_name = f"{unit.id}.toml"
        if destination.name != expected_name:
            msg = f"Documentary unit {unit.id} must be written to a file named {expected_name}."
            raise EntityWriteError(msg)
        self.validate_references(unit)
        if destination.exists() and not overwrite:
            msg = f"Refusing to overwrite existing documentary file: {destination}."
            raise EntityWriteError(msg)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.dumps(unit))
        return destination

    def validate_references(self, unit: AnyDocumentaryUnit) -> None:
        """Validate repository-level relations for one documentary unit."""
        match unit:
            case Component(
                holding_id=holding_id, parent_component_id=parent_component_id
            ):
                self._require_holding_exists(unit.id, holding_id)
                if parent_component_id is not None:
                    parent = self._load_component(parent_component_id)
                    if parent.holding_id != holding_id:
                        msg = (
                            f"Component {unit.id} references parent component {parent_component_id!r} "
                            f"in a different holding."
                        )
                        raise EntityValidationError(msg)
            case ContentItem(
                holding_id=holding_id,
                component_id=component_id,
                parent_content_item_id=parent_content_item_id,
            ):
                self._require_holding_exists(unit.id, holding_id)
                if component_id is not None:
                    component = self._load_component(component_id)
                    if component.holding_id != holding_id:
                        msg = (
                            f"Content item {unit.id} references component {component_id!r} "
                            f"in a different holding."
                        )
                        raise EntityValidationError(msg)
                if parent_content_item_id is not None:
                    parent = self._load_content_item(parent_content_item_id)
                    if parent.holding_id != holding_id:
                        msg = (
                            f"Content item {unit.id} references parent content item "
                            f"{parent_content_item_id!r} in a different holding."
                        )
                        raise EntityValidationError(msg)
                    if (
                        component_id is not None
                        and parent.component_id is not None
                        and parent.component_id != component_id
                    ):
                        msg = (
                            f"Content item {unit.id} references parent content item "
                            f"{parent_content_item_id!r} in a different component."
                        )
                        raise EntityValidationError(msg)
            case Holding():
                pass
        for statement in unit.statements:
            match statement.value:
                case EntityValue(entity_id=target_id):
                    self._validate_entity_reference(unit, statement.property, target_id)
                case _:
                    continue

    def _validate_entity_reference(
        self,
        unit: AnyDocumentaryUnit,
        property_name: StatementProperty | str,
        target_id: str,
    ) -> None:
        target_path = self.layout.entity_path(target_id)
        if not target_path.exists():
            msg = (
                f"Documentary unit {unit.id} references missing entity {target_id!r} "
                f"via property {getattr(property_name, 'value', property_name)!r}."
            )
            raise EntityValidationError(msg)
        target_entity = _entity_from_mapping(
            _require_table(tomllib.loads(target_path.read_text()))
        )
        allowed_types = allowed_target_entity_types(property_name)
        if allowed_types is None:
            return
        target_type = entity_type_for_instance(target_entity)
        target_type_value = getattr(target_type, "value", None)
        if target_type_value not in allowed_types:
            allowed = ", ".join(sorted(allowed_types))
            actual = target_type_value or "untyped"
            msg = (
                f"Property {getattr(property_name, 'value', property_name)!r} on documentary unit {unit.id} "
                f"must point to one of [{allowed}], not {actual!r}."
            )
            raise EntityValidationError(msg)

    def _documentary_type_for_path(self, path: Path) -> DocumentaryType:
        directory = path.parent.name
        if directory == self.layout.holdings_directory:
            return DocumentaryType.HOLDING
        if directory == self.layout.components_directory:
            return DocumentaryType.COMPONENT
        if directory == self.layout.content_items_directory:
            return DocumentaryType.CONTENT_ITEM
        msg = f"Cannot infer documentary type from path: {path}."
        raise EntityValidationError(msg)

    def _path_for_unit(self, unit: AnyDocumentaryUnit) -> Path:
        match unit:
            case Holding(id=unit_id):
                return self.layout.holding_path(unit_id)
            case Component(id=unit_id):
                return self.layout.component_path(unit_id)
            case ContentItem(id=unit_id):
                return self.layout.content_item_path(unit_id)

    def _require_holding_exists(self, unit_id: str, holding_id: str) -> None:
        if not self.layout.holding_path(holding_id).exists():
            msg = (
                f"Documentary unit {unit_id} references missing holding {holding_id!r}."
            )
            raise EntityValidationError(msg)

    def _load_component(self, component_id: str) -> Component:
        path = self.layout.component_path(component_id)
        if not path.exists():
            msg = f"Missing component {component_id!r}."
            raise EntityValidationError(msg)
        component = self.loads(
            path.read_text(), documentary_type=DocumentaryType.COMPONENT
        )
        assert isinstance(component, Component)
        return component

    def _load_content_item(self, content_item_id: str) -> ContentItem:
        path = self.layout.content_item_path(content_item_id)
        if not path.exists():
            msg = f"Missing content item {content_item_id!r}."
            raise EntityValidationError(msg)
        content_item = self.loads(
            path.read_text(),
            documentary_type=DocumentaryType.CONTENT_ITEM,
        )
        assert isinstance(content_item, ContentItem)
        return content_item


def _documentary_unit_from_mapping(
    data: dict[str, object],
    *,
    documentary_type: DocumentaryType,
) -> AnyDocumentaryUnit:
    match documentary_type:
        case DocumentaryType.HOLDING:
            return _holding_from_mapping(data)
        case DocumentaryType.COMPONENT:
            return _component_from_mapping(data)
        case DocumentaryType.CONTENT_ITEM:
            return _content_item_from_mapping(data)


def _holding_from_mapping(data: dict[str, object]) -> Holding:
    allowed_keys = {"id", "appellations", "identifiers", "statements", "note"}
    _validate_keys(data, allowed_keys, label="holding")
    return Holding(
        id=_require_string(data, "id"),
        appellations=_parse_appellations(data.get("appellations")),
        identifiers=_parse_identifiers(data.get("identifiers")),
        statements=_parse_statements(data.get("statements")),
        note=_optional_string(data, "note"),
    )


def _component_from_mapping(data: dict[str, object]) -> Component:
    allowed_keys = {
        "id",
        "holding",
        "parent_component",
        "appellations",
        "identifiers",
        "statements",
        "note",
    }
    _validate_keys(data, allowed_keys, label="component")
    return Component(
        id=_require_string(data, "id"),
        holding_id=_require_string(data, "holding"),
        parent_component_id=_optional_string(data, "parent_component"),
        appellations=_parse_appellations(data.get("appellations")),
        identifiers=_parse_identifiers(data.get("identifiers")),
        statements=_parse_statements(data.get("statements")),
        note=_optional_string(data, "note"),
    )


def _content_item_from_mapping(data: dict[str, object]) -> ContentItem:
    allowed_keys = {
        "id",
        "holding",
        "component",
        "parent_content_item",
        "appellations",
        "identifiers",
        "statements",
        "note",
    }
    _validate_keys(data, allowed_keys, label="content item")
    return ContentItem(
        id=_require_string(data, "id"),
        holding_id=_require_string(data, "holding"),
        component_id=_optional_string(data, "component"),
        parent_content_item_id=_optional_string(data, "parent_content_item"),
        appellations=_parse_appellations(data.get("appellations")),
        identifiers=_parse_identifiers(data.get("identifiers")),
        statements=_parse_statements(data.get("statements")),
        note=_optional_string(data, "note"),
    )


def _validate_keys(
    data: dict[str, object], allowed_keys: set[str], *, label: str
) -> None:
    extra_keys = set(data) - allowed_keys
    if extra_keys:
        extras = ", ".join(sorted(extra_keys))
        msg = f"Unexpected {label} fields: {extras}."
        raise EntityValidationError(msg)
