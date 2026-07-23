"""Compose and execute the Inventory Synchronization Laboratory CLI."""

import argparse
from collections.abc import Sequence

from inventory_sim.cli import correctness, foundations, integration, reliability
from inventory_sim.cli.common import CommandSpec, register_commands

COMMANDS = (
    CommandSpec("doctor", "verify the laboratory environment", foundations.doctor),
    CommandSpec("demo", "run the Chapter 0 smoke test", foundations.demo),
    CommandSpec("ledger", "replay the Chapter 3 inventory ledger", foundations.ledger),
    CommandSpec(
        "projections",
        "manually refresh Chapter 4 inventory projections",
        foundations.projections,
    ),
    CommandSpec(
        "timeline", "run the Chapter 5 deterministic timeline", foundations.timeline
    ),
    CommandSpec(
        "sync-direct",
        "run the Chapter 6 direct synchronization scenario",
        foundations.sync_direct,
    ),
    CommandSpec(
        "sync-queue",
        "run the Chapter 7 queued synchronization scenario",
        foundations.sync_queue,
    ),
    CommandSpec(
        "worker-capacity",
        "run the Chapter 8 worker-capacity scenario",
        foundations.worker_capacity,
    ),
    CommandSpec(
        "multiple-workers",
        "run the Chapter 9 two-worker scenario",
        foundations.multiple_workers,
    ),
    CommandSpec(
        "stale-snapshots",
        "run the Chapter 10 stale-snapshot scenario",
        correctness.stale_snapshots,
    ),
    CommandSpec(
        "freshness",
        "run the Chapter 11 freshness-measurement scenario",
        correctness.freshness,
    ),
    CommandSpec(
        "revisions",
        "run the Chapter 12 inventory-revision scenario",
        correctness.revisions,
    ),
    CommandSpec(
        "detect-stale",
        "run the Chapter 13 stale-detection scenario",
        correctness.detect_stale,
    ),
    CommandSpec(
        "reject-stale",
        "run the Chapter 14 stale-rejection scenario",
        correctness.reject_stale,
    ),
    CommandSpec(
        "multiple-projections",
        "run the Chapter 15 multiple-projection scenario",
        correctness.multiple_projections,
    ),
    CommandSpec("fanout", "run the Chapter 16 fan-out scenario", reliability.fanout),
    CommandSpec(
        "retries", "run the Chapter 17 retry-policy scenario", reliability.retries
    ),
    CommandSpec(
        "duplicate-delivery",
        "run the Chapter 18 duplicate-delivery scenario",
        reliability.duplicate_delivery,
    ),
    CommandSpec(
        "idempotency",
        "run the Chapter 19 idempotent synchronization scenario",
        reliability.idempotency,
    ),
    CommandSpec(
        "out-of-order",
        "run the Chapter 20 out-of-order delivery scenario",
        reliability.out_of_order,
    ),
    CommandSpec(
        "ordering",
        "run the Chapter 21 monotonic-ordering scenario",
        reliability.ordering,
    ),
    CommandSpec(
        "dead-letter",
        "run the Chapter 22 dead-letter queue scenario",
        reliability.dead_letter,
    ),
    CommandSpec(
        "laboratory",
        "run the Chapter 23 end-to-end operations laboratory",
        integration.laboratory,
    ),
)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="inventory-sim",
        description="Commands for the Inventory Synchronization Laboratory.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    register_commands(subparsers, COMMANDS)
    inventory_parser = subparsers.add_parser(
        "inventory", help="display a Chapter 1 inventory state"
    )
    inventory_parser.add_argument("--on-hand", type=int, default=10)
    inventory_parser.add_argument("--reserved", type=int, default=3)
    inventory_parser.set_defaults(
        handler=lambda args: foundations.inventory(args.on_hand, args.reserved)
    )
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
    authority_parser.set_defaults(handler=_run_authority)
    return parser


def _run_authority(args: argparse.Namespace) -> int:
    return foundations.authority(
        args.authority_on_hand,
        args.authority_reserved,
        args.website_on_hand,
        args.website_reserved,
        args.marketplace_on_hand,
        args.marketplace_reserved,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the requested laboratory command."""
    args = build_parser().parse_args(argv)
    if args.command == "inventory" or args.command == "authority":
        return args.handler(args)
    return args.handler()
