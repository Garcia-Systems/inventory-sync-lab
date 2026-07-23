from dataclasses import FrozenInstanceError

import pytest

from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve
from inventory_sim.revisions import (
    InventoryRevision,
    RevisionedInventoryState,
    observe_ledger_revisions,
    run_inventory_revisions_scenario,
)


def test_revisions_follow_ledger_replay_deterministically() -> None:
    ledger = InventoryLedger((Receive(10), Reserve(3), Receive(3)))

    first = observe_ledger_revisions(ledger)
    second = observe_ledger_revisions(ledger)

    assert first == second
    assert [item.revision.value for item in first] == [1, 2, 3]
    assert [item.state.available for item in first] == [10, 7, 10]


def test_revision_values_are_immutable_and_orderable() -> None:
    revision = InventoryRevision(1)

    with pytest.raises(FrozenInstanceError):
        revision.value = 2  # type: ignore[misc]

    assert revision < InventoryRevision(2) < InventoryRevision(3)


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "1"])
def test_revision_requires_a_positive_integer(value: object) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        InventoryRevision(value)  # type: ignore[arg-type]


def test_revisioned_state_validates_its_values() -> None:
    with pytest.raises(TypeError, match="InventoryRevision"):
        RevisionedInventoryState(1, InventoryState(1, 0))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="InventoryState"):
        RevisionedInventoryState(InventoryRevision(1), object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="InventoryLedger"):
        observe_ledger_revisions(object())  # type: ignore[arg-type]


def test_synchronization_requests_copy_states_without_revision_policy() -> None:
    result = run_inventory_revisions_scenario()

    assert result.observations[0].state.available == 10
    assert result.observations[2].state.available == 10
    assert result.observations[0].revision < result.observations[2].revision
    assert result.synchronized_states == tuple(
        request.authoritative_state for request in result.requests
    )
