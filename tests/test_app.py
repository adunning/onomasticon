from __future__ import annotations

from pathlib import Path

from onomasticon.app import OnomasticonApp
from onomasticon.core.ports import DocumentaryStore, EntityStore, SourceRecordStore
from onomasticon.core.repository import EntityRepository
from onomasticon.documentary import DocumentaryRepository
from onomasticon.sources import SourceRecordRepository


def test_app_builds_default_stores_from_root() -> None:
    app = OnomasticonApp.from_root(Path("/repo"))

    assert isinstance(app.entity_store, EntityStore)
    assert isinstance(app.documentary_store, DocumentaryStore)
    assert isinstance(app.source_record_store, SourceRecordStore)
    assert isinstance(app.entity_store, EntityRepository)
    assert isinstance(app.documentary_store, DocumentaryRepository)
    assert isinstance(app.source_record_store, SourceRecordRepository)
    assert app.entity_store.layout.root == Path("/repo")
    assert app.entity_store.layout.entities_directory == "entities"
    assert app.documentary_store.layout.root == Path("/repo")
    assert app.source_record_store.layout.root == Path("/repo")


def test_app_repository_alias_exposes_entity_store() -> None:
    app = OnomasticonApp.from_root(Path("/repo"))

    assert app.repository is app.entity_store
