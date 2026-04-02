"""Models for source mentions and lightweight reconciliation outcomes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from onomasticon.core.appellations import Appellation
from onomasticon.core.entities import EntityType
from onomasticon.core.identifiers import Identifier
from onomasticon.core.local_ids import validate_local_identifier
from onomasticon.core.properties import property_allowed_for_entity_type
from onomasticon.core.statements import Certainty, Reference, Statement
from onomasticon.core.validation import optional_string, require_non_empty_string


@dataclass(slots=True, frozen=True)
class Mention:
    """One extracted occurrence of a scholarly entity-like mention in a source.

    Mentions are intentionally separate from canonical entities. They are
    anchored in source context and do not require a local Onomasticon ID.
    """

    source: str
    record: str | None = None
    locator: str | None = None
    label: str | None = None
    entity_type: EntityType | None = None
    appellations: tuple[Appellation, ...] = field(default_factory=tuple)
    identifiers: tuple[Identifier, ...] = field(default_factory=tuple)
    statements: tuple[Statement, ...] = field(default_factory=tuple)
    resolution_status: ResolutionStatus | str = "unresolved"
    resolved_target: MentionTarget | None = None
    candidate_targets: tuple[MentionTarget, ...] = field(default_factory=tuple)
    certainty: Certainty | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        require_non_empty_string(self.source, field_name="source")
        if self.record is not None:
            require_non_empty_string(self.record, field_name="record")
        if self.locator is not None:
            require_non_empty_string(self.locator, field_name="locator")
        if self.record is None and self.locator is None:
            msg = "mention must define at least one of record or locator."
            raise ValueError(msg)
        if self.label is not None:
            optional_string(self.label, field_name="label")
        if self.entity_type is not None:
            for statement in self.statements:
                if not property_allowed_for_entity_type(
                    statement.property,
                    self.entity_type,
                ):
                    property_name = getattr(
                        statement.property,
                        "value",
                        statement.property,
                    )
                    msg = (
                        f"Property {property_name!r} is not allowed on "
                        f"{self.entity_type.value} mentions."
                    )
                    raise ValueError(msg)
        status_value = require_non_empty_string(
            self.resolution_status,
            field_name="resolution_status",
        )
        try:
            normalized_status = ResolutionStatus(status_value)
        except ValueError as exc:
            msg = f"Unknown resolution status: {status_value}."
            raise ValueError(msg) from exc
        object.__setattr__(self, "resolution_status", normalized_status)
        if normalized_status is ResolutionStatus.MATCHED:
            if self.resolved_target is None:
                msg = "matched mention must define a resolved target."
                raise ValueError(msg)
            if self.candidate_targets:
                msg = "matched mention cannot define alternative candidates."
                raise ValueError(msg)
        elif normalized_status is ResolutionStatus.AMBIGUOUS:
            if self.resolved_target is not None:
                msg = "ambiguous mention cannot define a resolved target."
                raise ValueError(msg)
            if len(self.candidate_targets) < 2:
                msg = "ambiguous mention must define at least two candidate targets."
                raise ValueError(msg)
        else:
            if self.resolved_target is not None:
                msg = f"{normalized_status.value} mention cannot define a resolved target."
                raise ValueError(msg)
            if self.candidate_targets:
                msg = f"{normalized_status.value} mention cannot define candidate targets."
                raise ValueError(msg)
        if self.note is not None:
            optional_string(self.note, field_name="note")

    @property
    def reference(self) -> Reference:
        """Return this mention's source anchor as a normalized reference."""

        return Reference(
            source=self.source,
            record=self.record,
            locator=self.locator,
        )


@dataclass(slots=True, frozen=True)
class LocalEntityTarget:
    """A reconciliation target pointing to one canonical local entity."""

    entity_id: str

    def __post_init__(self) -> None:
        validate_local_identifier(self.entity_id, field_name="entity_id")


@dataclass(slots=True, frozen=True)
class ExternalAuthorityTarget:
    """A reconciliation target pointing to one external authority identifier."""

    identifier: Identifier
    label: str | None = None

    def __post_init__(self) -> None:
        if self.label is not None:
            optional_string(self.label, field_name="label")


type MentionTarget = LocalEntityTarget | ExternalAuthorityTarget


class ResolutionStatus(StrEnum):
    """Controlled reconciliation outcomes for one mention."""

    MATCHED = "matched"
    AMBIGUOUS = "ambiguous"
    UNRESOLVED = "unresolved"
    REJECTED = "rejected"
