"""Documentary models for source-facing physical and descriptive units."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from onomasticon.core.appellations import Appellation
from onomasticon.core.identifiers import Identifier
from onomasticon.core.local_ids import validate_local_identifier
from onomasticon.core.properties import property_allowed_for_documentary_type
from onomasticon.core.statements import Statement


class DocumentaryType(StrEnum):
    """Known documentary unit types."""

    HOLDING = "holding"
    COMPONENT = "component"
    CONTENT_ITEM = "content_item"


@dataclass(slots=True, frozen=True)
class Holding:
    """A deliverable physical library unit such as a manuscript volume."""

    id: str
    appellations: tuple[Appellation, ...] = field(default_factory=tuple)
    identifiers: tuple[Identifier, ...] = field(default_factory=tuple)
    statements: tuple[Statement, ...] = field(default_factory=tuple)
    note: str | None = None

    def __post_init__(self) -> None:
        validate_local_identifier(self.id, field_name="id")
        for statement in self.statements:
            if not property_allowed_for_documentary_type(
                statement.property, DocumentaryType.HOLDING
            ):
                property_name = getattr(statement.property, "value", statement.property)
                msg = (
                    f"Property {property_name!r} is not allowed on "
                    f"{DocumentaryType.HOLDING.value} records."
                )
                raise ValueError(msg)


@dataclass(slots=True, frozen=True)
class Component:
    """A physical sub-unit within one holding."""

    id: str
    holding_id: str
    parent_component_id: str | None = None
    appellations: tuple[Appellation, ...] = field(default_factory=tuple)
    identifiers: tuple[Identifier, ...] = field(default_factory=tuple)
    statements: tuple[Statement, ...] = field(default_factory=tuple)
    note: str | None = None

    def __post_init__(self) -> None:
        validate_local_identifier(self.id, field_name="id")
        validate_local_identifier(self.holding_id, field_name="holding_id")
        if self.parent_component_id is not None:
            validate_local_identifier(
                self.parent_component_id,
                field_name="parent_component_id",
            )
            if self.parent_component_id == self.id:
                msg = "A component cannot parent itself."
                raise ValueError(msg)
        for statement in self.statements:
            if not property_allowed_for_documentary_type(
                statement.property, DocumentaryType.COMPONENT
            ):
                property_name = getattr(statement.property, "value", statement.property)
                msg = (
                    f"Property {property_name!r} is not allowed on "
                    f"{DocumentaryType.COMPONENT.value} records."
                )
                raise ValueError(msg)


@dataclass(slots=True, frozen=True)
class ContentItem:
    """A descriptive content unit located within a holding or component."""

    id: str
    holding_id: str
    component_id: str | None = None
    parent_content_item_id: str | None = None
    appellations: tuple[Appellation, ...] = field(default_factory=tuple)
    identifiers: tuple[Identifier, ...] = field(default_factory=tuple)
    statements: tuple[Statement, ...] = field(default_factory=tuple)
    note: str | None = None

    def __post_init__(self) -> None:
        validate_local_identifier(self.id, field_name="id")
        validate_local_identifier(self.holding_id, field_name="holding_id")
        if self.component_id is not None:
            validate_local_identifier(self.component_id, field_name="component_id")
        if self.parent_content_item_id is not None:
            validate_local_identifier(
                self.parent_content_item_id,
                field_name="parent_content_item_id",
            )
            if self.parent_content_item_id == self.id:
                msg = "A content item cannot parent itself."
                raise ValueError(msg)
        for statement in self.statements:
            if not property_allowed_for_documentary_type(
                statement.property, DocumentaryType.CONTENT_ITEM
            ):
                property_name = getattr(statement.property, "value", statement.property)
                msg = (
                    f"Property {property_name!r} is not allowed on "
                    f"{DocumentaryType.CONTENT_ITEM.value} records."
                )
                raise ValueError(msg)


type AnyDocumentaryUnit = Holding | Component | ContentItem


def documentary_type_for_unit(unit: AnyDocumentaryUnit) -> DocumentaryType:
    """Return the documentary type implied by one unit instance."""
    match unit:
        case Holding():
            return DocumentaryType.HOLDING
        case Component():
            return DocumentaryType.COMPONENT
        case ContentItem():
            return DocumentaryType.CONTENT_ITEM
