from __future__ import annotations

from pathlib import Path

from onomasticon.core.ports import DocumentaryStore, EntityStore, SourceRecordStore
from onomasticon.core.repository import EntityRepository, RepositoryLayout
from onomasticon.documentary import DocumentaryLayout, DocumentaryRepository
from onomasticon.sources import SourceLayout, SourceRecordRepository


def test_entity_repository_implements_entity_store_protocol() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))

    assert isinstance(repository, EntityStore)


def test_documentary_repository_implements_documentary_store_protocol() -> None:
    repository = DocumentaryRepository(layout=DocumentaryLayout(root=Path("/repo")))

    assert isinstance(repository, DocumentaryStore)


def test_source_record_repository_implements_source_record_store_protocol() -> None:
    repository = SourceRecordRepository(layout=SourceLayout(root=Path("/repo")))

    assert isinstance(repository, SourceRecordStore)
