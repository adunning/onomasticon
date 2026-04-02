"""Controlled statement property vocabulary."""

from __future__ import annotations

from enum import StrEnum


class StatementProperty(StrEnum):
    """Controlled property vocabulary for the current canonical model."""

    ATTESTED = "attested"
    AUTHOR = "author"
    COLLECTION = "collection"
    BIRTH = "birth"
    COORDINATES = "coordinates"
    DEATH = "death"
    FLORUIT = "floruit"
    FOUNDATION = "foundation"
    INCEPTION = "inception"
    LANGUAGE = "language"
    LOCATOR = "locator"
    LOCUS = "locus"
    LOCATION = "location"
    NATIONALITY = "nationality"
    ORIGIN_DATE = "origin_date"
    ORIGIN_PLACE = "origin_place"
    PROVENANCE = "provenance"
    RELIGIOUS_ORDER = "religious_order"
    REPOSITORY = "repository"
    SETTLEMENT = "settlement"
    SAME_AS = "same_as"
    SEX = "sex"
    SHELFMARK = "shelfmark"
    TITLE = "title"
    TRANSLATOR = "translator"
    DISSOLUTION = "dissolution"


_PROPERTY_APPLICABILITY: dict[StatementProperty, frozenset[str]] = {
    StatementProperty.ATTESTED: frozenset(
        {"work", "expression", "manifestation", "item"}
    ),
    StatementProperty.AUTHOR: frozenset({"work", "expression"}),
    StatementProperty.BIRTH: frozenset({"person"}),
    StatementProperty.COORDINATES: frozenset({"place"}),
    StatementProperty.DEATH: frozenset({"person"}),
    StatementProperty.DISSOLUTION: frozenset({"organization"}),
    StatementProperty.FLORUIT: frozenset({"person"}),
    StatementProperty.FOUNDATION: frozenset({"organization"}),
    StatementProperty.INCEPTION: frozenset({"organization", "place", "manifestation"}),
    StatementProperty.LANGUAGE: frozenset({"work", "expression"}),
    StatementProperty.LOCATION: frozenset({"organization"}),
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

_DOCUMENTARY_PROPERTY_APPLICABILITY: dict[StatementProperty, frozenset[str]] = {
    StatementProperty.COLLECTION: frozenset({"holding"}),
    StatementProperty.LOCATOR: frozenset({"component"}),
    StatementProperty.LOCUS: frozenset({"content_item"}),
    StatementProperty.ORIGIN_DATE: frozenset({"holding", "component"}),
    StatementProperty.ORIGIN_PLACE: frozenset({"holding", "component"}),
    StatementProperty.PROVENANCE: frozenset({"holding", "component"}),
    StatementProperty.REPOSITORY: frozenset({"holding"}),
    StatementProperty.SETTLEMENT: frozenset({"holding"}),
    StatementProperty.SHELFMARK: frozenset({"holding"}),
    StatementProperty.AUTHOR: frozenset({"content_item"}),
    StatementProperty.LANGUAGE: frozenset({"content_item"}),
    StatementProperty.TITLE: frozenset({"content_item"}),
    StatementProperty.TRANSLATOR: frozenset({"content_item"}),
    StatementProperty.ATTESTED: frozenset({"content_item"}),
}

_ENTITY_REFERENCE_TARGETS: dict[StatementProperty, frozenset[str]] = {
    StatementProperty.AUTHOR: frozenset({"person"}),
    StatementProperty.LOCATION: frozenset({"place", "country"}),
    StatementProperty.NATIONALITY: frozenset({"country"}),
    StatementProperty.ORIGIN_PLACE: frozenset({"place", "country"}),
    StatementProperty.RELIGIOUS_ORDER: frozenset({"religious_order"}),
    StatementProperty.REPOSITORY: frozenset({"organization"}),
    StatementProperty.SETTLEMENT: frozenset({"place", "country"}),
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
    allowed_types = _PROPERTY_APPLICABILITY.get(normalized_property)
    if allowed_types is None:
        return False
    return entity_type_name in allowed_types


def property_allowed_for_documentary_type(
    property_name: StatementProperty | str,
    documentary_type: object,
) -> bool:
    """Return whether a property is allowed on the given documentary type."""
    property_value = getattr(property_name, "value", property_name)
    documentary_type_name = getattr(documentary_type, "value", documentary_type)
    if not isinstance(property_value, str) or not isinstance(
        documentary_type_name, str
    ):
        return False
    try:
        normalized_property = StatementProperty(property_value)
    except ValueError:
        return False
    allowed_types = _DOCUMENTARY_PROPERTY_APPLICABILITY.get(normalized_property)
    if allowed_types is None:
        return False
    return documentary_type_name in allowed_types


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
