"""Source-side normalized records."""

from __future__ import annotations

from dataclasses import dataclass, field

from onomasticon.core.entities import EntityType
from onomasticon.core.statements import Statement


@dataclass(slots=True, frozen=True)
class SourceRecord:
    """A normalized record imported from one external or local source."""

    source: str
    record_id: str
    entity_type: EntityType | None = None
    statements: tuple[Statement, ...] = field(default_factory=tuple)
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.source.strip():
            msg = "source must be a non-empty string."
            raise ValueError(msg)
        if not self.record_id.strip():
            msg = "record_id must be a non-empty string."
            raise ValueError(msg)
