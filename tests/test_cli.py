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
    assert "Inventory synchronization is not implemented" in output
    assert "Queues and workers are not implemented" in output
    assert "Chapter 6 introduces direct synchronization" in output
    assert "Chapter 3 adds an inventory ledger" in output
    assert "inventory-sim inventory" in output


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
