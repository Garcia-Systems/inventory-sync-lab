from dataclasses import FrozenInstanceError

import pytest

from inventory_sim.retries import run_retry_scenario


def test_retry_scheduling_is_deterministic() -> None:
    first = run_retry_scenario()
    second = run_retry_scenario()

    assert first == second
    assert tuple(item.attempt.request.system for item in first.completions) == (
        "Storefront",
        "Warehouse",
        "Reporting",
        "Warehouse",
    )


def test_attempts_are_counted_per_immutable_request() -> None:
    result = run_retry_scenario()
    warehouse = result.requests[1]
    warehouse_attempts = tuple(
        item for item in result.completions if item.attempt.request is warehouse
    )

    assert tuple(item.attempt.number for item in warehouse_attempts) == (1, 2)
    assert (
        warehouse_attempts[0].attempt.request is warehouse_attempts[1].attempt.request
    )
    assert (
        warehouse_attempts[0].attempt.request.authoritative_state
        is warehouse.authoritative_state
    )
    with pytest.raises(FrozenInstanceError):
        warehouse.system = "Changed"  # type: ignore[misc]


def test_failed_attempt_eventually_succeeds_and_all_projections_update() -> None:
    result = run_retry_scenario()

    assert tuple(item.succeeded for item in result.completions) == (
        True,
        False,
        True,
        True,
    )
    assert len(result.retry_attempts) == 1
    assert result.final_queue_depth == 0
    assert all(
        projection.state == result.authority.state
        for projection in result.final_projections
    )
