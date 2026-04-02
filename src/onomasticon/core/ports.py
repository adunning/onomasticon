"""Format-agnostic ports for storage and serialisation adapters.

These protocols define the stable boundary between the scholarly core model and
specific carriers such as TOML, JSON, TEI, or another persistence layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from onomasticon.core.documentary import AnyDocumentaryUnit, DocumentaryType
from onomasticon.core.entities import AnyEntity
from onomasticon.sources.records import SourceRecord


@runtime_checkable
class EntityCodec(Protocol):
    """Serialise canonical entities to and from one carrier format."""

    def loads(self, content: str) -> AnyEntity:
        """Parse one canonical entity from text."""

    def dumps(self, entity: AnyEntity) -> str:
        """Serialise one canonical entity to text."""


@runtime_checkable
class EntityStore(EntityCodec, Protocol):
    """Read, write, and validate canonical entities in one backing store."""

    def load(self, path: Path) -> AnyEntity:
        """Load one canonical entity from the backing store."""

    def dump(
        self,
        entity: AnyEntity,
        path: Path | None = None,
        *,
        overwrite: bool = False,
    ) -> Path:
        """Write one canonical entity to the backing store."""

    def validate_cross_entity_references(self, entity: AnyEntity) -> None:
        """Validate repository-level entity references for one entity."""

    def mint_id(self, *, max_attempts: int = 64) -> str:
        """Mint one unused local identifier."""


@runtime_checkable
class DocumentaryCodec(Protocol):
    """Serialise documentary units to and from one carrier format."""

    def loads(
        self, content: str, *, documentary_type: DocumentaryType
    ) -> AnyDocumentaryUnit:
        """Parse one documentary unit from text."""

    def dumps(self, unit: AnyDocumentaryUnit) -> str:
        """Serialise one documentary unit to text."""


@runtime_checkable
class DocumentaryStore(DocumentaryCodec, Protocol):
    """Read, write, and validate documentary units in one backing store."""

    def load(self, path: Path) -> AnyDocumentaryUnit:
        """Load one documentary unit from the backing store."""

    def dump(
        self,
        unit: AnyDocumentaryUnit,
        path: Path | None = None,
        *,
        overwrite: bool = False,
    ) -> Path:
        """Write one documentary unit to the backing store."""

    def validate_references(self, unit: AnyDocumentaryUnit) -> None:
        """Validate repository-level relations for one documentary unit."""


@runtime_checkable
class SourceRecordCodec(Protocol):
    """Serialise normalized source records to and from one carrier format."""

    def loads(self, content: str) -> SourceRecord:
        """Parse one normalized source record from text."""

    def dumps(self, record: SourceRecord) -> str:
        """Serialise one normalized source record to text."""


@runtime_checkable
class SourceRecordStore(SourceRecordCodec, Protocol):
    """Read and write normalized source records in one backing store."""

    def load(self, path: Path) -> SourceRecord:
        """Load one normalized source record from the backing store."""

    def dump(
        self,
        record: SourceRecord,
        path: Path | None = None,
        *,
        overwrite: bool = False,
    ) -> Path:
        """Write one normalized source record to the backing store."""
