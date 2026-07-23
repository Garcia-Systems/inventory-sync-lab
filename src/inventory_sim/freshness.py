"""Deterministic freshness measurements introduced in Chapter 11."""

from dataclasses import dataclass

from inventory_sim.capacity import CapacityQueue, SynchronizationWorkItem, WorkerState
from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import ProjectionRegistry, SynchronizationRequest
from inventory_sim.simulation import EventExecution, EventScheduler, VirtualClock


@dataclass(frozen=True)
class FreshnessObservation:
    """Timing facts observed when one synchronization finishes."""

    request: str
    request_created_at: int
    synchronization_completed_at: int
    current_time: int
    wait_time: int
    service_time: int
    snapshot_age: int
    authority_changed_after_creation: bool


@dataclass(frozen=True)
class FreshnessResult:
    """Inspectable output from the canonical Chapter 11 scenario."""

    observations: tuple[FreshnessObservation, ...]
    scheduler_executions: tuple[EventExecution, ...]
    final_authority: InventoryState
    final_projections: tuple[InventoryProjection, ...]
    final_time: int


def measure_freshness(
    *,
    request: str,
    request_created_at: int,
    synchronization_completed_at: int,
    current_time: int,
    wait_time: int,
    service_time: int,
    authority_change_times: tuple[int, ...],
) -> FreshnessObservation:
    """Measure elapsed ticks since the first authority change a snapshot missed."""
    missed_changes = tuple(
        change
        for change in authority_change_times
        if request_created_at < change <= synchronization_completed_at
    )
    snapshot_age = (
        synchronization_completed_at - missed_changes[0] if missed_changes else 0
    )
    return FreshnessObservation(
        request,
        request_created_at,
        synchronization_completed_at,
        current_time,
        wait_time,
        service_time,
        snapshot_age,
        bool(missed_changes),
    )


def run_freshness_scenario() -> FreshnessResult:
    """Run three FIFO requests while authority changes at known times."""
    original_ledger = InventoryLedger([Receive(10), Reserve(3)])
    authority = original_ledger.current_state()
    registry = ProjectionRegistry(
        tuple(
            InventoryProjection(name, InventoryState(10, 0)) for name in ("A", "B", "C")
        )
    )
    queue = CapacityQueue()
    worker = WorkerState(service_time=3)
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    authority_change_times: list[int] = []
    observations: list[FreshnessObservation] = []

    def start_next() -> None:
        if worker.is_busy:
            return
        start = worker.start_next(queue=queue, current_time=clock.now)
        if start is not None:
            scheduler.schedule(
                at=start.completes_at,
                label=f"Complete request {start.system}",
                action=complete,
            )

    def complete() -> None:
        completion = worker.complete(projections=registry, current_time=clock.now)
        observations.append(
            measure_freshness(
                request=completion.system,
                request_created_at=completion.arrived_at,
                synchronization_completed_at=completion.completed_at,
                current_time=clock.now,
                wait_time=completion.wait_time,
                service_time=completion.service_time,
                authority_change_times=tuple(authority_change_times),
            )
        )
        start_next()

    def arrive(name: str) -> None:
        queue.enqueue(
            SynchronizationWorkItem(SynchronizationRequest(name, authority), clock.now)
        )
        start_next()

    def change_authority(quantity: int) -> None:
        nonlocal authority
        authority = InventoryLedger(
            (*original_ledger.events, Receive(quantity))
        ).current_state()
        authority_change_times.append(clock.now)

    scheduler.schedule(at=0, label="Capture and enqueue A", action=lambda: arrive("A"))
    scheduler.schedule(at=1, label="Capture and enqueue B", action=lambda: arrive("B"))
    scheduler.schedule(at=1, label="Capture and enqueue C", action=lambda: arrive("C"))
    scheduler.schedule(
        at=4, label="Authority receives 2", action=lambda: change_authority(2)
    )
    scheduler.schedule(
        at=7, label="Authority receives 4", action=lambda: change_authority(4)
    )

    history = scheduler.run()
    return FreshnessResult(
        tuple(observations),
        history,
        authority,
        registry.projections,
        clock.now,
    )
