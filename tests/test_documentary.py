from __future__ import annotations

import pytest

from onomasticon.core.appellations import Appellation, AppellationKind
from onomasticon.core.documentary import (
    Component,
    ContentItem,
    DocumentaryType,
    Holding,
    documentary_type_for_unit,
)
from onomasticon.core.identifiers import Identifier
from onomasticon.core.properties import (
    StatementProperty,
    property_allowed_for_documentary_type,
    property_allowed_for_entity_type,
)
from onomasticon.core.statements import DateValue, EntityValue, Statement, TextValue
from onomasticon.core.temporal import TemporalValue


def test_documentary_core_models_validate_allowed_properties() -> None:
    holding = Holding(
        id="a1b2c3",
        identifiers=(Identifier("mmol", "MS_LAUD_MISC_108"),),
        statements=(
            Statement(
                property=StatementProperty.SHELFMARK,
                value=TextValue("MS Laud misc. 108"),
            ),
        ),
    )
    component = Component(
        id="b1c2d3",
        holding_id="a1b2c3",
        statements=(
            Statement(
                property=StatementProperty.LOCATOR,
                value=TextValue("ff. 1-48"),
            ),
        ),
    )
    content_item = ContentItem(
        id="c1d2e3",
        holding_id="a1b2c3",
        component_id="b1c2d3",
        appellations=(
            Appellation(kind=AppellationKind.TITLE, value="Boethius", language="la"),
        ),
        statements=(
            Statement(
                property=StatementProperty.LOCUS,
                value=TextValue("ff. 1r-20v"),
            ),
            Statement(
                property=StatementProperty.AUTHOR,
                value=EntityValue("d1e2f3"),
            ),
        ),
    )

    assert documentary_type_for_unit(holding) is DocumentaryType.HOLDING
    assert documentary_type_for_unit(component) is DocumentaryType.COMPONENT
    assert documentary_type_for_unit(content_item) is DocumentaryType.CONTENT_ITEM


@pytest.mark.parametrize(
    ("documentary_type", "property_name"),
    [
        (DocumentaryType.HOLDING, StatementProperty.SHELFMARK),
        (DocumentaryType.COMPONENT, StatementProperty.LOCATOR),
        (DocumentaryType.CONTENT_ITEM, StatementProperty.LOCUS),
        (DocumentaryType.CONTENT_ITEM, StatementProperty.TITLE),
    ],
)
def test_property_allowed_for_documentary_type_accepts_configured_pairs(
    documentary_type: DocumentaryType,
    property_name: StatementProperty,
) -> None:
    assert property_allowed_for_documentary_type(property_name, documentary_type)


@pytest.mark.parametrize(
    ("documentary_type", "property_name"),
    [
        (DocumentaryType.HOLDING, StatementProperty.AUTHOR),
        (DocumentaryType.COMPONENT, StatementProperty.SHELFMARK),
        (DocumentaryType.CONTENT_ITEM, StatementProperty.REPOSITORY),
    ],
)
def test_property_allowed_for_documentary_type_rejects_invalid_pairs(
    documentary_type: DocumentaryType,
    property_name: StatementProperty,
) -> None:
    assert not property_allowed_for_documentary_type(property_name, documentary_type)


def test_documentary_records_reject_disallowed_properties() -> None:
    with pytest.raises(ValueError, match="not allowed on holding records"):
        Holding(
            id="a1b2c3",
            statements=(
                Statement(
                    property=StatementProperty.AUTHOR,
                    value=EntityValue("d1e2f3"),
                ),
            ),
        )

    with pytest.raises(ValueError, match="not allowed on component records"):
        Component(
            id="b1c2d3",
            holding_id="a1b2c3",
            statements=(
                Statement(
                    property=StatementProperty.LOCUS,
                    value=TextValue("ff. 1r-20v"),
                ),
            ),
        )


def test_documentary_property_vocabulary_does_not_change_entity_rules() -> None:
    assert property_allowed_for_entity_type(StatementProperty.AUTHOR, "work")
    assert not property_allowed_for_entity_type(StatementProperty.SHELFMARK, "work")


def test_component_rejects_self_parenting() -> None:
    with pytest.raises(ValueError, match="cannot parent itself"):
        Component(id="a1b2c3", holding_id="d1e2f3", parent_component_id="a1b2c3")


def test_content_item_rejects_self_parenting() -> None:
    with pytest.raises(ValueError, match="cannot parent itself"):
        ContentItem(
            id="a1b2c3",
            holding_id="d1e2f3",
            parent_content_item_id="a1b2c3",
        )


def test_content_item_accepts_attested_and_title_statements() -> None:
    item = ContentItem(
        id="a1b2c3",
        holding_id="d1e2f3",
        statements=(
            Statement(
                property=StatementProperty.ATTESTED,
                value=DateValue(TemporalValue("123X/1245")),
            ),
            Statement(
                property=StatementProperty.TITLE,
                value=TextValue("De consolatione"),
            ),
        ),
    )

    assert item.statements[0].property is StatementProperty.ATTESTED
    assert item.statements[1].property is StatementProperty.TITLE
