"""Thin command-line interface for Onomasticon."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from onomasticon.app import OnomasticonApp


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level command-line parser."""
    parser = argparse.ArgumentParser(
        prog="onomasticon",
        description="Work with the Onomasticon scholarly model through local storage adapters.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate one canonical entity record file.",
    )
    validate_parser.add_argument(
        "path", type=Path, help="Path to the canonical entity record file."
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line application."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate":
        app = OnomasticonApp.from_root(Path.cwd())
        app.repository.load(args.path)
    return 0
