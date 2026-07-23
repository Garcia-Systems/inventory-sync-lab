from inventory_sim.inventory import InventoryState
from inventory_sim.multiple_projections import run_multiple_projections_scenario
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import ProjectionRegistry


def test_registry_registers_multiple_named_projections() -> None:
    registry = ProjectionRegistry(
        tuple(
            InventoryProjection(name, InventoryState(10, 2))
            for name in ("Storefront", "Warehouse", "Reporting")
        )
    )

    assert tuple(item.system for item in registry.projections) == (
        "Storefront",
        "Warehouse",
        "Reporting",
    )


def test_updates_across_projections_are_deterministic() -> None:
    first = run_multiple_projections_scenario()
    second = run_multiple_projections_scenario()

    assert first == second
    assert {item.revision.value for item in first.final_projections} == {6}
    assert {item.projection.state.available for item in first.final_projections} == {18}


def test_projection_state_is_independent() -> None:
    result = run_multiple_projections_scenario()

    assert len({id(item.projection) for item in result.final_projections}) == 3
    assert tuple(item.projection.system for item in result.final_projections) == (
        "Storefront",
        "Warehouse",
        "Reporting",
    )


def test_stale_rejection_is_isolated_to_storefront() -> None:
    result = run_multiple_projections_scenario()
    second_batch = result.inspections[3:6]

    assert [item.projection_updated for item in second_batch] == [False, True, True]
    assert (
        result.completions[3].projection_after
        == result.completions[3].projection_before
    )
    assert (
        result.completions[4].projection_after
        != result.completions[4].projection_before
    )
    assert (
        result.completions[5].projection_after
        != result.completions[5].projection_before
    )
    assert result.final_queue_depth == 0
