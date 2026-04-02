from __future__ import annotations

from pathlib import Path

from onomasticon.cli import build_parser, main


def test_cli_parses_validate_command() -> None:
    parser = build_parser()

    args = parser.parse_args(["validate", "records/entity.toml"])

    assert args.command == "validate"
    assert args.path == Path("records/entity.toml")


def test_cli_main_validates_one_entity_file(tmp_path: Path) -> None:
    entity_path = tmp_path / "entity.toml"
    entity_path.write_text('id = "a1b2c3"\n')

    assert main(["validate", str(entity_path)]) == 0
