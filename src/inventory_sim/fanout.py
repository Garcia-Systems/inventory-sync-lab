"""Deterministic synchronization fan-out introduced in Chapter 16."""

from dataclasses import dataclass

from inventory_sim.capacity import (
    CapacityQueue,
    SynchronizationWorkItem,
    WorkerCompletion,
)
from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve, Ship
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import ProjectionRegistry, SynchronizationRequest
from inventory_sim.revisions import (
    InventoryRevision,
    RevisionedInventoryState,
    observe_ledger_revisions,
)
from inventory_sim.simulation import EventExecution, EventScheduler, VirtualClock
from inventory_sim.worker_pool import WorkerPool


class FanOutGenerator:
    """Create one ordered synchronization request per registered projection."""

    def __init__(self, projections: ProjectionRegistry) -> None:
        if not isinstance(projections, ProjectionRegistry):
            raise TypeError("projections must be a ProjectionRegistry")
        self._projections = projections

    def generate(
        self, authority: RevisionedInventoryState
    ) -> tuple[SynchronizationRequest, ...]:
        """Copy one authority snapshot into work ordered by registry order."""
        if not isinstance(authority, RevisionedInventoryState):
            raise TypeError("authority must be a RevisionedInventoryState")
        return tuple(
            SynchronizationRequest(projection.system, authority.state)
            for projection in self._projections.projections
        )


@dataclass(frozen=True)
class RevisionedProjection:
    """A projection paired with the authority revision it has applied."""

    projection: InventoryProjection
    revision: InventoryRevision


@dataclass(frozen=True)
class FanOutResult:
    """Inspectable outcome of the deterministic Chapter 16 scenario."""

    authority: RevisionedInventoryState
    requests: tuple[SynchronizationRequest, ...]
    initial_projections: tuple[RevisionedProjection, ...]
    final_projections: tuple[RevisionedProjection, ...]
    completions: tuple[WorkerCompletion, ...]
    scheduler_executions: tuple[EventExecution, ...]
    final_queue_depth: int
    final_time: int


def run_fanout_scenario() -> FanOutResult:
    """Fan one Revision 8 snapshot out to three independent projections."""
    ledger = InventoryLedger(
        (
            Receive(20),
            Reserve(2),
            Ship(1),
            Receive(4),
            Reserve(3),
            Ship(2),
            Receive(1),
            Reserve(1),
        )
    )
    authority = observe_ledger_revisions(ledger)[-1]
    systems = ("Storefront", "Warehouse", "Reporting")
    initial = tuple(
        RevisionedProjection(
            InventoryProjection(system, InventoryState(0, 0)), InventoryRevision(1)
        )
        for system in systems
    )
    registry = ProjectionRegistry(tuple(item.projection for item in initial))
    requests = FanOutGenerator(registry).generate(authority)
    revisions = {item.projection.system: item.revision for item in initial}
    queue = CapacityQueue()
    pool = WorkerPool(worker_count=3, service_time=1)
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    completions: list[WorkerCompletion] = []

    def generate_work() -> None:
        for request in requests:
            queue.enqueue(SynchronizationWorkItem(request, clock.now))
        pool.assign_available(
            queue=queue,
            current_time=clock.now,
            scheduler=scheduler,
            completion_action=complete,
        )

    def complete(worker_name: str) -> None:
        completion = pool.complete(
            worker_name=worker_name, projections=registry, current_time=clock.now
        )
        completions.append(completion)
        revisions[completion.system] = authority.revision

    scheduler.schedule(at=1, label="Generate fan-out requests", action=generate_work)
    history = scheduler.run()
    final = tuple(
        RevisionedProjection(projection, revisions[projection.system])
        for projection in registry.projections
    )
    return FanOutResult(
        authority,
        requests,
        initial,
        final,
        tuple(completions),
        history,
        queue.depth,
        clock.now,
    )
