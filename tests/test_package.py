import subprocess
import sys

import inventory_sim
from inventory_sim import (
    DeadLetterQueue,
    EventScheduler,
    InventoryLedger,
    InventoryProjection,
    InventoryState,
    RetryPolicy,
    RevisionedProjection,
    SynchronizationRequest,
    VirtualClock,
    WorkerPool,
)
from inventory_sim.revisions import RevisionedProjection as CanonicalProjection

PUBLIC_SYMBOLS = {
    "DeadLetterQueue",
    "EventScheduler",
    "InventoryLedger",
    "InventoryProjection",
    "InventoryState",
    "RevisionedProjection",
    "RetryPolicy",
    "SynchronizationRequest",
    "VirtualClock",
    "WorkerPool",
    "run_laboratory_scenario",
}


def test_package_exposes_a_version() -> None:
    assert inventory_sim.__version__


def test_package_root_exposes_supported_volume_one_concepts() -> None:
    assert PUBLIC_SYMBOLS <= set(inventory_sim.__all__)
    assert all(getattr(inventory_sim, name) is not None for name in PUBLIC_SYMBOLS)


def test_public_api_has_no_duplicate_names_and_keeps_internals_private() -> None:
    assert len(inventory_sim.__all__) == len(set(inventory_sim.__all__))
    assert "main" not in inventory_sim.__all__
    assert "_ScheduledEvent" not in inventory_sim.__all__


def test_revisioned_projection_has_one_canonical_public_identity() -> None:
    assert RevisionedProjection is CanonicalProjection
    assert all(
        concept is not None
        for concept in (
            DeadLetterQueue,
            EventScheduler,
            InventoryLedger,
            InventoryProjection,
            InventoryState,
            RetryPolicy,
            SynchronizationRequest,
            VirtualClock,
            WorkerPool,
        )
    )


def test_package_module_is_executable() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inventory_sim", "doctor"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "Laboratory environment is ready." in completed.stdout
