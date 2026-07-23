"""Fixed-time, single-worker processing introduced in Chapter 8."""

from collections import deque
from dataclasses import dataclass

from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import ProjectionRegistry, SynchronizationRequest
from inventory_sim.simulation import EventExecution, EventScheduler, VirtualClock
from inventory_sim.synchronization import ProjectionInspection, synchronize_directly


def _nonnegative_time(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} cannot be negative")
    return value


@dataclass(frozen=True)
class SynchronizationWorkItem:
    """A synchronization request paired with its simulated arrival time."""

    request: SynchronizationRequest
    arrived_at: int

    def __post_init__(self) -> None:
        if not isinstance(self.request, SynchronizationRequest):
            raise TypeError("request must be a SynchronizationRequest")
        _nonnegative_time(self.arrived_at, name="arrival time")


class CapacityQueue:
    """The FIFO collection of work items waiting to start."""

    def __init__(self) -> None:
        self._items: deque[SynchronizationWorkItem] = deque()

    @property
    def depth(self) -> int:
        return len(self._items)

    @property
    def is_empty(self) -> bool:
        return not self._items

    def enqueue(self, item: SynchronizationWorkItem) -> None:
        if not isinstance(item, SynchronizationWorkItem):
            raise TypeError("item must be a SynchronizationWorkItem")
        self._items.append(item)

    def dequeue(self) -> SynchronizationWorkItem:
        if self.is_empty:
            raise IndexError("cannot dequeue from an empty capacity queue")
        return self._items.popleft()


@dataclass(frozen=True)
class WorkerProcessingStart:
    """An immutable record of a request leaving the queue and starting."""

    system: str
    arrived_at: int
    started_at: int
    completes_at: int
    queue_depth_after: int
    wait_time: int


@dataclass(frozen=True)
class WorkerCompletion:
    """An immutable record of a request completing and becoming visible."""

    system: str
    arrived_at: int
    started_at: int
    completed_at: int
    wait_time: int
    service_time: int
    total_time: int
    projection_before: InventoryProjection
    projection_after: InventoryProjection
    available_difference_before: int
    available_difference_after: int


class WorkerState:
    """One simulated worker with a fixed service time."""

    def __init__(self, service_time: int) -> None:
        validated = _nonnegative_time(service_time, name="service time")
        if validated == 0:
            raise ValueError("service time must be positive")
        self._service_time = validated
        self._current: SynchronizationWorkItem | None = None
        self._started_at: int | None = None
        self._completes_at: int | None = None

    @property
    def service_time(self) -> int:
        return self._service_time

    @property
    def current(self) -> SynchronizationWorkItem | None:
        return self._current

    @property
    def started_at(self) -> int | None:
        return self._started_at

    @property
    def completes_at(self) -> int | None:
        return self._completes_at

    @property
    def is_idle(self) -> bool:
        return self._current is None

    @property
    def is_busy(self) -> bool:
        return not self.is_idle

    def start_next(
        self, *, queue: CapacityQueue, current_time: int
    ) -> WorkerProcessingStart | None:
        """Start the oldest waiting item; a busy worker raises RuntimeError."""
        now = _nonnegative_time(current_time, name="current time")
        if not isinstance(queue, CapacityQueue):
            raise TypeError("queue must be a CapacityQueue")
        if self.is_busy:
            raise RuntimeError("busy worker cannot start another request")
        if queue.is_empty:
            return None
        item = queue.dequeue()
        if now < item.arrived_at:
            raise ValueError("work cannot start before it arrives")
        self._current = item
        self._started_at = now
        self._completes_at = now + self.service_time
        return WorkerProcessingStart(
            item.request.system,
            item.arrived_at,
            now,
            self._completes_at,
            queue.depth,
            now - item.arrived_at,
        )

    def complete(
        self, *, projections: ProjectionRegistry, current_time: int
    ) -> WorkerCompletion:
        """Complete current work at its scheduled time and become idle."""
        now = _nonnegative_time(current_time, name="current time")
        if not isinstance(projections, ProjectionRegistry):
            raise TypeError("projections must be a ProjectionRegistry")
        if self.is_idle:
            raise RuntimeError("idle worker has no request to complete")
        if now != self._completes_at:
            raise ValueError("work must complete at its scheduled completion time")

        item = self._current
        started_at = self._started_at
        assert item is not None and started_at is not None
        request = item.request
        before = projections.get(request.system)
        before_difference = before.compare_to(
            request.authoritative_state
        ).available_difference
        after = synchronize_directly(
            projection=before, authoritative_state=request.authoritative_state
        )
        after_difference = after.compare_to(
            request.authoritative_state
        ).available_difference
        projections.replace(after)
        completion = WorkerCompletion(
            request.system,
            item.arrived_at,
            started_at,
            now,
            started_at - item.arrived_at,
            self.service_time,
            now - item.arrived_at,
            before,
            after,
            before_difference,
            after_difference,
        )
        self._current = None
        self._started_at = None
        self._completes_at = None
        return completion


@dataclass(frozen=True)
class RequestArrival:
    time: int
    system: str
    queue_depth: int
    started_immediately: bool


@dataclass(frozen=True)
class CapacityScenarioInspection:
    time: int
    worker_status: str
    current_system: str | None
    current_completion_time: int | None
    queue_depth: int
    projections: tuple[ProjectionInspection, ...]


@dataclass(frozen=True)
class WorkerCapacityResult:
    authoritative_state: InventoryState
    initial_projections: tuple[InventoryProjection, ...]
    initial_available_differences: tuple[int, ...]
    arrivals: tuple[RequestArrival, ...]
    processing_starts: tuple[WorkerProcessingStart, ...]
    completions: tuple[WorkerCompletion, ...]
    inspections: tuple[CapacityScenarioInspection, ...]
    scheduler_executions: tuple[EventExecution, ...]
    final_projections: tuple[InventoryProjection, ...]
    final_queue_depth: int
    final_worker_status: str
    final_time: int
    service_time: int
    busy_time: int
    utilization: float


def run_worker_capacity_scenario() -> WorkerCapacityResult:
    """Run the canonical fixed-service-time Chapter 8 scenario."""
    authority = InventoryLedger([Receive(10), Reserve(3)]).current_state()
    initial = (
        InventoryProjection("website", InventoryState(10, 0)),
        InventoryProjection("marketplace", InventoryState(10, 1)),
        InventoryProjection("storefront", InventoryState(8, 0)),
    )
    initial_differences = tuple(
        projection.compare_to(authority).available_difference for projection in initial
    )
    queue = CapacityQueue()
    registry = ProjectionRegistry(initial)
    worker = WorkerState(service_time=3)
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    arrivals: list[RequestArrival] = []
    starts: list[WorkerProcessingStart] = []
    completions: list[WorkerCompletion] = []
    inspections: list[CapacityScenarioInspection] = []

    def start_next() -> WorkerProcessingStart | None:
        start = worker.start_next(queue=queue, current_time=clock.now)
        if start is not None:
            starts.append(start)
            scheduler.schedule(
                at=start.completes_at,
                label=f"Complete {start.system} synchronization",
                action=complete_current,
            )
        return start

    def complete_current() -> None:
        completions.append(
            worker.complete(projections=registry, current_time=clock.now)
        )
        start_next()

    def arrive(system: str) -> None:
        queue.enqueue(
            SynchronizationWorkItem(
                SynchronizationRequest(system, authority), clock.now
            )
        )
        started_immediately = worker.is_idle
        if started_immediately:
            start_next()
        arrivals.append(
            RequestArrival(clock.now, system, queue.depth, started_immediately)
        )

    def inspect() -> None:
        observations = tuple(
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
            CapacityScenarioInspection(
                clock.now,
                "IDLE" if worker.is_idle else "BUSY",
                None if worker.current is None else worker.current.request.system,
                worker.completes_at,
                queue.depth,
                observations,
            )
        )

    for at, system in ((1, "website"), (2, "marketplace"), (3, "storefront")):
        scheduler.schedule(
            at=at,
            label=f"{system.capitalize()} request arrives",
            action=lambda system=system: arrive(system),
        )
    for at in (3, 5, 8, 11):
        scheduler.schedule(at=at, label=f"Inspect at time {at}", action=inspect)
    history = scheduler.run()
    busy_time = len(completions) * worker.service_time
    return WorkerCapacityResult(
        authority,
        initial,
        initial_differences,
        tuple(arrivals),
        tuple(starts),
        tuple(completions),
        tuple(inspections),
        history,
        registry.projections,
        queue.depth,
        "IDLE" if worker.is_idle else "BUSY",
        clock.now,
        worker.service_time,
        busy_time,
        busy_time / clock.now,
    )
