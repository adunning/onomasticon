from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from onomasticon.core.entities import (
    AnyEntity,
    Organization,
    OrganizationSubtype,
    Person,
    Place,
    PlaceSubtype,
    Work,
)
from onomasticon.core.identifiers import Identifier
from onomasticon.core.properties import StatementProperty
from onomasticon.core.repository import (
    EntityRepository,
    EntityValidationError,
    EntityWriteError,
    IdentifierCollisionError,
    RepositoryLayout,
)
from onomasticon.core.statements import (
    Certainty,
    DateValue,
    EntityValue,
    Reference,
    Sex,
    SexValue,
    Statement,
    StatementStatus,
)
from onomasticon.core.temporal import TemporalValue


def test_entity_round_trips_through_toml() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))
    entity = Work(
        id="a1b2c3",
        identifiers=(Identifier("wikidata", "Q12345"),),
        statements=(
            Statement(
                property=StatementProperty.CREATOR,
                value=EntityValue("p9x2k4"),
                references=(
                    Reference(source="wikidata", record="Q12345", locator="P50"),
                ),
                certainty=Certainty.HIGH,
            ),
        ),
        note="Sparse test entity.",
    )

    serialized = repository.dumps(entity)
    reparsed = repository.loads(serialized)

    assert reparsed == entity
    assert isinstance(reparsed, Work)


def test_repository_layout_uses_one_entity_per_file() -> None:
    layout = RepositoryLayout(root=Path("/repo"))

    assert layout.entity_path("a1b2c3") == Path("/repo/entities/a1b2c3.toml")


def test_repository_rejects_invalid_entity_documents() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))

    with pytest.raises(ValueError, match="redirect to itself"):
        repository.loads('id = "a1b2c3"\nredirect = "a1b2c3"\n')


def test_repository_rejects_unknown_types() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))

    with pytest.raises(EntityValidationError, match="Unknown type: foobar"):
        repository.loads('id = "a1b2c3"\ntype = "foobar"\n')


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


def test_repository_round_trips_place_and_organization_subtypes() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))
    place = Place(id="a1b2c3", subtype=PlaceSubtype.COUNTRY)
    organization = Organization(
        id="b1c2d3",
        subtype=OrganizationSubtype.RELIGIOUS_ORDER,
    )

    place_serialized = repository.dumps(place)
    organization_serialized = repository.dumps(organization)

    assert 'type = "country"' in place_serialized
    assert 'type = "religious_order"' in organization_serialized
    assert "subtype =" not in place_serialized
    assert "subtype =" not in organization_serialized
    assert repository.loads(place_serialized) == place
    assert repository.loads(organization_serialized) == organization


def test_repository_round_trips_temporal_values() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))
    entity = Work(
        id="a1b2c3",
        statements=(
            Statement(
                property=StatementProperty.ATTESTED,
                value=DateValue(TemporalValue("2024~", label="circa 2024")),
                status=StatementStatus.ATTESTED_ONLY,
                certainty=Certainty.MEDIUM,
            ),
        ),
    )

    serialized = repository.dumps(entity)
    reparsed = repository.loads(serialized)

    assert 'date = { edtf = "2024~", label = "circa 2024" }' in serialized
    assert 'status = "attested_only"' in serialized
    assert 'certainty = "medium"' in serialized
    assert reparsed == entity


def test_repository_round_trips_temporal_intervals() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))
    entity = Person(
        id="a1b2c3",
        statements=(
            Statement(
                property=StatementProperty.FLORUIT,
                value=DateValue(TemporalValue("123X/1245")),
            ),
        ),
    )

    serialized = repository.dumps(entity)
    reparsed = repository.loads(serialized)

    assert 'date = "123X/1245"' in serialized
    assert reparsed == entity


@pytest.mark.parametrize(
    ("type", "expected_class"),
    [
        ("person", Person),
    ],
)
def test_repository_loads_return_concrete_types(
    type: str,
    expected_class: type[Person],
) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))

    entity: AnyEntity = repository.loads(f'id = "a1b2c3"\ntype = "{type}"\n')

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
    entity = Work(
        id="a1b2c3",
        identifiers=(Identifier("wikidata", "Q12345"),),
        statements=(
            Statement(
                property=StatementProperty.CREATOR,
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


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (
            'id = "a1b2c3"\n[[statements]]\nproperty = "floruit"\ndate = { label = "no edtf" }\n',
            "edtf must be a non-empty string",
        ),
        (
            'id = "a1b2c3"\n[[statements]]\nproperty = "floruit"\ndate = { edtf = 42 }\n',
            "edtf must be a non-empty string",
        ),
        (
            'id = "a1b2c3"\n[[statements]]\nproperty = "floruit"\ndate = { edtf = "2024", extra = "x" }\n',
            "Unexpected temporal value fields: extra",
        ),
    ],
)
def test_repository_rejects_invalid_temporal_value_shapes(
    content: str,
    message: str,
) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))

    with pytest.raises(EntityValidationError, match=message):
        repository.loads(content)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (
            'id = "a1b2c3"\n[[statements]]\nproperty = "death"\ndate = "1217"\nstatus = "wrong"\n',
            "Unknown statement status: wrong",
        ),
        (
            'id = "a1b2c3"\n[[statements]]\nproperty = "death"\ndate = "1217"\ncertainty = "probable"\n',
            "Unknown statement certainty: probable",
        ),
    ],
)
def test_repository_rejects_unknown_statement_status_and_certainty(
    content: str,
    message: str,
) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))

    with pytest.raises(EntityValidationError, match=message):
        repository.loads(content)


def test_repository_rejects_unknown_statement_properties() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))

    with pytest.raises(
        EntityValidationError, match="Unknown statement property: unknown"
    ):
        repository.loads(
            'id = "a1b2c3"\n[[statements]]\nproperty = "unknown"\ntext = "x"\n'
        )


def test_repository_rejects_properties_not_allowed_on_type() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))

    with pytest.raises(
        ValueError,
        match="Property 'inception' is not allowed on person entities",
    ):
        repository.loads(
            'id = "a1b2c3"\ntype = "person"\n[[statements]]\nproperty = "inception"\ndate = "1245"\n'
        )


def test_repository_round_trips_person_relationship_properties() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))
    entity = Person(
        id="a1b2c3",
        statements=(
            Statement(
                property=StatementProperty.NATIONALITY,
                value=EntityValue("b1c2d3"),
            ),
            Statement(
                property=StatementProperty.RELIGIOUS_ORDER,
                value=EntityValue("c2d3e4"),
            ),
            Statement(
                property=StatementProperty.SEX,
                value=SexValue(Sex.MALE),
            ),
        ),
    )

    serialized = repository.dumps(entity)
    reparsed = repository.loads(serialized)

    assert 'property = "nationality"' in serialized
    assert 'property = "religious_order"' in serialized
    assert 'property = "sex"' in serialized
    assert 'sex = "male"' in serialized
    assert reparsed == entity


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (
            'id = "a1b2c3"\ntype = "place"\nsubtype = "principality"\n',
            "Unexpected entity fields: subtype",
        ),
        (
            'id = "a1b2c3"\ntype = "person"\nsubtype = "country"\n',
            "Unexpected entity fields: subtype",
        ),
        (
            'id = "a1b2c3"\ntype = "person"\n[[statements]]\nproperty = "sex"\nsex = "ambiguous"\n',
            "Unknown sex value: ambiguous",
        ),
    ],
)
def test_repository_rejects_invalid_subtypes_and_sex_values(
    content: str,
    message: str,
) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))

    with pytest.raises(EntityValidationError, match=message):
        repository.loads(content)


def test_repository_loads_leaf_types_as_broad_classes_with_subtypes() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))

    country = repository.loads('id = "a1b2c3"\ntype = "country"\n')
    religious_order = repository.loads('id = "b1c2d3"\ntype = "religious_order"\n')

    assert isinstance(country, Place)
    assert country.subtype is PlaceSubtype.COUNTRY
    assert isinstance(religious_order, Organization)
    assert religious_order.subtype is OrganizationSubtype.RELIGIOUS_ORDER
