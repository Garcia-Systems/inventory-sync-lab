"""Scheduled direct inventory synchronization introduced in Chapter 6."""

from dataclasses import dataclass

from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve
from inventory_sim.projections import InventoryProjection
from inventory_sim.simulation import EventExecution, EventScheduler, VirtualClock


def synchronize_directly(
    *, projection: InventoryProjection, authoritative_state: InventoryState
) -> InventoryProjection:
    """Copy authoritative state into a new projection without scheduling work."""
    if not isinstance(projection, InventoryProjection):
        raise TypeError("projection must be an InventoryProjection")
    if not isinstance(authoritative_state, InventoryState):
        raise TypeError("authoritative_state must be an InventoryState")
    return projection.refresh_from(authoritative_state)


@dataclass(frozen=True)
class ProjectionInspection:
    """An immutable observation of a projection at one simulated time."""

    time: int
    system: str
    state: InventoryState
    available_difference: int
    matches: bool


@dataclass(frozen=True)
class DirectSynchronizationExecution:
    """An immutable record of one completed direct synchronization."""

    time: int
    system: str
    before: InventoryProjection
    after: InventoryProjection
    available_difference_before: int
    available_difference_after: int


@dataclass(frozen=True)
class DirectSynchronizationResult:
    """The inspectable result of the canonical Chapter 6 scenario."""

    authoritative_state: InventoryState
    initial_projection: InventoryProjection
    initial_available_difference: int
    inspections: tuple[ProjectionInspection, ...]
    synchronization: DirectSynchronizationExecution
    scheduler_executions: tuple[EventExecution, ...]
    final_projection: InventoryProjection
    final_time: int


class _ProjectionSlot:
    """A replaceable simulation reference to an immutable projection value."""

    def __init__(self, current: InventoryProjection) -> None:
        self.current = current

    def replace(self, projection: InventoryProjection) -> None:
        self.current = projection


def run_direct_synchronization_scenario() -> DirectSynchronizationResult:
    """Run the fixed, deterministic before/synchronize/after lesson."""
    authoritative_state = InventoryLedger([Receive(10), Reserve(3)]).current_state()
    initial_projection = InventoryProjection("website", InventoryState(10, 0))
    initial_comparison = initial_projection.compare_to(authoritative_state)
    slot = _ProjectionSlot(initial_projection)
    inspections: list[ProjectionInspection] = []
    synchronizations: list[DirectSynchronizationExecution] = []
    clock = VirtualClock()
    scheduler = EventScheduler(clock)

    def inspect() -> None:
        projection = slot.current
        comparison = projection.compare_to(authoritative_state)
        inspections.append(
            ProjectionInspection(
                clock.now,
                projection.system,
                projection.state,
                comparison.available_difference,
                comparison.matches,
            )
        )

    def synchronize() -> None:
        before = slot.current
        before_comparison = before.compare_to(authoritative_state)
        after = synchronize_directly(
            projection=before, authoritative_state=authoritative_state
        )
        after_comparison = after.compare_to(authoritative_state)
        slot.replace(after)
        synchronizations.append(
            DirectSynchronizationExecution(
                clock.now,
                before.system,
                before,
                after,
                before_comparison.available_difference,
                after_comparison.available_difference,
            )
        )

    scheduler.schedule(
        at=4, label="Inspect website before synchronization", action=inspect
    )
    scheduler.schedule(at=6, label="Directly synchronize website", action=synchronize)
    scheduler.schedule(
        at=8, label="Inspect website after synchronization", action=inspect
    )
    scheduler_executions = scheduler.run()
    return DirectSynchronizationResult(
        authoritative_state,
        initial_projection,
        initial_comparison.available_difference,
        tuple(inspections),
        synchronizations[0],
        scheduler_executions,
        slot.current,
        clock.now,
    )
