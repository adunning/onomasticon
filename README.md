# Onomasticon

Onomasticon is a Git-backed scholarly entity repository implemented in Python 3.14. TOML files in Git are the canonical editable source of truth.

## Current scope

This first commit focuses on the minimal application framework and the core concept of an entity.

An entity currently has only one universal requirement:

- a stable opaque six-character local identifier

Everything else is optional at this stage. In particular, an entity may simply redirect to another entity.

## Principles

- TOML is the canonical datastore
- one entity lives in one file
- the repository in Git is the long-lived source of truth
- validation is handled with the standard library and explicit repository checks
- the core remains thin, object-oriented, and output-independent
- WEMI, statements, provenance, and richer schema layers will be added on top of this baseline

## Package structure

- `src/onomasticon/app.py`: thin application shell
- `src/onomasticon/cli.py`: thin `argparse` command-line interface
- `src/onomasticon/core/entities.py`: minimal canonical entity model
- `src/onomasticon/core/repository.py`: TOML parsing, serialization, and repository layout

## Example entity

```toml
id = "a1b2c3"
type = "person"
```

`type` belongs to the TOML document layer so the repository can reconstruct
the proper domain class. The domain objects themselves do not duplicate that field.

## Example redirect

```toml
id = "b2c3d4"
redirect = "a1b2c3"
```

## Development

Run the test suite with:

```bash
uv run pytest
```

Optional local hook setup:

```bash
git config core.hooksPath .githooks
```

The pre-commit hook runs Ruff formatting, Ruff linting, and `ty` type checking. If formatting changes files, it stops so the updated files can be reviewed and staged before committing again.

## Repository

Canonical repository: [adunning/onomasticon](https://github.com/adunning/onomasticon)
