import subprocess
import sys

import pytest

from inventory_sim.cli import main


def test_doctor_reports_readiness(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["doctor"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Laboratory environment is ready." in output
    assert "version" in output


def test_demo_explains_current_status(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["demo"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Chapter 1 inventory-state model" in output
    assert "authoritative-record comparison example" in output
    assert "Chapter 6 adds direct synchronization" in output
    assert "Chapter 7 adds queued synchronization" in output
    assert "FIFO request processing" in output
    assert "Chapter 8 adds fixed processing time" in output
    assert "One worker is BUSY" in output
    assert "fixed two-worker pool" in output
    assert "Random latency is not implemented" in output
    assert "Chapter 10 introduces changing authority" in output
    assert "Chapter 3 adds an inventory ledger" in output
    assert "inventory-sim inventory" in output


def test_multiple_workers_command_reports_canonical_lesson(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["multiple-workers"]) == 0
    output = capsys.readouterr().out
    for wording in (
        "Multiple Workers",
        "Workers: 2",
        "Service time: 3 ticks",
        "website\n  Worker: worker-1",
        "marketplace\n  Worker: worker-2",
        "storefront\n  Worker: worker-1",
        "partner\n  Worker: worker-2",
        "Completion: 4",
        "Completion: 7",
        "Wait: 0",
        "Wait: 2",
        "Wait: 1",
        "Inspection at time 8",
        "worker-1: IDLE",
        "worker-2: IDLE",
        "Maximum queue depth: 2",
        "Final queue depth: 0",
        "Final simulated time: 8",
        "assignment deterministic",
        "No threads",
    ):
        assert wording in output


def test_package_module_supports_multiple_workers_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "multiple-workers"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "Average wait time: 0.75 ticks" in completed.stdout


def test_stale_snapshots_command_reports_successful_obsolete_copy(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["stale-snapshots"]) == 0
    output = capsys.readouterr().out
    for wording in (
        "Stale Snapshots",
        "Time 1 — Website request created and queued",
        "Request snapshot available: 7",
        "Time 2 — Authority changes: Receive 5",
        "Current authority available: 12",
        "Time 6 — Worker finishes",
        "Synchronization succeeded",
        "Resulting projection available: 7",
        "matches the request snapshot: MATCH",
        "differs from current authority: STALE",
        "Nothing failed",
        "No freshness validation",
    ):
        assert wording in output


def test_package_module_supports_stale_snapshots_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "stale-snapshots"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "copied snapshot became outdated" in completed.stdout


def test_freshness_command_reports_measured_values(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["freshness"]) == 0
    output = capsys.readouterr().out
    assert "Measuring Freshness" in output
    assert "Request    Wait    Service    Snapshot Age" in output
    assert "A          0       3          0" in output
    assert "B          2       3          2" in output
    assert "C          5       3          5" in output
    assert "No request was rejected" in output


def test_package_module_supports_freshness_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "freshness"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "Time 9 — Request C completes" in completed.stdout


def test_revisions_command_orders_repeated_quantities(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["revisions"]) == 0
    output = capsys.readouterr().out
    assert "Revision    Available" in output
    assert "1           10" in output
    assert "2           7" in output
    assert "3           10" in output
    assert "Revision 3 is newer than Revision 1" in output
    assert "ordering information only" in output


def test_package_module_supports_revisions_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "revisions"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "Synchronization requests still copy their snapshots" in completed.stdout


def test_detect_stale_command_observes_and_continues(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["detect-stale"]) == 0
    output = capsys.readouterr().out
    for wording in (
        "Detecting Stale Synchronizations",
        "Worker: worker-1",
        "Request revision: 2",
        "Authority revision: 4",
        "Stale request: YES",
        "Worker: worker-2",
        "Request revision: 4",
        "Stale request: NO",
        "Continuing synchronization...",
        "Both requests were processed",
        "no request was rejected",
    ):
        assert wording in output


def test_package_module_supports_detect_stale_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "detect-stale"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "Detection was an observation only" in completed.stdout


def test_reject_stale_command_reports_policy_outcomes(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["reject-stale"]) == 0
    output = capsys.readouterr().out
    for wording in (
        "Rejecting Stale Synchronizations",
        "Worker: worker-1",
        "Request revision: 2",
        "Result: REJECTED",
        "Projection unchanged.",
        "Worker: worker-2",
        "Request revision: 4",
        "Result: ACCEPTED",
        "Projection updated.",
        "Accepted requests: 1",
        "Rejected requests: 1",
        "Final authoritative revision: 4",
        "Final projection revision: 4",
    ):
        assert wording in output


def test_package_module_supports_reject_stale_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "reject-stale"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "Both workers complete normally" in completed.stdout


def test_worker_capacity_command_reports_canonical_lesson(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["worker-capacity"]) == 0
    output = capsys.readouterr().out
    for wording in (
        "Workers and Capacity",
        "Available: 7",
        "Service time: 3 ticks",
        "Capacity: one request at a time",
        "Time 1 — website",
        "Time 2 — marketplace",
        "Time 3 — storefront",
        "completion scheduled for time 4",
        "completion scheduled for time 7",
        "completion scheduled for time 10",
        "Wait: 0",
        "Wait: 2",
        "Wait: 4",
        "Queue depth: 2",
        "Final worker state: IDLE",
        "Final queue depth: 0",
        "Final simulated time: 11",
        "Requests arrived faster",
        "No real waiting",
    ):
        assert wording in output


def test_package_module_supports_worker_capacity_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "worker-capacity"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "storefront\n  Arrival: 3" in completed.stdout


def test_inventory_command_displays_default_state(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["inventory"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Inventory State" in output
    assert "On hand:   10" in output
    assert "Reserved:  3" in output
    assert "Available: 7" in output


def test_inventory_command_accepts_custom_state(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["inventory", "--on-hand", "8", "--reserved", "2"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "On hand:   8" in output
    assert "Reserved:  2" in output
    assert "Available: 6" in output


@pytest.mark.parametrize(
    "arguments",
    [
        ["--on-hand", "5", "--reserved", "6"],
        ["--on-hand", "-1", "--reserved", "0"],
    ],
)
def test_inventory_command_reports_invalid_states_without_traceback(arguments) -> None:  # type: ignore[no-untyped-def]
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "inventory", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "Error: invalid inventory state:" in completed.stderr
    assert "Traceback" not in completed.stderr


def test_package_module_supports_inventory_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "inventory"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "Available: 7" in completed.stdout


def test_authority_command_displays_default_comparisons(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["authority"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Authority:" in output
    assert "inventory-authority" in output
    assert "website\n  Available:  7\n  Difference: +0\n  Status:     MATCH" in output
    assert "marketplace\n  Available:  10\n  Difference: +3" in output
    assert "Status:     DIFFERS" in output
    assert "no synchronization or repair occurred" in output


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        (
            [
                "--authority-on-hand",
                "12",
                "--authority-reserved",
                "4",
                "--website-on-hand",
                "12",
                "--website-reserved",
                "4",
                "--marketplace-on-hand",
                "12",
                "--marketplace-reserved",
                "4",
            ],
            "Difference: +0",
        ),
        (
            [
                "--authority-on-hand",
                "10",
                "--authority-reserved",
                "2",
                "--website-on-hand",
                "8",
                "--website-reserved",
                "2",
            ],
            "Difference: -2",
        ),
    ],
)
def test_authority_command_accepts_custom_states(arguments, expected, capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["authority", *arguments]) == 0
    assert expected in capsys.readouterr().out


def test_authority_command_reports_invalid_state_without_traceback() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "inventory_sim",
            "authority",
            "--authority-on-hand",
            "5",
            "--authority-reserved",
            "6",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "Error: invalid inventory state:" in completed.stderr
    assert "Traceback" not in completed.stderr


def test_package_module_supports_authority_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "authority"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "inventory-authority" in completed.stdout
    assert "Difference: +3" in completed.stdout


def test_ledger_command_displays_events_and_derived_inventory(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["ledger"]) == 0
    assert capsys.readouterr().out == (
        "Inventory Ledger\n\n"
        "1. Receive 10\n"
        "2. Reserve 3\n"
        "3. Ship 2\n\n"
        "Current Inventory\n\n"
        "On hand: 8\n"
        "Reserved: 1\n"
        "Available: 7\n"
    )


def test_package_module_supports_ledger_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "ledger"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "1. Receive 10" in completed.stdout
    assert "Available: 7" in completed.stdout


def test_projections_command_teaches_manual_refresh(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["projections"]) == 0
    output = capsys.readouterr().out

    assert "Authoritative ledger" in output
    assert "Authoritative state" in output
    assert "On hand:   10" in output
    assert "Reserved:  3" in output
    assert "warehouse\n" in output
    assert "website\n" in output
    assert "marketplace\n" in output
    assert output.count("Status:     MATCH") == 3
    assert "Difference: +3" in output
    assert "Status:     STALE" in output
    assert "Manual refresh" in output
    assert "No automatic synchronization occurred" in output
    assert "Projection after manual refresh" in output
    assert "Difference: +0" in output


def test_package_module_supports_projections_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "projections"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "marketplace" in completed.stdout
    assert "Status:     STALE" in completed.stdout
    assert "Status:     MATCH" in completed.stdout
    assert "Traceback" not in completed.stderr


def test_timeline_command_teaches_deterministic_event_order(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["timeline"]) == 0
    output = capsys.readouterr().out
    assert "Starting simulated time: 0" in output
    for label in (
        "Inspect inventory",
        "Refresh website projection",
        "Refresh marketplace projection",
        "Inspect inventory again",
    ):
        assert label in output
    execution = output.index("Execution")
    assert output.index("Time 2", execution) < output.index("Time 5", execution)
    assert output.index("Refresh website projection", execution) < output.index(
        "Refresh marketplace projection", execution
    )
    assert output.rindex("Time 8") > output.rindex("Time 5")
    assert "Final simulated time: 8" in output
    assert "No real waiting occurred" in output
    assert "did not synchronize inventory" in output


def test_package_module_supports_timeline_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "timeline"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "Final simulated time: 8" in completed.stdout
    assert "No real waiting occurred" in completed.stdout


def test_sync_direct_command_teaches_scheduled_copy(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["sync-direct"]) == 0
    output = capsys.readouterr().out
    assert "Direct Inventory Synchronization" in output
    assert "Authoritative state" in output
    assert "Available: 7" in output
    assert "Initial website projection" in output
    assert "Available:  10" in output
    assert "Difference: +3" in output
    assert "Time 4 — Inspect website" in output
    assert "Status: STALE" in output
    assert "Time 6 — Direct synchronization" in output
    assert "Before available: 10" in output
    assert "After available:  7" in output
    assert "Time 8 — Inspect website" in output
    assert "Difference: +0" in output
    assert "Status: MATCH" in output
    assert "Final simulated time: 8" in output
    assert "No queue, worker" in output
    assert "real waiting" in output
    assert "no transport delay" in output


def test_package_module_supports_sync_direct_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "sync-direct"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "Time 6 — Direct synchronization" in completed.stdout
    assert "Final simulated time: 8" in completed.stdout


def test_sync_queue_command_teaches_fifo_waiting(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["sync-queue"]) == 0
    output = capsys.readouterr().out
    assert "Queued Inventory Synchronization" in output
    assert "Available: 7" in output
    assert "website\n  Available:  10\n  Difference: +3" in output
    assert "marketplace\n  Available:  9\n  Difference: +2" in output
    assert "Time 2 — Enqueue website" in output
    assert "Time 3 — Enqueue marketplace" in output
    assert "Time 4 — Inspect system\n  Queue depth: 2" in output
    assert "Time 5 — Worker processes next request\n  Processed: website" in output
    assert "Queue depth: 1" in output
    assert "Time 7 — Worker processes next request\n  Processed: marketplace" in output
    assert "Time 8 — Final inspection\n  Queue depth: 0" in output
    assert "website: MATCH" in output
    assert "marketplace: MATCH" in output
    assert "Enqueuing did not update either projection" in output
    assert "one request at a time in FIFO order" in output
    assert "No retries, failures" in output
    assert "parallel workers, or real waiting" in output


def test_package_module_supports_sync_queue_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "sync-queue"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "Processed: website" in completed.stdout
    assert "Processed: marketplace" in completed.stdout
    assert "Final simulated time: 8" in completed.stdout
