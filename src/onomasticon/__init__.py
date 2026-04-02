"""Onomasticon application package."""

from onomasticon.app import OnomasticonApp
from onomasticon.core.entities import AnyEntity, Entity, EntityType, Organization
from onomasticon.core.statements import Reference, Statement
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
]
