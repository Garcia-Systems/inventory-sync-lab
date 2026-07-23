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
from inventory_sim.capacity import run_worker_capacity_scenario
from inventory_sim.freshness import run_freshness_scenario
from inventory_sim.inventory import InventoryState
from inventory_sim.ledger import InventoryLedger, Receive, Reserve, Ship
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import run_queue_synchronization_scenario
from inventory_sim.revisions import run_inventory_revisions_scenario
from inventory_sim.simulation import EventScheduler, VirtualClock
from inventory_sim.stale_detection import run_stale_detection_scenario
from inventory_sim.stale_snapshots import run_stale_snapshots_scenario
from inventory_sim.synchronization import run_direct_synchronization_scenario
from inventory_sim.worker_pool import run_multiple_workers_scenario


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
    print("Chapter 3 adds an inventory ledger that derives state from events.")
    print("Chapter 4 adds inventory projections and explicit manual refresh.")
    print("Chapter 5 adds a deterministic virtual timeline of generic actions.")
    print("Chapter 6 adds direct synchronization at a deterministic simulated time.")
    print("Chapter 7 adds queued synchronization and FIFO request processing.")
    print("Chapter 8 adds fixed processing time, worker capacity, and request waits.")
    print("One worker is BUSY while servicing one request and IDLE otherwise.")
    print("Queue depth grows when arrivals outpace completion capacity.")
    print("Chapter 9 adds a fixed two-worker pool and deterministic assignment.")
    print("Multiple requests can now be in progress in simulated time.")
    print("No operating-system concurrency, worker failures, or retries are used.")
    print("Service time remains fixed. Random latency is not implemented.")
    print("Chapter 10 introduces changing authority while work is waiting.")
    print("Chapter 11 measures queue wait, service time, and snapshot age.")
    print(
        "Chapter 12 adds revisions that order inventory states independently "
        "of quantity."
    )
    print("Chapter 13 detects stale request revisions without rejecting work.")
    print(
        "Run `inventory-sim inventory`, `inventory-sim authority`, or "
        "`inventory-sim ledger`, `inventory-sim projections`, or "
        "`inventory-sim timeline`, `inventory-sim sync-direct`, or "
        "`inventory-sim sync-queue`, `inventory-sim worker-capacity`, or "
        "`inventory-sim multiple-workers`, `inventory-sim stale-snapshots`, or "
        "`inventory-sim freshness`, `inventory-sim revisions`, or "
        "`inventory-sim detect-stale` "
        "to explore."
    )
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


def ledger() -> int:
    """Display the canonical Chapter 3 ledger and its derived state."""
    inventory_ledger = InventoryLedger([Receive(10), Reserve(3), Ship(2)])
    print("Inventory Ledger\n")
    for position, event in enumerate(inventory_ledger.events, start=1):
        print(f"{position}. {event.event_type.value} {event.quantity}")
    state = inventory_ledger.current_state()
    print("\nCurrent Inventory\n")
    print(f"On hand: {state.on_hand}")
    print(f"Reserved: {state.reserved}")
    print(f"Available: {state.available}")
    return 0


def projections() -> int:
    """Demonstrate Chapter 4 projections and an explicit manual refresh."""
    inventory_ledger = InventoryLedger([Receive(10), Reserve(3)])
    authoritative_state = inventory_ledger.current_state()
    system_projections = (
        InventoryProjection("warehouse", authoritative_state),
        InventoryProjection("website", authoritative_state),
        InventoryProjection("marketplace", InventoryState(10, 0)),
    )

    print("Inventory Projections\n")
    print("Authoritative ledger")
    for position, recorded in enumerate(inventory_ledger.events, start=1):
        print(f"{position}. {recorded.event_type.value} {recorded.quantity}")
    print("\nAuthoritative state")
    print(f"On hand:   {authoritative_state.on_hand}")
    print(f"Reserved:  {authoritative_state.reserved}")
    print(f"Available: {authoritative_state.available}")
    print("\nProjections before manual refresh")
    for projection in system_projections:
        _print_projection(projection, authoritative_state)

    marketplace = system_projections[-1]
    refreshed = marketplace.refresh_from(authoritative_state)
    print("\nManual refresh")
    print("marketplace copied the authoritative state by explicit manual operation.")
    print("No automatic synchronization occurred.")
    print("\nProjection after manual refresh")
    _print_projection(refreshed, authoritative_state)
    return 0


def timeline() -> int:
    """Demonstrate Chapter 5's deterministic simulated timeline."""
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    events = (
        (2, "Inspect inventory"),
        (5, "Refresh website projection"),
        (5, "Refresh marketplace projection"),
        (8, "Inspect inventory again"),
    )

    print("Deterministic Timeline\n")
    print(f"Starting simulated time: {clock.now}\n")
    print("Scheduled events")
    for position, (at, label) in enumerate(events, start=1):
        print(f"{position}. Time {at} — {label}")
        scheduler.schedule(at=at, label=label, action=lambda: None)

    print("\nExecution")
    for execution in scheduler.run():
        print(f"\nTime {execution.time}\n  {execution.label}")
    print(f"\nFinal simulated time: {clock.now}\n")
    print("No real waiting occurred.")
    print("Events at the same time ran in scheduling order.")
    print("These descriptive actions did not synchronize inventory.")
    return 0


def sync_direct() -> int:
    """Run the canonical Chapter 6 direct synchronization scenario."""
    result = run_direct_synchronization_scenario()
    authority = result.authoritative_state
    initial = result.initial_projection
    print("Direct Inventory Synchronization\n")
    print("Authoritative state")
    print(f"On hand:   {authority.on_hand}")
    print(f"Reserved:  {authority.reserved}")
    print(f"Available: {authority.available}\n")
    print("Initial website projection")
    print(f"On hand:    {initial.state.on_hand}")
    print(f"Reserved:   {initial.state.reserved}")
    print(f"Available:  {initial.state.available}")
    print(f"Difference: {result.initial_available_difference:+d}")
    print("Status:     STALE\n")
    print("Timeline")
    before, after = result.inspections
    print(f"\nTime {before.time} — Inspect website")
    print(f"  Available: {before.state.available}")
    print(f"  Difference: {before.available_difference:+d}")
    print(f"  Status: {'MATCH' if before.matches else 'STALE'}")
    synchronization = result.synchronization
    print(f"\nTime {synchronization.time} — Direct synchronization")
    print("  Website copied the authoritative state.")
    print(f"  Before available: {synchronization.before.state.available}")
    print(f"  After available:  {synchronization.after.state.available}")
    print(f"\nTime {after.time} — Inspect website")
    print(f"  Available: {after.state.available}")
    print(f"  Difference: {after.available_difference:+d}")
    print(f"  Status: {'MATCH' if after.matches else 'STALE'}")
    print(f"\nFinal simulated time: {result.final_time}\n")
    print("The projection was updated directly.")
    print("No queue, worker, retry, network delay, or real waiting was used.")
    print("The model includes no transport delay.")
    return 0


def sync_queue() -> int:
    """Run the canonical Chapter 7 queued synchronization scenario."""
    result = run_queue_synchronization_scenario()
    authority = result.authoritative_state
    print("Queued Inventory Synchronization\n")
    print("Authoritative state")
    print(f"On hand:   {authority.on_hand}")
    print(f"Reserved:  {authority.reserved}")
    print(f"Available: {authority.available}\n")
    print("Initial projections")
    for projection, difference in zip(
        result.initial_projections,
        result.initial_available_differences,
        strict=True,
    ):
        print(f"\n{projection.system}")
        print(f"  Available:  {projection.state.available}")
        print(f"  Difference: {difference:+d}")
        print("  Status:     STALE")

    print("\nTimeline")
    for execution in result.enqueues:
        print(f"\nTime {execution.time} — Enqueue {execution.system} synchronization")
        print(f"  Queue depth: {execution.queue_depth}")

    by_time = {inspection.time: inspection for inspection in result.inspections}

    def print_inspection(time: int, label: str) -> None:
        inspection = by_time[time]
        print(f"\nTime {time} — {label}")
        print(f"  Queue depth: {inspection.queue_depth}")
        for projection in inspection.projections:
            status = "MATCH" if projection.matches else "STALE"
            print(
                f"  {projection.system}: {status} "
                f"({projection.available_difference:+d})"
            )

    print_inspection(4, "Inspect system")
    for execution, inspection_time in zip(
        result.worker_executions, (6, 8), strict=True
    ):
        inspection = by_time[inspection_time]
        print(f"\nTime {execution.time} — Worker processes next request")
        print(f"  Processed: {execution.system}")
        print(f"  Queue depth: {execution.queue_depth_after}")
        for projection in inspection.projections:
            status = "MATCH" if projection.matches else "STALE"
            print(f"  {projection.system}: {status}")
    print_inspection(8, "Final inspection")
    print(f"\nFinal simulated time: {result.final_time}\n")
    print("Enqueuing did not update either projection.")
    print("A single worker processed one request at a time in FIFO order.")
    print(
        "No retries, failures, network delay, parallel workers, or real waiting "
        "were used."
    )
    return 0


def worker_capacity() -> int:
    """Run the canonical Chapter 8 worker-capacity scenario."""
    result = run_worker_capacity_scenario()
    authority = result.authoritative_state
    print("Workers and Capacity\n")
    print("Authoritative state")
    print(f"On hand:   {authority.on_hand}")
    print(f"Reserved:  {authority.reserved}")
    print(f"Available: {authority.available}\n")
    print("Worker")
    print(f"Service time: {result.service_time} ticks")
    print("Capacity: one request at a time\n")
    print("Request arrivals")
    for arrival in result.arrivals:
        print(f"Time {arrival.time} — {arrival.system}")
    print("\nProcessing timeline")
    arrivals = {arrival.time: arrival for arrival in result.arrivals}
    starts = {start.started_at: start for start in result.processing_starts}
    completions = {
        completion.completed_at: completion for completion in result.completions
    }
    for time in (1, 2, 3, 4, 7, 10):
        print(f"\nTime {time}")
        if time in arrivals:
            arrival = arrivals[time]
            print(f"  {arrival.system} arrived")
        if time in completions:
            completion = completions[time]
            print(f"  {completion.system} completed")
            print(f"  {completion.system} now MATCHES")
        if time in starts:
            start = starts[time]
            immediate = " immediately" if start.wait_time == 0 else ""
            print(f"  {start.system} started{immediate}")
            print(f"  completion scheduled for time {start.completes_at}")
            print(f"  queue depth: {start.queue_depth_after}")
        elif time in arrivals:
            arrival = arrivals[time]
            active = next(
                inspection.current_system
                for inspection in result.inspections
                if inspection.time == 3
            )
            print(f"  worker busy with {active}")
            print(f"  queue depth: {arrival.queue_depth}")
        if time == 10:
            print("  worker became IDLE")
            print("  queue depth: 0")
    print("\nRequest timing")
    for completion in result.completions:
        print(f"\n{completion.system}")
        print(f"  Arrival: {completion.arrived_at}")
        print(f"  Start: {completion.started_at}")
        print(f"  Completion: {completion.completed_at}")
        print(f"  Wait: {completion.wait_time}")
        print(f"  Service: {completion.service_time}")
        print(f"  Total: {completion.total_time}")
    print("\nInspections")
    for inspection in result.inspections:
        detail = inspection.worker_status
        if inspection.current_system is not None:
            detail += (
                f" with {inspection.current_system} until time "
                f"{inspection.current_completion_time}"
            )
        print(f"\nInspection at time {inspection.time}")
        print(f"  Worker: {detail}")
        print(f"  Queue depth: {inspection.queue_depth}")
        for projection in inspection.projections:
            print(
                f"  {projection.system}: {'MATCH' if projection.matches else 'STALE'}"
            )
    print(f"\nFinal worker state: {result.final_worker_status}")
    print(f"Final queue depth: {result.final_queue_depth}")
    print(f"Final simulated time: {result.final_time}\n")
    print("Requests arrived faster than one worker could complete them.")
    print("Waiting time increased even though service time remained fixed.")
    print(
        "No real waiting, parallel workers, failures, retries, or random timing "
        "were used."
    )
    return 0


def multiple_workers() -> int:
    """Run the canonical Chapter 9 two-worker scenario."""
    result = run_multiple_workers_scenario()
    authority = result.authoritative_state
    print("Multiple Workers\n")
    print("Authoritative state")
    print(f"On hand:   {authority.on_hand}")
    print(f"Reserved:  {authority.reserved}")
    print(f"Available: {authority.available}\n")
    print("Worker pool")
    print(f"Workers: {result.worker_count}")
    print(f"Service time: {result.service_time} ticks")
    print("Capacity: two requests at a time\n")
    print("Request arrivals")
    for arrival in result.arrivals:
        print(f"Time {arrival.time} — {arrival.system}")
    print("\nRequest timing")
    for completion in result.completions:
        print(f"\n{completion.system}")
        print(f"  Worker: {completion.worker_name}")
        print(f"  Arrival: {completion.arrived_at}")
        print(f"  Start: {completion.started_at}")
        print(f"  Completion: {completion.completed_at}")
        print(f"  Wait: {completion.wait_time}")
        print(f"  Service: {completion.service_time}")
        print(f"  Total: {completion.total_time}")
    print("\nInspections")
    for inspection in result.inspections:
        print(f"\nInspection at time {inspection.time}")
        for worker in inspection.workers:
            detail = worker.status
            if worker.current_system is not None:
                detail += (
                    f" with {worker.current_system} until time {worker.completion_time}"
                )
            print(f"  {worker.name}: {detail}")
        print(f"  Busy workers: {inspection.busy_worker_count}")
        print(f"  Queue depth: {inspection.queue_depth}")
        for projection in inspection.projections:
            print(
                f"  {projection.system}: {'MATCH' if projection.matches else 'STALE'}"
            )
    print(f"\nMaximum queue depth: {result.maximum_queue_depth}")
    print(f"Average wait time: {result.average_wait_time:.2f} ticks")
    print(f"Final queue depth: {result.final_queue_depth}")
    print(f"Final simulated time: {result.final_time}\n")
    print(
        "Two workers processed different requests during the same simulated intervals."
    )
    print(
        "FIFO requests and lowest-numbered idle workers made assignment deterministic."
    )
    print("Projections changed only when processing completed.")
    print(
        "No threads, real parallelism, failures, retries, or random timing were used."
    )
    return 0


def stale_snapshots() -> int:
    """Run the canonical Chapter 10 stale-snapshot scenario."""
    result = run_stale_snapshots_scenario()
    snapshot = result.request.authoritative_state
    authority = result.current_authority
    projection = result.inspection.resulting_projection.state
    website_start = result.processing_starts[1]
    website_completion = result.completions[1]

    print("Stale Snapshots\n")
    print("Time 0 — Authority derived from Receive 10 and Reserve 3")
    print(f"  Available: {result.original_authority.available}")
    print("  Worker begins an earlier synchronization.\n")
    print("Time 1 — Website request created and queued")
    print(f"  Request snapshot available: {snapshot.available}")
    print("  The request waits while the worker remains busy.\n")
    print("Time 2 — Authority changes: Receive 5")
    print(f"  Current authority available: {authority.available}")
    print(f"  Queued request snapshot remains: {snapshot.available}\n")
    print(f"Time {website_start.started_at} — Worker starts the queued request")
    print(f"  Completion scheduled for time {website_start.completes_at}.\n")
    print(f"Time {website_completion.completed_at} — Worker finishes")
    print("  Synchronization succeeded; projection updated from the request.")
    print(f"  Request snapshot available: {snapshot.available}")
    print(f"  Resulting projection available: {projection.available}")
    print(f"  Current authority available: {authority.available}\n")
    print("The projection matches the request snapshot: MATCH.")
    print("The projection differs from current authority: STALE.")
    print("Nothing failed. The copied snapshot became outdated while it waited.")
    print("No freshness validation, rejection, versioning, or retry was used.")
    return 0


def freshness() -> int:
    """Run the canonical Chapter 11 freshness-measurement scenario."""
    result = run_freshness_scenario()
    print("Measuring Freshness\n")
    print("Time 0 — Request A captures authority and starts immediately.")
    print("Time 1 — Requests B and C capture authority and enter the queue.")
    print("Time 3 — Request A completes.")
    print("Time 4 — Authority changes while later requests are in flight.")
    print("Time 6 — Request B completes.")
    print("Time 7 — Authority changes again while request C is in flight.")
    print("Time 9 — Request C completes.\n")
    print("Request    Wait    Service    Snapshot Age")
    print("-------------------------------------------")
    for observation in result.observations:
        print(
            f"{observation.request:<11}"
            f"{observation.wait_time:<8}"
            f"{observation.service_time:<11}"
            f"{observation.snapshot_age}"
        )
    print("\nAll values are simulated timing observations.")
    print("No request was rejected and no freshness policy was applied.")
    return 0


def revisions() -> int:
    """Run the canonical Chapter 12 inventory-revision scenario."""
    result = run_inventory_revisions_scenario()
    print("Inventory Revisions\n")
    print("Revision    Available")
    print("---------------------")
    for observation in result.observations:
        print(f"{observation.revision.value:<12}{observation.state.available}")
    print("\nRevision 3 is newer than Revision 1 even though both report")
    print("the same available quantity (10).")
    print(
        "Synchronization requests still copy their snapshots without revision policy."
    )
    print(
        "Revisions provide ordering information only; none is classified "
        "stale or fresh."
    )
    return 0


def detect_stale() -> int:
    """Run the canonical Chapter 13 stale-detection scenario."""
    result = run_stale_detection_scenario()
    print("Detecting Stale Synchronizations\n")
    print("Time 1 — Request A captures Revision 2.")
    print("Time 2 — Authority advances to Revision 4.")
    print("Time 3 — Request B captures Revision 4.")
    print("Time 4 — Workers begin processing.\n")
    for inspection in result.inspections:
        detection = inspection.detection
        print(f"Worker: {inspection.worker_name}")
        print(f"System: {inspection.system}\n")
        print(f"Request revision: {detection.request_revision.value}")
        print(f"Authority revision: {detection.authority_revision.value}\n")
        print(f"Stale request: {'YES' if detection.stale else 'NO'}\n")
        print("Continuing synchronization...\n")
    print(f"Time {result.final_time} — Both synchronizations complete.")
    print("Both requests were processed, including the stale request.")
    print("Detection was an observation only; no request was rejected.")
    return 0


def _print_projection(
    projection: InventoryProjection, authoritative_state: InventoryState
) -> None:
    comparison = projection.compare_to(authoritative_state)
    print(f"\n{projection.system}")
    print(f"  On hand:    {projection.state.on_hand}")
    print(f"  Reserved:   {projection.state.reserved}")
    print(f"  Available:  {projection.state.available}")
    print(f"  Difference: {comparison.available_difference:+d}")
    print(f"  Status:     {'MATCH' if comparison.matches else 'STALE'}")


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="inventory-sim",
        description="Commands for the Inventory Synchronization Laboratory.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="verify the laboratory environment")
    subparsers.add_parser("demo", help="run the Chapter 0 smoke test")
    subparsers.add_parser("ledger", help="replay the Chapter 3 inventory ledger")
    subparsers.add_parser(
        "projections", help="manually refresh Chapter 4 inventory projections"
    )
    subparsers.add_parser("timeline", help="run the Chapter 5 deterministic timeline")
    subparsers.add_parser(
        "sync-direct", help="run the Chapter 6 direct synchronization scenario"
    )
    subparsers.add_parser(
        "sync-queue", help="run the Chapter 7 queued synchronization scenario"
    )
    subparsers.add_parser(
        "worker-capacity", help="run the Chapter 8 worker-capacity scenario"
    )
    subparsers.add_parser(
        "multiple-workers", help="run the Chapter 9 two-worker scenario"
    )
    subparsers.add_parser(
        "stale-snapshots", help="run the Chapter 10 stale-snapshot scenario"
    )
    subparsers.add_parser(
        "freshness", help="run the Chapter 11 freshness-measurement scenario"
    )
    subparsers.add_parser(
        "revisions", help="run the Chapter 12 inventory-revision scenario"
    )
    subparsers.add_parser(
        "detect-stale", help="run the Chapter 13 stale-detection scenario"
    )
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
    if args.command == "ledger":
        return ledger()
    if args.command == "projections":
        return projections()
    if args.command == "timeline":
        return timeline()
    if args.command == "sync-direct":
        return sync_direct()
    if args.command == "sync-queue":
        return sync_queue()
    if args.command == "worker-capacity":
        return worker_capacity()
    if args.command == "multiple-workers":
        return multiple_workers()
    if args.command == "stale-snapshots":
        return stale_snapshots()
    if args.command == "freshness":
        return freshness()
    if args.command == "revisions":
        return revisions()
    if args.command == "detect-stale":
        return detect_stale()
    return authority(
        args.authority_on_hand,
        args.authority_reserved,
        args.website_on_hand,
        args.website_reserved,
        args.marketplace_on_hand,
        args.marketplace_reserved,
    )
