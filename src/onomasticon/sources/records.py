"""Source-side normalized records."""

from __future__ import annotations

from dataclasses import dataclass, field

from onomasticon.core.entities import EntityType, OrganizationSubtype, PlaceSubtype
from onomasticon.core.identifiers import Identifier
from onomasticon.core.properties import property_allowed_for_entity_type
from onomasticon.core.statements import Statement
from onomasticon.core.validation import require_non_empty_string


@dataclass(slots=True, frozen=True)
class SourceRecord:
    """A normalized record imported from one external or local source."""

    source: str
    record_id: str
    entity_type: EntityType | None = None
    subtype: PlaceSubtype | OrganizationSubtype | None = None
    identifiers: tuple[Identifier, ...] = field(default_factory=tuple)
    statements: tuple[Statement, ...] = field(default_factory=tuple)
    note: str | None = None

    def __post_init__(self) -> None:
        require_non_empty_string(self.source, field_name="source")
        require_non_empty_string(self.record_id, field_name="record_id")
        if self.subtype is not None and self.entity_type not in {
            EntityType.PLACE,
            EntityType.ORGANIZATION,
            EntityType.COUNTRY,
            EntityType.RELIGIOUS_ORDER,
        }:
            msg = "Subtype is only allowed for place and organization source records."
            raise ValueError(msg)
        if self.entity_type is not None:
            for statement in self.statements:
                if not property_allowed_for_entity_type(
                    statement.property,
                    self.entity_type,
                ):
                    property_name = getattr(
                        statement.property, "value", statement.property
                    )
                    msg = (
                        f"Property {property_name!r} is not allowed on "
                        f"{self.entity_type.value} source records."
                    )
                    raise ValueError(msg)
