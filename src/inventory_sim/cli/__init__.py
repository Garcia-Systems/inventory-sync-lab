"""Command-line interface for the Inventory Synchronization Laboratory."""

from inventory_sim.cli.correctness import *  # noqa: F403
from inventory_sim.cli.foundations import *  # noqa: F403
from inventory_sim.cli.integration import *  # noqa: F403
from inventory_sim.cli.main import build_parser, main
from inventory_sim.cli.reliability import *  # noqa: F403

__all__ = ["build_parser", "main"]
