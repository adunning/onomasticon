"""TOML-backed persistence for canonical entities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from secrets import choice
import tomllib

from onomasticon.core.entities import (
    AnyEntity,
    Entity,
    EntityType,
    Expression,
    Item,
    LOCAL_IDENTIFIER_LENGTH,
    Manifestation,
    Organization,
    Person,
    Place,
    Work,
)

_IDENTIFIER_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"
DEFAULT_ID_MINT_ATTEMPTS = 64


class RepositoryError(Exception):
    """Base class for repository-layer errors."""


class EntityValidationError(RepositoryError, ValueError):
    """Raised when an entity document fails repository validation."""


class IdentifierCollisionError(RepositoryError):
    """Raised when ID minting exhausts its retry budget."""


class EntityWriteError(RepositoryError):
    """Raised when repository write semantics are violated."""


@dataclass(slots=True, frozen=True)
class RepositoryLayout:
    """Path policy for the Git-backed entity repository."""

    root: Path
    entities_directory: str = "entities"

    def entity_path(self, entity_id: str) -> Path:
        """Return the canonical path for one entity file."""
        return self.root / self.entities_directory / f"{entity_id}.toml"

    def entity_exists(self, entity_id: str) -> bool:
        """Return whether the given entity identifier is already present."""
        return self.entity_path(entity_id).exists()


@dataclass(slots=True, frozen=True)
class EntityRepository:
    """Load and serialize canonical entity records."""

    layout: RepositoryLayout

    def loads(self, content: str) -> AnyEntity:
        """Parse one entity from TOML text."""
        try:
            data = _require_table(tomllib.loads(content))
        except tomllib.TOMLDecodeError as exc:
            msg = "Invalid TOML entity document."
            raise EntityValidationError(msg) from exc
        return _entity_from_mapping(data)

    def load(self, path: Path) -> AnyEntity:
        """Load one entity from a TOML file."""
        return self.loads(path.read_text())

    def dumps(self, entity: AnyEntity) -> str:
        """Serialize one entity to TOML."""
        lines = [f'id = {self._quote(entity.id)}']
        entity_type = _entity_type_for(entity)
        if entity_type is not None:
            lines.append(f'entity_type = {self._quote(entity_type.value)}')
        if entity.redirect is not None:
            lines.append(f'redirect = {self._quote(entity.redirect)}')
        if entity.note is not None:
            lines.append(f'note = {self._quote(entity.note)}')
        return "\n".join(lines) + "\n"

    def dump(
        self,
        entity: AnyEntity,
        path: Path | None = None,
        *,
        overwrite: bool = False,
    ) -> Path:
        """Write one entity to disk and return the path used."""
        destination = path or self.layout.entity_path(entity.id)
        expected_name = f"{entity.id}.toml"
        if destination.name != expected_name:
            msg = f"Entity {entity.id} must be written to a file named {expected_name}."
            raise EntityWriteError(msg)
        if destination.exists() and not overwrite:
            msg = f"Refusing to overwrite existing entity file: {destination}."
            raise EntityWriteError(msg)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.dumps(entity))
        return destination

    def mint_id(self, *, max_attempts: int = DEFAULT_ID_MINT_ATTEMPTS) -> str:
        """Mint a new six-character local identifier with collision checking."""
        for _ in range(max_attempts):
            candidate = "".join(choice(_IDENTIFIER_ALPHABET) for _ in range(LOCAL_IDENTIFIER_LENGTH))
            if not self.layout.entity_exists(candidate):
                return candidate
        msg = f"Unable to mint a unique entity identifier after {max_attempts} attempts."
        raise IdentifierCollisionError(msg)

    @staticmethod
    def _quote(value: str) -> str:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'


def _entity_type_for(entity: AnyEntity) -> EntityType | None:
    match entity:
        case Person():
            return EntityType.PERSON
        case Place():
            return EntityType.PLACE
        case Organization():
            return EntityType.ORGANIZATION
        case Work():
            return EntityType.WORK
        case Expression():
            return EntityType.EXPRESSION
        case Manifestation():
            return EntityType.MANIFESTATION
        case Item():
            return EntityType.ITEM
        case Entity():
            return None


def _entity_from_mapping(data: dict[str, object]) -> AnyEntity:
    allowed_keys = {"id", "entity_type", "redirect", "note"}
    extra_keys = set(data) - allowed_keys
    if extra_keys:
        extras = ", ".join(sorted(extra_keys))
        msg = f"Unexpected entity fields: {extras}."
        raise EntityValidationError(msg)

    entity_id = _require_string(data, "id")
    entity_type_raw = _optional_string(data, "entity_type")
    redirect = _optional_string(data, "redirect")
    note = _optional_string(data, "note")

    try:
        entity_type = EntityType(entity_type_raw) if entity_type_raw is not None else None
    except ValueError as exc:
        msg = f"Unknown entity_type: {entity_type_raw}."
        raise EntityValidationError(msg) from exc

    match entity_type:
        case EntityType.PERSON:
            return Person(id=entity_id, redirect=redirect, note=note)
        case EntityType.PLACE:
            return Place(id=entity_id, redirect=redirect, note=note)
        case EntityType.ORGANIZATION:
            return Organization(id=entity_id, redirect=redirect, note=note)
        case EntityType.WORK:
            return Work(id=entity_id, redirect=redirect, note=note)
        case EntityType.EXPRESSION:
            return Expression(id=entity_id, redirect=redirect, note=note)
        case EntityType.MANIFESTATION:
            return Manifestation(id=entity_id, redirect=redirect, note=note)
        case EntityType.ITEM:
            return Item(id=entity_id, redirect=redirect, note=note)
        case None:
            return Entity(id=entity_id, redirect=redirect, note=note)


def _require_table(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict):
        msg = "Expected a TOML table."
        raise EntityValidationError(msg)
    table: dict[str, object] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            msg = "Expected a TOML table with string keys."
            raise EntityValidationError(msg)
        table[key] = value
    return table


def _require_string(data: dict[str, object], key: str) -> str:
    raw = data.get(key)
    if not isinstance(raw, str) or not raw.strip():
        msg = f"Expected '{key}' to be a non-empty string."
        raise EntityValidationError(msg)
    return raw


def _optional_string(data: dict[str, object], key: str) -> str | None:
    raw = data.get(key)
    if raw is None:
        return None
    if not isinstance(raw, str):
        msg = f"Expected '{key}' to be a string."
        raise EntityValidationError(msg)
    return raw
