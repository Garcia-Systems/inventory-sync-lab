"""CLI demonstrations for integration."""

from inventory_sim.laboratory import run_laboratory_scenario


def laboratory() -> int:
    """Present Chapter 23's complete scenario as an operational walkthrough."""
    result = run_laboratory_scenario()
    latest = result.authorities[-1]
    print("=== Ledger ===\n")
    print(f"Recorded {len(result.ledger.events)} immutable inventory events.")
    print("Receive and Reserve events replay in their recorded order.\n")
    print("=== Authority ===\n")
    print(f"Revision {latest.revision.value}: {latest.state}")
    print(f"Available inventory: {latest.state.available}\n")
    print("=== Fan-Out ===\n")
    print("Revisions 15 and 16 each produce one request per projection.")
    for request in result.requests:
        print(f"Request {request.request_id} -> {request.system}")
    print("\n=== Queue ===\n")
    print("Immutable requests enter a deterministic FIFO CapacityQueue.")
    print("The second wave also contains one duplicate and one delayed old request.\n")
    print("=== Worker Pool ===\n")
    print("Two fixed-time workers process requests without threads or real waiting.")
    for operation in result.operations:
        print(
            f"Time {operation.time} — {operation.worker} — "
            f"{operation.request.system} revision {operation.revision.value} "
            f"attempt {operation.attempt}: {operation.outcome}"
        )
    print("\n=== Retry ===\n")
    print(f"Retries requeue the same request: {result.summary.retries}\n")
    print("=== Duplicate Delivery ===\n")
    print(
        "Storefront revision 16 is delivered twice; its second delivery is skipped.\n"
    )
    print("=== Ordering ===\n")
    print("Warehouse revision 15 arrives after revision 16 and cannot move backward.\n")
    print("=== Dead Letter Queue ===\n")
    for entry in result.dead_letters:
        print(
            f"{entry.request.system} revision {entry.revision.value}: "
            f"{entry.reason} after {entry.attempts} attempts"
        )
    print("\n=== Final Summary ===\n")
    summary = result.summary
    labels = (
        ("Authority Revision", summary.authority_revision),
        ("Registered Projections", summary.registered_projections),
        ("Synchronization Requests", summary.synchronization_requests),
        ("Successful Synchronizations", summary.successful_synchronizations),
        ("Retries", summary.retries),
        ("Duplicate Deliveries", summary.duplicate_deliveries),
        ("Idempotent Skips", summary.idempotent_skips),
        ("Rejected Stale Updates", summary.rejected_stale_updates),
        ("Ordering Skips", summary.ordering_skips),
        ("Dead Letter Entries", summary.dead_letter_entries),
    )
    for label, value in labels:
        print(f"{label}: {value}")
    print("\nFinal Projection Revisions\n")
    for projection in result.final_projections:
        print(f"{projection.projection.system} {projection.revision.value}")
    return 0
