"""Application wiring for Onomasticon.

The application shell binds the canonical scholarly model to concrete storage
adapters. The default deployment uses Git-backed TOML stores, but the core can
equally be projected through other carriers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from onomasticon.core.ports import DocumentaryStore, EntityStore, SourceRecordStore
from onomasticon.core.repository import EntityRepository, RepositoryLayout
from onomasticon.documentary import DocumentaryLayout, DocumentaryRepository
from onomasticon.sources import SourceLayout, SourceRecordRepository


@dataclass(slots=True, frozen=True)
class OnomasticonApp:
    """Thin application shell around the configured scholarly stores."""

    entity_store: EntityStore
    documentary_store: DocumentaryStore
    source_record_store: SourceRecordStore

    @property
    def repository(self) -> EntityStore:
        """Return the canonical entity store.

        This compatibility alias preserves the older application surface while
        the wider store-based API settles.
        """

        return self.entity_store

    @classmethod
    def from_root(cls, root: Path) -> "OnomasticonApp":
        """Build an application instance for the default Git-backed TOML stores."""
        entity_layout = RepositoryLayout(root=root)
        documentary_layout = DocumentaryLayout(root=root)
        source_layout = SourceLayout(root=root)
        return cls(
            entity_store=EntityRepository(layout=entity_layout),
            documentary_store=DocumentaryRepository(layout=documentary_layout),
            source_record_store=SourceRecordRepository(layout=source_layout),
        )
