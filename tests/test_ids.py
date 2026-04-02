from __future__ import annotations

import pytest

from onomasticon.core.entities import Entity


def test_entity_id_uses_local_opaque_identifier_shape() -> None:
    entity = Entity(id="a1b2c3")

    assert entity.id == "a1b2c3"


def test_entity_id_rejects_incorrect_length() -> None:
    with pytest.raises(ValueError, match="exactly 6 characters"):
        Entity(id="a1b2c3d")
