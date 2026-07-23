"""Chapter 23's deterministic end-to-end operations laboratory."""

from dataclasses import dataclass

from inventory_sim.capacity import CapacityQueue, SynchronizationWorkItem
from inventory_sim.dead_letter import (
    MAXIMUM_ATTEMPTS_EXCEEDED,
    DeadLetterEntry,
    DeadLetterQueue,
    DeadLetterRetryPolicy,
)
from inventory_sim.fanout import FanOutGenerator
from inventory_sim.idempotency import AppliedRequestRegistry
from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve
from inventory_sim.ordering import revision_advances_projection
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import ProjectionRegistry, SynchronizationRequest
from inventory_sim.retries import SynchronizationAttempt
from inventory_sim.revisions import (
    InventoryRevision,
    RevisionedInventoryState,
    RevisionedProjection,
)
from inventory_sim.simulation import EventExecution, EventScheduler, VirtualClock
from inventory_sim.worker_pool import WorkerPool


@dataclass(frozen=True)
class LaboratoryOperation:
    """One completed delivery and the policies applied to it."""

    time: int
    worker: str
    request: SynchronizationRequest
    revision: InventoryRevision
    attempt: int
    outcome: str


@dataclass(frozen=True)
class OperationalSummary:
    """The concise, inspectable dashboard for the complete run."""

    authority_revision: int
    registered_projections: int
    synchronization_requests: int
    successful_synchronizations: int
    retries: int
    duplicate_deliveries: int
    idempotent_skips: int
    rejected_stale_updates: int
    ordering_skips: int
    dead_letter_entries: int


@dataclass(frozen=True)
class LaboratoryResult:
    """All important inputs, events, and outputs of the capstone scenario."""

    ledger: InventoryLedger
    authorities: tuple[RevisionedInventoryState, ...]
    requests: tuple[SynchronizationRequest, ...]
    operations: tuple[LaboratoryOperation, ...]
    final_projections: tuple[RevisionedProjection, ...]
    dead_letters: tuple[DeadLetterEntry, ...]
    scheduler_executions: tuple[EventExecution, ...]
    summary: OperationalSummary
    final_queue_depth: int
    final_time: int


def run_laboratory_scenario() -> LaboratoryResult:
    """Run one fixed scenario through the components from Chapters 1--22."""
    ledger = InventoryLedger((Receive(2), Reserve(1)) * 8)
    authorities = tuple(
        RevisionedInventoryState(
            InventoryRevision(position),
            InventoryLedger(ledger.events[:position]).current_state(),
        )
        for position in (15, 16)
    )
    registry = ProjectionRegistry(
        tuple(
            InventoryProjection(system, InventoryState(0, 0))
            for system in ("Storefront", "Warehouse", "Reporting")
        )
    )
    requests = tuple(
        SynchronizationRequest(
            request.system, request.authoritative_state, authority.revision.value
        )
        for authority in authorities
        for request in FanOutGenerator(registry).generate(authority)
    )
    request_revisions = {
        (request.system, request.request_id): InventoryRevision(request.request_id)
        for request in requests
        if request.request_id is not None
    }
    delayed_stale_request = SynchronizationRequest(
        "Warehouse", authorities[0].state, request_id=151
    )
    request_revisions[("Warehouse", 151)] = authorities[0].revision
    projection_revisions = {
        projection.system: InventoryRevision(1) for projection in registry.projections
    }
    policy = DeadLetterRetryPolicy(
        maximum_attempts=3,
        fail_first_attempt_for=("Warehouse",),
        always_fail_for=("Reporting",),
    )
    applied = AppliedRequestRegistry()
    dead_letters = DeadLetterQueue()
    queue = CapacityQueue()
    pool = WorkerPool(worker_count=2, service_time=1)
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    attempts: dict[tuple[str, int], int] = {}
    active: dict[str, SynchronizationAttempt] = {}
    operations: list[LaboratoryOperation] = []
    retries = 0
    duplicates = 0
    idempotent_skips = 0
    ordering_skips = 0
    successes = 0
    second_wave_started = False

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
            assert request.request_id is not None
            key = (request.system, request.request_id)
            attempts[key] = attempts.get(key, 0) + 1
            active[start.worker_name] = SynchronizationAttempt(request, attempts[key])

    def enqueue_second_wave() -> None:
        nonlocal second_wave_started
        second_wave_started = True
        newest = requests[3:]
        deliveries = (*newest, newest[0], delayed_stale_request)
        for request in deliveries:
            queue.enqueue(SynchronizationWorkItem(request, clock.now))
        assign()

    def coordinate() -> None:
        if not queue.is_empty:
            assign()
        elif pool.busy_worker_count == 0 and not second_wave_started:
            scheduler.schedule(
                at=clock.now,
                label="Fan out Revision 16 plus duplicate and delayed stale work",
                action=enqueue_second_wave,
            )

    def complete(worker_name: str) -> None:
        nonlocal retries, duplicates, idempotent_skips, ordering_skips, successes
        attempt = active.pop(worker_name)
        request = attempt.request
        assert request.request_id is not None
        revision = request_revisions[(request.system, request.request_id)]
        # Reporting 15 is the permanent failure; Reporting 16 demonstrates recovery.
        fails = request.request_id == 15 and not policy.succeeds(attempt)
        duplicate = applied.already_applied(request)
        advances = revision_advances_projection(
            request_revision=revision,
            projection_revision=projection_revisions[request.system],
        )
        update = not fails and not duplicate and advances
        pool.complete(
            worker_name=worker_name,
            projections=registry,
            current_time=clock.now,
            update_projection=update,
        )
        if fails and policy.may_retry(attempt):
            retries += 1
            outcome = "RETRY"
            queue.enqueue(SynchronizationWorkItem(request, clock.now))
        elif fails:
            outcome = "DEAD LETTER"
            dead_letters.enqueue(
                DeadLetterEntry(
                    request, revision, MAXIMUM_ATTEMPTS_EXCEEDED, attempt.number
                )
            )
        elif duplicate:
            duplicates += 1
            idempotent_skips += 1
            outcome = "IDEMPOTENT SKIP"
        elif not advances:
            ordering_skips += 1
            outcome = "ORDERING SKIP"
            applied.record_applied(request)
        else:
            successes += 1
            outcome = "APPLIED"
            applied.record_applied(request)
            projection_revisions[request.system] = revision
        operations.append(
            LaboratoryOperation(
                clock.now, worker_name, request, revision, attempt.number, outcome
            )
        )
        scheduler.schedule(
            at=clock.now, label="Coordinate worker pool", action=coordinate
        )

    def first_wave() -> None:
        for request in requests[:3]:
            queue.enqueue(SynchronizationWorkItem(request, clock.now))
        assign()

    scheduler.schedule(at=1, label="Fan out Revision 15", action=first_wave)
    history = scheduler.run()
    final_projections = tuple(
        RevisionedProjection(projection, projection_revisions[projection.system])
        for projection in registry.projections
    )
    summary = OperationalSummary(
        authority_revision=16,
        registered_projections=len(final_projections),
        synchronization_requests=len(requests) + 1,
        successful_synchronizations=successes,
        retries=retries,
        duplicate_deliveries=duplicates,
        idempotent_skips=idempotent_skips,
        rejected_stale_updates=ordering_skips,
        ordering_skips=ordering_skips,
        dead_letter_entries=dead_letters.depth,
    )
    return LaboratoryResult(
        ledger,
        authorities,
        requests,
        tuple(operations),
        final_projections,
        dead_letters.entries,
        history,
        summary,
        queue.depth,
        clock.now,
    )
