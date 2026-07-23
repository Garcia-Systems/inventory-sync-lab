from dataclasses import FrozenInstanceError

import pytest

from inventory_sim.revisions import InventoryRevision
from inventory_sim.stale_rejection import (
    SynchronizationRejectionInspection,
    inspect_synchronization_policy,
    run_stale_rejection_scenario,
)


def test_stale_request_is_rejected() -> None:
    inspection = inspect_synchronization_policy(
        time=4,
        worker_name="worker-1",
        request_revision=InventoryRevision(2),
        authority_revision=InventoryRevision(4),
    )

    assert inspection.stale is True
    assert inspection.projection_updated is False
    assert inspection.rejection_reason == "request revision is older than authority"


def test_current_request_is_accepted() -> None:
    inspection = inspect_synchronization_policy(
        time=4,
        worker_name="worker-2",
        request_revision=InventoryRevision(4),
        authority_revision=InventoryRevision(4),
    )

    assert inspection.stale is False
    assert inspection.projection_updated is True
    assert inspection.rejection_reason is None


def test_rejection_inspection_is_immutable() -> None:
    inspection = inspect_synchronization_policy(
        time=4,
        worker_name="worker-1",
        request_revision=InventoryRevision(2),
        authority_revision=InventoryRevision(4),
    )

    with pytest.raises(FrozenInstanceError):
        inspection.stale = False  # type: ignore[misc]


def test_scenario_rejects_stale_update_and_accepts_current_update() -> None:
    result = run_stale_rejection_scenario()
    rejected, accepted = result.completions

    assert rejected.projection_after == rejected.projection_before
    assert accepted.projection_after != accepted.projection_before
    assert result.final_projections[0].state.available == 8
    assert result.final_projections[1].state.available == 8
    assert result.accepted_requests == 1
    assert result.rejected_requests == 1
    assert result.final_queue_depth == 0


def test_scenario_execution_is_deterministic() -> None:
    assert run_stale_rejection_scenario() == run_stale_rejection_scenario()


def test_inspection_record_contains_only_educational_outcome_fields() -> None:
    assert tuple(SynchronizationRejectionInspection.__dataclass_fields__) == (
        "time",
        "worker_name",
        "request_revision",
        "authority_revision",
        "stale",
        "projection_updated",
        "rejection_reason",
    )
