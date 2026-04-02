"""Shared temporal models."""

from __future__ import annotations

from dataclasses import dataclass

from edtf import parse_edtf
from edtf.parser.edtf_exceptions import EDTFParseException

from onomasticon.core.validation import optional_string, require_non_empty_string


@dataclass(slots=True, frozen=True)
class TemporalValue:
    """An ISO 8601 / EDTF temporal value."""

    edtf: str
    label: str | None = None

    def __post_init__(self) -> None:
        edtf = require_non_empty_string(self.edtf, field_name="edtf")
        try:
            parse_edtf(edtf)
        except EDTFParseException as exc:
            msg = f"edtf must be a valid EDTF string: {edtf!r}."
            raise ValueError(msg) from exc
        if self.label is not None:
            optional_string(self.label, field_name="label")
