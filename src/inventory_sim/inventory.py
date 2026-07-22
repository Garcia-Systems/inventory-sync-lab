"""The small inventory-state model introduced in Chapter 1."""

from dataclasses import dataclass


@dataclass(frozen=True)
class InventoryState:
    """A current inventory state with physical and reserved quantities."""

    on_hand: int
    reserved: int

    def __post_init__(self) -> None:
        """Reject quantities that cannot describe a valid inventory state."""
        for field_name, quantity in (
            ("on_hand", self.on_hand),
            ("reserved", self.reserved),
        ):
            if type(quantity) is not int:
                raise ValueError(
                    f"{field_name} must be an integer (Boolean values are not allowed)"
                )

        if self.on_hand < 0:
            raise ValueError("on_hand cannot be negative")
        if self.reserved < 0:
            raise ValueError("reserved cannot be negative")
        if self.reserved > self.on_hand:
            raise ValueError("reserved cannot exceed on_hand")

    @property
    def available(self) -> int:
        """Return units that can still be offered for sale."""
        return self.on_hand - self.reserved
