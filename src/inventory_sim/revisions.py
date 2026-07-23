"""Deterministic inventory ordering introduced in Chapter 12."""

from dataclasses import dataclass

from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import SynchronizationRequest
from inventory_sim.synchronization import synchronize_directly


@dataclass(frozen=True, order=True)
class InventoryRevision:
    """A positive, monotonically increasing position in ledger history."""

    value: int

    def __post_init__(self) -> None:
        if type(self.value) is not int or self.value < 1:
            raise ValueError("revision must be a positive integer")


@dataclass(frozen=True)
class RevisionedInventoryState:
    """An immutable inventory state observed at one ledger revision."""

    revision: InventoryRevision
    state: InventoryState

    def __post_init__(self) -> None:
        if not isinstance(self.revision, InventoryRevision):
            raise TypeError("revision must be an InventoryRevision")
        if not isinstance(self.state, InventoryState):
            raise TypeError("state must be an InventoryState")


@dataclass(frozen=True)
class RevisionScenarioResult:
    """The inspectable result of the canonical ordering demonstration."""

    observations: tuple[RevisionedInventoryState, ...]
    requests: tuple[SynchronizationRequest, ...]
    synchronized_states: tuple[InventoryState, ...]


def observe_ledger_revisions(
    ledger: InventoryLedger,
) -> tuple[RevisionedInventoryState, ...]:
    """Replay each non-empty ledger prefix as its deterministic revision."""
    if not isinstance(ledger, InventoryLedger):
        raise TypeError("ledger must be an InventoryLedger")
    return tuple(
        RevisionedInventoryState(
            InventoryRevision(position),
            InventoryLedger(ledger.events[:position]).current_state(),
        )
        for position in range(1, len(ledger.events) + 1)
    )


def run_inventory_revisions_scenario() -> RevisionScenarioResult:
    """Show repeated quantity, increasing revision, and unchanged copying."""
    ledger = InventoryLedger((Receive(10), Reserve(3), Receive(3)))
    observations = observe_ledger_revisions(ledger)
    requests = tuple(
        SynchronizationRequest("website", observation.state)
        for observation in observations
    )
    projection = InventoryProjection("website", InventoryState(0, 0))
    synchronized_states: list[InventoryState] = []
    for request in requests:
        projection = synchronize_directly(
            projection=projection,
            authoritative_state=request.authoritative_state,
        )
        synchronized_states.append(projection.state)
    return RevisionScenarioResult(observations, requests, tuple(synchronized_states))
