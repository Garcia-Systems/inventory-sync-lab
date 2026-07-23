import subprocess
import sys

from inventory_sim.cli import main
from inventory_sim.laboratory import OperationalSummary, run_laboratory_scenario


def test_end_to_end_laboratory_has_deterministic_final_state() -> None:
    result = run_laboratory_scenario()
    assert result == run_laboratory_scenario()
    assert result.final_queue_depth == 0
    assert tuple(item.revision.value for item in result.final_projections) == (
        16,
        16,
        16,
    )
    assert all(
        item.projection.state == result.authorities[-1].state
        for item in result.final_projections
    )
    assert tuple(entry.request.system for entry in result.dead_letters) == (
        "Reporting",
    )


def test_laboratory_operational_summary() -> None:
    assert run_laboratory_scenario().summary == OperationalSummary(
        authority_revision=16,
        registered_projections=3,
        synchronization_requests=7,
        successful_synchronizations=5,
        retries=3,
        duplicate_deliveries=1,
        idempotent_skips=1,
        rejected_stale_updates=1,
        ordering_skips=1,
        dead_letter_entries=1,
    )


def test_laboratory_cli_walks_through_complete_pipeline(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["laboratory"]) == 0
    output = capsys.readouterr().out
    for heading in (
        "=== Ledger ===",
        "=== Authority ===",
        "=== Fan-Out ===",
        "=== Queue ===",
        "=== Worker Pool ===",
        "=== Retry ===",
        "=== Duplicate Delivery ===",
        "=== Ordering ===",
        "=== Dead Letter Queue ===",
        "=== Final Summary ===",
    ):
        assert heading in output
    assert "Authority Revision: 16" in output
    assert "Warehouse 16" in output


def test_package_module_supports_laboratory_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "laboratory"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "Dead Letter Entries: 1" in completed.stdout
