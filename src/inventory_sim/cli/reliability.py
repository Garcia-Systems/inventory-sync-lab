"""CLI demonstrations for reliability."""

from inventory_sim.dead_letter import run_dead_letter_scenario
from inventory_sim.duplicate_delivery import run_duplicate_delivery_scenario
from inventory_sim.fanout import run_fanout_scenario
from inventory_sim.idempotency import run_idempotency_scenario
from inventory_sim.ordering import run_ordering_scenario
from inventory_sim.out_of_order import run_out_of_order_scenario
from inventory_sim.retries import run_retry_scenario


def fanout() -> int:
    """Run the canonical Chapter 16 fan-out scenario."""
    result = run_fanout_scenario()
    print("Fan-Out Synchronization\n")
    print(f"Authority advanced to Revision {result.authority.revision.value}\n")
    print("Generating synchronization requests...\n")
    for number, request in enumerate(result.requests, start=1):
        print(f"{request.system:<12} -> Request {number}")
    print("\nWorker processing...\n")
    for projection in result.final_projections:
        print(
            f"{projection.projection.system} updated to "
            f"Revision {projection.revision.value}"
        )
    print("\nSummary")
    print(f"Authoritative revision: {result.authority.revision.value}")
    print(f"Generated requests: {len(result.requests)}")
    print(f"Projections updated: {len(result.completions)}")
    print("\nOne inventory event became three independent work items.")
    print("No retries, networking, or messaging infrastructure was used.")
    return 0


def retries() -> int:
    """Run the canonical Chapter 17 deterministic retry scenario."""
    result = run_retry_scenario()
    print("Retry Policies\n")
    print(f"Revision {result.authority.revision.value}")
    for request in result.requests:
        print(f"\n{request.system}")
        for completion in (
            item for item in result.completions if item.attempt.request is request
        ):
            print(f"Attempt {completion.attempt.number}")
            print("Success" if completion.succeeded else "Failed")
            if not completion.succeeded:
                print("\nRetry scheduled\n")
    print("\nSummary")
    print(f"Requests created: {len(result.requests)}")
    print(f"Attempts performed: {len(result.completions)}")
    print(f"Retries required: {len(result.retry_attempts)}")
    print(
        "Successful synchronizations: "
        f"{sum(completion.succeeded for completion in result.completions)}"
    )
    print("\nRetries improved delivery; they did not add duplicate handling.")
    return 0


def duplicate_delivery() -> int:
    """Run the canonical Chapter 18 duplicate-delivery scenario."""
    result = run_duplicate_delivery_scenario()
    print(f"Authority Revision {result.authority.revision.value}\n")
    print(f"Synchronization Request {result.request_id}")
    for delivery in result.deliveries:
        print(f"\nDelivery {delivery.number}")
        print(f"Projection updated to Revision {result.authority.revision.value}")
    print(f"\nBusiness events: {len(result.business_events)}")
    print(f"Request deliveries: {len(result.deliveries)}")
    print(f"Projection updates: {result.projection_update_count}")
    print(
        "\nDuplicate delivery is expected in many reliable messaging systems; "
        "this scenario intentionally performs both updates."
    )
    return 0


def idempotency() -> int:
    """Run the canonical Chapter 19 idempotent-synchronization scenario."""
    result = run_idempotency_scenario()
    print(f"Authority Revision {result.authority.revision.value}\n")
    print(f"Synchronization Request {result.request.request_id}")
    for delivery in result.deliveries:
        print(f"\nDelivery {delivery.number}\n")
        print("Result:")
        if delivery.projection_updated:
            print("Projection updated.")
        else:
            print("Already applied.\n")
            print("Projection unchanged.")
    print("\nSummary\n")
    print(f"Deliveries: {len(result.deliveries)}\n")
    print(f"Projection updates: {result.projection_update_count}")
    return 0


def out_of_order() -> int:
    """Run the canonical Chapter 20 reversed-delivery scenario."""
    result = run_out_of_order_scenario()
    print("Authority\n")
    for snapshot in result.created_revisions:
        print(f"Revision {snapshot.revision.value} created\n")
    print("Delivery order\n")
    for delivery in result.deliveries:
        print(f"Revision {delivery.revision.value}\n")
    print("Processing\n")
    for delivery in result.deliveries:
        print(f"Revision {delivery.revision.value} applied\n")
        print(f"Projection revision: {delivery.revision.value}\n")
    print(f"Final authority revision: {result.authority.revision.value}\n")
    print(f"Final projection revision: {result.final_projection_revision.value}\n")
    print("Projection is behind authority.\n")
    print("No retries occurred. No duplicate deliveries occurred.")
    print("Every request succeeded and was processed exactly once.")
    print("Ordering alone caused the incorrect result.")
    return 0


def ordering() -> int:
    """Run the canonical Chapter 21 monotonic-ordering scenario."""
    result = run_ordering_scenario()
    print("Authority\n")
    for snapshot in result.created_revisions:
        print(f"Revision {snapshot.revision.value} created\n")
    print("Delivery order\n")
    for delivery in result.deliveries:
        print(f"Revision {delivery.revision.value}\n")
    print("Processing\n")
    for delivery in result.deliveries:
        print(f"Revision {delivery.revision.value}\n")
        if delivery.projection_updated:
            print("Projection updated\n")
        else:
            print("Older than current projection\n")
            print("Update skipped\n")
        print(f"Projection revision: {delivery.projection_revision_after.value}\n")
    print(f"Final authority revision: {result.authority.revision.value}\n")
    print(f"Final projection revision: {result.final_projection.revision.value}\n")
    print("The projection never moves backward.")
    return 0


def dead_letter() -> int:
    """Run the canonical Chapter 22 terminal-failure scenario."""
    result = run_dead_letter_scenario()
    print("Synchronization Summary\n")
    by_system: dict[str, list] = {}
    for completion in result.completions:
        by_system.setdefault(completion.attempt.request.system, []).append(completion)

    print("Storefront")
    print("Success\n")
    print("Warehouse")
    print("Succeeded after retry\n")
    print("Reporting")
    for completion in by_system["Reporting"]:
        print(f"Retry {completion.attempt.number} failed")
    print("\nMoved to Dead Letter Queue\n")
    print("Dead Letter Queue\n")
    for entry in result.dead_letters:
        print(entry.request.system)
        print(f"Revision {entry.revision.value}")
        print("Reason:")
        print(f"{entry.reason}\n")
    print("Operational Summary\n")
    print(f"Successful requests: {len(result.successful_requests)}")
    print(f"Retries performed: {result.retry_count}")
    print(f"Dead-letter entries: {len(result.dead_letters)}")
    print("Terminal work is isolated; other synchronization continues.")
    return 0
