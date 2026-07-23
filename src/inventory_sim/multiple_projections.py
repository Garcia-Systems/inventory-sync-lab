"""One authority feeding independent projections, introduced in Chapter 15."""

from dataclasses import dataclass

from inventory_sim.capacity import (
    CapacityQueue,
    SynchronizationWorkItem,
    WorkerCompletion,
)
from inventory_sim.ledger import InventoryLedger, Receive, Reserve, Ship
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import ProjectionRegistry, SynchronizationRequest
from inventory_sim.revisions import (
    InventoryRevision,
    RevisionedInventoryState,
    observe_ledger_revisions,
)
from inventory_sim.simulation import EventExecution, EventScheduler, VirtualClock
from inventory_sim.stale_rejection import (
    SynchronizationRejectionInspection,
    inspect_synchronization_policy,
)
from inventory_sim.worker_pool import WorkerPool


@dataclass(frozen=True)
class RevisionedProjection:
    """An immutable projection together with the authority revision it copied."""

    projection: InventoryProjection
    revision: InventoryRevision


@dataclass(frozen=True)
class MultipleProjectionsResult:
    """Inspectable outcome of the deterministic Chapter 15 scenario."""

    authority: RevisionedInventoryState
    initial_projections: tuple[RevisionedProjection, ...]
    final_projections: tuple[RevisionedProjection, ...]
    inspections: tuple[SynchronizationRejectionInspection, ...]
    completions: tuple[WorkerCompletion, ...]
    scheduler_executions: tuple[EventExecution, ...]
    final_queue_depth: int
    final_time: int


def run_multiple_projections_scenario() -> MultipleProjectionsResult:
    """Synchronize three named projections twice, isolating one stale request."""
    ledger = InventoryLedger(
        (Receive(20), Reserve(2), Receive(3), Reserve(1), Ship(1), Reserve(2))
    )
    observations = observe_ledger_revisions(ledger)
    first_authority = observations[2]
    authority = observations[-1]
    systems = ("Storefront", "Warehouse", "Reporting")
    initial = tuple(
        RevisionedProjection(
            InventoryProjection(system, observations[0].state), observations[0].revision
        )
        for system in systems
    )
    registry = ProjectionRegistry(tuple(item.projection for item in initial))
    projection_revisions = {item.projection.system: item.revision for item in initial}
    request_revisions: dict[str, InventoryRevision] = {}
    outcomes: dict[str, SynchronizationRejectionInspection] = {}
    queue = CapacityQueue()
    pool = WorkerPool(worker_count=3, service_time=1)
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    inspections: list[SynchronizationRejectionInspection] = []
    completions: list[WorkerCompletion] = []
    current_authority = first_authority

    def enqueue(system: str, snapshot: RevisionedInventoryState) -> None:
        request_revisions[system] = snapshot.revision
        queue.enqueue(
            SynchronizationWorkItem(
                SynchronizationRequest(system, snapshot.state), clock.now
            )
        )

    def complete(worker_name: str) -> None:
        outcome = outcomes[worker_name]
        completion = pool.complete(
            worker_name=worker_name,
            projections=registry,
            current_time=clock.now,
            update_projection=outcome.projection_updated,
        )
        completions.append(completion)
        if outcome.projection_updated:
            projection_revisions[completion.system] = outcome.request_revision

    def assign() -> None:
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
                authority_revision=current_authority.revision,
            )
            outcomes[start.worker_name] = outcome
            inspections.append(outcome)

    def enqueue_first_batch() -> None:
        for system in systems:
            enqueue(system, first_authority)
        assign()

    def advance_authority() -> None:
        nonlocal current_authority
        current_authority = authority

    def enqueue_second_batch() -> None:
        # Storefront receives an old snapshot while the other two receive Revision 6.
        enqueue("Storefront", first_authority)
        enqueue("Warehouse", authority)
        enqueue("Reporting", authority)
        assign()

    scheduler.schedule(at=1, label="Synchronize Revision 3", action=enqueue_first_batch)
    scheduler.schedule(
        at=3, label="Authority advances to Revision 6", action=advance_authority
    )
    scheduler.schedule(
        at=4, label="Synchronize independent projections", action=enqueue_second_batch
    )
    scheduler.schedule(
        at=6,
        label="Refresh Storefront",
        action=lambda: (enqueue("Storefront", authority), assign()),
    )
    history = scheduler.run()
    final = tuple(
        RevisionedProjection(projection, projection_revisions[projection.system])
        for projection in registry.projections
    )
    return MultipleProjectionsResult(
        authority,
        initial,
        final,
        tuple(inspections),
        tuple(completions),
        history,
        queue.depth,
        clock.now,
    )
