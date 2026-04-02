# Onomasticon

Onomasticon is a scholarly entity and reconciliation system implemented in Python 3.14. Its stable centre is a canonical model for entities, appellations, identifiers, statements, provenance, and documentary structures. That model can be carried through different storage and exchange formats.

The current default deployment is a Git-backed TOML repository. That is one adapter, not the definition of the project.

## Scope

The current code establishes the first serious architectural slice:

- a canonical scholarly core model
- explicit ports for entity, documentary, and source-record stores
- default Git-backed TOML adapters for canonical entities, documentary units, and normalized source records
- a thin CLI and application shell over those adapters
- a technology-independent core model
- explicit parsing, serialization, and validation at the adapter boundary

The model is already oriented around scholarly assertions rather than flat record fields.

## Principles

- the canonical model is primary
- storage and exchange formats are adapters around that model
- the default local deployment is a Git-backed TOML repository
- one record lives in one file in the default TOML deployment
- the core remains carrier-independent
- identifiers, appellations, statements, and provenance are first-class objects
- statements are relational and provenance-bearing
- dates are validated as EDTF
- language tags are validated as BCP 47
- validation is explicit and local, with minimal dependencies where practical

## Deployment patterns

The project should support several distinct patterns without changing the core model:

- native repository: manage a local scholarly repository in TOML, JSON, or another canonical store
- ingest source: import external repertories, catalogues, editions, or spreadsheets into normalized records or transient matching inputs
- annotation target: read TEI, resolve names and works against local or external repertories, and write enriched TEI back out
- publication target: export structured data as JSON, TEI, or another downstream view

TEI therefore has more than one role:

- as source material to ingest from
- as an editorial document to annotate and round-trip
- as a publication format to project into

It should not be treated as merely another local datastore.

## Architecture

The intended architectural split is:

- `onomasticon.core`: canonical domain objects and validation rules
- store and codec ports: format-agnostic interfaces for persistence and serialisation
- TOML adapters: the present concrete implementation for local Git-backed work
- workflows: import, reconcile, annotate, publish

In this design, local entity creation is one possible outcome of reconciliation, not the default meaning of reconciliation.

## Canonical entities versus source mentions

Onomasticon now distinguishes clearly between:

- canonical local entities: curated first-class objects in the local repository, each with a stable local identifier
- source mentions: extracted occurrences such as TEI `persName`, `orgName`, `geogName`, `author`, or `title`, anchored in source context and not requiring a local identifier
- mention-level matching outcomes: lightweight fields on the mention recording a local target, an external authority, several candidates, or no target

This means internal PIDs are required for canonical local entities, but not for every extracted occurrence.

For example:

- a person in a local prosopography should receive a stable local identifier
- a `persName` in a TEI edition may remain a mention resolved to an external authority or an existing local entity, then be written back into the TEI without creating a new local object
- an imported repertory row may remain a normalized source record plus reconciliation evidence until there is a reason to promote it into the local canonical store

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
- an optional unstructured `value`
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

Store operations may validate certain entity-valued relations against the configured local entity store:

- `author` must point to a `person`
- `translator` must point to a `person`
- `nationality` must point to a `country`
- `religious_order` must point to a `religious_order`

These checks run when canonical entities are loaded from or written to a store that has the necessary local context.

### Sources

Normalized source records live separately from canonical entities. They can carry:

- `source`
- `record_id`
- optional `type`
- optional appellations
- optional identifiers
- optional statements
- optional note

This keeps external-source normalization distinct from local canonical scholarship. It also allows ingest workflows in which imported records are matched and reasoned over without being promoted immediately into local canonical entities.

### Mentions and matching

Source mentions model extracted occurrences in a document or source record. They are anchored by source, record, and or locator information and may carry appellations, identifiers, and statements as evidence for matching.

Each mention may then record whether it:

- matched one local canonical entity
- matched one external authority
- remained ambiguous among several candidates
- remained unresolved or was explicitly rejected

### Documentary units

Documentary units model the source-facing physical and descriptive structure used by
catalogues such as TEI `msDesc` records.

The current documentary types are:

- `holding`: a deliverable physical library unit such as a manuscript volume or printed book
- `component`: a physical sub-unit within one holding, corresponding for example to one `msPart`
- `content_item`: a descriptive unit located within a holding or component, corresponding for example to one `msItem`

`content_item` records may themselves be nested. This allows one aggregate item to contain
smaller identifiable items such as individual tales, sermons, or image cycles while keeping
those inner units first-class and independently referenceable.

Documentary store operations validate:

- `component.holding_id` must point to an existing `holding`
- `component.parent_component_id`, if present, must point to a component in the same holding
- `content_item.holding_id` must point to an existing `holding`
- `content_item.component_id`, if present, must point to a component in the same holding
- `content_item.parent_content_item_id`, if present, must point to a content item in the same holding

Certain documentary statement properties also validate canonical entity targets against the
configured local entity store:

- `repository` must point to an `organization`
- `settlement` must point to a `place` or `country`
- `origin_place` must point to a `place` or `country`
- `author` must point to a `person`
- `translator` must point to a `person`

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
value = "De tribulatione"

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

### Holding

```toml
id = "h1a2b3"

[[statements]]
property = "repository"
entity = "o1a2b3"

[[statements]]
property = "settlement"
entity = "p1a2b3"

[[statements]]
property = "shelfmark"
text = "MS Laud misc. 108"

[[identifiers]]
scheme = "mmol"
value = "MS_LAUD_MISC_108"
```

### Component

```toml
id = "c1d2e3"
holding = "h1a2b3"

[[statements]]
property = "locator"
text = "ff. 1-48"
```

### Nested content items

```toml
id = "m1n2o3"
holding = "h1a2b3"
component = "c1d2e3"

[[appellations]]
kind = "title"
value = "Canterbury Tales"
language = "en"
```

```toml
id = "p4q5r6"
holding = "h1a2b3"
component = "c1d2e3"
parent_content_item = "m1n2o3"

[[appellations]]
kind = "title"
value = "The Miller's Tale"
language = "en"

[[statements]]
property = "locus"
text = "ff. 12r-18v"

[[statements]]
property = "author"
entity = "a1b2c3"
status = "attested_only"
```

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

- `src/onomasticon/app.py`: application wiring for the default TOML deployment
- `src/onomasticon/cli.py`: thin `argparse` command-line interface
- `src/onomasticon/core/entities.py`: canonical entity classes and subtypes
- `src/onomasticon/core/appellations.py`: provenance-bearing designations and structured name parts
- `src/onomasticon/core/identifiers.py`: external identifiers
- `src/onomasticon/core/statements.py`: typed scholarly statements, references, qualifiers, status, and certainty
- `src/onomasticon/core/temporal.py`: EDTF-backed temporal values
- `src/onomasticon/core/properties.py`: controlled statement property vocabulary and applicability rules
- `src/onomasticon/core/reconciliation.py`: source mentions and reconciliation outcomes
- `src/onomasticon/core/ports.py`: format-agnostic storage and serialisation ports
- `src/onomasticon/core/repository.py`: default TOML adapter for canonical entities
- `src/onomasticon/core/documentary.py`: documentary models for holdings, components, and content items
- `src/onomasticon/documentary/repository.py`: default TOML adapter for documentary units
- `src/onomasticon/sources/records.py`: normalized source-record model
- `src/onomasticon/sources/repository.py`: default TOML adapter for source records

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
