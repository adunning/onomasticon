from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from onomasticon.core.entities import AnyEntity, Person
from onomasticon.core.identifiers import Identifier
from onomasticon.core.repository import (
    EntityRepository,
    EntityValidationError,
    EntityWriteError,
    IdentifierCollisionError,
    RepositoryLayout,
)
from onomasticon.core.statements import EntityValue, Reference, Statement


def test_entity_round_trips_through_toml() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))
    entity = Person(
        id="a1b2c3",
        identifiers=(Identifier("wikidata", "Q12345"),),
        statements=(
            Statement(
                property="creator",
                value=EntityValue("p9x2k4"),
                references=(
                    Reference(source="wikidata", record="Q12345", locator="P50"),
                ),
            ),
        ),
        note="Sparse test entity.",
    )

    serialized = repository.dumps(entity)
    reparsed = repository.loads(serialized)

    assert reparsed == entity
    assert isinstance(reparsed, Person)


def test_repository_layout_uses_one_entity_per_file() -> None:
    layout = RepositoryLayout(root=Path("/repo"))

    assert layout.entity_path("a1b2c3") == Path("/repo/entities/a1b2c3.toml")


def test_repository_rejects_invalid_entity_documents() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))

    with pytest.raises(ValueError, match="redirect to itself"):
        repository.loads('id = "a1b2c3"\nredirect = "a1b2c3"\n')


def test_repository_rejects_unknown_entity_types() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))

    with pytest.raises(EntityValidationError, match="Unknown entity_type: foobar"):
        repository.loads('id = "a1b2c3"\nentity_type = "foobar"\n')


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ('id = "a1b2c3"\ninvalid = [\n', "Invalid TOML entity document"),
        ('id = "a1b2c3"\nextra = "value"\n', "Unexpected entity fields: extra"),
        ("id = 42\n", "id must be a non-empty string"),
        ('id = "a1b2c3"\nnote = 42\n', "note must be a string"),
        (
            'id = "a1b2c3"\n[[identifiers]]\nscheme = 42\nvalue = "Q12345"\n',
            "scheme must be a non-empty string",
        ),
    ],
)
def test_repository_rejects_invalid_toml_shapes(content: str, message: str) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))

    with pytest.raises(EntityValidationError, match=message):
        repository.loads(content)


@pytest.mark.parametrize(
    ("entity_type", "expected_class"),
    [
        ("person", Person),
    ],
)
def test_repository_loads_return_concrete_entity_types(
    entity_type: str,
    expected_class: type[Person],
) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))

    entity: AnyEntity = repository.loads(
        f'id = "a1b2c3"\nentity_type = "{entity_type}"\n'
    )

    assert isinstance(entity, expected_class)


def test_repository_mints_six_character_ids_and_retries_on_collision(
    tmp_path: Path,
) -> None:
    layout = RepositoryLayout(root=tmp_path)
    repository = EntityRepository(layout=layout)
    layout.entity_path("aaaaaa").parent.mkdir(parents=True, exist_ok=True)
    layout.entity_path("aaaaaa").write_text('id = "aaaaaa"\n')

    with patch(
        "onomasticon.core.repository.choice",
        side_effect=["a", "a", "a", "a", "a", "a", "b", "1", "c", "2", "d", "3"],
    ):
        minted = repository.mint_id()

    assert minted == "b1c2d3"


def test_repository_raises_when_id_minting_exhausts_attempts(tmp_path: Path) -> None:
    layout = RepositoryLayout(root=tmp_path)
    repository = EntityRepository(layout=layout)
    layout.entity_path("aaaaaa").parent.mkdir(parents=True, exist_ok=True)
    layout.entity_path("aaaaaa").write_text('id = "aaaaaa"\n')

    with patch(
        "onomasticon.core.repository.choice", side_effect=["a", "a", "a", "a", "a", "a"]
    ):
        with pytest.raises(IdentifierCollisionError, match="after 1 attempts"):
            repository.mint_id(max_attempts=1)


def test_repository_dump_refuses_to_overwrite_by_default(tmp_path: Path) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=tmp_path))
    entity = Person(id="a1b2c3")
    repository.dump(entity)

    with pytest.raises(EntityWriteError, match="Refusing to overwrite"):
        repository.dump(entity)


def test_repository_dump_can_overwrite_explicitly(tmp_path: Path) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=tmp_path))
    initial = Person(id="a1b2c3", note="Initial")
    updated = Person(id="a1b2c3", note="Updated")
    destination = repository.dump(initial)

    repository.dump(updated, overwrite=True)

    assert destination.read_text() == repository.dumps(updated)


def test_repository_can_write_and_reload_entity_file(tmp_path: Path) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=tmp_path))
    entity = Person(
        id="a1b2c3",
        identifiers=(Identifier("wikidata", "Q12345"),),
        statements=(
            Statement(
                property="creator",
                value=EntityValue("p9x2k4"),
                references=(Reference(source="wikidata", record="Q12345"),),
            ),
        ),
    )

    written_path = repository.dump(entity)
    loaded = repository.load(written_path)

    assert written_path == tmp_path / "entities" / "a1b2c3.toml"
    assert loaded == entity


def test_repository_dump_rejects_mismatched_filenames(tmp_path: Path) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=tmp_path))
    entity = Person(id="a1b2c3")

    with pytest.raises(
        EntityWriteError, match="must be written to a file named a1b2c3.toml"
    ):
        repository.dump(entity, path=tmp_path / "entities" / "wrong.toml")
