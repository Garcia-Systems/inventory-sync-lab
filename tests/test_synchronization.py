from dataclasses import FrozenInstanceError

import pytest

from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve
from inventory_sim.projections import InventoryProjection
from inventory_sim.synchronization import (
    run_direct_synchronization_scenario,
    synchronize_directly,
)


def test_direct_synchronization_copies_authority_into_a_new_projection() -> None:
    authority = InventoryState(10, 3)
    original = InventoryProjection("website", InventoryState(10, 0))

    refreshed = synchronize_directly(projection=original, authoritative_state=authority)

    assert refreshed is not original
    assert refreshed.system == "website"
    assert refreshed.state is authority
    assert original.state == InventoryState(10, 0)
    assert authority == InventoryState(10, 3)
    comparison = refreshed.compare_to(authority)
    assert comparison.matches
    assert (
        comparison.on_hand_difference,
        comparison.reserved_difference,
        comparison.available_difference,
    ) == (0, 0, 0)


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (
            {"projection": object(), "authoritative_state": InventoryState(1, 0)},
            "projection must be an InventoryProjection",
        ),
        (
            {
                "projection": InventoryProjection("website", InventoryState(1, 0)),
                "authoritative_state": object(),
            },
            "authoritative_state must be an InventoryState",
        ),
    ],
)
def test_direct_synchronization_rejects_invalid_types(arguments, message) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(TypeError, match=message):
        synchronize_directly(**arguments)


def test_existing_projection_validation_still_applies() -> None:
    with pytest.raises(ValueError, match="system must not be empty"):
        InventoryProjection(" ", InventoryState(1, 0))


def test_canonical_scenario_records_before_sync_and_after() -> None:
    result = run_direct_synchronization_scenario()

    assert (
        result.authoritative_state
        == InventoryLedger([Receive(10), Reserve(3)]).current_state()
    )
    assert result.authoritative_state.available == 7
    assert result.initial_projection.state.available == 10
    assert result.initial_available_difference == 3
    before, after = result.inspections
    assert (before.time, before.state.available, before.available_difference) == (
        4,
        10,
        3,
    )
    assert not before.matches
    assert (after.time, after.state.available, after.available_difference) == (8, 7, 0)
    assert after.matches
    execution = result.synchronization
    assert execution.time == 6
    assert execution.before.state.available == 10
    assert execution.after.state.available == 7
    assert execution.available_difference_before == 3
    assert execution.available_difference_after == 0
    assert result.final_projection.state.available == 7
    assert result.final_time == 8


def test_scenario_is_ordered_once_immutable_and_repeatable() -> None:
    first = run_direct_synchronization_scenario()
    second = run_direct_synchronization_scenario()

    assert first == second
    assert [execution.time for execution in first.scheduler_executions] == [4, 6, 8]
    assert [execution.order for execution in first.scheduler_executions] == [1, 2, 3]
    assert first.initial_projection.state == InventoryState(10, 0)
    assert first.initial_projection is first.synchronization.before
    assert first.final_projection is first.synchronization.after
    assert first.final_projection is not first.initial_projection
    with pytest.raises(FrozenInstanceError):
        first.final_projection.system = "changed"  # type: ignore[misc]
