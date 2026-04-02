"""Shared scholarly statement models."""

from __future__ import annotations

from dataclasses import dataclass, field

from onomasticon.core.local_ids import validate_local_identifier


@dataclass(slots=True, frozen=True)
class Reference:
    """A normalized provenance reference for one statement."""

    source: str
    record: str | None = None
    locator: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.source.strip():
            msg = "source must be a non-empty string."
            raise ValueError(msg)
        if self.record is not None and not self.record.strip():
            msg = "record must be a non-empty string when present."
            raise ValueError(msg)
        if self.locator is not None and not self.locator.strip():
            msg = "locator must be a non-empty string when present."
            raise ValueError(msg)
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

    scheme: str
    value: str

    def __post_init__(self) -> None:
        if not self.scheme.strip():
            msg = "scheme must be a non-empty string."
            raise ValueError(msg)
        if not self.value.strip():
            msg = "value must be a non-empty string."
            raise ValueError(msg)


@dataclass(slots=True, frozen=True)
class TextValue:
    """A statement value carrying plain text."""

    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            msg = "text must be a non-empty string."
            raise ValueError(msg)


@dataclass(slots=True, frozen=True)
class LanguageTagValue:
    """A statement value carrying an IETF language tag."""

    language_tag: str

    def __post_init__(self) -> None:
        if not self.language_tag.strip():
            msg = "language_tag must be a non-empty string."
            raise ValueError(msg)


@dataclass(slots=True, frozen=True)
class DateValue:
    """A statement value carrying an EDTF-compatible date string."""

    edtf: str

    def __post_init__(self) -> None:
        if not self.edtf.strip():
            msg = "edtf must be a non-empty string."
            raise ValueError(msg)


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
        if not self.property.strip():
            msg = "property must be a non-empty string."
            raise ValueError(msg)
