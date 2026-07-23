"""Deterministic retry policies introduced in Chapter 17."""

from dataclasses import dataclass

from inventory_sim.capacity import CapacityQueue, SynchronizationWorkItem
from inventory_sim.fanout import FanOutGenerator
from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import ProjectionRegistry, SynchronizationRequest
from inventory_sim.revisions import InventoryRevision, RevisionedInventoryState
from inventory_sim.simulation import EventExecution, EventScheduler, VirtualClock
from inventory_sim.worker_pool import WorkerPool


@dataclass(frozen=True)
class SynchronizationAttempt:
    """One numbered delivery attempt for an unchanged request."""

    request: SynchronizationRequest
    number: int


@dataclass(frozen=True)
class AttemptCompletion:
    """The deterministic outcome of one synchronization attempt."""

    attempt: SynchronizationAttempt
    time: int
    succeeded: bool


@dataclass(frozen=True)
class RetryPolicy:
    """Fail configured systems once, then permit their next attempt."""

    fail_first_attempt_for: tuple[str, ...] = ()

    def succeeds(self, attempt: SynchronizationAttempt) -> bool:
        """Return the reproducible outcome for an attempt."""
        return not (
            attempt.number == 1
            and attempt.request.system in self.fail_first_attempt_for
        )


@dataclass(frozen=True)
class RetryScenarioResult:
    authority: RevisionedInventoryState
    requests: tuple[SynchronizationRequest, ...]
    completions: tuple[AttemptCompletion, ...]
    retry_attempts: tuple[SynchronizationAttempt, ...]
    final_projections: tuple[InventoryProjection, ...]
    scheduler_executions: tuple[EventExecution, ...]
    final_queue_depth: int
    final_time: int


def run_retry_scenario() -> RetryScenarioResult:
    """Run the fixed Revision 10 scenario in deterministic simulated time."""
    ledger = InventoryLedger((Receive(20), Reserve(1)) * 5)
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
    policy = RetryPolicy(("Warehouse",))
    queue = CapacityQueue()
    pool = WorkerPool(worker_count=1, service_time=1)
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    counts: dict[str, int] = {}
    active_attempts: dict[str, SynchronizationAttempt] = {}
    completions: list[AttemptCompletion] = []
    retries: list[SynchronizationAttempt] = []

    def assign() -> None:
        starts = pool.assign_available(
            queue=queue,
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
        attempt = active_attempts.pop(worker_name)
        succeeded = policy.succeeds(attempt)
        pool.complete(
            worker_name=worker_name,
            projections=registry,
            current_time=clock.now,
            update_projection=succeeded,
        )
        completions.append(AttemptCompletion(attempt, clock.now, succeeded))
        if not succeeded:
            retry = SynchronizationAttempt(attempt.request, attempt.number + 1)
            retries.append(retry)
            queue.enqueue(SynchronizationWorkItem(attempt.request, clock.now))
        scheduler.schedule(
            at=clock.now,
            label="Assign next synchronization attempt",
            action=assign,
        )

    def create_requests() -> None:
        for request in requests:
            queue.enqueue(SynchronizationWorkItem(request, clock.now))
        assign()

    scheduler.schedule(
        at=1, label="Create synchronization requests", action=create_requests
    )
    history = scheduler.run()
    return RetryScenarioResult(
        authority,
        requests,
        tuple(completions),
        tuple(retries),
        registry.projections,
        history,
        queue.depth,
        clock.now,
    )
