from dataclasses import FrozenInstanceError

import pytest

from inventory_sim import InventoryProjection, InventoryState
from inventory_sim.authority import (
    AuthoritativeInventoryRecord,
    InventoryCopy,
    compare_inventory,
)


def test_projection_exposes_normalized_identity_and_copied_state() -> None:
    state = InventoryState(10, 3)
    projection = InventoryProjection(" warehouse ", state)

    assert projection.system == "warehouse"
    assert projection.state is state


def test_matching_projection_is_identified() -> None:
    comparison = InventoryProjection("website", InventoryState(10, 3)).compare_to(
        InventoryState(10, 3)
    )
    assert comparison.matches
    assert comparison.on_hand_difference == 0
    assert comparison.reserved_difference == 0
    assert comparison.available_difference == 0


def test_stale_projection_has_positive_differences() -> None:
    comparison = InventoryProjection("marketplace", InventoryState(12, 2)).compare_to(
        InventoryState(10, 3)
    )
    assert not comparison.matches
    assert comparison.on_hand_difference == 2
    assert comparison.reserved_difference == -1
    assert comparison.available_difference == 3


def test_projection_can_have_negative_available_difference() -> None:
    comparison = InventoryProjection("website", InventoryState(8, 3)).compare_to(
        InventoryState(10, 3)
    )
    assert comparison.available_difference == -2


def test_manual_refresh_returns_new_match_without_mutating_inputs() -> None:
    authority = InventoryState(10, 3)
    stale = InventoryProjection("marketplace", InventoryState(10, 0))

    refreshed = stale.refresh_from(authority)

    assert refreshed is not stale
    assert refreshed.system == stale.system
    assert refreshed.state is authority
    assert refreshed.compare_to(authority).matches
    assert stale.state == InventoryState(10, 0)
    assert stale.state.available == 10
    assert authority == InventoryState(10, 3)


def test_projection_is_immutable() -> None:
    projection = InventoryProjection("website", InventoryState(10, 3))
    with pytest.raises(FrozenInstanceError):
        projection.system = "marketplace"  # type: ignore[misc]


@pytest.mark.parametrize("system", ["", "   "])
def test_projection_rejects_blank_system_names(system: str) -> None:
    with pytest.raises(ValueError, match="system must not be empty or whitespace"):
        InventoryProjection(system, InventoryState(1, 0))


def test_projection_rejects_non_string_system_name() -> None:
    with pytest.raises(TypeError, match="system must be a string"):
        InventoryProjection(42, InventoryState(1, 0))  # type: ignore[arg-type]


def test_projection_rejects_invalid_state_type() -> None:
    with pytest.raises(TypeError, match="state must be an InventoryState"):
        InventoryProjection("website", object())  # type: ignore[arg-type]


def test_refresh_rejects_invalid_authoritative_state_type() -> None:
    projection = InventoryProjection("website", InventoryState(1, 0))
    with pytest.raises(TypeError, match="state must be an InventoryState"):
        projection.refresh_from(object())  # type: ignore[arg-type]


def test_inventory_state_invariants_still_apply() -> None:
    with pytest.raises(ValueError, match="reserved cannot exceed on_hand"):
        InventoryProjection("website", InventoryState(1, 2))


def test_chapter_2_comparison_behavior_is_unchanged() -> None:
    comparison = compare_inventory(
        AuthoritativeInventoryRecord("authority", InventoryState(10, 3)),
        InventoryCopy("website", InventoryState(10, 0)),
    )
    assert not comparison.matches
    assert comparison.available_difference == 3
