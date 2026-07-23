"""Idempotent synchronization introduced in Chapter 19."""

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
from inventory_sim.revisions import InventoryRevision, RevisionedInventoryState
from inventory_sim.simulation import EventExecution, EventScheduler, VirtualClock
from inventory_sim.worker_pool import WorkerPool


class AppliedRequestRegistry:
    """Remember request identifiers applied by each projection in this simulation."""

    def __init__(self) -> None:
        self._applied: dict[str, set[int]] = {}

    def already_applied(self, request: SynchronizationRequest) -> bool:
        """Report whether this projection has applied the identified request."""
        request_id = self._validated_id(request)
        return request_id in self._applied.get(request.system, set())

    def record_applied(self, request: SynchronizationRequest) -> None:
        """Record a successful first application for its target projection."""
        request_id = self._validated_id(request)
        self._applied.setdefault(request.system, set()).add(request_id)

    @staticmethod
    def _validated_id(request: SynchronizationRequest) -> int:
        if not isinstance(request, SynchronizationRequest):
            raise TypeError("request must be a SynchronizationRequest")
        if request.request_id is None:
            raise ValueError("idempotent synchronization requires a request id")
        return request.request_id


@dataclass(frozen=True)
class IdempotentDelivery:
    """The outcome of processing one delivery of an immutable request."""

    number: int
    request: SynchronizationRequest
    completion: WorkerCompletion
    projection_updated: bool

    @property
    def already_applied(self) -> bool:
        return not self.projection_updated


@dataclass(frozen=True)
class IdempotencyResult:
    """Inspectable outcome of the fixed Chapter 19 scenario."""

    authority: RevisionedInventoryState
    request: SynchronizationRequest
    deliveries: tuple[IdempotentDelivery, ...]
    initial_projection: InventoryProjection
    final_projection: InventoryProjection
    scheduler_executions: tuple[EventExecution, ...]
    final_queue_depth: int
    final_time: int

    @property
    def projection_update_count(self) -> int:
        return sum(delivery.projection_updated for delivery in self.deliveries)


def run_idempotency_scenario() -> IdempotencyResult:
    """Deliver Request 57 three times while applying it only once."""
    ledger = InventoryLedger((Receive(20), Reserve(1)) * 6)
    authority = RevisionedInventoryState(
        InventoryRevision(len(ledger.events)), ledger.current_state()
    )
    request = SynchronizationRequest("Projection", authority.state, request_id=57)
    initial = InventoryProjection(request.system, InventoryState(0, 0))
    projections = ProjectionRegistry((initial,))
    applied_requests = AppliedRequestRegistry()
    queue = CapacityQueue()
    pool = WorkerPool(worker_count=1, service_time=1)
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    deliveries: list[IdempotentDelivery] = []

    def assign() -> None:
        pool.assign_available(
            queue=queue,
            current_time=clock.now,
            scheduler=scheduler,
            completion_action=complete,
        )

    def complete(worker_name: str) -> None:
        duplicate = applied_requests.already_applied(request)
        completion = pool.complete(
            worker_name=worker_name,
            projections=projections,
            current_time=clock.now,
            update_projection=not duplicate,
        )
        if not duplicate:
            applied_requests.record_applied(request)
        deliveries.append(
            IdempotentDelivery(len(deliveries) + 1, request, completion, not duplicate)
        )
        scheduler.schedule(at=clock.now, label="Assign next delivery", action=assign)

    def deliver_three_times() -> None:
        for _ in range(3):
            queue.enqueue(SynchronizationWorkItem(request, clock.now))
        assign()

    scheduler.schedule(
        at=1, label="Deliver Request 57 three times", action=deliver_three_times
    )
    history = scheduler.run()
    return IdempotencyResult(
        authority,
        request,
        tuple(deliveries),
        initial,
        projections.get(request.system),
        history,
        queue.depth,
        clock.now,
    )
