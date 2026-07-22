"""Command-line foundation for the laboratory."""

import argparse
import platform
import sys
from collections.abc import Sequence

from inventory_sim import __version__
from inventory_sim.inventory import InventoryState


def doctor() -> int:
    """Report whether the local laboratory foundation is operational."""
    print("Inventory Synchronization Laboratory")
    print()
    print(f"[OK] Python {platform.python_version()}")
    print(f"[OK] inventory_sim package is available (version {__version__})")
    print("[OK] inventory-sim CLI is operational")
    print()
    print("Laboratory environment is ready.")
    return 0


def demo() -> int:
    """Run the Chapter 0 demonstration without simulating inventory."""
    print("Welcome to the Inventory Synchronization Laboratory!")
    print("The development environment and command-line interface are functioning.")
    print("The laboratory now includes a basic Chapter 1 inventory-state example.")
    print("Synchronization and the full simulator have not been implemented yet.")
    print("Run `inventory-sim inventory` to explore the Chapter 1 model.")
    return 0


def inventory(on_hand: int, reserved: int) -> int:
    """Display a validated Chapter 1 inventory state."""
    try:
        state = InventoryState(on_hand=on_hand, reserved=reserved)
    except ValueError as error:
        print(f"Error: invalid inventory state: {error}", file=sys.stderr)
        return 2

    print("Inventory State")
    print()
    print(f"On hand:   {state.on_hand}")
    print(f"Reserved:  {state.reserved}")
    print(f"Available: {state.available}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="inventory-sim",
        description="Commands for the Inventory Synchronization Laboratory.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="verify the laboratory environment")
    subparsers.add_parser("demo", help="run the Chapter 0 smoke test")
    inventory_parser = subparsers.add_parser(
        "inventory", help="display a Chapter 1 inventory state"
    )
    inventory_parser.add_argument("--on-hand", type=int, default=10)
    inventory_parser.add_argument("--reserved", type=int, default=3)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the requested laboratory command."""
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        return doctor()
    if args.command == "demo":
        return demo()
    return inventory(args.on_hand, args.reserved)
