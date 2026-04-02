"""TOML-backed persistence for normalized source records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib

from onomasticon.core.entities import (
    EntityType,
    OrganizationSubtype,
    PlaceSubtype,
)
from onomasticon.core.repository import (
    _dump_appellations,
    _dump_identifiers,
    _parse_appellations,
    _parse_identifiers,
    _dump_reference,
    EntityValidationError,
    EntityWriteError,
    _optional_string,
    _parse_statements,
    _quote_string,
    _require_string,
    _require_table,
)
from onomasticon.core.statements import (
    DateValue,
    EntityValue,
    IdentifierValue,
    LanguageTagValue,
    Reference,
    SexValue,
    Statement,
    StatementStatus,
    TextValue,
)
from onomasticon.sources.records import SourceRecord


@dataclass(slots=True, frozen=True)
class SourceLayout:
    """Path policy for normalized source records."""

    root: Path
    sources_directory: str = "sources"

    def source_record_path(self, source: str, record_id: str) -> Path:
        """Return the canonical path for one source record."""
        return self.root / self.sources_directory / source / f"{record_id}.toml"


@dataclass(slots=True, frozen=True)
class SourceRecordRepository:
    """Load and serialize normalized source records."""

    layout: SourceLayout

    def loads(self, content: str) -> SourceRecord:
        try:
            data = _require_table(tomllib.loads(content))
        except tomllib.TOMLDecodeError as exc:
            msg = "Invalid TOML source record."
            raise EntityValidationError(msg) from exc
        return _source_record_from_mapping(data)

    def load(self, path: Path) -> SourceRecord:
        return self.loads(path.read_text())

    def dumps(self, record: SourceRecord) -> str:
        lines = [
            f"source = {_quote_string(record.source)}",
            f"record_id = {_quote_string(record.record_id)}",
        ]
        if record.entity_type is not None:
            lines.append(f"type = {_quote_string(record.entity_type.value)}")
        if record.note is not None:
            lines.append(f"note = {_quote_string(record.note)}")
        lines.extend(_dump_appellations(record.appellations))
        lines.extend(_dump_identifiers(record.identifiers))
        lines.extend(
            _dump_source_statements(
                record.statements,
                source=record.source,
                record_id=record.record_id,
            )
        )
        return "\n".join(lines) + "\n"

    def dump(
        self,
        record: SourceRecord,
        path: Path | None = None,
        *,
        overwrite: bool = False,
    ) -> Path:
        destination = path or self.layout.source_record_path(
            record.source, record.record_id
        )
        expected_name = f"{record.record_id}.toml"
        if destination.name != expected_name:
            msg = f"Source record {record.record_id} must be written to a file named {expected_name}."
            raise EntityWriteError(msg)
        if destination.exists() and not overwrite:
            msg = f"Refusing to overwrite existing source record file: {destination}."
            raise EntityWriteError(msg)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.dumps(record))
        return destination


def _source_record_from_mapping(data: dict[str, object]) -> SourceRecord:
    allowed_keys = {
        "source",
        "record_id",
        "type",
        "appellations",
        "identifiers",
        "note",
        "statements",
    }
    extra_keys = set(data) - allowed_keys
    if extra_keys:
        extras = ", ".join(sorted(extra_keys))
        msg = f"Unexpected source record fields: {extras}."
        raise EntityValidationError(msg)
    entity_type_raw = _optional_string(data, "type")
    try:
        entity_type = (
            EntityType(entity_type_raw) if entity_type_raw is not None else None
        )
    except ValueError as exc:
        msg = f"Unknown type: {entity_type_raw}."
        raise EntityValidationError(msg) from exc
    return SourceRecord(
        source=_require_string(data, "source"),
        record_id=_require_string(data, "record_id"),
        entity_type=entity_type,
        subtype=_parse_source_record_subtype(entity_type),
        appellations=_parse_appellations(data.get("appellations")),
        identifiers=_parse_identifiers(data.get("identifiers")),
        statements=_parse_source_statements(
            data.get("statements"),
            source=_require_string(data, "source"),
            record_id=_require_string(data, "record_id"),
        ),
        note=_optional_string(data, "note"),
    )


def _parse_source_statements(
    raw: object,
    *,
    source: str,
    record_id: str,
) -> tuple[Statement, ...]:
    statements = _parse_statements(raw)
    normalized: list[Statement] = []
    for statement in statements:
        references = tuple(
            _normalize_reference(reference, source=source, record_id=record_id)
            for reference in statement.references
        )
        normalized.append(
            Statement(
                property=statement.property,
                value=statement.value,
                references=references,
                status=statement.status,
                certainty=statement.certainty,
                note=statement.note,
            )
        )
    return tuple(normalized)


def _normalize_reference(
    reference: Reference,
    *,
    source: str,
    record_id: str,
) -> Reference:
    if reference.record is None and reference.source == source:
        return Reference(
            source=reference.source,
            record=record_id,
            locator=reference.locator,
            note=reference.note,
        )
    return reference


def _dump_source_statements(
    statements: tuple[Statement, ...],
    *,
    source: str,
    record_id: str,
) -> list[str]:
    lines: list[str] = []
    for statement in statements:
        lines.append("[[statements]]")
        lines.append(f"property = {_quote_string(statement.property)}")
        match statement.value:
            case EntityValue(entity_id=entity_id):
                lines.append(f"entity = {_quote_string(entity_id)}")
            case IdentifierValue(identifier=identifier):
                lines.append(
                    "identifier = "
                    f"{{ scheme = {_quote_string(identifier.scheme)}, value = {_quote_string(identifier.value)} }}"
                )
            case TextValue(text=text):
                lines.append(f"text = {_quote_string(text)}")
            case LanguageTagValue(language_tag=language_tag):
                lines.append(f"lang = {_quote_string(language_tag)}")
            case DateValue(temporal=temporal):
                if temporal.label is None:
                    lines.append(f"date = {_quote_string(temporal.edtf)}")
                else:
                    lines.append(
                        "date = "
                        f"{{ edtf = {_quote_string(temporal.edtf)}, label = {_quote_string(temporal.label)} }}"
                    )
            case SexValue(sex=sex):
                lines.append(f"sex = {_quote_string(sex.value)}")
        if statement.note is not None:
            lines.append(f"note = {_quote_string(statement.note)}")
        if statement.status is not StatementStatus.ACCEPTED:
            lines.append(f"status = {_quote_string(statement.status.value)}")
        if statement.certainty is not None:
            lines.append(f"certainty = {_quote_string(statement.certainty.value)}")
        if statement.references:
            refs = ", ".join(
                _dump_source_reference(
                    reference,
                    source=source,
                    record_id=record_id,
                )
                for reference in statement.references
            )
            lines.append(f"refs = [{refs}]")
    return lines


def _dump_source_reference(
    reference: Reference,
    *,
    source: str,
    record_id: str,
) -> str:
    if (
        reference.record == record_id
        and reference.source == source
        and reference.locator is not None
    ):
        compact = Reference(
            source=reference.source,
            locator=reference.locator,
            note=reference.note,
        )
        return _dump_reference(compact)
    return _dump_reference(reference)


def _parse_source_record_subtype(
    entity_type: EntityType | None,
) -> PlaceSubtype | OrganizationSubtype | None:
    match entity_type:
        case EntityType.COUNTRY:
            return PlaceSubtype.COUNTRY
        case EntityType.RELIGIOUS_ORDER:
            return OrganizationSubtype.RELIGIOUS_ORDER
        case _:
            return None
