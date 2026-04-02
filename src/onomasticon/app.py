"""Application wiring for Onomasticon."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from onomasticon.core.repository import EntityRepository, RepositoryLayout


@dataclass(slots=True, frozen=True)
class OnomasticonApp:
    """Thin application shell around the canonical entity repository."""

    repository: EntityRepository

    @classmethod
    def from_root(cls, root: Path) -> "OnomasticonApp":
        """Build an application instance for one repository root."""
        layout = RepositoryLayout(root=root)
        return cls(repository=EntityRepository(layout=layout))
