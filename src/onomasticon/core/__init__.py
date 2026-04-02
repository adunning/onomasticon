"""Canonical core models for Onomasticon."""

from onomasticon.core.entities import (
    AnyEntity,
    Entity,
    EntityType,
    Expression,
    Item,
    Manifestation,
    Organization,
    Person,
    Place,
    Work,
)
from onomasticon.core.identifiers import Identifier
from onomasticon.core.local_ids import (
    LOCAL_IDENTIFIER_LENGTH,
    validate_local_identifier,
)
from onomasticon.core.repository import EntityRepository, RepositoryLayout
from onomasticon.core.repository import (
    EntityValidationError,
    EntityWriteError,
    IdentifierCollisionError,
    RepositoryError,
)
from onomasticon.core.statements import (
    DateValue,
    EntityValue,
    IdentifierValue,
    LanguageTagValue,
    Reference,
    Statement,
    StatementValue,
    TextValue,
)

__all__ = [
    "AnyEntity",
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
    "Person",
    "Place",
    "Reference",
    "RepositoryError",
    "RepositoryLayout",
    "Statement",
    "StatementValue",
    "TextValue",
    "Work",
    "validate_local_identifier",
]
