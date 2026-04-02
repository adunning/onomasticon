from __future__ import annotations

from dataclasses import is_dataclass

import pytest

from onomasticon.core.appellations import (
    Appellation,
    AppellationKind,
    AppellationPart,
    AppellationPartKind,
)
from onomasticon.core.entities import (
    Entity,
    Organization,
    OrganizationSubtype,
    Person,
    Place,
    PlaceSubtype,
)
from onomasticon.core.properties import StatementProperty
from onomasticon.core.statements import DateValue, EntityValue, Sex, SexValue, Statement
from onomasticon.core.temporal import TemporalValue


def test_entity_requires_only_an_id() -> None:
    entity = Entity(id="a1b2c3")

    assert is_dataclass(entity)
    assert entity.id == "a1b2c3"
    assert entity.appellations == ()
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


def test_organization_accepts_location_foundation_and_dissolution() -> None:
    entity = Organization(
        id="a1b2c3",
        statements=(
            Statement(
                property=StatementProperty.LOCATION,
                value=EntityValue("b1c2d3"),
            ),
            Statement(
                property=StatementProperty.FOUNDATION,
                value=DateValue(TemporalValue("1140")),
            ),
            Statement(
                property=StatementProperty.DISSOLUTION,
                value=DateValue(TemporalValue("1539")),
            ),
        ),
    )

    assert len(entity.statements) == 3


def test_place_and_organization_can_carry_subtypes() -> None:
    place = Place(id="a1b2c3", subtype=PlaceSubtype.COUNTRY)
    organization = Organization(
        id="b1c2d3",
        subtype=OrganizationSubtype.RELIGIOUS_ORDER,
    )

    assert place.subtype is PlaceSubtype.COUNTRY
    assert organization.subtype is OrganizationSubtype.RELIGIOUS_ORDER


def test_person_rejects_inapplicable_statement_properties() -> None:
    with pytest.raises(ValueError, match="not allowed on person entities"):
        Person(
            id="a1b2c3",
            statements=(
                Statement(
                    property=StatementProperty.INCEPTION,
                    value=DateValue(TemporalValue("1245")),
                ),
            ),
        )


def test_person_accepts_person_specific_relationship_properties() -> None:
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
            Statement(
                property=StatementProperty.SEX,
                value=SexValue(Sex.MALE),
            ),
        ),
    )

    assert len(person.statements) == 3


def test_entity_can_carry_appellations() -> None:
    entity = Person(
        id="a1b2c3",
        appellations=(
            Appellation(
                kind=AppellationKind.PREFERRED,
                parts=(
                    AppellationPart(kind=AppellationPartKind.BYNAME, value="Pseudo"),
                    AppellationPart(
                        kind=AppellationPartKind.HONORIFIC, value="Dionysius"
                    ),
                ),
                language="en",
            ),
        ),
    )

    assert entity.appellations[0].parts[0].value == "Pseudo"
