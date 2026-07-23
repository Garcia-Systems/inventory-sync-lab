"""Deterministic stale-snapshot lesson introduced in Chapter 10."""

from dataclasses import dataclass

from inventory_sim.capacity import (
    CapacityQueue,
    SynchronizationWorkItem,
    WorkerCompletion,
    WorkerProcessingStart,
    WorkerState,
)
from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import ProjectionRegistry, SynchronizationRequest
from inventory_sim.simulation import EventExecution, EventScheduler, VirtualClock


@dataclass(frozen=True)
class StaleSnapshotInspection:
    """The three inventory values that expose an outdated successful copy."""

    request_snapshot: InventoryState
    current_authority: InventoryState
    resulting_projection: InventoryProjection


@dataclass(frozen=True)
class StaleSnapshotsResult:
    """Inspectable result of the canonical Chapter 10 scenario."""

    original_authority: InventoryState
    current_authority: InventoryState
    request: SynchronizationRequest
    processing_starts: tuple[WorkerProcessingStart, ...]
    completions: tuple[WorkerCompletion, ...]
    inspection: StaleSnapshotInspection
    scheduler_executions: tuple[EventExecution, ...]
    final_time: int


def run_stale_snapshots_scenario() -> StaleSnapshotsResult:
    """Copy a queued snapshot after authority has legitimately changed."""
    original_ledger = InventoryLedger([Receive(10), Reserve(3)])
    original_authority = original_ledger.current_state()
    registry = ProjectionRegistry(
        (
            InventoryProjection("warehouse", original_authority),
            InventoryProjection("website", InventoryState(10, 0)),
        )
    )
    queue = CapacityQueue()
    worker = WorkerState(service_time=3)
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    starts: list[WorkerProcessingStart] = []
    completions: list[WorkerCompletion] = []
    authority = original_authority
    request: SynchronizationRequest | None = None

    def start_next() -> None:
        start = worker.start_next(queue=queue, current_time=clock.now)
        if start is None:
            return
        starts.append(start)
        scheduler.schedule(
            at=start.completes_at,
            label=f"Complete {start.system} synchronization",
            action=complete,
        )

    def complete() -> None:
        completions.append(
            worker.complete(projections=registry, current_time=clock.now)
        )
        start_next()

    def occupy_worker() -> None:
        queue.enqueue(
            SynchronizationWorkItem(
                SynchronizationRequest("warehouse", authority), clock.now
            )
        )
        start_next()

    def capture_request() -> None:
        nonlocal request
        request = SynchronizationRequest("website", authority)
        queue.enqueue(SynchronizationWorkItem(request, clock.now))

    def change_authority() -> None:
        nonlocal authority
        authority = InventoryLedger(
            (*original_ledger.events, Receive(5))
        ).current_state()

    scheduler.schedule(at=0, label="Worker begins earlier work", action=occupy_worker)
    scheduler.schedule(
        at=1, label="Website snapshot enters queue", action=capture_request
    )
    scheduler.schedule(
        at=2, label="Authority receives five units", action=change_authority
    )
    history = scheduler.run()
    assert request is not None
    projection = registry.get("website")
    inspection = StaleSnapshotInspection(
        request.authoritative_state, authority, projection
    )
    return StaleSnapshotsResult(
        original_authority,
        authority,
        request,
        tuple(starts),
        tuple(completions),
        inspection,
        history,
        clock.now,
    )
