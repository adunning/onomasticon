from __future__ import annotations

from onomasticon.core import (
    AnyEntity,
    Entity,
    EntityRepository,
    EntityValidationError,
    EntityWriteError,
    IdentifierCollisionError,
    Organization,
    RepositoryLayout,
)


def test_core_exports_minimal_entity_baseline() -> None:
    assert AnyEntity is not None
    assert Entity is not None
    assert EntityRepository is not None
    assert EntityValidationError is not None
    assert EntityWriteError is not None
    assert IdentifierCollisionError is not None
    assert Organization is not None
    assert RepositoryLayout is not None
