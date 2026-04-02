from __future__ import annotations

import pytest

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
        DateValue("2024"),
        IdentifierValue("wikidata", "Q12345"),
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
