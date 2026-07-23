from dataclasses import FrozenInstanceError

import pytest

from inventory_sim import (
    CapacityQueue,
    EventScheduler,
    InventoryProjection,
    InventoryState,
    ProjectionRegistry,
    SynchronizationRequest,
    SynchronizationWorkItem,
    WorkerPool,
    WorkerState,
    run_multiple_workers_scenario,
    run_worker_capacity_scenario,
)


@pytest.mark.parametrize("invalid", [True, 1.5, "2"])
def test_pool_rejects_non_integer_worker_counts(invalid: object) -> None:
    with pytest.raises(TypeError, match="worker count must be an integer"):
        WorkerPool(invalid, 3)  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid", [0, -1])
def test_pool_requires_positive_worker_count(invalid: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        WorkerPool(invalid, 3)


@pytest.mark.parametrize("invalid", ["", "   "])
def test_worker_rejects_empty_names(invalid: str) -> None:
    with pytest.raises(ValueError, match="empty or whitespace"):
        WorkerState(3, invalid)


def test_worker_rejects_non_string_name_and_pool_rejects_duplicates() -> None:
    with pytest.raises(TypeError, match="worker name must be a string"):
        WorkerState(3, 1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unique"):
        WorkerPool.from_workers((WorkerState(3, "same"), WorkerState(3, "same")))


def test_pool_is_ordered_immutable_and_initially_idle() -> None:
    pool = WorkerPool(2, 3)
    assert tuple(worker.name for worker in pool.workers) == ("worker-1", "worker-2")
    assert pool.worker_count == pool.idle_worker_count == 2
    assert pool.busy_worker_count == 0
    assert isinstance(pool.workers, tuple)
    with pytest.raises(KeyError, match="unknown worker"):
        pool.get("worker-3")


def test_assignment_is_fifo_uses_idle_order_and_does_not_update_projections() -> None:
    authority = InventoryState(10, 3)
    originals = (
        InventoryProjection("website", InventoryState(10, 0)),
        InventoryProjection("marketplace", InventoryState(10, 1)),
        InventoryProjection("storefront", InventoryState(8, 0)),
    )
    registry = ProjectionRegistry(originals)
    queue = CapacityQueue()
    for system in ("website", "marketplace", "storefront"):
        queue.enqueue(
            SynchronizationWorkItem(SynchronizationRequest(system, authority), 1)
        )
    pool = WorkerPool(2, 3)
    scheduler = EventScheduler()
    completed: list[str] = []
    starts = pool.assign_available(
        queue=queue,
        current_time=1,
        scheduler=scheduler,
        completion_action=completed.append,
    )
    assert [(s.worker_name, s.system) for s in starts] == [
        ("worker-1", "website"),
        ("worker-2", "marketplace"),
    ]
    assert [s.completes_at for s in starts] == [4, 4]
    assert [s.queue_depth_after for s in starts] == [2, 1]
    assert queue.depth == 1
    assert pool.busy_worker_count == 2
    assert registry.projections == originals
    assert [event.time for event in scheduler.run()] == [4, 4]
    assert completed == ["worker-1", "worker-2"]
    assert (
        pool.assign_available(
            queue=CapacityQueue(),
            current_time=4,
            scheduler=scheduler,
            completion_action=completed.append,
        )
        == ()
    )


def test_worker_name_is_stable_through_processing() -> None:
    pool = WorkerPool(1, 3)
    worker = pool.workers[0]
    queue = CapacityQueue()
    authority = InventoryState(10, 3)
    registry = ProjectionRegistry(
        (InventoryProjection("website", InventoryState(10, 0)),)
    )
    queue.enqueue(
        SynchronizationWorkItem(SynchronizationRequest("website", authority), 1)
    )
    scheduler = EventScheduler()
    starts = pool.assign_available(
        queue=queue,
        current_time=1,
        scheduler=scheduler,
        completion_action=lambda _: None,
    )
    completion = pool.complete(
        worker_name="worker-1", projections=registry, current_time=4
    )
    assert starts[0].worker_name == completion.worker_name == worker.name == "worker-1"


def test_canonical_multiple_worker_scenario() -> None:
    result = run_multiple_workers_scenario()
    assert result.authoritative_state.available == 7
    assert result.initial_available_differences == (3, 2, 1, 2)
    assert result.worker_count == 2 and result.service_time == 3
    assert [
        (s.worker_name, s.system, s.started_at, s.completes_at, s.wait_time)
        for s in result.processing_starts
    ] == [
        ("worker-1", "website", 1, 4, 0),
        ("worker-2", "marketplace", 1, 4, 0),
        ("worker-1", "storefront", 4, 7, 2),
        ("worker-2", "partner", 4, 7, 1),
    ]
    assert [(c.worker_name, c.system) for c in result.completions] == [
        ("worker-1", "website"),
        ("worker-2", "marketplace"),
        ("worker-1", "storefront"),
        ("worker-2", "partner"),
    ]
    assert [c.total_time for c in result.completions] == [3, 3, 5, 4]
    assert all(c.total_time == c.wait_time + c.service_time for c in result.completions)
    assert result.maximum_queue_depth == 2
    assert result.average_wait_time == 0.75 and result.maximum_wait_time == 2
    assert result.final_queue_depth == 0 and result.final_time == 8
    assert all(worker.status == "IDLE" for worker in result.final_workers)
    assert all(
        p.compare_to(result.authoritative_state).matches
        for p in result.final_projections
    )
    assert run_multiple_workers_scenario() == result
    assert run_worker_capacity_scenario().final_time == 11
    with pytest.raises(FrozenInstanceError):
        result.inspections[0].queue_depth = 9  # type: ignore[misc]


def test_inspections_distinguish_queue_from_in_progress_work() -> None:
    by_time = {i.time: i for i in run_multiple_workers_scenario().inspections}
    expected = {
        3: (2, 2, ["website", "marketplace"], [False] * 4),
        5: (0, 2, ["storefront", "partner"], [True, True, False, False]),
        8: (0, 0, [None, None], [True] * 4),
    }
    for time, (depth, busy, systems, matches) in expected.items():
        inspection = by_time[time]
        assert inspection.queue_depth == depth
        assert inspection.busy_worker_count == busy
        assert inspection.busy_worker_count + inspection.idle_worker_count == 2
        assert [worker.current_system for worker in inspection.workers] == systems
        assert [projection.matches for projection in inspection.projections] == matches


def test_same_time_completion_coordination_is_explicit_and_ordered() -> None:
    result = run_multiple_workers_scenario()
    at_four = [event.label for event in result.scheduler_executions if event.time == 4]
    assert at_four == [
        "worker-1 completes website",
        "worker-2 completes marketplace",
        "Assign waiting work at time 4",
    ]
