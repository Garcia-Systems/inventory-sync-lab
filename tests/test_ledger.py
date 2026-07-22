from dataclasses import FrozenInstanceError

import pytest

from inventory_sim import (
    Adjustment,
    InventoryEvent,
    InventoryLedger,
    Receive,
    ReleaseReservation,
    Reserve,
    Ship,
)


def test_receive_and_positive_adjustment_increase_on_hand() -> None:
    state = InventoryLedger([Receive(5), Adjustment(2)]).current_state()
    assert (state.on_hand, state.reserved, state.available) == (7, 0, 7)


def test_reserve_reduces_available_without_changing_on_hand() -> None:
    state = InventoryLedger([Receive(10), Reserve(3)]).current_state()
    assert (state.on_hand, state.reserved, state.available) == (10, 3, 7)


def test_release_makes_reserved_inventory_available_again() -> None:
    state = InventoryLedger(
        [Receive(10), Reserve(3), ReleaseReservation(2)]
    ).current_state()
    assert (state.on_hand, state.reserved, state.available) == (10, 1, 9)


def test_ship_removes_inventory_and_its_reservation() -> None:
    state = InventoryLedger([Receive(10), Reserve(3), Ship(2)]).current_state()
    assert (state.on_hand, state.reserved, state.available) == (8, 1, 7)


def test_replay_respects_event_order() -> None:
    with pytest.raises(ValueError, match="event 1: cannot reserve"):
        InventoryLedger([Reserve(1), Receive(1)])


@pytest.mark.parametrize(
    ("events", "message"),
    [
        ([Reserve(1)], "cannot reserve"),
        ([Receive(2), Ship(1)], "cannot ship"),
        ([Receive(2), ReleaseReservation(1)], "cannot release"),
        ([Receive(2), Reserve(1), Reserve(2)], "cannot reserve"),
    ],
)
def test_impossible_histories_are_rejected(events, message: str) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError, match=message):
        InventoryLedger(events)


@pytest.mark.parametrize("quantity", [0, -1, True, 1.5, "1"])
def test_event_quantity_must_be_a_positive_integer(quantity: object) -> None:
    with pytest.raises(ValueError, match="quantity must be a positive integer"):
        Receive(quantity)  # type: ignore[arg-type]


def test_event_type_must_be_valid() -> None:
    with pytest.raises(ValueError, match="valid InventoryEventType"):
        InventoryEvent("Receive", 1)  # type: ignore[arg-type]


def test_ledger_accepts_an_empty_history() -> None:
    assert InventoryLedger().current_state().available == 0


def test_ledger_rejects_values_that_are_not_events() -> None:
    with pytest.raises(ValueError, match="only InventoryEvent"):
        InventoryLedger(["Receive 1"])  # type: ignore[list-item]


def test_event_and_ledger_are_immutable_and_input_is_copied() -> None:
    source = [Receive(1)]
    ledger = InventoryLedger(source)
    source.append(Receive(2))
    assert len(ledger.events) == 1
    with pytest.raises(FrozenInstanceError):
        ledger.events = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        ledger.events[0].quantity = 2  # type: ignore[misc]
