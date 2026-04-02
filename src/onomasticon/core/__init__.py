"""Canonical core models for Onomasticon."""

from onomasticon.core.entities import (
    AnyEntity,
    Entity,
    EntityType,
    Expression,
    Item,
    Manifestation,
    Organization,
    OrganizationSubtype,
    Person,
    Place,
    PlaceSubtype,
    Work,
)
from onomasticon.core.identifiers import Identifier
from onomasticon.core.local_ids import (
    LOCAL_IDENTIFIER_LENGTH,
    validate_local_identifier,
)
from onomasticon.core.properties import (
    StatementProperty,
    property_allowed_for_entity_type,
)
from onomasticon.core.repository import EntityRepository, RepositoryLayout
from onomasticon.core.repository import (
    EntityValidationError,
    EntityWriteError,
    IdentifierCollisionError,
    RepositoryError,
)
from onomasticon.core.statements import (
    Certainty,
    DateValue,
    EntityValue,
    IdentifierValue,
    LanguageTagValue,
    Reference,
    Sex,
    SexValue,
    Statement,
    StatementStatus,
    StatementValue,
    TextValue,
)
from onomasticon.core.temporal import TemporalValue

__all__ = [
    "AnyEntity",
    "Certainty",
    "DateValue",
    "Entity",
    "EntityRepository",
    "EntityValue",
    "EntityValidationError",
    "EntityWriteError",
    "EntityType",
    "Expression",
    "IdentifierValue",
    "Identifier",
    "IdentifierCollisionError",
    "Item",
    "LanguageTagValue",
    "LOCAL_IDENTIFIER_LENGTH",
    "Manifestation",
    "Organization",
    "OrganizationSubtype",
    "Person",
    "Place",
    "PlaceSubtype",
    "Reference",
    "RepositoryError",
    "RepositoryLayout",
    "Sex",
    "SexValue",
    "Statement",
    "StatementProperty",
    "StatementStatus",
    "StatementValue",
    "TemporalValue",
    "TextValue",
    "Work",
    "property_allowed_for_entity_type",
    "validate_local_identifier",
]
