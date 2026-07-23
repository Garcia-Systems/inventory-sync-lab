from dataclasses import FrozenInstanceError

import pytest

from inventory_sim.idempotency import (
    AppliedRequestRegistry,
    run_idempotency_scenario,
)


def test_first_delivery_updates_projection() -> None:
    result = run_idempotency_scenario()

    assert result.authority.revision.value == 12
    assert result.deliveries[0].projection_updated
    assert (
        result.deliveries[0].completion.projection_before == result.initial_projection
    )
    assert result.deliveries[0].completion.projection_after == result.final_projection


def test_repeated_deliveries_leave_projection_unchanged() -> None:
    result = run_idempotency_scenario()

    assert len(result.deliveries) == 3
    assert result.projection_update_count == 1
    assert all(delivery.already_applied for delivery in result.deliveries[1:])
    assert all(
        delivery.completion.projection_before
        == delivery.completion.projection_after
        == result.final_projection
        for delivery in result.deliveries[1:]
    )
    assert result.final_projection.state == result.authority.state
    assert result.final_queue_depth == 0


def test_duplicate_detection_is_deterministic_and_per_projection() -> None:
    first = run_idempotency_scenario()
    second = run_idempotency_scenario()

    assert first == second
    assert [delivery.projection_updated for delivery in first.deliveries] == [
        True,
        False,
        False,
    ]


def test_synchronization_request_remains_immutable() -> None:
    request = run_idempotency_scenario().request

    with pytest.raises(FrozenInstanceError):
        request.request_id = 58  # type: ignore[misc]


def test_idempotency_registry_requires_an_identified_request() -> None:
    request = run_idempotency_scenario().request
    unidentified = type(request)(request.system, request.authoritative_state)

    with pytest.raises(ValueError, match="requires a request id"):
        AppliedRequestRegistry().already_applied(unidentified)


def test_request_identifier_and_registry_inputs_are_validated() -> None:
    request = run_idempotency_scenario().request

    for invalid_id in (True, 0):
        with pytest.raises(ValueError, match="positive integer"):
            type(request)(request.system, request.authoritative_state, invalid_id)
    with pytest.raises(TypeError, match="SynchronizationRequest"):
        AppliedRequestRegistry().already_applied(object())  # type: ignore[arg-type]
