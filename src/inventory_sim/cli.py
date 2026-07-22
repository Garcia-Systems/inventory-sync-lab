"""Command-line foundation for the laboratory."""

import argparse
import platform
from collections.abc import Sequence

from inventory_sim import __version__


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
    print("The inventory simulator has not been implemented yet.")
    print("Continue to Chapter 1 when it becomes available.")
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the requested laboratory command."""
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        return doctor()
    return demo()
