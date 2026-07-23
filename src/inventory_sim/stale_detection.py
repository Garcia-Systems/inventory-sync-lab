"""Observation-only stale synchronization detection introduced in Chapter 13."""

from dataclasses import dataclass

from inventory_sim.capacity import (
    CapacityQueue,
    SynchronizationWorkItem,
    WorkerCompletion,
)
from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import ProjectionRegistry, SynchronizationRequest
from inventory_sim.revisions import InventoryRevision, observe_ledger_revisions
from inventory_sim.simulation import EventExecution, EventScheduler, VirtualClock
from inventory_sim.worker_pool import WorkerPool


@dataclass(frozen=True)
class StaleDetection:
    """An immutable revision comparison with no synchronization policy."""

    request_revision: InventoryRevision
    authority_revision: InventoryRevision
    stale: bool


def detect_stale_request(
    request_revision: InventoryRevision, authority_revision: InventoryRevision
) -> StaleDetection:
    """Observe whether a request precedes the current authority revision."""
    if not isinstance(request_revision, InventoryRevision):
        raise TypeError("request revision must be an InventoryRevision")
    if not isinstance(authority_revision, InventoryRevision):
        raise TypeError("authority revision must be an InventoryRevision")
    return StaleDetection(
        request_revision,
        authority_revision,
        request_revision < authority_revision,
    )


@dataclass(frozen=True)
class WorkerStaleInspection:
    """A stale observation made when one worker begins a request."""

    time: int
    worker_name: str
    system: str
    detection: StaleDetection


@dataclass(frozen=True)
class StaleDetectionResult:
    """The inspectable result of the Chapter 13 scenario."""

    authority_revision: InventoryRevision
    inspections: tuple[WorkerStaleInspection, ...]
    completions: tuple[WorkerCompletion, ...]
    final_projections: tuple[InventoryProjection, ...]
    scheduler_executions: tuple[EventExecution, ...]
    final_time: int


def run_stale_detection_scenario() -> StaleDetectionResult:
    """Detect one stale and one current request, then complete both normally."""
    ledger = InventoryLedger((Receive(10), Reserve(3), Receive(2), Reserve(1)))
    revisions = observe_ledger_revisions(ledger)
    authority = revisions[-1]
    requests = (
        ("website", revisions[1]),
        ("marketplace", authority),
    )
    registry = ProjectionRegistry(
        (
            InventoryProjection("website", InventoryState(0, 0)),
            InventoryProjection("marketplace", InventoryState(0, 0)),
        )
    )
    queue = CapacityQueue()
    pool = WorkerPool(worker_count=2, service_time=2)
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    request_revisions: dict[str, InventoryRevision] = {}
    inspections: list[WorkerStaleInspection] = []
    completions: list[WorkerCompletion] = []

    def enqueue(system: str, index: int) -> None:
        observation = requests[index][1]
        request_revisions[system] = observation.revision
        queue.enqueue(
            SynchronizationWorkItem(
                SynchronizationRequest(system, observation.state), clock.now
            )
        )

    def complete(worker_name: str) -> None:
        completions.append(
            pool.complete(
                worker_name=worker_name, projections=registry, current_time=clock.now
            )
        )

    def begin_processing() -> None:
        starts = pool.assign_available(
            queue=queue,
            current_time=clock.now,
            scheduler=scheduler,
            completion_action=complete,
        )
        for start in starts:
            inspections.append(
                WorkerStaleInspection(
                    clock.now,
                    start.worker_name,
                    start.system,
                    detect_stale_request(
                        request_revisions[start.system], authority.revision
                    ),
                )
            )

    scheduler.schedule(
        at=1,
        label="Request Revision 2 arrives",
        action=lambda: enqueue("website", 0),
    )
    scheduler.schedule(
        at=2, label="Authority advances to Revision 4", action=lambda: None
    )
    scheduler.schedule(
        at=3,
        label="Request Revision 4 arrives",
        action=lambda: enqueue("marketplace", 1),
    )
    scheduler.schedule(at=4, label="Workers begin processing", action=begin_processing)
    history = scheduler.run()
    return StaleDetectionResult(
        authority.revision,
        tuple(inspections),
        tuple(completions),
        registry.projections,
        history,
        clock.now,
    )
