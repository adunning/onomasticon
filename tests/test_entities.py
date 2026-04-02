from __future__ import annotations

from dataclasses import is_dataclass

import pytest

from onomasticon.core.entities import Entity, Organization


def test_entity_requires_only_an_id() -> None:
    entity = Entity(id="a1b2c3")

    assert is_dataclass(entity)
    assert entity.id == "a1b2c3"
    assert entity.redirect is None
    assert entity.is_redirect is False


def test_entity_can_be_a_redirect() -> None:
    entity = Entity(id="a1b2c3", redirect="z9y8x7")

    assert entity.is_redirect is True
    assert entity.redirect == "z9y8x7"


@pytest.mark.parametrize(
    ("entity_id", "redirect", "message"),
    [
        ("a1b2c3", "a1b2c3", "cannot redirect to itself"),
        ("short", None, "exactly 6 characters"),
        ("ABC123", None, "lowercase ASCII letters and digits"),
    ],
)
def test_entity_rejects_invalid_identifiers(
    entity_id: str,
    redirect: str | None,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        Entity(id=entity_id, redirect=redirect)


def test_organization_is_a_first_class_entity() -> None:
    entity = Organization(id="a1b2c3")

    assert isinstance(entity, Organization)
