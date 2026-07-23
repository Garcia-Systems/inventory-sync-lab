"""Deterministic dead-letter isolation introduced in Chapter 22."""

from dataclasses import dataclass

from inventory_sim.capacity import CapacityQueue, SynchronizationWorkItem
from inventory_sim.fanout import FanOutGenerator
from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import ProjectionRegistry, SynchronizationRequest
from inventory_sim.retries import AttemptCompletion, SynchronizationAttempt
from inventory_sim.revisions import InventoryRevision, RevisionedInventoryState
from inventory_sim.simulation import EventExecution, EventScheduler, VirtualClock
from inventory_sim.worker_pool import WorkerPool

MAXIMUM_ATTEMPTS_EXCEEDED = "Maximum retry attempts exceeded"


@dataclass(frozen=True)
class DeadLetterEntry:
    """An immutable request isolated after its final permitted attempt."""

    request: SynchronizationRequest
    revision: InventoryRevision
    reason: str
    attempts: int


class DeadLetterQueue:
    """A deterministic insertion-ordered collection for terminal failures."""

    def __init__(self) -> None:
        self._entries: list[DeadLetterEntry] = []

    def enqueue(self, entry: DeadLetterEntry) -> None:
        """Append a terminal failure for later inspection."""
        self._entries.append(entry)

    @property
    def entries(self) -> tuple[DeadLetterEntry, ...]:
        """Return an immutable, insertion-ordered snapshot of the queue."""
        return tuple(self._entries)

    @property
    def depth(self) -> int:
        """Return the number of isolated requests."""
        return len(self._entries)


@dataclass(frozen=True)
class DeadLetterRetryPolicy:
    """Bound attempts and provide fixed outcomes for the chapter scenario."""

    maximum_attempts: int
    fail_first_attempt_for: tuple[str, ...] = ()
    always_fail_for: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.maximum_attempts, bool) or not isinstance(
            self.maximum_attempts, int
        ):
            raise TypeError("maximum attempts must be an integer")
        if self.maximum_attempts <= 0:
            raise ValueError("maximum attempts must be positive")

    def succeeds(self, attempt: SynchronizationAttempt) -> bool:
        """Return the configured deterministic outcome for an attempt."""
        system = attempt.request.system
        if system in self.always_fail_for:
            return False
        return not (attempt.number == 1 and system in self.fail_first_attempt_for)

    def may_retry(self, attempt: SynchronizationAttempt) -> bool:
        """Return whether another attempt remains within the configured limit."""
        return attempt.number < self.maximum_attempts


@dataclass(frozen=True)
class DeadLetterScenarioResult:
    authority: RevisionedInventoryState
    requests: tuple[SynchronizationRequest, ...]
    completions: tuple[AttemptCompletion, ...]
    retry_count: int
    successful_requests: tuple[SynchronizationRequest, ...]
    dead_letters: tuple[DeadLetterEntry, ...]
    final_projections: tuple[InventoryProjection, ...]
    scheduler_executions: tuple[EventExecution, ...]
    final_queue_depth: int
    final_time: int


def run_dead_letter_scenario(
    maximum_attempts: int = 3,
) -> DeadLetterScenarioResult:
    """Run the fixed three-request dead-letter scenario in simulated time."""
    ledger = InventoryLedger((Receive(2), Reserve(1)) * 7 + (Receive(2),))
    authority = RevisionedInventoryState(
        InventoryRevision(len(ledger.events)), ledger.current_state()
    )
    registry = ProjectionRegistry(
        tuple(
            InventoryProjection(system, InventoryState(0, 0))
            for system in ("Storefront", "Warehouse", "Reporting")
        )
    )
    requests = FanOutGenerator(registry).generate(authority)
    policy = DeadLetterRetryPolicy(
        maximum_attempts,
        fail_first_attempt_for=("Warehouse",),
        always_fail_for=("Reporting",),
    )
    work_queue = CapacityQueue()
    dead_letter_queue = DeadLetterQueue()
    pool = WorkerPool(worker_count=1, service_time=1)
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    counts: dict[str, int] = {}
    active_attempts: dict[str, SynchronizationAttempt] = {}
    completions: list[AttemptCompletion] = []
    successful: list[SynchronizationRequest] = []
    retry_count = 0

    def assign() -> None:
        starts = pool.assign_available(
            queue=work_queue,
            current_time=clock.now,
            scheduler=scheduler,
            completion_action=complete,
        )
        for start in starts:
            worker = pool.get(start.worker_name)
            assert worker.current is not None
            request = worker.current.request
            counts[request.system] = counts.get(request.system, 0) + 1
            active_attempts[start.worker_name] = SynchronizationAttempt(
                request, counts[request.system]
            )

    def complete(worker_name: str) -> None:
        nonlocal retry_count
        attempt = active_attempts.pop(worker_name)
        succeeded = policy.succeeds(attempt)
        pool.complete(
            worker_name=worker_name,
            projections=registry,
            current_time=clock.now,
            update_projection=succeeded,
        )
        completions.append(AttemptCompletion(attempt, clock.now, succeeded))
        if succeeded:
            successful.append(attempt.request)
        elif policy.may_retry(attempt):
            retry_count += 1
            work_queue.enqueue(SynchronizationWorkItem(attempt.request, clock.now))
        else:
            dead_letter_queue.enqueue(
                DeadLetterEntry(
                    attempt.request,
                    authority.revision,
                    MAXIMUM_ATTEMPTS_EXCEEDED,
                    attempt.number,
                )
            )
        scheduler.schedule(
            at=clock.now,
            label="Assign next synchronization attempt",
            action=assign,
        )

    def create_requests() -> None:
        for request in requests:
            work_queue.enqueue(SynchronizationWorkItem(request, clock.now))
        assign()

    scheduler.schedule(
        at=1, label="Create synchronization requests", action=create_requests
    )
    history = scheduler.run()
    return DeadLetterScenarioResult(
        authority=authority,
        requests=requests,
        completions=tuple(completions),
        retry_count=retry_count,
        successful_requests=tuple(successful),
        dead_letters=dead_letter_queue.entries,
        final_projections=registry.projections,
        scheduler_executions=history,
        final_queue_depth=work_queue.depth,
        final_time=clock.now,
    )
