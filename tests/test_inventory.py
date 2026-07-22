from dataclasses import FrozenInstanceError

import pytest

from inventory_sim import InventoryState


def test_valid_state_exposes_quantities_and_derives_available() -> None:
    state = InventoryState(on_hand=10, reserved=3)

    assert state.on_hand == 10
    assert state.reserved == 3
    assert state.available == 7


@pytest.mark.parametrize(
    ("on_hand", "reserved", "available"),
    [(0, 0, 0), (5, 5, 0)],
)
def test_boundary_states_are_valid(on_hand: int, reserved: int, available: int) -> None:
    assert InventoryState(on_hand, reserved).available == available


@pytest.mark.parametrize(
    ("on_hand", "reserved", "message"),
    [
        (-1, 0, "on_hand cannot be negative"),
        (5, -1, "reserved cannot be negative"),
        (5, 6, "reserved cannot exceed on_hand"),
    ],
)
def test_invalid_quantities_are_rejected(
    on_hand: int, reserved: int, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        InventoryState(on_hand, reserved)


@pytest.mark.parametrize("value", [True, False, 1.0, "1", None])
@pytest.mark.parametrize("field_name", ["on_hand", "reserved"])
def test_quantities_must_be_actual_integers(value: object, field_name: str) -> None:
    quantities = {"on_hand": 1, "reserved": 0, field_name: value}

    with pytest.raises(ValueError, match=field_name):
        InventoryState(**quantities)  # type: ignore[arg-type]


def test_state_is_immutable() -> None:
    state = InventoryState(on_hand=10, reserved=3)

    with pytest.raises(FrozenInstanceError):
        state.reserved = 20  # type: ignore[misc]
