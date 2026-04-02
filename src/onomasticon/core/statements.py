"""Shared scholarly statement models."""

from __future__ import annotations

from dataclasses import dataclass, field

from langcodes import Language

from onomasticon.core.identifiers import Identifier
from onomasticon.core.local_ids import validate_local_identifier
from onomasticon.core.temporal import TemporalValue
from onomasticon.core.validation import require_non_empty_string


@dataclass(slots=True, frozen=True)
class Reference:
    """A normalized provenance reference for one statement."""

    source: str
    record: str | None = None
    locator: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        require_non_empty_string(self.source, field_name="source")
        if self.record is not None:
            require_non_empty_string(self.record, field_name="record")
        if self.locator is not None:
            require_non_empty_string(self.locator, field_name="locator")
        if self.record is None and self.locator is None:
            msg = "reference must define at least one of record or locator."
            raise ValueError(msg)


@dataclass(slots=True, frozen=True)
class EntityValue:
    """A statement value pointing to a local entity identifier."""

    entity_id: str

    def __post_init__(self) -> None:
        validate_local_identifier(self.entity_id, field_name="entity_id")


@dataclass(slots=True, frozen=True)
class IdentifierValue:
    """A statement value carrying an external identifier."""

    identifier: Identifier


@dataclass(slots=True, frozen=True)
class TextValue:
    """A statement value carrying plain text."""

    text: str

    def __post_init__(self) -> None:
        require_non_empty_string(self.text, field_name="text")


@dataclass(slots=True, frozen=True)
class LanguageTagValue:
    """A statement value carrying an IETF language tag."""

    language_tag: str

    def __post_init__(self) -> None:
        language_tag = require_non_empty_string(
            self.language_tag,
            field_name="language_tag",
        )
        parsed = Language.get(language_tag)
        if not parsed.is_valid():
            msg = f"language_tag must be a valid BCP 47 language tag: {language_tag!r}."
            raise ValueError(msg)
        object.__setattr__(self, "language_tag", str(parsed))

    def label(self, *, display_language: str = "en") -> str:
        """Return a human-readable label for the normalized tag."""
        return Language.get(self.language_tag).display_name(display_language)


@dataclass(slots=True, frozen=True)
class DateValue:
    """A statement value carrying an EDTF-compatible temporal value."""

    temporal: TemporalValue


type StatementValue = (
    EntityValue | IdentifierValue | TextValue | LanguageTagValue | DateValue
)


@dataclass(slots=True, frozen=True)
class Statement:
    """One normalized scholarly statement."""

    property: str
    value: StatementValue
    references: tuple[Reference, ...] = field(default_factory=tuple)
    note: str | None = None

    def __post_init__(self) -> None:
        require_non_empty_string(self.property, field_name="property")
