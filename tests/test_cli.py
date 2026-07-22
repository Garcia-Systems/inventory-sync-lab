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
    assert "Chapter 1 inventory-state example" in output
    assert "full simulator have not been implemented yet" in output
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
