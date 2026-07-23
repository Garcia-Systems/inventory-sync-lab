"""Deterministic fixed-size worker pool introduced in Chapter 9."""

from collections.abc import Callable
from dataclasses import dataclass

from inventory_sim.capacity import (
    CapacityQueue,
    RequestArrival,
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
from inventory_sim.synchronization import ProjectionInspection


@dataclass(frozen=True)
class WorkerInspection:
    """One worker's immutable state at an inspection boundary."""

    name: str
    status: str
    current_system: str | None
    completion_time: int | None


@dataclass(frozen=True)
class MultipleWorkersInspection:
    """An immutable observation of pool, queue, and projection state."""

    time: int
    queue_depth: int
    total_worker_count: int
    busy_worker_count: int
    idle_worker_count: int
    workers: tuple[WorkerInspection, ...]
    projections: tuple[ProjectionInspection, ...]


class WorkerPool:
    """A fixed ordered collection of equally fast simulated workers."""

    def __init__(self, worker_count: int, service_time: int) -> None:
        if isinstance(worker_count, bool) or not isinstance(worker_count, int):
            raise TypeError("worker count must be an integer")
        if worker_count <= 0:
            raise ValueError("worker count must be positive")
        self._workers = tuple(
            WorkerState(service_time, name=f"worker-{number}")
            for number in range(1, worker_count + 1)
        )

    @classmethod
    def from_workers(cls, workers: tuple[WorkerState, ...]) -> "WorkerPool":
        """Build a pool from explicitly named workers, validating uniqueness."""
        if not isinstance(workers, tuple) or not workers:
            raise ValueError("workers must be a nonempty tuple")
        if any(not isinstance(worker, WorkerState) for worker in workers):
            raise TypeError("each worker must be a WorkerState")
        if len({worker.name for worker in workers}) != len(workers):
            raise ValueError("worker names must be unique within a pool")
        pool = cls.__new__(cls)
        pool._workers = workers
        return pool

    @property
    def workers(self) -> tuple[WorkerState, ...]:
        return self._workers

    @property
    def worker_count(self) -> int:
        return len(self._workers)

    @property
    def busy_worker_count(self) -> int:
        return sum(worker.is_busy for worker in self._workers)

    @property
    def idle_worker_count(self) -> int:
        return self.worker_count - self.busy_worker_count

    @property
    def service_time(self) -> int:
        return self._workers[0].service_time

    def get(self, name: str) -> WorkerState:
        for worker in self._workers:
            if worker.name == name:
                return worker
        raise KeyError(f"unknown worker: {name}")

    def assign_available(
        self,
        *,
        queue: CapacityQueue,
        current_time: int,
        scheduler: EventScheduler,
        completion_action: Callable[[str], None],
    ) -> tuple[WorkerProcessingStart, ...]:
        """Pair FIFO work with idle workers in stable worker-number order."""
        starts = []
        for worker in self._workers:
            if queue.is_empty:
                break
            if worker.is_busy:
                continue
            start = worker.start_next(queue=queue, current_time=current_time)
            assert start is not None
            starts.append(start)
            scheduler.schedule(
                at=start.completes_at,
                label=f"{worker.name} completes {start.system}",
                action=lambda name=worker.name: completion_action(name),
            )
        return tuple(starts)

    def complete(
        self,
        *,
        worker_name: str,
        projections: ProjectionRegistry,
        current_time: int,
        update_projection: bool = True,
    ) -> WorkerCompletion:
        return self.get(worker_name).complete(
            projections=projections,
            current_time=current_time,
            update_projection=update_projection,
        )


@dataclass(frozen=True)
class MultipleWorkersResult:
    authoritative_state: InventoryState
    initial_projections: tuple[InventoryProjection, ...]
    initial_available_differences: tuple[int, ...]
    worker_count: int
    service_time: int
    arrivals: tuple[RequestArrival, ...]
    processing_starts: tuple[WorkerProcessingStart, ...]
    completions: tuple[WorkerCompletion, ...]
    inspections: tuple[MultipleWorkersInspection, ...]
    scheduler_executions: tuple[EventExecution, ...]
    final_projections: tuple[InventoryProjection, ...]
    final_queue_depth: int
    final_workers: tuple[WorkerInspection, ...]
    final_time: int
    maximum_queue_depth: int
    average_wait_time: float
    maximum_wait_time: int


def run_multiple_workers_scenario() -> MultipleWorkersResult:
    """Run the canonical deterministic two-worker Chapter 9 scenario."""
    authority = InventoryLedger([Receive(10), Reserve(3)]).current_state()
    initial = (
        InventoryProjection("website", InventoryState(10, 0)),
        InventoryProjection("marketplace", InventoryState(10, 1)),
        InventoryProjection("storefront", InventoryState(8, 0)),
        InventoryProjection("partner", InventoryState(11, 2)),
    )
    registry = ProjectionRegistry(initial)
    queue = CapacityQueue()
    pool = WorkerPool(worker_count=2, service_time=3)
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    arrivals: list[RequestArrival] = []
    starts: list[WorkerProcessingStart] = []
    completions: list[WorkerCompletion] = []
    inspections: list[MultipleWorkersInspection] = []
    maximum_depth = 0
    coordination_times: set[int] = set()

    def assign() -> None:
        starts.extend(
            pool.assign_available(
                queue=queue,
                current_time=clock.now,
                scheduler=scheduler,
                completion_action=complete,
            )
        )

    def complete(worker_name: str) -> None:
        completions.append(
            pool.complete(
                worker_name=worker_name, projections=registry, current_time=clock.now
            )
        )
        # The first completion adds one coordination event behind every completion
        # already scheduled for this time. Thus all workers become idle first.
        if clock.now not in coordination_times:
            coordination_times.add(clock.now)
            scheduler.schedule(
                at=clock.now,
                label=f"Assign waiting work at time {clock.now}",
                action=assign,
            )

    def arrive(system: str) -> None:
        nonlocal maximum_depth
        queue.enqueue(
            SynchronizationWorkItem(
                SynchronizationRequest(system, authority), clock.now
            )
        )
        maximum_depth = max(maximum_depth, queue.depth)
        arrivals.append(RequestArrival(clock.now, system, queue.depth, False))

    def inspect() -> None:
        workers = tuple(
            WorkerInspection(
                worker.name,
                "IDLE" if worker.is_idle else "BUSY",
                None if worker.current is None else worker.current.request.system,
                worker.completes_at,
            )
            for worker in pool.workers
        )
        projections = tuple(
            ProjectionInspection(
                clock.now,
                projection.system,
                projection.state,
                projection.compare_to(authority).available_difference,
                projection.compare_to(authority).matches,
            )
            for projection in registry.projections
        )
        inspections.append(
            MultipleWorkersInspection(
                clock.now,
                queue.depth,
                pool.worker_count,
                pool.busy_worker_count,
                pool.idle_worker_count,
                workers,
                projections,
            )
        )

    # Same-time arrivals are deliberately enqueued before one assignment event.
    scheduler.schedule(
        at=1, label="Website request arrives", action=lambda: arrive("website")
    )
    scheduler.schedule(
        at=1, label="Marketplace request arrives", action=lambda: arrive("marketplace")
    )
    scheduler.schedule(at=1, label="Assign time-1 arrivals", action=assign)
    for at, system in ((2, "storefront"), (3, "partner")):
        scheduler.schedule(
            at=at,
            label=f"{system.capitalize()} request arrives",
            action=lambda system=system: arrive(system),
        )
        scheduler.schedule(at=at, label=f"Assign time-{at} arrivals", action=assign)
    for at in (3, 5, 8):
        scheduler.schedule(at=at, label=f"Inspect at time {at}", action=inspect)

    history = scheduler.run()
    final_workers = inspections[-1].workers
    waits = [completion.wait_time for completion in completions]
    return MultipleWorkersResult(
        authority,
        initial,
        tuple(p.compare_to(authority).available_difference for p in initial),
        pool.worker_count,
        pool.service_time,
        tuple(arrivals),
        tuple(starts),
        tuple(completions),
        tuple(inspections),
        history,
        registry.projections,
        queue.depth,
        final_workers,
        clock.now,
        maximum_depth,
        sum(waits) / len(waits),
        max(waits),
    )
