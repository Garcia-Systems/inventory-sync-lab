from inventory_sim.inventory import InventoryState
from inventory_sim.stale_snapshots import run_stale_snapshots_scenario


def test_authority_changes_while_original_snapshot_waits() -> None:
    result = run_stale_snapshots_scenario()

    assert result.original_authority == InventoryState(10, 3)
    assert result.request.authoritative_state == result.original_authority
    assert result.processing_starts[1].arrived_at == 1
    assert result.processing_starts[1].started_at == 3
    assert result.current_authority == InventoryState(15, 3)
    assert result.request.authoritative_state == InventoryState(10, 3)


def test_successful_projection_matches_snapshot_not_current_authority() -> None:
    result = run_stale_snapshots_scenario()
    inspection = result.inspection

    assert result.completions[1].completed_at == 6
    assert inspection.resulting_projection.state == inspection.request_snapshot
    assert inspection.resulting_projection.state != inspection.current_authority
    assert result.completions[1].available_difference_after == 0


def test_stale_snapshot_scenario_is_deterministic() -> None:
    first = run_stale_snapshots_scenario()
    second = run_stale_snapshots_scenario()

    assert first == second
    assert [execution.time for execution in first.scheduler_executions] == [
        0,
        1,
        2,
        3,
        6,
    ]
