"""Onomasticon application package."""

from onomasticon.app import OnomasticonApp
from onomasticon.core.appellations import Appellation, AppellationKind
from onomasticon.core.documentary import (
    Component,
    ContentItem,
    DocumentaryType,
    Holding,
)
from onomasticon.core.entities import (
    AnyEntity,
    Entity,
    EntityType,
    Organization,
    OrganizationSubtype,
    PlaceSubtype,
)
from onomasticon.core.ports import (
    DocumentaryStore,
    EntityStore,
    SourceRecordStore,
)
from onomasticon.core.reconciliation import (
    ExternalAuthorityTarget,
    LocalEntityTarget,
    Mention,
    ResolutionStatus,
)
from onomasticon.core.properties import (
    StatementProperty,
    property_allowed_for_documentary_type,
    property_allowed_for_entity_type,
)
from onomasticon.core.statements import (
    Ascription,
    Certainty,
    Qualifier,
    QualifierProperty,
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
from onomasticon.documentary import DocumentaryLayout, DocumentaryRepository

__all__ = [
    "Appellation",
    "AppellationKind",
    "AnyEntity",
    "Certainty",
    "Component",
    "ContentItem",
    "DocumentaryLayout",
    "DocumentaryRepository",
    "DocumentaryType",
    "DocumentaryStore",
    "Entity",
    "EntityRepository",
    "EntityStore",
    "EntityValidationError",
    "EntityWriteError",
    "EntityType",
    "IdentifierCollisionError",
    "Holding",
    "OnomasticonApp",
    "Organization",
    "OrganizationSubtype",
    "PlaceSubtype",
    "Mention",
    "Ascription",
    "ExternalAuthorityTarget",
    "LocalEntityTarget",
    "Qualifier",
    "QualifierProperty",
    "Reference",
    "RepositoryError",
    "RepositoryLayout",
    "ResolutionStatus",
    "Sex",
    "SourceRecordStore",
    "Statement",
    "StatementProperty",
    "StatementStatus",
    "TemporalValue",
    "property_allowed_for_documentary_type",
    "property_allowed_for_entity_type",
]
