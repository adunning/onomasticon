"""Shared identifier models."""

from __future__ import annotations

from dataclasses import dataclass

from onomasticon.core.validation import require_non_empty_string


@dataclass(slots=True, frozen=True)
class Identifier:
    """An identifier expressed within a named scheme."""

    scheme: str
    value: str
    note: str | None = None

    def __post_init__(self) -> None:
        require_non_empty_string(self.scheme, field_name="scheme")
        require_non_empty_string(self.value, field_name="value")
