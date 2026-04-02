from __future__ import annotations

import pytest

from onomasticon.core import (
    Appellation,
    AppellationKind,
    Certainty,
    EntityType,
    ExternalAuthorityTarget,
    Identifier,
    LocalEntityTarget,
    Mention,
    ResolutionStatus,
)
from onomasticon.core.properties import StatementProperty
from onomasticon.core.statements import DateValue, Statement, TextValue
from onomasticon.core.temporal import TemporalValue


def test_mention_can_model_extracted_source_occurrence_without_local_id() -> None:
    mention = Mention(
        source="tei",
        record="oxford_bodleian_laud_misc_108",
        locator="msDesc/msContents/msItem[1]/author[1]",
        label="Galfridus Chaucer",
        entity_type=EntityType.PERSON,
        appellations=(
            Appellation(
                kind=AppellationKind.ATTESTED,
                value="Galfridus Chaucer",
                language="la",
            ),
        ),
        statements=(
            Statement(
                property=StatementProperty.FLORUIT,
                value=DateValue(TemporalValue("1380/1400")),
            ),
        ),
    )

    assert mention.record == "oxford_bodleian_laud_misc_108"
    assert mention.locator == "msDesc/msContents/msItem[1]/author[1]"
    assert mention.label == "Galfridus Chaucer"
    assert mention.reference.source == "tei"
    assert mention.reference.record == "oxford_bodleian_laud_misc_108"
    assert mention.resolution_status is ResolutionStatus.UNRESOLVED


def test_mention_requires_record_or_locator() -> None:
    with pytest.raises(ValueError, match="at least one of record or locator"):
        Mention(source="tei")


def test_mention_validates_statements_against_entity_type() -> None:
    with pytest.raises(ValueError, match="not allowed on person mentions"):
        Mention(
            source="tei",
            locator="//persName[1]",
            entity_type=EntityType.PERSON,
            statements=(
                Statement(
                    property=StatementProperty.INCEPTION,
                    value=TextValue("x"),
                ),
            ),
        )


def test_local_entity_target_requires_local_identifier() -> None:
    with pytest.raises(ValueError, match="lowercase ASCII letters and digits"):
        LocalEntityTarget("Q12345")


def test_mention_can_record_match_to_local_entity() -> None:
    mention = Mention(
        source="tei",
        locator="//persName[1]",
        entity_type=EntityType.PERSON,
        label="Geoffrey Chaucer",
        resolution_status=ResolutionStatus.MATCHED,
        resolved_target=LocalEntityTarget("a1b2c3"),
        certainty=Certainty.HIGH,
    )

    assert mention.resolution_status is ResolutionStatus.MATCHED
    assert isinstance(mention.resolved_target, LocalEntityTarget)
    assert mention.resolved_target.entity_id == "a1b2c3"
    assert mention.certainty is Certainty.HIGH


def test_mention_can_record_match_to_external_authority_without_local_entity() -> None:
    mention = Mention(
        source="tei",
        locator="//title[1]",
        entity_type=EntityType.WORK,
        label="De tribulatione",
        resolution_status=ResolutionStatus.MATCHED,
        resolved_target=ExternalAuthorityTarget(
            identifier=Identifier("wikidata", "Q12345"),
            label="De tribulatione",
        ),
    )

    assert isinstance(mention.resolved_target, ExternalAuthorityTarget)
    assert mention.resolved_target.identifier.scheme == "wikidata"
    assert mention.resolved_target.identifier.value == "Q12345"


def test_ambiguous_mention_requires_multiple_candidate_targets() -> None:
    with pytest.raises(
        ValueError,
        match="ambiguous mention must define at least two candidate targets",
    ):
        Mention(
            source="tei",
            locator="//persName[1]",
            entity_type=EntityType.PERSON,
            label="Johannes",
            resolution_status=ResolutionStatus.AMBIGUOUS,
            candidate_targets=(LocalEntityTarget("a1b2c3"),),
        )


@pytest.mark.parametrize(
    "status", [ResolutionStatus.UNRESOLVED, ResolutionStatus.REJECTED]
)
def test_non_match_mentions_cannot_define_resolved_target(
    status: ResolutionStatus,
) -> None:
    with pytest.raises(
        ValueError,
        match=f"{status.value} mention cannot define a resolved target",
    ):
        Mention(
            source="tei",
            locator="//persName[1]",
            entity_type=EntityType.PERSON,
            label="Johannes",
            resolution_status=status,
            resolved_target=LocalEntityTarget("a1b2c3"),
        )
