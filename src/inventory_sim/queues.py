"""Deterministic queued inventory synchronization introduced in Chapter 7."""

from collections import deque
from dataclasses import dataclass

from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve
from inventory_sim.projections import InventoryProjection
from inventory_sim.simulation import EventExecution, EventScheduler, VirtualClock
from inventory_sim.synchronization import ProjectionInspection, synchronize_directly


@dataclass(frozen=True)
class SynchronizationRequest:
    """An immutable request carrying authority as a creation-time snapshot."""

    system: str
    authoritative_state: InventoryState

    def __post_init__(self) -> None:
        # InventoryProjection owns the existing system-name validation rules.
        validated = InventoryProjection(self.system, self.authoritative_state)
        object.__setattr__(self, "system", validated.system)


class SynchronizationQueue:
    """A deterministic in-memory FIFO queue of synchronization requests."""

    def __init__(self) -> None:
        self._requests: deque[SynchronizationRequest] = deque()

    @property
    def depth(self) -> int:
        """Return the number of requests waiting to be processed."""
        return len(self._requests)

    @property
    def is_empty(self) -> bool:
        """Report whether no requests are waiting."""
        return not self._requests

    def enqueue(self, request: SynchronizationRequest) -> None:
        """Add a valid request to the back of the queue."""
        if not isinstance(request, SynchronizationRequest):
            raise TypeError("request must be a SynchronizationRequest")
        self._requests.append(request)

    def dequeue(self) -> SynchronizationRequest:
        """Remove the oldest request; raise IndexError when the queue is empty."""
        if self.is_empty:
            raise IndexError("cannot dequeue from an empty synchronization queue")
        return self._requests.popleft()


class ProjectionRegistry:
    """A small mutable holder for current immutable projection values."""

    def __init__(self, projections: tuple[InventoryProjection, ...]) -> None:
        if not isinstance(projections, tuple):
            raise TypeError("projections must be a tuple")
        current: dict[str, InventoryProjection] = {}
        for projection in projections:
            if not isinstance(projection, InventoryProjection):
                raise TypeError("each projection must be an InventoryProjection")
            if projection.system in current:
                raise ValueError(f"duplicate projection system: {projection.system}")
            current[projection.system] = projection
        self._current = current

    @property
    def projections(self) -> tuple[InventoryProjection, ...]:
        """Return an immutable snapshot of projections in registry order."""
        return tuple(self._current.values())

    def get(self, system: str) -> InventoryProjection:
        """Retrieve the current projection for a known system."""
        if not isinstance(system, str):
            raise TypeError("system must be a string")
        try:
            return self._current[system]
        except KeyError:
            raise KeyError(f"unknown projection system: {system}") from None

    def replace(self, projection: InventoryProjection) -> None:
        """Replace the current immutable value for an existing system."""
        if not isinstance(projection, InventoryProjection):
            raise TypeError("projection must be an InventoryProjection")
        if projection.system not in self._current:
            raise KeyError(f"unknown projection system: {projection.system}")
        self._current[projection.system] = projection


@dataclass(frozen=True)
class WorkerExecution:
    """An immutable record of one request processed by the single worker."""

    time: int
    system: str
    queue_depth_before: int
    queue_depth_after: int
    projection_before: InventoryProjection
    projection_after: InventoryProjection
    available_difference_before: int
    available_difference_after: int


class SynchronizationWorker:
    """Process at most one queued request each time it is called."""

    def __init__(
        self, *, queue: SynchronizationQueue, projections: ProjectionRegistry
    ) -> None:
        if not isinstance(queue, SynchronizationQueue):
            raise TypeError("queue must be a SynchronizationQueue")
        if not isinstance(projections, ProjectionRegistry):
            raise TypeError("projections must be a ProjectionRegistry")
        self._queue = queue
        self._projections = projections

    def process_next(self, *, time: int) -> WorkerExecution | None:
        """Process one oldest request, or return None when there is no work."""
        if isinstance(time, bool) or not isinstance(time, int):
            raise TypeError("time must be an integer")
        if time < 0:
            raise ValueError("time cannot be negative")
        if self._queue.is_empty:
            return None

        depth_before = self._queue.depth
        request = self._queue.dequeue()
        before = self._projections.get(request.system)
        before_comparison = before.compare_to(request.authoritative_state)
        after = synchronize_directly(
            projection=before, authoritative_state=request.authoritative_state
        )
        after_comparison = after.compare_to(request.authoritative_state)
        self._projections.replace(after)
        return WorkerExecution(
            time,
            request.system,
            depth_before,
            self._queue.depth,
            before,
            after,
            before_comparison.available_difference,
            after_comparison.available_difference,
        )


@dataclass(frozen=True)
class QueueEnqueueExecution:
    """An immutable observation of a request entering the queue."""

    time: int
    system: str
    queue_depth: int


@dataclass(frozen=True)
class QueueScenarioInspection:
    """An immutable observation of queue depth and both projections."""

    time: int
    queue_depth: int
    projections: tuple[ProjectionInspection, ...]


@dataclass(frozen=True)
class QueueSynchronizationResult:
    """The inspectable result of the canonical Chapter 7 scenario."""

    authoritative_state: InventoryState
    initial_projections: tuple[InventoryProjection, ...]
    initial_available_differences: tuple[int, ...]
    enqueues: tuple[QueueEnqueueExecution, ...]
    inspections: tuple[QueueScenarioInspection, ...]
    worker_executions: tuple[WorkerExecution, ...]
    scheduler_executions: tuple[EventExecution, ...]
    final_projections: tuple[InventoryProjection, ...]
    final_queue_depth: int
    final_time: int


def run_queue_synchronization_scenario() -> QueueSynchronizationResult:
    """Run the fixed Chapter 7 FIFO queue and single-worker lesson."""
    authority = InventoryLedger([Receive(10), Reserve(3)]).current_state()
    initial = (
        InventoryProjection("website", InventoryState(10, 0)),
        InventoryProjection("marketplace", InventoryState(10, 1)),
    )
    initial_differences = tuple(
        projection.compare_to(authority).available_difference for projection in initial
    )
    queue = SynchronizationQueue()
    registry = ProjectionRegistry(initial)
    worker = SynchronizationWorker(queue=queue, projections=registry)
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    enqueues: list[QueueEnqueueExecution] = []
    inspections: list[QueueScenarioInspection] = []
    worker_executions: list[WorkerExecution] = []

    def inspect() -> None:
        observations = []
        for projection in registry.projections:
            comparison = projection.compare_to(authority)
            observations.append(
                ProjectionInspection(
                    clock.now,
                    projection.system,
                    projection.state,
                    comparison.available_difference,
                    comparison.matches,
                )
            )
        inspections.append(
            QueueScenarioInspection(clock.now, queue.depth, tuple(observations))
        )

    def enqueue(system: str) -> None:
        # The authority snapshot is captured here, when the request is created.
        queue.enqueue(SynchronizationRequest(system, authority))
        enqueues.append(QueueEnqueueExecution(clock.now, system, queue.depth))

    def process_next() -> None:
        execution = worker.process_next(time=clock.now)
        if execution is not None:
            worker_executions.append(execution)

    actions = (
        (1, "Inspect initial projections", inspect),
        (2, "Enqueue website synchronization", lambda: enqueue("website")),
        (3, "Enqueue marketplace synchronization", lambda: enqueue("marketplace")),
        (4, "Inspect queued projections", inspect),
        (5, "Worker processes one request", process_next),
        (6, "Inspect projections after first worker action", inspect),
        (7, "Worker processes one request", process_next),
        (8, "Inspect final projections", inspect),
    )
    for at, label, action in actions:
        scheduler.schedule(at=at, label=label, action=action)
    scheduler_executions = scheduler.run()

    return QueueSynchronizationResult(
        authority,
        initial,
        initial_differences,
        tuple(enqueues),
        tuple(inspections),
        tuple(worker_executions),
        scheduler_executions,
        registry.projections,
        queue.depth,
        clock.now,
    )
