from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from onomasticon.core.appellations import (
    Appellation,
    AppellationKind,
    AppellationPart,
    AppellationPartKind,
)
from onomasticon.core.entities import (
    AnyEntity,
    Expression,
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
    Ascription,
    AscriptionValue,
    Certainty,
    DateValue,
    EntityValue,
    Qualifier,
    QualifierProperty,
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
        appellations=(
            Appellation(
                kind=AppellationKind.TITLE,
                value="De tribulatione",
                language="la",
            ),
        ),
        identifiers=(Identifier("wikidata", "Q12345"),),
        statements=(
            Statement(
                property=StatementProperty.AUTHOR,
                value=EntityValue("p9x2k4"),
                references=(
                    Reference(source="wikidata", record="Q12345", locator="P50"),
                ),
                qualifiers=(
                    Qualifier(
                        property=QualifierProperty.ASCRIPTION,
                        value=AscriptionValue(Ascription.ATTRIBUTED),
                    ),
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
    assert "[[appellations]]" in serialized
    assert (
        'qualifiers = [{ property = "ascription", ascription = "attributed" }]'
        in serialized
    )


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


def test_repository_round_trips_descriptive_work_appellations() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))
    entity = Work(
        id="a1b2c3",
        appellations=(
            Appellation(
                kind=AppellationKind.DESCRIPTIVE,
                value="Letter from X to Y concerning Z",
                language="en",
            ),
            Appellation(
                kind=AppellationKind.INCIPIT,
                value="In principio tribulationis",
                language="la",
            ),
            Appellation(
                kind=AppellationKind.EXPLICIT,
                value="Explicit de tribulatione",
                language="la",
            ),
        ),
    )

    serialized = repository.dumps(entity)
    reparsed = repository.loads(serialized)

    assert 'kind = "descriptive"' in serialized
    assert 'kind = "incipit"' in serialized
    assert 'kind = "explicit"' in serialized
    assert 'value = "Letter from X to Y concerning Z"' in serialized
    assert 'value = "In principio tribulationis"' in serialized
    assert 'value = "Explicit de tribulatione"' in serialized
    assert reparsed == entity


def test_repository_round_trips_person_name_parts_with_references() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))
    entity = Person(
        id="a1b2c3",
        appellations=(
            Appellation(
                kind=AppellationKind.ATTESTED,
                parts=(
                    AppellationPart(kind=AppellationPartKind.GIVEN, value="Galfridus"),
                    AppellationPart(kind=AppellationPartKind.FAMILY, value="Chaucer"),
                ),
                language="la",
                references=(Reference(source="dnb", record="123456"),),
                status=StatementStatus.ATTESTED_ONLY,
                certainty=Certainty.HIGH,
            ),
        ),
    )

    serialized = repository.dumps(entity)
    reparsed = repository.loads(serialized)

    assert 'kind = "given"' in serialized
    assert 'kind = "family"' in serialized
    assert 'status = "attested_only"' in serialized
    assert 'certainty = "high"' in serialized
    assert 'refs = [{ source = "dnb", record = "123456" }]' in serialized
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
    repository.dump(Person(id="p9x2k4"))
    repository.dump(Person(id="q9x2k4"))
    entity = Work(
        id="a1b2c3",
        identifiers=(Identifier("wikidata", "Q12345"),),
        statements=(
            Statement(
                property=StatementProperty.AUTHOR,
                value=EntityValue("p9x2k4"),
                references=(Reference(source="wikidata", record="Q12345"),),
            ),
            Statement(
                property=StatementProperty.AUTHOR,
                value=EntityValue("q9x2k4"),
            ),
        ),
    )

    written_path = repository.dump(entity)
    loaded = repository.load(written_path)

    assert written_path == tmp_path / "entities" / "a1b2c3.toml"
    assert loaded == entity


def test_repository_validates_cross_entity_targets_on_dump(tmp_path: Path) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=tmp_path))
    repository.dump(Place(id="b1c2d3"))

    entity = Person(
        id="a1b2c3",
        statements=(
            Statement(
                property=StatementProperty.NATIONALITY,
                value=EntityValue("b1c2d3"),
            ),
        ),
    )

    with pytest.raises(
        EntityValidationError,
        match=r"Property 'nationality' on entity a1b2c3 must point to one of \[country\], not 'place'",
    ):
        repository.dump(entity)


def test_repository_validates_cross_entity_targets_on_load(tmp_path: Path) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=tmp_path))
    repository.dump(Organization(id="b1c2d3"))
    person_path = tmp_path / "entities" / "a1b2c3.toml"
    person_path.parent.mkdir(parents=True, exist_ok=True)
    person_path.write_text(
        "\n".join(
            [
                'id = "a1b2c3"',
                'type = "person"',
                "[[statements]]",
                'property = "religious_order"',
                'entity = "b1c2d3"',
                "",
            ]
        )
    )

    with pytest.raises(
        EntityValidationError,
        match=r"Property 'religious_order' on entity a1b2c3 must point to one of \[religious_order\], not 'organization'",
    ):
        repository.load(person_path)


def test_repository_rejects_missing_cross_entity_targets(tmp_path: Path) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=tmp_path))
    entity = Person(
        id="a1b2c3",
        statements=(
            Statement(
                property=StatementProperty.NATIONALITY,
                value=EntityValue("b1c2d3"),
            ),
        ),
    )

    with pytest.raises(
        EntityValidationError,
        match=r"references missing entity 'b1c2d3' via property 'nationality'",
    ):
        repository.dump(entity)


def test_repository_accepts_valid_cross_entity_targets(tmp_path: Path) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=tmp_path))
    repository.dump(Place(id="b1c2d3", subtype=PlaceSubtype.COUNTRY))
    repository.dump(
        Organization(
            id="c2d3e4",
            subtype=OrganizationSubtype.RELIGIOUS_ORDER,
        )
    )
    person = Person(
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
        ),
    )

    written_path = repository.dump(person)

    assert repository.load(written_path) == person


def test_repository_rejects_author_target_that_is_not_a_person(tmp_path: Path) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=tmp_path))
    repository.dump(Organization(id="b1c2d3"))
    work = Work(
        id="a1b2c3",
        statements=(
            Statement(
                property=StatementProperty.AUTHOR,
                value=EntityValue("b1c2d3"),
            ),
        ),
    )

    with pytest.raises(
        EntityValidationError,
        match=r"Property 'author' on entity a1b2c3 must point to one of \[person\], not 'organization'",
    ):
        repository.dump(work)


def test_repository_accepts_author_and_translator_targets_that_are_people(
    tmp_path: Path,
) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=tmp_path))
    repository.dump(Person(id="b1c2d3"))
    repository.dump(Person(id="c2d3e4"))
    expression = Expression(
        id="a1b2c3",
        statements=(
            Statement(
                property=StatementProperty.AUTHOR,
                value=EntityValue("b1c2d3"),
            ),
            Statement(
                property=StatementProperty.TRANSLATOR,
                value=EntityValue("c2d3e4"),
            ),
        ),
    )

    written_path = repository.dump(expression)

    assert repository.load(written_path) == expression


def test_repository_accepts_multiple_author_targets_that_are_people(
    tmp_path: Path,
) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=tmp_path))
    repository.dump(Person(id="b1c2d3"))
    repository.dump(Person(id="c2d3e4"))
    work = Work(
        id="a1b2c3",
        statements=(
            Statement(
                property=StatementProperty.AUTHOR,
                value=EntityValue("b1c2d3"),
            ),
            Statement(
                property=StatementProperty.AUTHOR,
                value=EntityValue("c2d3e4"),
            ),
        ),
    )

    written_path = repository.dump(work)

    assert repository.load(written_path) == work


def test_repository_rejects_translator_target_that_is_not_a_person(
    tmp_path: Path,
) -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=tmp_path))
    repository.dump(Place(id="b1c2d3"))
    expression = Expression(
        id="a1b2c3",
        statements=(
            Statement(
                property=StatementProperty.TRANSLATOR,
                value=EntityValue("b1c2d3"),
            ),
        ),
    )

    with pytest.raises(
        EntityValidationError,
        match=r"Property 'translator' on entity a1b2c3 must point to one of \[person\], not 'place'",
    ):
        repository.dump(expression)


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


def test_repository_rejects_invalid_qualifiers() -> None:
    repository = EntityRepository(layout=RepositoryLayout(root=Path("/repo")))

    with pytest.raises(
        EntityValidationError,
        match="Unknown qualifier property: unknown",
    ):
        repository.loads(
            'id = "a1b2c3"\n[[statements]]\nproperty = "author"\nentity = "p9x2k4"\nqualifiers = [{ property = "unknown", text = "x" }]\n'
        )

    with pytest.raises(
        EntityValidationError,
        match="Unknown ascription value: doubtful",
    ):
        repository.loads(
            'id = "a1b2c3"\n[[statements]]\nproperty = "author"\nentity = "p9x2k4"\nqualifiers = [{ property = "ascription", ascription = "doubtful" }]\n'
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
