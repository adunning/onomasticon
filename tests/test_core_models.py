from __future__ import annotations

from onomasticon.core import (
    Appellation,
    AppellationKind,
    AnyEntity,
    AnyDocumentaryUnit,
    Certainty,
    Component,
    ContentItem,
    DocumentaryType,
    Entity,
    EntityRepository,
    Identifier,
    EntityValidationError,
    EntityWriteError,
    Holding,
    IdentifierCollisionError,
    Organization,
    OrganizationSubtype,
    PlaceSubtype,
    RepositoryLayout,
    Sex,
    StatementProperty,
    StatementStatus,
    TemporalValue,
    property_allowed_for_documentary_type,
    property_allowed_for_entity_type,
)


def test_core_exports_minimal_entity_baseline() -> None:
    assert AnyEntity is not None
    assert AnyDocumentaryUnit is not None
    assert Appellation is not None
    assert AppellationKind is not None
    assert Certainty is not None
    assert Component is not None
    assert ContentItem is not None
    assert DocumentaryType is not None
    assert Entity is not None
    assert EntityRepository is not None
    assert Identifier is not None
    assert EntityValidationError is not None
    assert EntityWriteError is not None
    assert Holding is not None
    assert IdentifierCollisionError is not None
    assert Organization is not None
    assert OrganizationSubtype is not None
    assert PlaceSubtype is not None
    assert RepositoryLayout is not None
    assert Sex is not None
    assert StatementProperty is not None
    assert StatementStatus is not None
    assert TemporalValue is not None
    assert property_allowed_for_documentary_type is not None
    assert property_allowed_for_entity_type is not None
