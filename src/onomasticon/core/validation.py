"""Shared validation helpers."""

from __future__ import annotations


def require_non_empty_string(value: object, *, field_name: str) -> str:
    """Return a validated non-empty string."""
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string."
        raise ValueError(msg)
    return value


def optional_string(value: object, *, field_name: str) -> str | None:
    """Return a validated optional string."""
    if value is None:
        return None
    if not isinstance(value, str):
        msg = f"{field_name} must be a string."
        raise ValueError(msg)
    return value


def require_list(value: object, *, field_name: str) -> list[object]:
    """Return a validated list value."""
    if not isinstance(value, list):
        msg = f"{field_name} must be a list."
        raise ValueError(msg)
    return [item for item in value]
