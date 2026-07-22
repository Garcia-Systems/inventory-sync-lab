"""Command-line foundation for the laboratory."""

import argparse
import platform
import sys
from collections.abc import Sequence

from inventory_sim import __version__
from inventory_sim.authority import (
    AuthoritativeInventoryRecord,
    InventoryCopy,
    compare_inventory,
)
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
    """Summarize the concepts currently implemented by the laboratory."""
    print("Welcome to the Inventory Synchronization Laboratory!")
    print("The development environment and command-line interface are functioning.")
    print("The laboratory includes a basic Chapter 1 inventory-state model.")
    print("Chapter 2 adds an authoritative-record comparison example.")
    print("Synchronization and the simulation engine are not implemented.")
    print("Chapter 3 will introduce the inventory ledger.")
    print("Run `inventory-sim inventory` or `inventory-sim authority` to explore.")
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


def authority(
    authority_on_hand: int,
    authority_reserved: int,
    website_on_hand: int,
    website_reserved: int,
    marketplace_on_hand: int,
    marketplace_reserved: int,
) -> int:
    """Compare the two Chapter 2 copies with the authoritative record."""
    try:
        authoritative = AuthoritativeInventoryRecord(
            "inventory-authority",
            InventoryState(authority_on_hand, authority_reserved),
        )
        copies = (
            InventoryCopy("website", InventoryState(website_on_hand, website_reserved)),
            InventoryCopy(
                "marketplace",
                InventoryState(marketplace_on_hand, marketplace_reserved),
            ),
        )
    except ValueError as error:
        print(f"Error: invalid inventory state: {error}", file=sys.stderr)
        return 2

    print("Authority:")
    print(f"  System:    {authoritative.system}")
    print(f"  On hand:   {authoritative.state.on_hand}")
    print(f"  Reserved:  {authoritative.state.reserved}")
    print(f"  Available: {authoritative.state.available}")
    print("\nCopies:")
    for copied_record in copies:
        comparison = compare_inventory(authoritative, copied_record)
        print(f"\n{copied_record.system}")
        print(f"  Available:  {copied_record.state.available}")
        print(f"  Difference: {comparison.available_difference:+d}")
        print(f"  Status:     {'MATCH' if comparison.matches else 'DIFFERS'}")
    print("\nComparison only: no synchronization or repair occurred.")
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
    authority_parser = subparsers.add_parser(
        "authority", help="compare Chapter 2 inventory copies with the authority"
    )
    for system, on_hand, reserved in (
        ("authority", 10, 3),
        ("website", 10, 3),
        ("marketplace", 10, 0),
    ):
        authority_parser.add_argument(f"--{system}-on-hand", type=int, default=on_hand)
        authority_parser.add_argument(
            f"--{system}-reserved", type=int, default=reserved
        )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the requested laboratory command."""
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        return doctor()
    if args.command == "demo":
        return demo()
    if args.command == "inventory":
        return inventory(args.on_hand, args.reserved)
    return authority(
        args.authority_on_hand,
        args.authority_reserved,
        args.website_on_hand,
        args.website_reserved,
        args.marketplace_on_hand,
        args.marketplace_reserved,
    )
