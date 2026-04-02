"""Canonical entity models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from onomasticon.core.local_ids import validate_local_identifier
from onomasticon.core.statements import Statement


class EntityType(StrEnum):
    """Known first-class entity types."""

    PERSON = "person"
    PLACE = "place"
    ORGANIZATION = "organization"
    WORK = "work"
    EXPRESSION = "expression"
    MANIFESTATION = "manifestation"
    ITEM = "item"


@dataclass(slots=True, frozen=True)
class Entity:
    """Minimal canonical entity.

    The only universal requirement is a stable local identifier. Everything else
    remains optional at this stage so the repository can hold sparse entities and
    simple redirects without forcing premature structure.
    """

    id: str
    statements: tuple[Statement, ...] = field(default_factory=tuple)
    redirect: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        validate_local_identifier(self.id, field_name="id")
        if self.redirect is not None:
            validate_local_identifier(self.redirect, field_name="redirect")
            if self.redirect == self.id:
                msg = "An entity cannot redirect to itself."
                raise ValueError(msg)

    @property
    def is_redirect(self) -> bool:
        """Return whether this entity simply redirects to another entity."""
        return self.redirect is not None


@dataclass(slots=True, frozen=True)
class Person(Entity):
    """Person entity."""


@dataclass(slots=True, frozen=True)
class Place(Entity):
    """Place entity."""


@dataclass(slots=True, frozen=True)
class Organization(Entity):
    """Organization entity."""


@dataclass(slots=True, frozen=True)
class Work(Entity):
    """Work entity."""


@dataclass(slots=True, frozen=True)
class Expression(Entity):
    """Expression entity."""


@dataclass(slots=True, frozen=True)
class Manifestation(Entity):
    """Manifestation entity."""


@dataclass(slots=True, frozen=True)
class Item(Entity):
    """Item entity."""


type AnyEntity = (
    Entity | Person | Place | Organization | Work | Expression | Manifestation | Item
)
