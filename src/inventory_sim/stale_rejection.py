"""Deterministic stale-synchronization rejection introduced in Chapter 14."""

from dataclasses import dataclass

from inventory_sim.capacity import (
    CapacityQueue,
    SynchronizationWorkItem,
    WorkerCompletion,
)
from inventory_sim.ledger import InventoryLedger, Receive, Reserve
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import ProjectionRegistry, SynchronizationRequest
from inventory_sim.revisions import InventoryRevision, observe_ledger_revisions
from inventory_sim.simulation import EventExecution, EventScheduler, VirtualClock
from inventory_sim.stale_detection import detect_stale_request
from inventory_sim.worker_pool import WorkerPool


@dataclass(frozen=True)
class SynchronizationRejectionInspection:
    """The immutable policy outcome recorded when a worker starts work."""

    time: int
    worker_name: str
    request_revision: InventoryRevision
    authority_revision: InventoryRevision
    stale: bool
    projection_updated: bool
    rejection_reason: str | None


@dataclass(frozen=True)
class StaleRejectionResult:
    """The inspectable result of the Chapter 14 scenario."""

    inspections: tuple[SynchronizationRejectionInspection, ...]
    completions: tuple[WorkerCompletion, ...]
    accepted_requests: int
    rejected_requests: int
    authority_revision: InventoryRevision
    projection_revision: InventoryRevision
    final_projections: tuple[InventoryProjection, ...]
    final_queue_depth: int
    scheduler_executions: tuple[EventExecution, ...]
    final_time: int


def inspect_synchronization_policy(
    *,
    time: int,
    worker_name: str,
    request_revision: InventoryRevision,
    authority_revision: InventoryRevision,
) -> SynchronizationRejectionInspection:
    """Apply the rejection policy to one already-started request."""
    detection = detect_stale_request(request_revision, authority_revision)
    return SynchronizationRejectionInspection(
        time,
        worker_name,
        request_revision,
        authority_revision,
        detection.stale,
        not detection.stale,
        "request revision is older than authority" if detection.stale else None,
    )


def run_stale_rejection_scenario() -> StaleRejectionResult:
    """Reject Revision 2 and accept Revision 4 in a deterministic worker run."""
    ledger = InventoryLedger((Receive(10), Reserve(3), Receive(2), Reserve(1)))
    revisions = observe_ledger_revisions(ledger)
    authority = revisions[-1]
    requests = (("website", revisions[1]), ("marketplace", authority))
    registry = ProjectionRegistry(
        (
            InventoryProjection("website", authority.state),
            InventoryProjection("marketplace", revisions[0].state),
        )
    )
    queue = CapacityQueue()
    pool = WorkerPool(worker_count=2, service_time=2)
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    request_revisions: dict[str, InventoryRevision] = {}
    outcomes: dict[str, SynchronizationRejectionInspection] = {}
    inspections: list[SynchronizationRejectionInspection] = []
    completions: list[WorkerCompletion] = []

    def enqueue(index: int) -> None:
        system, snapshot = requests[index]
        request_revisions[system] = snapshot.revision
        queue.enqueue(
            SynchronizationWorkItem(
                SynchronizationRequest(system, snapshot.state), clock.now
            )
        )

    def complete(worker_name: str) -> None:
        outcome = outcomes[worker_name]
        completions.append(
            pool.complete(
                worker_name=worker_name,
                projections=registry,
                current_time=clock.now,
                update_projection=outcome.projection_updated,
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
            outcome = inspect_synchronization_policy(
                time=clock.now,
                worker_name=start.worker_name,
                request_revision=request_revisions[start.system],
                authority_revision=authority.revision,
            )
            outcomes[start.worker_name] = outcome
            inspections.append(outcome)

    scheduler.schedule(
        at=1, label="Request Revision 2 arrives", action=lambda: enqueue(0)
    )
    scheduler.schedule(
        at=2, label="Authority advances to Revision 4", action=lambda: None
    )
    scheduler.schedule(
        at=3, label="Request Revision 4 arrives", action=lambda: enqueue(1)
    )
    scheduler.schedule(at=4, label="Workers begin processing", action=begin_processing)
    history = scheduler.run()
    accepted = sum(outcome.projection_updated for outcome in inspections)
    rejected = len(inspections) - accepted
    return StaleRejectionResult(
        tuple(inspections),
        tuple(completions),
        accepted,
        rejected,
        authority.revision,
        authority.revision,
        registry.projections,
        queue.depth,
        history,
        clock.now,
    )
