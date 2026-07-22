"""Copied inventory views introduced in Chapter 4."""

from dataclasses import dataclass

from inventory_sim.authority import (
    AuthoritativeInventoryRecord,
    InventoryComparison,
    InventoryCopy,
    compare_inventory,
)
from inventory_sim.inventory import InventoryState


@dataclass(frozen=True)
class InventoryProjection:
    """An immutable inventory state copied for another system's use."""

    system: str
    state: InventoryState

    def __post_init__(self) -> None:
        # InventoryCopy owns Chapter 2's system-name and state validation rules.
        validated = InventoryCopy(self.system, self.state)
        object.__setattr__(self, "system", validated.system)

    def compare_to(self, authoritative_state: InventoryState) -> InventoryComparison:
        """Compare this copied view with an authoritative state."""
        authority = AuthoritativeInventoryRecord(
            f"{self.system} (authority)", authoritative_state
        )
        return compare_inventory(authority, InventoryCopy(self.system, self.state))

    def refresh_from(
        self, authoritative_state: InventoryState
    ) -> "InventoryProjection":
        """Return a new projection containing the supplied authoritative state."""
        return InventoryProjection(self.system, authoritative_state)
