from inventory_sim.ordering import (
    revision_advances_projection,
    run_ordering_scenario,
)
from inventory_sim.revisions import InventoryRevision


def test_newer_revision_advances_projection() -> None:
    assert revision_advances_projection(
        request_revision=InventoryRevision(14),
        projection_revision=InventoryRevision(13),
    )


def test_older_revision_is_skipped() -> None:
    assert not revision_advances_projection(
        request_revision=InventoryRevision(13),
        projection_revision=InventoryRevision(14),
    )


def test_equal_revision_remains_idempotent() -> None:
    assert not revision_advances_projection(
        request_revision=InventoryRevision(14),
        projection_revision=InventoryRevision(14),
    )


def test_reversed_delivery_preserves_latest_projection() -> None:
    result = run_ordering_scenario()

    assert tuple(item.revision.value for item in result.deliveries) == (14, 13)
    assert tuple(item.projection_updated for item in result.deliveries) == (True, False)
    assert tuple(
        item.projection_revision_after.value for item in result.deliveries
    ) == (14, 14)
    assert result.final_projection.revision == result.authority.revision
    assert result.final_projection.projection.state == result.authority.state
    assert result.final_queue_depth == 0


def test_ordering_scenario_is_deterministic() -> None:
    assert run_ordering_scenario() == run_ordering_scenario()
