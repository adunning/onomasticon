"""TOML-backed persistence for normalized source records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib

from onomasticon.core.entities import EntityType
from onomasticon.core.repository import (
    EntityValidationError,
    EntityWriteError,
    _dump_statements,
    _optional_string,
    _parse_statements,
    _quote_string,
    _require_string,
    _require_table,
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
            lines.append(f"entity_type = {_quote_string(record.entity_type.value)}")
        if record.note is not None:
            lines.append(f"note = {_quote_string(record.note)}")
        lines.extend(_dump_statements(record.statements))
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
    allowed_keys = {"source", "record_id", "entity_type", "note", "statements"}
    extra_keys = set(data) - allowed_keys
    if extra_keys:
        extras = ", ".join(sorted(extra_keys))
        msg = f"Unexpected source record fields: {extras}."
        raise EntityValidationError(msg)
    entity_type_raw = _optional_string(data, "entity_type")
    try:
        entity_type = (
            EntityType(entity_type_raw) if entity_type_raw is not None else None
        )
    except ValueError as exc:
        msg = f"Unknown entity_type: {entity_type_raw}."
        raise EntityValidationError(msg) from exc
    return SourceRecord(
        source=_require_string(data, "source"),
        record_id=_require_string(data, "record_id"),
        entity_type=entity_type,
        statements=_parse_statements(data.get("statements")),
        note=_optional_string(data, "note"),
    )
