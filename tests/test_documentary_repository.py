from __future__ import annotations

from pathlib import Path

import pytest

from onomasticon.core.appellations import Appellation, AppellationKind
from onomasticon.core.documentary import (
    Component,
    ContentItem,
    DocumentaryType,
    Holding,
)
from onomasticon.core.entities import Organization, Person, Place
from onomasticon.core.identifiers import Identifier
from onomasticon.core.properties import StatementProperty
from onomasticon.core.repository import (
    EntityRepository,
    EntityValidationError,
    EntityWriteError,
    RepositoryLayout,
)
from onomasticon.core.statements import DateValue, EntityValue, Statement, TextValue
from onomasticon.core.temporal import TemporalValue
from onomasticon.documentary import DocumentaryLayout, DocumentaryRepository


def test_documentary_repository_round_trips_holding() -> None:
    repository = DocumentaryRepository(layout=DocumentaryLayout(root=Path("/repo")))
    holding = Holding(
        id="a1b2c3",
        identifiers=(Identifier("mmol", "MS_LAUD_MISC_108"),),
        statements=(
            Statement(
                property=StatementProperty.SHELFMARK,
                value=TextValue("MS Laud misc. 108"),
            ),
            Statement(
                property=StatementProperty.ORIGIN_DATE,
                value=DateValue(TemporalValue("1100")),
            ),
        ),
        note="Imported from MMOL.",
    )

    serialized = repository.dumps(holding)
    reparsed = repository.loads(serialized, documentary_type=DocumentaryType.HOLDING)

    assert reparsed == holding
    assert 'property = "shelfmark"' in serialized
    assert 'property = "origin_date"' in serialized


def test_documentary_repository_round_trips_component_and_content_item() -> None:
    repository = DocumentaryRepository(layout=DocumentaryLayout(root=Path("/repo")))
    component = Component(
        id="b1c2d3",
        holding_id="a1b2c3",
        statements=(
            Statement(
                property=StatementProperty.LOCATOR,
                value=TextValue("ff. 1-48"),
            ),
        ),
    )
    content_item = ContentItem(
        id="c1d2e3",
        holding_id="a1b2c3",
        component_id="b1c2d3",
        parent_content_item_id="d1e2f3",
        appellations=(
            Appellation(kind=AppellationKind.TITLE, value="Boethius", language="la"),
        ),
        statements=(
            Statement(
                property=StatementProperty.LOCUS,
                value=TextValue("ff. 1r-20v"),
            ),
        ),
    )

    component_serialized = repository.dumps(component)
    content_item_serialized = repository.dumps(content_item)

    assert (
        repository.loads(
            component_serialized,
            documentary_type=DocumentaryType.COMPONENT,
        )
        == component
    )
    assert (
        repository.loads(
            content_item_serialized,
            documentary_type=DocumentaryType.CONTENT_ITEM,
        )
        == content_item
    )
    assert 'holding = "a1b2c3"' in component_serialized
    assert 'component = "b1c2d3"' in content_item_serialized
    assert 'parent_content_item = "d1e2f3"' in content_item_serialized


def test_documentary_layout_uses_separate_directories() -> None:
    layout = DocumentaryLayout(root=Path("/repo"))

    assert layout.holding_path("a1b2c3") == Path("/repo/holdings/a1b2c3.toml")
    assert layout.component_path("b1c2d3") == Path("/repo/components/b1c2d3.toml")
    assert layout.content_item_path("c1d2e3") == Path("/repo/content-items/c1d2e3.toml")


def test_documentary_repository_can_write_and_reload_units(tmp_path: Path) -> None:
    repository = DocumentaryRepository(layout=DocumentaryLayout(root=tmp_path))

    holding = Holding(id="a1b2c3")
    component = Component(id="b1c2d3", holding_id="a1b2c3")
    parent_item = ContentItem(id="d1e2f3", holding_id="a1b2c3", component_id="b1c2d3")
    content_item = ContentItem(
        id="c1d2e3",
        holding_id="a1b2c3",
        component_id="b1c2d3",
        parent_content_item_id="d1e2f3",
    )

    holding_path = repository.dump(holding)
    component_path = repository.dump(component)
    repository.dump(parent_item)
    content_item_path = repository.dump(content_item)

    assert holding_path == tmp_path / "holdings" / "a1b2c3.toml"
    assert component_path == tmp_path / "components" / "b1c2d3.toml"
    assert content_item_path == tmp_path / "content-items" / "c1d2e3.toml"
    assert repository.load(holding_path) == holding
    assert repository.load(component_path) == component
    assert repository.load(content_item_path) == content_item


def test_documentary_repository_validates_missing_holding_for_component(
    tmp_path: Path,
) -> None:
    repository = DocumentaryRepository(layout=DocumentaryLayout(root=tmp_path))
    component = Component(id="b1c2d3", holding_id="a1b2c3")

    with pytest.raises(
        EntityValidationError, match="references missing holding 'a1b2c3'"
    ):
        repository.dump(component)


def test_documentary_repository_validates_component_parent_holding_match(
    tmp_path: Path,
) -> None:
    repository = DocumentaryRepository(layout=DocumentaryLayout(root=tmp_path))
    repository.dump(Holding(id="a1b2c3"))
    repository.dump(Holding(id="d1e2f3"))
    repository.dump(Component(id="b1c2d3", holding_id="a1b2c3"))
    component = Component(
        id="c1d2e3", holding_id="d1e2f3", parent_component_id="b1c2d3"
    )

    with pytest.raises(EntityValidationError, match="in a different holding"):
        repository.dump(component)


def test_documentary_repository_validates_content_item_component_holding_match(
    tmp_path: Path,
) -> None:
    repository = DocumentaryRepository(layout=DocumentaryLayout(root=tmp_path))
    repository.dump(Holding(id="a1b2c3"))
    repository.dump(Holding(id="d1e2f3"))
    repository.dump(Component(id="b1c2d3", holding_id="a1b2c3"))
    item = ContentItem(id="c1d2e3", holding_id="d1e2f3", component_id="b1c2d3")

    with pytest.raises(EntityValidationError, match="in a different holding"):
        repository.dump(item)


def test_documentary_repository_validates_parent_content_item_holding_match(
    tmp_path: Path,
) -> None:
    repository = DocumentaryRepository(layout=DocumentaryLayout(root=tmp_path))
    repository.dump(Holding(id="a1b2c3"))
    repository.dump(Holding(id="d1e2f3"))
    repository.dump(ContentItem(id="b1c2d3", holding_id="a1b2c3"))
    item = ContentItem(
        id="c1d2e3",
        holding_id="d1e2f3",
        parent_content_item_id="b1c2d3",
    )

    with pytest.raises(
        EntityValidationError,
        match="parent content item 'b1c2d3' in a different holding",
    ):
        repository.dump(item)


def test_documentary_repository_validates_parent_content_item_component_match(
    tmp_path: Path,
) -> None:
    repository = DocumentaryRepository(layout=DocumentaryLayout(root=tmp_path))
    repository.dump(Holding(id="a1b2c3"))
    repository.dump(Component(id="b1c2d3", holding_id="a1b2c3"))
    repository.dump(Component(id="c1d2e3", holding_id="a1b2c3"))
    repository.dump(
        ContentItem(
            id="d1e2f3",
            holding_id="a1b2c3",
            component_id="b1c2d3",
        )
    )
    item = ContentItem(
        id="e1f2g3",
        holding_id="a1b2c3",
        component_id="c1d2e3",
        parent_content_item_id="d1e2f3",
    )

    with pytest.raises(EntityValidationError, match="in a different component"):
        repository.dump(item)


def test_documentary_repository_validates_entity_targets(tmp_path: Path) -> None:
    entity_repository = EntityRepository(layout=RepositoryLayout(root=tmp_path))
    documentary_repository = DocumentaryRepository(
        layout=DocumentaryLayout(root=tmp_path)
    )

    entity_repository.dump(Organization(id="o1a2b3"))
    entity_repository.dump(Place(id="p1a2b3"))
    documentary_repository.dump(
        Holding(
            id="a1b2c3",
            statements=(
                Statement(
                    property=StatementProperty.REPOSITORY,
                    value=EntityValue("o1a2b3"),
                ),
                Statement(
                    property=StatementProperty.SETTLEMENT,
                    value=EntityValue("p1a2b3"),
                ),
            ),
        )
    )

    entity_repository.dump(Person(id="z1y2x3"))
    item = ContentItem(
        id="c1d2e3",
        holding_id="a1b2c3",
        statements=(
            Statement(
                property=StatementProperty.AUTHOR,
                value=EntityValue("z1y2x3"),
            ),
        ),
    )

    path = documentary_repository.dump(item)
    assert documentary_repository.load(path) == item


def test_documentary_repository_rejects_invalid_entity_targets(tmp_path: Path) -> None:
    entity_repository = EntityRepository(layout=RepositoryLayout(root=tmp_path))
    documentary_repository = DocumentaryRepository(
        layout=DocumentaryLayout(root=tmp_path)
    )

    documentary_repository.dump(Holding(id="a1b2c3"))
    entity_repository.dump(Place(id="p1a2b3"))
    item = ContentItem(
        id="c1d2e3",
        holding_id="a1b2c3",
        statements=(
            Statement(
                property=StatementProperty.AUTHOR,
                value=EntityValue("p1a2b3"),
            ),
        ),
    )

    with pytest.raises(
        EntityValidationError,
        match=r"Property 'author' on documentary unit c1d2e3 must point to one of \[person\], not 'place'",
    ):
        documentary_repository.dump(item)


def test_documentary_repository_rejects_missing_entity_targets(tmp_path: Path) -> None:
    repository = DocumentaryRepository(layout=DocumentaryLayout(root=tmp_path))
    repository.dump(Holding(id="a1b2c3"))
    item = ContentItem(
        id="c1d2e3",
        holding_id="a1b2c3",
        statements=(
            Statement(
                property=StatementProperty.AUTHOR,
                value=EntityValue("p1a2b3"),
            ),
        ),
    )

    with pytest.raises(
        EntityValidationError,
        match=r"references missing entity 'p1a2b3' via property 'author'",
    ):
        repository.dump(item)


def test_documentary_repository_enforces_canonical_filename(tmp_path: Path) -> None:
    repository = DocumentaryRepository(layout=DocumentaryLayout(root=tmp_path))
    holding = Holding(id="a1b2c3")

    with pytest.raises(
        EntityWriteError, match="must be written to a file named a1b2c3.toml"
    ):
        repository.dump(holding, path=tmp_path / "holdings" / "wrong.toml")
