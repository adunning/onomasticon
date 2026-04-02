# Onomasticon

Onomasticon is a Git-backed scholarly entity repository implemented in Python 3.14. TOML files in Git are the canonical editable source of truth. The project is designed as an application with a reusable internal library, not merely as a CLI wrapper around a file format.

## Scope

The current code establishes the first serious architectural slice:

- one canonical entity per TOML file in Git
- one normalized source record per TOML file in `sources/`
- a thin CLI and application shell
- a technology-independent core model
- explicit repository parsing, serialization, and validation

The model is already oriented around scholarly assertions rather than flat record fields.

## Principles

- TOML is the canonical native datastore
- one record lives in one file
- the repository in Git is the long-lived source of truth
- the core remains output-independent
- identifiers, appellations, statements, and provenance are first-class objects
- statements are relational and provenance-bearing
- dates are validated as EDTF
- language tags are validated as BCP 47
- validation is explicit and local, with minimal dependencies where practical

## Current model

### Entities

Every entity has:

- `id`
- optional `type`
- optional `redirect`
- optional `appellations`
- optional `identifiers`
- optional `statements`
- optional `note`

The current persisted leaf types include:

- `person`
- `place`
- `country`
- `organization`
- `religious_order`
- `work`
- `expression`
- `manifestation`
- `item`

Leaf types such as `country` and `religious_order` are resolved internally to broader entity classes with the appropriate subtype.

### Appellations

Appellations are provenance-bearing designations, not just plain strings.

Each appellation may carry:

- a controlled `kind`
- structured `parts`
- an optional unstructured `display_value`
- language and script
- references
- status and certainty
- note

This allows one source to attest `Galfridus Chaucer` and another to attest `Geoffrey Chaucer` while keeping each form, its parts, and its provenance together.

### Statements

Statements are the core assertion model. Each statement has:

- a controlled `property`
- one typed value
- references
- optional qualifiers
- status
- certainty
- note

Current value kinds include:

- local entity reference
- external identifier
- text
- language tag
- EDTF temporal value
- controlled sex value
- controlled ascription value for qualifiers

Current qualifier support is intentionally narrow. The first controlled qualifier is:

- `ascription`

with values:

- `attributed`
- `pseudonymous`
- `misattributed`
- `anonymous`

This makes it possible to distinguish, for example, accepted authorship from merely attested or rejected attribution without flattening everything into one status field.

### Cross-entity validation

Canonical repository operations validate certain entity-valued relations against the local repository:

- `author` must point to a `person`
- `translator` must point to a `person`
- `nationality` must point to a `country`
- `religious_order` must point to a `religious_order`

These checks run when canonical entities are loaded from disk or written to disk, where repository context is available.

### Sources

Normalized source records live separately from canonical entities. They can carry:

- `source`
- `record_id`
- optional `type`
- optional appellations
- optional identifiers
- optional statements
- optional note

This keeps external-source normalization distinct from local canonical scholarship.

## Example canonical records

### Person

```toml
id = "a1b2c3"
type = "person"

[[appellations]]
kind = "preferred"
language = "en"
refs = [{ source = "wikidata", record = "Q12345" }]

[[appellations.parts]]
kind = "given"
value = "Geoffrey"

[[appellations.parts]]
kind = "family"
value = "Chaucer"

[[statements]]
property = "floruit"
date = "123X/1245"
status = "accepted"
certainty = "medium"
```

### Work with multiple authors and attestation date

```toml
id = "d4e5f6"
type = "work"

[[appellations]]
kind = "title"
language = "la"
display_value = "De tribulatione"

[[statements]]
property = "author"
entity = "a1b2c3"

[[statements]]
property = "author"
entity = "b2c3d4"
status = "attested_only"
qualifiers = [{ property = "ascription", ascription = "attributed" }]

[[statements]]
property = "attested"
date = "123X/1245"
status = "attested_only"
refs = [{ source = "mmol", record = "manuscript_12345" }]
```

Witness-specific observations such as incipits, explicits, rubrics, and final rubrics are not yet modelled separately. The current code can store them as appellations, but the intended long-term home for that material is a witness-level observation or attestation layer rather than the abstract `work` itself.

### Country

```toml
id = "g7h8i9"
type = "country"
```

### Redirect

```toml
id = "b2c3d4"
redirect = "a1b2c3"
```

## Package structure

- `src/onomasticon/app.py`: thin application shell
- `src/onomasticon/cli.py`: thin `argparse` command-line interface
- `src/onomasticon/core/entities.py`: canonical entity classes and subtypes
- `src/onomasticon/core/appellations.py`: provenance-bearing designations and structured name parts
- `src/onomasticon/core/identifiers.py`: external identifiers
- `src/onomasticon/core/statements.py`: typed scholarly statements, references, qualifiers, status, and certainty
- `src/onomasticon/core/temporal.py`: EDTF-backed temporal values
- `src/onomasticon/core/properties.py`: controlled statement property vocabulary and applicability rules
- `src/onomasticon/core/repository.py`: canonical entity parsing, serialization, and repository layout
- `src/onomasticon/sources/records.py`: normalized source-record model
- `src/onomasticon/sources/repository.py`: source-record parsing, serialization, and repository layout

## Development

Run the checks with:

```bash
uv run ruff check .
uv run ty check
uv run pytest
```

Optional local hook setup:

```bash
git config core.hooksPath .githooks
```

The pre-commit hook runs Ruff formatting, Ruff linting, and `ty` type checking. If formatting changes files, it stops so the updated files can be reviewed and staged before committing again.

## Repository

Canonical repository: [adunning/onomasticon](https://github.com/adunning/onomasticon)
