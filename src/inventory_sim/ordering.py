"""Monotonic projection ordering introduced in Chapter 21."""

from dataclasses import dataclass

from inventory_sim.capacity import (
    CapacityQueue,
    SynchronizationWorkItem,
    WorkerCompletion,
)
from inventory_sim.idempotency import AppliedRequestRegistry
from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve
from inventory_sim.multiple_projections import RevisionedProjection
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import ProjectionRegistry, SynchronizationRequest
from inventory_sim.revisions import InventoryRevision, RevisionedInventoryState
from inventory_sim.simulation import EventExecution, EventScheduler, VirtualClock
from inventory_sim.worker_pool import WorkerPool


def revision_advances_projection(
    *, request_revision: InventoryRevision, projection_revision: InventoryRevision
) -> bool:
    """Return whether a request is strictly newer than a projection."""
    if not isinstance(request_revision, InventoryRevision):
        raise TypeError("request revision must be an InventoryRevision")
    if not isinstance(projection_revision, InventoryRevision):
        raise TypeError("projection revision must be an InventoryRevision")
    return request_revision > projection_revision


@dataclass(frozen=True)
class OrderedDelivery:
    """One completed request and the ordering decision made for it."""

    request: SynchronizationRequest
    revision: InventoryRevision
    projection_revision_before: InventoryRevision
    projection_revision_after: InventoryRevision
    projection_updated: bool
    completion: WorkerCompletion


@dataclass(frozen=True)
class OrderingResult:
    """Inspectable outcome of the fixed monotonic-ordering scenario."""

    authority: RevisionedInventoryState
    created_revisions: tuple[RevisionedInventoryState, ...]
    requests: tuple[SynchronizationRequest, ...]
    deliveries: tuple[OrderedDelivery, ...]
    final_projection: RevisionedProjection
    scheduler_executions: tuple[EventExecution, ...]
    final_queue_depth: int
    final_time: int


def run_ordering_scenario() -> OrderingResult:
    """Deliver Revisions 14 then 13 while keeping the projection at 14."""
    baseline_events = (Receive(20), Reserve(1)) * 6
    revision_13_ledger = InventoryLedger((*baseline_events, Receive(2)))
    revision_13 = RevisionedInventoryState(
        InventoryRevision(13), revision_13_ledger.current_state()
    )
    revision_14 = RevisionedInventoryState(
        InventoryRevision(14),
        InventoryLedger((*revision_13_ledger.events, Reserve(1))).current_state(),
    )
    created_revisions = (revision_13, revision_14)
    requests = tuple(
        SynchronizationRequest("Projection", snapshot.state, snapshot.revision.value)
        for snapshot in created_revisions
    )
    registry = ProjectionRegistry(
        (InventoryProjection("Projection", InventoryState(0, 0)),)
    )
    projection_revision = InventoryRevision(1)
    applied = AppliedRequestRegistry()
    queue = CapacityQueue()
    pool = WorkerPool(worker_count=1, service_time=1)
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    deliveries: list[OrderedDelivery] = []
    revisions = {
        snapshot.revision.value: snapshot.revision for snapshot in created_revisions
    }

    def assign() -> None:
        pool.assign_available(
            queue=queue,
            current_time=clock.now,
            scheduler=scheduler,
            completion_action=complete,
        )

    def complete(worker_name: str) -> None:
        nonlocal projection_revision
        current = pool.get(worker_name).current
        assert current is not None and current.request.request_id is not None
        request = current.request
        request_revision = revisions[request.request_id]
        before_revision = projection_revision
        update = not applied.already_applied(request) and revision_advances_projection(
            request_revision=request_revision,
            projection_revision=projection_revision,
        )
        completion = pool.complete(
            worker_name=worker_name,
            projections=registry,
            current_time=clock.now,
            update_projection=update,
        )
        if not applied.already_applied(request):
            applied.record_applied(request)
        if update:
            projection_revision = request_revision
        deliveries.append(
            OrderedDelivery(
                request,
                request_revision,
                before_revision,
                projection_revision,
                update,
                completion,
            )
        )
        scheduler.schedule(at=clock.now, label="Assign next delivery", action=assign)

    def deliver_in_reverse() -> None:
        for request in reversed(requests):
            queue.enqueue(SynchronizationWorkItem(request, clock.now))
        assign()

    scheduler.schedule(
        at=1, label="Deliver Revision 14 before Revision 13", action=deliver_in_reverse
    )
    history = scheduler.run()
    return OrderingResult(
        revision_14,
        created_revisions,
        requests,
        tuple(deliveries),
        RevisionedProjection(registry.get("Projection"), projection_revision),
        history,
        queue.depth,
        clock.now,
    )
