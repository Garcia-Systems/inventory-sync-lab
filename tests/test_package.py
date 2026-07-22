import subprocess
import sys

import inventory_sim


def test_package_exposes_a_version() -> None:
    assert inventory_sim.__version__


def test_package_module_is_executable() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "doctor"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "Laboratory environment is ready." in completed.stdout
