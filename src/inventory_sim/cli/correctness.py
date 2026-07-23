"""CLI demonstrations for correctness."""

from inventory_sim.freshness import run_freshness_scenario
from inventory_sim.multiple_projections import run_multiple_projections_scenario
from inventory_sim.revisions import run_inventory_revisions_scenario
from inventory_sim.stale_detection import run_stale_detection_scenario
from inventory_sim.stale_rejection import run_stale_rejection_scenario
from inventory_sim.stale_snapshots import run_stale_snapshots_scenario


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


def reject_stale() -> int:
    """Run the canonical Chapter 14 stale-rejection scenario."""
    result = run_stale_rejection_scenario()
    print("Rejecting Stale Synchronizations\n")
    print("Time 1 — Request A captures Revision 2.")
    print("Time 2 — Authority advances to Revision 4.")
    print("Time 3 — Request B captures Revision 4.")
    print("Time 4 — Workers begin processing.\n")
    for inspection in result.inspections:
        print(f"Worker: {inspection.worker_name}\n")
        print(f"Request revision: {inspection.request_revision.value}")
        print(f"Authority revision: {inspection.authority_revision.value}\n")
        print(
            f"Result: {'ACCEPTED' if inspection.projection_updated else 'REJECTED'}\n"
        )
        if inspection.projection_updated:
            print("Projection updated.\n")
        else:
            print(f"Reason: {inspection.rejection_reason}.")
            print("Projection unchanged.\n")
    print(f"Time {result.final_time} — Both workers complete normally.\n")
    print("Summary")
    print(f"Accepted requests: {result.accepted_requests}")
    print(f"Rejected requests: {result.rejected_requests}")
    print(f"Final authoritative revision: {result.authority_revision.value}")
    print(f"Final projection revision: {result.projection_revision.value}")
    return 0


def multiple_projections() -> int:
    """Run the canonical Chapter 15 multiple-projection scenario."""
    result = run_multiple_projections_scenario()
    authority = result.authority
    print("Multiple Projections\n")
    print("One authoritative inventory feeds three independent views.")
    print("Storefront first receives stale Revision 3 and rejects it; Warehouse")
    print("and Reporting accept Revision 6 and remain unaffected. Storefront then")
    print("accepts a current request.\n")
    print("Authority")
    print(f"Revision: {authority.revision.value}")
    print(f"Available: {authority.state.available}")
    for item in result.final_projections:
        print(f"\n{item.projection.system}")
        print(f"Revision: {item.revision.value}")
        print(f"Available: {item.projection.state.available}")
    print("\nAll projections independently reached the same final revision.")
    print("No retries, networking, event bus, or messaging infrastructure was used.")
    return 0
