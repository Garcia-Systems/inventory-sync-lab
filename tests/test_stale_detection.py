from dataclasses import FrozenInstanceError

import pytest

from inventory_sim.revisions import InventoryRevision
from inventory_sim.stale_detection import (
    StaleDetection,
    detect_stale_request,
    run_stale_detection_scenario,
)


def test_older_request_revision_is_detected_as_stale() -> None:
    detection = detect_stale_request(InventoryRevision(2), InventoryRevision(4))

    assert detection == StaleDetection(
        InventoryRevision(2), InventoryRevision(4), stale=True
    )


def test_equal_request_revision_is_detected_as_current() -> None:
    detection = detect_stale_request(InventoryRevision(4), InventoryRevision(4))

    assert detection.stale is False


def test_revision_comparison_is_deterministic() -> None:
    first = detect_stale_request(InventoryRevision(2), InventoryRevision(4))
    second = detect_stale_request(InventoryRevision(2), InventoryRevision(4))

    assert first == second


def test_detection_record_is_immutable() -> None:
    detection = detect_stale_request(InventoryRevision(2), InventoryRevision(4))

    with pytest.raises(FrozenInstanceError):
        detection.stale = False  # type: ignore[misc]


@pytest.mark.parametrize("position", ["request", "authority"])
def test_detection_requires_inventory_revisions(position: str) -> None:
    request: object = InventoryRevision(2)
    authority: object = InventoryRevision(4)
    if position == "request":
        request = 2
    else:
        authority = 4

    with pytest.raises(TypeError, match=f"{position} revision"):
        detect_stale_request(request, authority)  # type: ignore[arg-type]


def test_scenario_detects_but_completes_stale_and_current_requests() -> None:
    result = run_stale_detection_scenario()

    assert [inspection.detection.stale for inspection in result.inspections] == [
        True,
        False,
    ]
    assert [completion.system for completion in result.completions] == [
        "website",
        "marketplace",
    ]
    assert result.final_projections[0].state.available == 7
    assert result.final_projections[1].state.available == 8
    assert result.final_time == 6
