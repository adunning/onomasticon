from __future__ import annotations

import pytest

from onomasticon.core.appellations import (
    Appellation,
    AppellationKind,
    AppellationPart,
    AppellationPartKind,
)
from onomasticon.core.statements import Certainty, Reference, StatementStatus


def test_appellation_normalizes_kind_and_language() -> None:
    appellation = Appellation(
        kind="title",
        parts=(AppellationPart(kind="generic", value="De tribulatione"),),
        language="la",
    )

    assert appellation.kind is AppellationKind.TITLE
    assert appellation.language == "la"
    assert appellation.parts[0].kind is AppellationPartKind.GENERIC


def test_appellation_can_carry_provenance_and_editorial_metadata() -> None:
    appellation = Appellation(
        kind=AppellationKind.ATTESTED,
        parts=(
            AppellationPart(kind=AppellationPartKind.GIVEN, value="Galfridus"),
            AppellationPart(kind=AppellationPartKind.FAMILY, value="Chaucer"),
        ),
        references=(Reference(source="dnb", record="123456"),),
        status=StatementStatus.ATTESTED_ONLY,
        certainty=Certainty.HIGH,
    )

    assert appellation.references[0].source == "dnb"
    assert appellation.status is StatementStatus.ATTESTED_ONLY
    assert appellation.certainty is Certainty.HIGH


def test_appellation_can_fall_back_to_unstructured_display_value() -> None:
    appellation = Appellation(
        kind=AppellationKind.DESCRIPTIVE,
        display_value="Letter from X to Y concerning Z",
        language="en",
    )

    assert appellation.display_value == "Letter from X to Y concerning Z"
    assert appellation.parts == ()


def test_appellation_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError, match="Unknown appellation kind: heading"):
        Appellation(display_value="Heading", kind="heading")


def test_appellation_rejects_invalid_language_tags() -> None:
    with pytest.raises(ValueError, match="valid BCP 47 language tag"):
        Appellation(display_value="Heading", kind="descriptive", language="123")


def test_appellation_requires_parts_or_display_value() -> None:
    with pytest.raises(
        ValueError,
        match="appellation must define either parts or display_value",
    ):
        Appellation(kind="preferred")
