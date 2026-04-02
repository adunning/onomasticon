"""Shared appellation and designation models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from langcodes import Language

from onomasticon.core.statements import Certainty, Reference, StatementStatus
from onomasticon.core.validation import optional_string, require_non_empty_string


class AppellationKind(StrEnum):
    """Controlled appellation kinds."""

    PREFERRED = "preferred"
    VARIANT = "variant"
    ATTESTED = "attested"
    TITLE = "title"
    INCIPIT = "incipit"
    EXPLICIT = "explicit"
    DESCRIPTIVE = "descriptive"
    EDITORIAL = "editorial"
    SHORT = "short"


class AppellationPartKind(StrEnum):
    """Controlled appellation part kinds."""

    GIVEN = "given"
    FAMILY = "family"
    BYNAME = "byname"
    EPITHET = "epithet"
    LOCATIVE = "locative"
    PATRONYMIC = "patronymic"
    ORDINAL = "ordinal"
    HONORIFIC = "honorific"


@dataclass(slots=True, frozen=True)
class AppellationPart:
    """One structured part within an appellation."""

    kind: AppellationPartKind | str
    value: str

    def __post_init__(self) -> None:
        kind_value = require_non_empty_string(self.kind, field_name="kind")
        try:
            normalized_kind = AppellationPartKind(kind_value)
        except ValueError as exc:
            msg = f"Unknown appellation part kind: {kind_value}."
            raise ValueError(msg) from exc
        object.__setattr__(self, "kind", normalized_kind)
        require_non_empty_string(self.value, field_name="value")


@dataclass(slots=True, frozen=True)
class Appellation:
    """A provenance-bearing designation by which an entity is identified."""

    kind: AppellationKind | str
    parts: tuple[AppellationPart, ...] = field(default_factory=tuple)
    display_value: str | None = None
    language: str | None = None
    script: str | None = None
    references: tuple[Reference, ...] = field(default_factory=tuple)
    status: StatementStatus = StatementStatus.ACCEPTED
    certainty: Certainty | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        kind_value = require_non_empty_string(self.kind, field_name="kind")
        try:
            normalized_kind = AppellationKind(kind_value)
        except ValueError as exc:
            msg = f"Unknown appellation kind: {kind_value}."
            raise ValueError(msg) from exc
        object.__setattr__(self, "kind", normalized_kind)

        if not self.parts and self.display_value is None:
            msg = "appellation must define either parts or display_value."
            raise ValueError(msg)
        if self.display_value is not None:
            optional_string(self.display_value, field_name="display_value")

        if self.language is not None:
            language_value = require_non_empty_string(
                self.language,
                field_name="language",
            )
            parsed = Language.get(language_value)
            if not parsed.is_valid():
                msg = (
                    f"language must be a valid BCP 47 language tag: {language_value!r}."
                )
                raise ValueError(msg)
            object.__setattr__(self, "language", str(parsed))

        if self.script is not None:
            optional_string(self.script, field_name="script")
        if self.note is not None:
            optional_string(self.note, field_name="note")
