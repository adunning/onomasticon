from __future__ import annotations

import pytest

from onomasticon.core.identifiers import Identifier
from onomasticon.core.statements import (
    DateValue,
    EntityValue,
    IdentifierValue,
    LanguageTagValue,
    Reference,
    Statement,
    StatementValue,
    TextValue,
)
from onomasticon.core.temporal import TemporalValue


def test_statement_can_carry_reference_and_entity_value() -> None:
    statement = Statement(
        property="creator",
        value=EntityValue("p9x2k4"),
        references=(Reference(source="wikidata", record="Q12345", locator="P50"),),
    )

    assert statement.property == "creator"
    assert statement.references[0].source == "wikidata"
    assert statement.references[0].record == "Q12345"
    assert statement.references[0].locator == "P50"


@pytest.mark.parametrize(
    "value",
    [
        TextValue("De tribulatione"),
        LanguageTagValue("la"),
        DateValue(TemporalValue("2024")),
        IdentifierValue(Identifier("wikidata", "Q12345")),
    ],
)
def test_statement_accepts_multiple_value_kinds(value: StatementValue) -> None:
    statement = Statement(property="example", value=value)

    assert statement.value == value


def test_entity_value_rejects_non_local_identifier_shapes() -> None:
    with pytest.raises(ValueError, match="lowercase ASCII letters and digits"):
        EntityValue("Q12345")


def test_reference_requires_record_or_locator() -> None:
    with pytest.raises(ValueError, match="at least one of record or locator"):
        Reference(source="wikidata")


def test_temporal_value_carries_optional_label() -> None:
    value = DateValue(TemporalValue("2024~", label="circa 2024"))

    assert value.temporal.edtf == "2024~"
    assert value.temporal.label == "circa 2024"


@pytest.mark.parametrize(
    "edtf",
    [
        "1245",
        "1245-03-14",
        "123X",
        "12XX",
        "1245~",
        "1245?",
        "123X/1245",
        "../1245",
    ],
)
def test_temporal_value_accepts_supported_edtf_forms(edtf: str) -> None:
    value = TemporalValue(edtf)

    assert value.edtf == edtf


@pytest.mark.parametrize(
    "edtf",
    [
        "not-a-date",
        "2024-13",
        "2024-02-30",
        "",
    ],
)
def test_temporal_value_rejects_invalid_edtf(edtf: str) -> None:
    with pytest.raises(ValueError, match="edtf|non-empty string|valid EDTF string"):
        TemporalValue(edtf)
