from dataclasses import FrozenInstanceError

import pytest

from inventory_sim import (
    CapacityQueue,
    InventoryProjection,
    InventoryState,
    ProjectionRegistry,
    SynchronizationRequest,
    SynchronizationWorkItem,
    WorkerState,
    run_worker_capacity_scenario,
)


def request(system: str = "website") -> SynchronizationRequest:
    return SynchronizationRequest(system, InventoryState(10, 3))


def test_work_item_is_immutable_and_preserves_request_snapshot() -> None:
    synchronization_request = request()
    item = SynchronizationWorkItem(synchronization_request, 2)
    assert item.request is synchronization_request
    assert item.arrived_at == 2
    with pytest.raises(FrozenInstanceError):
        item.arrived_at = 3  # type: ignore[misc]


@pytest.mark.parametrize("invalid", [True, 1.5, "1"])
def test_work_item_rejects_non_integer_arrival(invalid: object) -> None:
    with pytest.raises(TypeError, match="arrival time must be an integer"):
        SynchronizationWorkItem(request(), invalid)  # type: ignore[arg-type]


def test_work_item_rejects_negative_arrival_and_invalid_request() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        SynchronizationWorkItem(request(), -1)
    with pytest.raises(TypeError, match="SynchronizationRequest"):
        SynchronizationWorkItem(object(), 1)  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid", [True, 1.5, "3"])
def test_worker_rejects_non_integer_service_time(invalid: object) -> None:
    with pytest.raises(TypeError, match="service time must be an integer"):
        WorkerState(invalid)  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid", [0, -1])
def test_worker_requires_positive_service_time(invalid: int) -> None:
    with pytest.raises(ValueError):
        WorkerState(invalid)


def test_worker_starts_without_updating_projection_and_completes_at_service_time() -> (
    None
):
    original = InventoryProjection("website", InventoryState(10, 0))
    registry = ProjectionRegistry((original,))
    queue = CapacityQueue()
    queue.enqueue(SynchronizationWorkItem(request(), 1))
    worker = WorkerState(3)
    assert worker.is_idle and not worker.is_busy
    assert worker.current is worker.started_at is worker.completes_at is None

    start = worker.start_next(queue=queue, current_time=1)
    assert start is not None
    assert worker.is_busy and not worker.is_idle
    assert worker.current.request.system == "website"  # type: ignore[union-attr]
    assert worker.started_at == 1
    assert worker.completes_at == 4
    assert queue.depth == 0
    assert registry.get("website") is original
    with pytest.raises(RuntimeError, match="busy"):
        worker.start_next(queue=queue, current_time=2)
    with pytest.raises(ValueError, match="scheduled"):
        worker.complete(projections=registry, current_time=3)

    completion = worker.complete(projections=registry, current_time=4)
    assert completion.projection_before is original
    assert completion.projection_after is not original
    assert completion.available_difference_before == 3
    assert completion.available_difference_after == 0
    assert worker.is_idle
    assert registry.get("website").state == InventoryState(10, 3)
    assert original.state == InventoryState(10, 0)


def test_worker_empty_queue_and_invalid_state_contracts() -> None:
    worker = WorkerState(3)
    queue = CapacityQueue()
    assert worker.start_next(queue=queue, current_time=0) is None
    with pytest.raises(RuntimeError, match="idle"):
        worker.complete(
            projections=ProjectionRegistry(
                (InventoryProjection("website", InventoryState(1, 0)),)
            ),
            current_time=0,
        )
    with pytest.raises(TypeError, match="CapacityQueue"):
        worker.start_next(queue=object(), current_time=0)  # type: ignore[arg-type]


def test_capacity_queue_validates_items_and_empty_dequeue() -> None:
    queue = CapacityQueue()
    assert queue.is_empty
    with pytest.raises(TypeError, match="SynchronizationWorkItem"):
        queue.enqueue(object())  # type: ignore[arg-type]
    with pytest.raises(IndexError, match="empty"):
        queue.dequeue()


def test_canonical_scenario_has_fifo_timing_and_increasing_waits() -> None:
    result = run_worker_capacity_scenario()
    assert result.authoritative_state.available == 7
    assert result.initial_available_differences == (3, 2, 1)
    assert result.service_time == 3
    assert [arrival.time for arrival in result.arrivals] == [1, 2, 3]
    assert [start.system for start in result.processing_starts] == [
        "website",
        "marketplace",
        "storefront",
    ]
    assert [start.started_at for start in result.processing_starts] == [1, 4, 7]
    assert [item.completed_at for item in result.completions] == [4, 7, 10]
    assert [item.wait_time for item in result.completions] == [0, 2, 4]
    assert [item.total_time for item in result.completions] == [3, 5, 7]
    assert all(
        item.total_time == item.wait_time + item.service_time
        for item in result.completions
    )
    assert result.busy_time == 9
    assert result.utilization == 9 / 11


def test_canonical_inspections_show_capacity_and_completion_visibility() -> None:
    result = run_worker_capacity_scenario()
    by_time = {inspection.time: inspection for inspection in result.inspections}
    expected = {
        3: ("BUSY", "website", 4, 2, [False, False, False]),
        5: ("BUSY", "marketplace", 7, 1, [True, False, False]),
        8: ("BUSY", "storefront", 10, 0, [True, True, False]),
        11: ("IDLE", None, None, 0, [True, True, True]),
    }
    for time, values in expected.items():
        inspection = by_time[time]
        assert (
            inspection.worker_status,
            inspection.current_system,
            inspection.current_completion_time,
            inspection.queue_depth,
            [projection.matches for projection in inspection.projections],
        ) == values
    assert result.final_time == 11
    assert result.final_worker_status == "IDLE"
    assert result.final_queue_depth == 0
    assert run_worker_capacity_scenario() == result


def test_scenario_schedules_completion_events_dynamically() -> None:
    labels = [
        event.label for event in run_worker_capacity_scenario().scheduler_executions
    ]
    assert labels.count("Complete website synchronization") == 1
    assert labels.count("Complete marketplace synchronization") == 1
    assert labels.count("Complete storefront synchronization") == 1
    times = [
        event.time for event in run_worker_capacity_scenario().scheduler_executions
    ]
    assert times == sorted(times)
