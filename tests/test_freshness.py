from dataclasses import FrozenInstanceError

import pytest

from inventory_sim.freshness import measure_freshness, run_freshness_scenario


def test_snapshot_age_is_elapsed_time_since_first_missed_change() -> None:
    observation = measure_freshness(
        request="example",
        request_created_at=1,
        synchronization_completed_at=8,
        current_time=8,
        wait_time=4,
        service_time=3,
        authority_change_times=(4, 7),
    )

    assert observation.snapshot_age == 4
    assert observation.authority_changed_after_creation is True


def test_freshness_scenario_has_deterministic_values() -> None:
    first = run_freshness_scenario()
    second = run_freshness_scenario()

    assert first == second
    measured = [
        (item.wait_time, item.service_time, item.snapshot_age)
        for item in first.observations
    ]
    assert measured == [
        (0, 3, 0),
        (2, 3, 2),
        (5, 3, 5),
    ]


def test_immediate_request_completes_with_zero_snapshot_age() -> None:
    result = run_freshness_scenario()

    assert result.observations[0].snapshot_age == 0
    assert result.observations[0].authority_changed_after_creation is False


def test_snapshot_age_increases_with_queue_delay() -> None:
    observations = run_freshness_scenario().observations

    assert [item.wait_time for item in observations] == [0, 2, 5]
    assert [item.snapshot_age for item in observations] == [0, 2, 5]


def test_freshness_observation_is_immutable() -> None:
    observation = run_freshness_scenario().observations[0]

    with pytest.raises(FrozenInstanceError):
        observation.snapshot_age = 99  # type: ignore[misc]
