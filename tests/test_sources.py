from __future__ import annotations

from pathlib import Path

import pytest

from onomasticon.core.appellations import (
    Appellation,
    AppellationKind,
)
from onomasticon.core.entities import (
    EntityType,
    OrganizationSubtype,
    PlaceSubtype,
)
from onomasticon.core.identifiers import Identifier
from onomasticon.core.properties import StatementProperty
from onomasticon.core.repository import EntityValidationError, EntityWriteError
from onomasticon.core.statements import (
    Ascription,
    AscriptionValue,
    Certainty,
    DateValue,
    IdentifierValue,
    Qualifier,
    QualifierProperty,
    Reference,
    Sex,
    SexValue,
    Statement,
    StatementStatus,
    TextValue,
)
from onomasticon.core.temporal import TemporalValue
from onomasticon.sources import SourceLayout, SourceRecord, SourceRecordRepository


def test_source_record_round_trips_through_toml() -> None:
    repository = SourceRecordRepository(layout=SourceLayout(root=Path("/repo")))
    record = SourceRecord(
        source="wikidata",
        record_id="Q12345",
        entity_type=EntityType.WORK,
        appellations=(
            Appellation(
                kind=AppellationKind.TITLE,
                display_value="De tribulatione",
                language="la",
            ),
        ),
        identifiers=(Identifier("wikidata", "Q12345"),),
        statements=(
            Statement(
                property=StatementProperty.TITLE,
                value=TextValue("De tribulatione"),
                references=(
                    Reference(source="wikidata", record="Q12345", locator="P1476"),
                ),
                certainty=Certainty.HIGH,
            ),
            Statement(
                property=StatementProperty.AUTHOR,
                value=TextValue("Attributed to Geoffrey Chaucer"),
                qualifiers=(
                    Qualifier(
                        property=QualifierProperty.ASCRIPTION,
                        value=AscriptionValue(Ascription.ATTRIBUTED),
                    ),
                ),
                status=StatementStatus.ATTESTED_ONLY,
            ),
            Statement(
                property=StatementProperty.SAME_AS,
                value=IdentifierValue(Identifier("wikidata", "Q12345")),
                status=StatementStatus.ATTESTED_ONLY,
            ),
        ),
        note="Normalized cache record.",
    )

    serialized = repository.dumps(record)
    reparsed = repository.loads(serialized)

    assert reparsed == record
    assert "[[appellations]]" in serialized
    assert (
        'qualifiers = [{ property = "ascription", ascription = "attributed" }]'
        in serialized
    )


def test_source_layout_uses_source_and_record_identifier() -> None:
    layout = SourceLayout(root=Path("/repo"))

    assert layout.source_record_path("wikidata", "Q12345") == Path(
        "/repo/sources/wikidata/Q12345.toml"
    )


def test_source_repository_round_trips_subtyped_records() -> None:
    repository = SourceRecordRepository(layout=SourceLayout(root=Path("/repo")))
    place_record = SourceRecord(
        source="wikidata",
        record_id="Q145",
        entity_type=EntityType.COUNTRY,
        subtype=PlaceSubtype.COUNTRY,
    )
    organization_record = SourceRecord(
        source="wikidata",
        record_id="Q123",
        entity_type=EntityType.RELIGIOUS_ORDER,
        subtype=OrganizationSubtype.RELIGIOUS_ORDER,
    )

    place_serialized = repository.dumps(place_record)
    organization_serialized = repository.dumps(organization_record)

    assert 'type = "country"' in place_serialized
    assert 'type = "religious_order"' in organization_serialized
    assert repository.loads(place_serialized) == place_record
    assert repository.loads(organization_serialized) == organization_record


def test_source_repository_can_write_and_reload_source_record(tmp_path: Path) -> None:
    repository = SourceRecordRepository(layout=SourceLayout(root=tmp_path))
    record = SourceRecord(
        source="wikidata",
        record_id="Q12345",
        entity_type=EntityType.WORK,
        identifiers=(Identifier("wikidata", "Q12345"),),
        statements=(
            Statement(
                property=StatementProperty.TITLE,
                value=TextValue("De tribulatione"),
                references=(Reference(source="wikidata", record="Q12345"),),
            ),
        ),
    )

    written_path = repository.dump(record)
    loaded = repository.load(written_path)

    assert written_path == tmp_path / "sources" / "wikidata" / "Q12345.toml"
    assert loaded == record


def test_source_repository_omits_redundant_record_identifier_in_references() -> None:
    repository = SourceRecordRepository(layout=SourceLayout(root=Path("/repo")))
    record = SourceRecord(
        source="wikidata",
        record_id="Q12345",
        statements=(
            Statement(
                property=StatementProperty.TITLE,
                value=TextValue("De tribulatione"),
                references=(
                    Reference(source="wikidata", record="Q12345", locator="P1476"),
                ),
            ),
        ),
    )

    serialized = repository.dumps(record)
    reparsed = repository.loads(serialized)

    assert 'record = "Q12345"' not in serialized
    assert reparsed.statements[0].references[0].record == "Q12345"


def test_source_repository_round_trips_temporal_value_tables() -> None:
    repository = SourceRecordRepository(layout=SourceLayout(root=Path("/repo")))
    record = SourceRecord(
        source="wikidata",
        record_id="Q12345",
        statements=(
            Statement(
                property=StatementProperty.INCEPTION,
                value=DateValue(TemporalValue("2024", label="year only")),
            ),
        ),
    )

    serialized = repository.dumps(record)
    reparsed = repository.loads(serialized)

    assert 'date = { edtf = "2024", label = "year only" }' in serialized
    assert reparsed == record


def test_source_repository_round_trips_temporal_intervals() -> None:
    repository = SourceRecordRepository(layout=SourceLayout(root=Path("/repo")))
    record = SourceRecord(
        source="wikidata",
        record_id="Q12345",
        statements=(
            Statement(
                property=StatementProperty.FLORUIT,
                value=DateValue(TemporalValue("123X/1245")),
            ),
        ),
    )

    serialized = repository.dumps(record)
    reparsed = repository.loads(serialized)

    assert 'date = "123X/1245"' in serialized
    assert reparsed == record


def test_source_repository_rejects_bad_statement_shapes() -> None:
    repository = SourceRecordRepository(layout=SourceLayout(root=Path("/repo")))

    with pytest.raises(EntityValidationError, match="exactly one value field"):
        repository.loads(
            'source = "wikidata"\nrecord_id = "Q12345"\n[[statements]]\nproperty = "author"\ntext = "A"\nlang = "la"\n'
        )


def test_source_repository_rejects_invalid_identifier_shapes() -> None:
    repository = SourceRecordRepository(layout=SourceLayout(root=Path("/repo")))

    with pytest.raises(EntityValidationError, match="value must be a non-empty string"):
        repository.loads(
            'source = "wikidata"\nrecord_id = "Q12345"\n[[identifiers]]\nscheme = "wikidata"\nvalue = 42\n'
        )


def test_source_repository_dump_rejects_mismatched_filenames(tmp_path: Path) -> None:
    repository = SourceRecordRepository(layout=SourceLayout(root=tmp_path))
    record = SourceRecord(source="wikidata", record_id="Q12345")

    with pytest.raises(
        EntityWriteError, match="must be written to a file named Q12345.toml"
    ):
        repository.dump(record, path=tmp_path / "sources" / "wikidata" / "wrong.toml")


def test_source_record_rejects_properties_not_allowed_on_type() -> None:
    with pytest.raises(
        ValueError,
        match="Property 'birth' is not allowed on work source records",
    ):
        SourceRecord(
            source="wikidata",
            record_id="Q12345",
            entity_type=EntityType.WORK,
            statements=(
                Statement(
                    property=StatementProperty.BIRTH,
                    value=DateValue(TemporalValue("1245")),
                ),
            ),
        )


def test_source_record_accepts_controlled_sex_value() -> None:
    record = SourceRecord(
        source="wikidata",
        record_id="Q12345",
        entity_type=EntityType.PERSON,
        statements=(
            Statement(
                property=StatementProperty.SEX,
                value=SexValue(Sex.FEMALE),
            ),
        ),
    )

    value = record.statements[0].value
    assert isinstance(value, SexValue)
    assert value.sex is Sex.FEMALE
