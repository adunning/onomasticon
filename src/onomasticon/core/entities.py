"""Canonical entity models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

LOCAL_IDENTIFIER_LENGTH = 6


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
    redirect: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        _validate_identifier(self.id, field_name="id")
        if self.redirect is not None:
            _validate_identifier(self.redirect, field_name="redirect")
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


def _validate_identifier(value: str, *, field_name: str) -> None:
    if len(value) != LOCAL_IDENTIFIER_LENGTH:
        msg = f"{field_name} must be exactly {LOCAL_IDENTIFIER_LENGTH} characters long."
        raise ValueError(msg)
    if not value.isascii() or not value.isalnum() or value.lower() != value:
        msg = f"{field_name} must contain only lowercase ASCII letters and digits."
        raise ValueError(msg)
