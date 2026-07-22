"""Authoritative inventory records and copied views introduced in Chapter 2."""

from dataclasses import dataclass

from inventory_sim.inventory import InventoryState


def _validate_record(record: object, expected_type: type, role: str) -> None:
    if not isinstance(record, expected_type):
        raise TypeError(f"{role} must be an {expected_type.__name__}")


@dataclass(frozen=True)
class AuthoritativeInventoryRecord:
    """The current inventory state the business designates as official."""

    system: str
    state: InventoryState

    def __post_init__(self) -> None:
        _validate_fields(self.system, self.state)
        object.__setattr__(self, "system", self.system.strip())


@dataclass(frozen=True)
class InventoryCopy:
    """A non-authoritative system's copy of current inventory state."""

    system: str
    state: InventoryState

    def __post_init__(self) -> None:
        _validate_fields(self.system, self.state)
        object.__setattr__(self, "system", self.system.strip())


def _validate_fields(system: object, state: object) -> None:
    if not isinstance(system, str):
        raise TypeError("system must be a string")
    if not system.strip():
        raise ValueError("system must not be empty or whitespace")
    if not isinstance(state, InventoryState):
        raise TypeError("state must be an InventoryState")


@dataclass(frozen=True)
class InventoryComparison:
    """A read-only comparison of one copy with the authority."""

    authority: AuthoritativeInventoryRecord
    copy: InventoryCopy
    matches: bool
    on_hand_difference: int
    reserved_difference: int
    available_difference: int


def compare_inventory(
    authority: AuthoritativeInventoryRecord, copy: InventoryCopy
) -> InventoryComparison:
    """Compare a copy with the authority without changing either record."""
    _validate_record(authority, AuthoritativeInventoryRecord, "authority")
    _validate_record(copy, InventoryCopy, "copy")
    if authority.system == copy.system:
        raise ValueError("authority and copy must use different system names")

    on_hand_difference = copy.state.on_hand - authority.state.on_hand
    reserved_difference = copy.state.reserved - authority.state.reserved
    available_difference = copy.state.available - authority.state.available
    return InventoryComparison(
        authority=authority,
        copy=copy,
        matches=authority.state == copy.state,
        on_hand_difference=on_hand_difference,
        reserved_difference=reserved_difference,
        available_difference=available_difference,
    )
