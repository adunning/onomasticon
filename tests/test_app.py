from __future__ import annotations

from pathlib import Path

from onomasticon.app import OnomasticonApp


def test_app_builds_repository_from_root() -> None:
    app = OnomasticonApp.from_root(Path("/repo"))

    assert app.repository.layout.root == Path("/repo")
    assert app.repository.layout.entities_directory == "entities"
