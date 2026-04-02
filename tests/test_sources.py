from __future__ import annotations

from pathlib import Path

import pytest

from onomasticon.core.entities import EntityType
from onomasticon.core.identifiers import Identifier
from onomasticon.core.repository import EntityValidationError, EntityWriteError
from onomasticon.core.statements import (
    DateValue,
    IdentifierValue,
    Reference,
    Statement,
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
        identifiers=(Identifier("wikidata", "Q12345"),),
        statements=(
            Statement(
                property="title",
                value=TextValue("De tribulatione"),
                references=(
                    Reference(source="wikidata", record="Q12345", locator="P1476"),
                ),
            ),
            Statement(
                property="same_as",
                value=IdentifierValue(Identifier("wikidata", "Q12345")),
            ),
        ),
        note="Normalized cache record.",
    )

    serialized = repository.dumps(record)
    reparsed = repository.loads(serialized)

    assert reparsed == record


def test_source_layout_uses_source_and_record_identifier() -> None:
    layout = SourceLayout(root=Path("/repo"))

    assert layout.source_record_path("wikidata", "Q12345") == Path(
        "/repo/sources/wikidata/Q12345.toml"
    )


def test_source_repository_can_write_and_reload_source_record(tmp_path: Path) -> None:
    repository = SourceRecordRepository(layout=SourceLayout(root=tmp_path))
    record = SourceRecord(
        source="wikidata",
        record_id="Q12345",
        entity_type=EntityType.WORK,
        identifiers=(Identifier("wikidata", "Q12345"),),
        statements=(
            Statement(
                property="title",
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
                property="title",
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
                property="inception",
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
                property="floruit",
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
            'source = "wikidata"\nrecord_id = "Q12345"\n[[statements]]\nproperty = "creator"\ntext = "A"\nlang = "la"\n'
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
