"""Shared local identifier rules."""

from __future__ import annotations

LOCAL_IDENTIFIER_LENGTH = 6


def validate_local_identifier(value: str, *, field_name: str) -> None:
    """Validate one opaque local identifier."""
    if len(value) != LOCAL_IDENTIFIER_LENGTH:
        msg = f"{field_name} must be exactly {LOCAL_IDENTIFIER_LENGTH} characters long."
        raise ValueError(msg)
    if not value.isascii() or not value.isalnum() or value.lower() != value:
        msg = f"{field_name} must contain only lowercase ASCII letters and digits."
        raise ValueError(msg)
