"""Inventory events and the immutable ledger introduced in Chapter 3."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from inventory_sim.inventory import InventoryState


class InventoryEventType(Enum):
    """The kinds of inventory change understood by the Chapter 3 ledger."""

    RECEIVE = "Receive"
    RESERVE = "Reserve"
    RELEASE_RESERVATION = "Release reservation"
    SHIP = "Ship"
    ADJUSTMENT = "Adjustment"


@dataclass(frozen=True)
class InventoryEvent:
    """A single recorded inventory change."""

    event_type: InventoryEventType
    quantity: int

    def __post_init__(self) -> None:
        if not isinstance(self.event_type, InventoryEventType):
            raise ValueError("event_type must be a valid InventoryEventType")
        if type(self.quantity) is not int or self.quantity <= 0:
            raise ValueError("quantity must be a positive integer")


def Receive(quantity: int) -> InventoryEvent:  # noqa: N802
    """Record inventory arriving."""
    return InventoryEvent(InventoryEventType.RECEIVE, quantity)


def Reserve(quantity: int) -> InventoryEvent:  # noqa: N802
    """Record inventory being reserved."""
    return InventoryEvent(InventoryEventType.RESERVE, quantity)


def ReleaseReservation(quantity: int) -> InventoryEvent:  # noqa: N802
    """Record a reservation being released."""
    return InventoryEvent(InventoryEventType.RELEASE_RESERVATION, quantity)


def Ship(quantity: int) -> InventoryEvent:  # noqa: N802
    """Record reserved inventory leaving."""
    return InventoryEvent(InventoryEventType.SHIP, quantity)


def Adjustment(quantity: int) -> InventoryEvent:  # noqa: N802
    """Record a positive Chapter 3 on-hand adjustment."""
    return InventoryEvent(InventoryEventType.ADJUSTMENT, quantity)


@dataclass(frozen=True, init=False)
class InventoryLedger:
    """An ordered, immutable history whose current state is derived by replay."""

    events: tuple[InventoryEvent, ...]

    def __init__(self, events: Iterable[InventoryEvent] = ()) -> None:
        event_tuple = tuple(events)
        if any(not isinstance(event, InventoryEvent) for event in event_tuple):
            raise ValueError("events must contain only InventoryEvent values")
        object.__setattr__(self, "events", event_tuple)
        self.current_state()  # Reject an impossible history at its boundary.

    def current_state(self) -> InventoryState:
        """Replay every event in order and return the derived inventory state."""
        on_hand = 0
        reserved = 0
        for position, event in enumerate(self.events, start=1):
            quantity = event.quantity
            if event.event_type in {
                InventoryEventType.RECEIVE,
                InventoryEventType.ADJUSTMENT,
            }:
                on_hand += quantity
            elif event.event_type is InventoryEventType.RESERVE:
                if quantity > on_hand - reserved:
                    raise ValueError(
                        f"event {position}: cannot reserve more than "
                        "available inventory"
                    )
                reserved += quantity
            elif event.event_type is InventoryEventType.RELEASE_RESERVATION:
                if quantity > reserved:
                    raise ValueError(
                        f"event {position}: cannot release more than reserved inventory"
                    )
                reserved -= quantity
            elif event.event_type is InventoryEventType.SHIP:
                if quantity > reserved:
                    raise ValueError(
                        f"event {position}: cannot ship more than reserved inventory"
                    )
                reserved -= quantity
                on_hand -= quantity
        return InventoryState(on_hand, reserved)
