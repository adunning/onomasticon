"""Controlled statement property vocabulary."""

from __future__ import annotations

from enum import StrEnum


class StatementProperty(StrEnum):
    """Controlled property vocabulary for the current canonical model."""

    ATTESTED = "attested"
    AUTHOR = "author"
    BIRTH = "birth"
    COORDINATES = "coordinates"
    DEATH = "death"
    FLORUIT = "floruit"
    INCEPTION = "inception"
    LANGUAGE = "language"
    NATIONALITY = "nationality"
    RELIGIOUS_ORDER = "religious_order"
    SAME_AS = "same_as"
    SEX = "sex"
    TITLE = "title"
    TRANSLATOR = "translator"


_PROPERTY_APPLICABILITY: dict[StatementProperty, frozenset[str]] = {
    StatementProperty.ATTESTED: frozenset(
        {"work", "expression", "manifestation", "item"}
    ),
    StatementProperty.AUTHOR: frozenset({"work", "expression"}),
    StatementProperty.BIRTH: frozenset({"person"}),
    StatementProperty.COORDINATES: frozenset({"place"}),
    StatementProperty.DEATH: frozenset({"person"}),
    StatementProperty.FLORUIT: frozenset({"person"}),
    StatementProperty.INCEPTION: frozenset({"organization", "place", "manifestation"}),
    StatementProperty.LANGUAGE: frozenset({"work", "expression"}),
    StatementProperty.NATIONALITY: frozenset({"person"}),
    StatementProperty.RELIGIOUS_ORDER: frozenset({"person"}),
    StatementProperty.SAME_AS: frozenset(
        {
            "person",
            "place",
            "organization",
            "work",
            "expression",
            "manifestation",
            "item",
        }
    ),
    StatementProperty.SEX: frozenset({"person"}),
    StatementProperty.TITLE: frozenset(
        {
            "work",
            "expression",
            "manifestation",
            "item",
        }
    ),
    StatementProperty.TRANSLATOR: frozenset({"expression", "manifestation"}),
}

_ENTITY_REFERENCE_TARGETS: dict[StatementProperty, frozenset[str]] = {
    StatementProperty.AUTHOR: frozenset({"person"}),
    StatementProperty.NATIONALITY: frozenset({"country"}),
    StatementProperty.RELIGIOUS_ORDER: frozenset({"religious_order"}),
    StatementProperty.TRANSLATOR: frozenset({"person"}),
}


def property_allowed_for_entity_type(
    property_name: StatementProperty | str,
    entity_type: object,
) -> bool:
    """Return whether a property is allowed on the given entity type."""
    property_value = getattr(property_name, "value", property_name)
    entity_type_name = getattr(entity_type, "value", entity_type)
    if not isinstance(property_value, str) or not isinstance(entity_type_name, str):
        return False
    entity_type_name = _canonical_entity_type_name(entity_type_name)
    try:
        normalized_property = StatementProperty(property_value)
    except ValueError:
        return False
    return entity_type_name in _PROPERTY_APPLICABILITY[normalized_property]


def _canonical_entity_type_name(entity_type_name: str) -> str:
    """Collapse leaf entity types onto their broad parent types."""
    match entity_type_name:
        case "country":
            return "place"
        case "religious_order":
            return "organization"
        case _:
            return entity_type_name


def allowed_target_entity_types(
    property_name: StatementProperty | str,
) -> frozenset[str] | None:
    """Return constrained target entity types for entity-valued statements."""
    property_value = getattr(property_name, "value", property_name)
    if not isinstance(property_value, str):
        return None
    try:
        normalized_property = StatementProperty(property_value)
    except ValueError:
        return None
    return _ENTITY_REFERENCE_TARGETS.get(normalized_property)
