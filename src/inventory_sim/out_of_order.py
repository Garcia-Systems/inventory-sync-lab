"""Intentional out-of-order delivery introduced in Chapter 20."""

from dataclasses import dataclass

from inventory_sim.capacity import (
    CapacityQueue,
    SynchronizationWorkItem,
    WorkerCompletion,
)
from inventory_sim.idempotency import AppliedRequestRegistry
from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import ProjectionRegistry, SynchronizationRequest
from inventory_sim.revisions import InventoryRevision, RevisionedInventoryState
from inventory_sim.simulation import EventExecution, EventScheduler, VirtualClock
from inventory_sim.worker_pool import WorkerPool


@dataclass(frozen=True)
class OutOfOrderDelivery:
    """One successful application, annotated with its creation revision."""

    request: SynchronizationRequest
    revision: InventoryRevision
    completion: WorkerCompletion


@dataclass(frozen=True)
class OutOfOrderResult:
    """Inspectable outcome of the fixed reversed-delivery scenario."""

    authority: RevisionedInventoryState
    created_revisions: tuple[RevisionedInventoryState, ...]
    requests: tuple[SynchronizationRequest, ...]
    deliveries: tuple[OutOfOrderDelivery, ...]
    final_projection: InventoryProjection
    final_projection_revision: InventoryRevision
    scheduler_executions: tuple[EventExecution, ...]
    final_queue_depth: int
    final_time: int

    @property
    def processed_request_ids(self) -> tuple[int, ...]:
        """Return the unique identifiers in actual processing order."""
        return tuple(
            delivery.request.request_id
            for delivery in self.deliveries
            if delivery.request.request_id is not None
        )


def run_out_of_order_scenario() -> OutOfOrderResult:
    """Create Revisions 13 then 14, but apply 14 then 13 exactly once."""
    baseline_events = (Receive(20), Reserve(1)) * 6
    revision_13_ledger = InventoryLedger((*baseline_events, Receive(2)))
    revision_13 = RevisionedInventoryState(
        InventoryRevision(13), revision_13_ledger.current_state()
    )
    revision_14_ledger = InventoryLedger((*revision_13_ledger.events, Reserve(1)))
    revision_14 = RevisionedInventoryState(
        InventoryRevision(14), revision_14_ledger.current_state()
    )
    created_revisions = (revision_13, revision_14)
    requests = tuple(
        SynchronizationRequest("Projection", snapshot.state, request_id=revision.value)
        for revision, snapshot in (
            (revision_13.revision, revision_13),
            (revision_14.revision, revision_14),
        )
    )

    projections = ProjectionRegistry(
        (InventoryProjection("Projection", InventoryState(0, 0)),)
    )
    applied = AppliedRequestRegistry()
    queue = CapacityQueue()
    pool = WorkerPool(worker_count=1, service_time=1)
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    deliveries: list[OutOfOrderDelivery] = []
    revision_by_id = {13: revision_13.revision, 14: revision_14.revision}

    def assign() -> None:
        pool.assign_available(
            queue=queue,
            current_time=clock.now,
            scheduler=scheduler,
            completion_action=complete,
        )

    def complete(worker_name: str) -> None:
        current = pool.workers[0].current
        assert current is not None
        request = current.request
        # IDs retain Chapter 19 idempotency. Each distinct request is applied once.
        duplicate = applied.already_applied(request)
        completion = pool.complete(
            worker_name=worker_name,
            projections=projections,
            current_time=clock.now,
            update_projection=not duplicate,
        )
        if not duplicate:
            applied.record_applied(request)
        assert request.request_id is not None
        deliveries.append(
            OutOfOrderDelivery(request, revision_by_id[request.request_id], completion)
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
    return OutOfOrderResult(
        revision_14,
        created_revisions,
        requests,
        tuple(deliveries),
        projections.get("Projection"),
        deliveries[-1].revision,
        history,
        queue.depth,
        clock.now,
    )
