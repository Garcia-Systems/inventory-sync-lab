from dataclasses import FrozenInstanceError

import pytest

from inventory_sim import InventoryState
from inventory_sim.authority import (
    AuthoritativeInventoryRecord,
    InventoryComparison,
    InventoryCopy,
    compare_inventory,
)


def authority(state: InventoryState | None = None) -> AuthoritativeInventoryRecord:
    return AuthoritativeInventoryRecord(
        " inventory-authority ", state or InventoryState(10, 3)
    )


def copy(state: InventoryState | None = None) -> InventoryCopy:
    return InventoryCopy(" website ", state or InventoryState(10, 3))


def test_records_represent_authority_and_copy_with_normalized_names() -> None:
    authoritative = authority()
    copied_record = copy()

    assert authoritative.system == "inventory-authority"
    assert authoritative.state.available == 7
    assert copied_record.system == "website"
    assert copied_record.state.available == 7


def test_equal_states_match_with_zero_differences() -> None:
    comparison = compare_inventory(authority(), copy())

    assert isinstance(comparison, InventoryComparison)
    assert comparison.matches
    assert comparison.on_hand_difference == 0
    assert comparison.reserved_difference == 0
    assert comparison.available_difference == 0


def test_different_states_have_quantity_differences() -> None:
    comparison = compare_inventory(authority(), copy(InventoryState(12, 1)))

    assert not comparison.matches
    assert comparison.on_hand_difference == 2
    assert comparison.reserved_difference == -2
    assert comparison.available_difference == 4


@pytest.mark.parametrize(
    ("copied_state", "difference"),
    [(InventoryState(10, 0), 3), (InventoryState(8, 2), -1)],
)
def test_available_difference_can_be_positive_or_negative(
    copied_state: InventoryState, difference: int
) -> None:
    assert (
        compare_inventory(authority(), copy(copied_state)).available_difference
        == difference
    )


@pytest.mark.parametrize("record_type", [AuthoritativeInventoryRecord, InventoryCopy])
@pytest.mark.parametrize("system", ["", "   "])
def test_records_reject_blank_system_names(record_type: type, system: str) -> None:
    with pytest.raises(ValueError, match="system must not be empty or whitespace"):
        record_type(system, InventoryState(1, 0))


@pytest.mark.parametrize("record_type", [AuthoritativeInventoryRecord, InventoryCopy])
def test_records_reject_invalid_field_types(record_type: type) -> None:
    with pytest.raises(TypeError, match="system must be a string"):
        record_type(42, InventoryState(1, 0))
    with pytest.raises(TypeError, match="state must be an InventoryState"):
        record_type("system", object())


def test_comparison_rejects_invalid_record_types() -> None:
    with pytest.raises(
        TypeError, match="authority must be an AuthoritativeInventoryRecord"
    ):
        compare_inventory(copy(), copy())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="copy must be an InventoryCopy"):
        compare_inventory(authority(), authority())  # type: ignore[arg-type]


def test_comparison_rejects_the_same_normalized_system_name() -> None:
    with pytest.raises(ValueError, match="different system names"):
        compare_inventory(
            authority(), InventoryCopy(" inventory-authority ", InventoryState(1, 0))
        )


def test_records_and_comparison_are_immutable() -> None:
    authoritative = authority()
    copied_record = copy()
    comparison = compare_inventory(authoritative, copied_record)

    with pytest.raises(FrozenInstanceError):
        authoritative.system = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        copied_record.system = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        comparison.matches = False  # type: ignore[misc]


def test_comparison_does_not_mutate_its_inputs() -> None:
    authoritative = authority()
    copied_record = copy(InventoryState(10, 0))

    compare_inventory(authoritative, copied_record)

    assert authoritative == authority()
    assert copied_record == copy(InventoryState(10, 0))


def test_records_reuse_inventory_state_invariants() -> None:
    with pytest.raises(ValueError, match="reserved cannot exceed on_hand"):
        InventoryCopy("website", InventoryState(1, 2))
