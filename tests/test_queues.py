from dataclasses import FrozenInstanceError

import pytest

from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import (
    ProjectionRegistry,
    SynchronizationQueue,
    SynchronizationRequest,
    SynchronizationWorker,
    run_queue_synchronization_scenario,
)


def request(system: str = "website", state: InventoryState | None = None):  # type: ignore[no-untyped-def]
    return SynchronizationRequest(system, state or InventoryState(10, 3))


def test_request_is_an_immutable_state_snapshot() -> None:
    state = InventoryState(10, 3)
    queued = request(state=state)
    assert queued.system == "website"
    assert queued.authoritative_state is state
    with pytest.raises(FrozenInstanceError):
        queued.system = "marketplace"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("system", "error", "message"),
    [
        ("", ValueError, "system must not be empty"),
        ("   ", ValueError, "system must not be empty"),
        (1, TypeError, "system must be a string"),
    ],
)
def test_request_reuses_system_validation(system, error, message) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(error, match=message):
        SynchronizationRequest(system, InventoryState(1, 0))


def test_request_rejects_invalid_state_type() -> None:
    with pytest.raises(TypeError, match="state must be an InventoryState"):
        SynchronizationRequest("website", object())  # type: ignore[arg-type]


def test_queue_begins_empty_changes_depth_and_reports_empty() -> None:
    queue = SynchronizationQueue()
    assert queue.depth == 0
    assert queue.is_empty
    queue.enqueue(request())
    assert queue.depth == 1
    assert not queue.is_empty
    queue.dequeue()
    assert queue.depth == 0
    assert queue.is_empty


def test_queue_is_fifo_for_different_systems() -> None:
    queue = SynchronizationQueue()
    website = request("website")
    marketplace = request("marketplace")
    queue.enqueue(website)
    queue.enqueue(marketplace)
    assert queue.dequeue() is website
    assert queue.dequeue() is marketplace


def test_queue_rejects_invalid_requests_and_empty_dequeue() -> None:
    queue = SynchronizationQueue()
    with pytest.raises(TypeError, match="request must be"):
        queue.enqueue(object())  # type: ignore[arg-type]
    with pytest.raises(IndexError, match="empty synchronization queue"):
        queue.dequeue()
    assert not hasattr(queue, "requests")


def test_registry_retrieves_replaces_and_does_not_expose_mapping() -> None:
    original = InventoryProjection("website", InventoryState(10, 0))
    registry = ProjectionRegistry((original,))
    assert registry.get("website") is original
    assert registry.projections == (original,)
    replacement = original.refresh_from(InventoryState(10, 3))
    registry.replace(replacement)
    assert registry.get("website") is replacement
    assert original.state.available == 10
    assert not hasattr(registry, "current")


def test_registry_rejects_invalid_duplicate_and_unknown_values() -> None:
    website = InventoryProjection("website", InventoryState(1, 0))
    with pytest.raises(TypeError, match="projections must be a tuple"):
        ProjectionRegistry([website])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="each projection"):
        ProjectionRegistry((object(),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="duplicate projection system"):
        ProjectionRegistry((website, website))
    registry = ProjectionRegistry((website,))
    with pytest.raises(TypeError, match="system must be a string"):
        registry.get(1)  # type: ignore[arg-type]
    with pytest.raises(KeyError, match="unknown projection system"):
        registry.get("marketplace")
    with pytest.raises(TypeError, match="projection must be"):
        registry.replace(object())  # type: ignore[arg-type]
    with pytest.raises(KeyError, match="unknown projection system"):
        registry.replace(InventoryProjection("marketplace", InventoryState(1, 0)))


def test_worker_processes_only_oldest_request_and_preserves_other_projection() -> None:
    website = InventoryProjection("website", InventoryState(10, 0))
    marketplace = InventoryProjection("marketplace", InventoryState(10, 1))
    registry = ProjectionRegistry((website, marketplace))
    queue = SynchronizationQueue()
    authority = InventoryState(10, 3)
    queue.enqueue(request("website", authority))
    queue.enqueue(request("marketplace", authority))
    worker = SynchronizationWorker(queue=queue, projections=registry)

    execution = worker.process_next(time=5)
    assert execution is not None
    assert execution.system == "website"
    assert (execution.queue_depth_before, execution.queue_depth_after) == (2, 1)
    assert execution.projection_before is website
    assert execution.projection_after is registry.get("website")
    assert execution.projection_after is not website
    assert execution.available_difference_before == 3
    assert execution.available_difference_after == 0
    assert registry.get("marketplace") is marketplace
    assert queue.depth == 1


def test_worker_returns_none_for_empty_queue_and_validates_inputs() -> None:
    registry = ProjectionRegistry(
        (InventoryProjection("website", InventoryState(1, 0)),)
    )
    queue = SynchronizationQueue()
    worker = SynchronizationWorker(queue=queue, projections=registry)
    assert worker.process_next(time=1) is None
    with pytest.raises(TypeError, match="time must be an integer"):
        worker.process_next(time=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="time cannot be negative"):
        worker.process_next(time=-1)
    with pytest.raises(TypeError, match="queue must be"):
        SynchronizationWorker(queue=object(), projections=registry)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="projections must be"):
        SynchronizationWorker(queue=queue, projections=object())  # type: ignore[arg-type]


def test_worker_uses_request_snapshot_not_a_fresh_authority_lookup() -> None:
    old_snapshot = InventoryState(10, 2)
    registry = ProjectionRegistry(
        (InventoryProjection("website", InventoryState(10, 0)),)
    )
    queue = SynchronizationQueue()
    queue.enqueue(request("website", old_snapshot))
    execution = SynchronizationWorker(queue=queue, projections=registry).process_next(
        time=5
    )
    assert execution is not None
    assert execution.projection_after.state is old_snapshot
    assert execution.projection_after.state != InventoryState(10, 3)


def test_canonical_queue_scenario_has_expected_timeline_and_state() -> None:
    result = run_queue_synchronization_scenario()
    assert (
        result.authoritative_state
        == InventoryLedger([Receive(10), Reserve(3)]).current_state()
    )
    assert result.authoritative_state.available == 7
    assert [item.state.available for item in result.initial_projections] == [10, 9]
    assert result.initial_available_differences == (3, 2)
    assert [(item.time, item.system, item.queue_depth) for item in result.enqueues] == [
        (2, "website", 1),
        (3, "marketplace", 2),
    ]
    inspections = {item.time: item for item in result.inspections}
    assert [item.time for item in result.inspections] == [1, 4, 6, 8]
    assert inspections[4].queue_depth == 2
    assert [item.matches for item in inspections[4].projections] == [False, False]
    assert [item.available_difference for item in inspections[4].projections] == [3, 2]
    assert [item.system for item in result.worker_executions] == [
        "website",
        "marketplace",
    ]
    assert [item.time for item in result.worker_executions] == [5, 7]
    assert [item.queue_depth_after for item in result.worker_executions] == [1, 0]
    assert [item.matches for item in inspections[6].projections] == [True, False]
    assert inspections[6].queue_depth == 1
    assert [item.matches for item in inspections[8].projections] == [True, True]
    assert inspections[8].queue_depth == 0
    assert all(item.state.available == 7 for item in result.final_projections)
    assert result.final_queue_depth == 0
    assert result.final_time == 8
    assert [item.time for item in result.scheduler_executions] == list(range(1, 9))
    assert [item.order for item in result.scheduler_executions] == list(range(1, 9))


def test_queue_scenario_is_repeatable_and_preserves_initial_values() -> None:
    first = run_queue_synchronization_scenario()
    assert first == run_queue_synchronization_scenario()
    assert first.initial_projections[0] is first.worker_executions[0].projection_before
    assert first.initial_projections[1] is first.worker_executions[1].projection_before
    assert first.final_projections[0] is first.worker_executions[0].projection_after
    assert first.final_projections[1] is first.worker_executions[1].projection_after
