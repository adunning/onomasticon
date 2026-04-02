"""Onomasticon application package."""

from onomasticon.app import OnomasticonApp
from onomasticon.core.appellations import Appellation, AppellationKind
from onomasticon.core.entities import (
    AnyEntity,
    Entity,
    EntityType,
    Organization,
    OrganizationSubtype,
    PlaceSubtype,
)
from onomasticon.core.properties import (
    StatementProperty,
    property_allowed_for_entity_type,
)
from onomasticon.core.statements import (
    Certainty,
    Reference,
    Sex,
    Statement,
    StatementStatus,
)
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
    "Appellation",
    "AppellationKind",
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
    "OrganizationSubtype",
    "PlaceSubtype",
    "Reference",
    "RepositoryError",
    "RepositoryLayout",
    "Sex",
    "Statement",
    "StatementProperty",
    "StatementStatus",
    "TemporalValue",
    "property_allowed_for_entity_type",
]
