"""Onomasticon application package."""

from onomasticon.app import OnomasticonApp
from onomasticon.core.entities import AnyEntity, Entity, EntityType, Organization
from onomasticon.core.properties import (
    StatementProperty,
    property_allowed_for_entity_type,
)
from onomasticon.core.statements import Certainty, Reference, Statement, StatementStatus
from onomasticon.core.temporal import TemporalValue
from onomasticon.core.repository import (
    EntityRepository,
    EntityValidationError,
    EntityWriteError,
    IdentifierCollisionError,
    RepositoryError,
    RepositoryLayout,
)

__all__ = [
    "AnyEntity",
    "Certainty",
    "Entity",
    "EntityRepository",
    "EntityValidationError",
    "EntityWriteError",
    "EntityType",
    "IdentifierCollisionError",
    "OnomasticonApp",
    "Organization",
    "Reference",
    "RepositoryError",
    "RepositoryLayout",
    "Statement",
    "StatementProperty",
    "StatementStatus",
    "TemporalValue",
    "property_allowed_for_entity_type",
]
