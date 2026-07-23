"""Intentional duplicate delivery introduced in Chapter 18."""

from dataclasses import dataclass

from inventory_sim.capacity import (
    CapacityQueue,
    SynchronizationWorkItem,
    WorkerCompletion,
)
from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryEvent, InventoryLedger, Receive, Reserve
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import ProjectionRegistry, SynchronizationRequest
from inventory_sim.revisions import InventoryRevision, RevisionedInventoryState
from inventory_sim.simulation import EventExecution, EventScheduler, VirtualClock
from inventory_sim.worker_pool import WorkerPool


@dataclass(frozen=True)
class RequestDelivery:
    """One numbered delivery of an unchanged synchronization request."""

    number: int
    request: SynchronizationRequest
    completion: WorkerCompletion


@dataclass(frozen=True)
class DuplicateDeliveryResult:
    """Inspectable outcome of the fixed duplicate-delivery scenario."""

    authority: RevisionedInventoryState
    business_events: tuple[InventoryEvent, ...]
    request_id: int
    request: SynchronizationRequest
    deliveries: tuple[RequestDelivery, ...]
    final_projection: InventoryProjection
    scheduler_executions: tuple[EventExecution, ...]
    final_queue_depth: int
    final_time: int

    @property
    def projection_update_count(self) -> int:
        """Count updates, including repeated writes of the same snapshot."""
        return len(self.deliveries)


def run_duplicate_delivery_scenario() -> DuplicateDeliveryResult:
    """Deliver Request 42 twice, without suppressing either delivery."""
    baseline_events = (Receive(20), Reserve(1)) * 5
    business_event = Receive(1)
    ledger = InventoryLedger((*baseline_events, business_event))
    authority = RevisionedInventoryState(
        InventoryRevision(len(ledger.events)), ledger.current_state()
    )
    request = SynchronizationRequest("Projection", authority.state)
    registry = ProjectionRegistry(
        (InventoryProjection(request.system, InventoryState(0, 0)),)
    )
    queue = CapacityQueue()
    pool = WorkerPool(worker_count=1, service_time=1)
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    deliveries: list[RequestDelivery] = []

    def assign() -> None:
        pool.assign_available(
            queue=queue,
            current_time=clock.now,
            scheduler=scheduler,
            completion_action=complete,
        )

    def complete(worker_name: str) -> None:
        completion = pool.complete(
            worker_name=worker_name,
            projections=registry,
            current_time=clock.now,
        )
        deliveries.append(RequestDelivery(len(deliveries) + 1, request, completion))
        scheduler.schedule(
            at=clock.now, label="Assign duplicate delivery", action=assign
        )

    def deliver_twice() -> None:
        # Both work items deliberately carry the exact same request object.
        queue.enqueue(SynchronizationWorkItem(request, clock.now))
        queue.enqueue(SynchronizationWorkItem(request, clock.now))
        assign()

    scheduler.schedule(at=1, label="Deliver Request 42 twice", action=deliver_twice)
    history = scheduler.run()
    return DuplicateDeliveryResult(
        authority,
        (business_event,),
        42,
        request,
        tuple(deliveries),
        registry.get(request.system),
        history,
        queue.depth,
        clock.now,
    )
