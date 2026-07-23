from dataclasses import FrozenInstanceError

import pytest

from inventory_sim.dead_letter import (
    MAXIMUM_ATTEMPTS_EXCEEDED,
    DeadLetterEntry,
    DeadLetterQueue,
    DeadLetterRetryPolicy,
    run_dead_letter_scenario,
)
from inventory_sim.inventory import InventoryState
from inventory_sim.queues import SynchronizationRequest
from inventory_sim.retries import SynchronizationAttempt
from inventory_sim.revisions import InventoryRevision


def request(system: str, revision: int) -> SynchronizationRequest:
    return SynchronizationRequest(system, InventoryState(10 + revision, 1))


def test_retry_limit_is_validated_and_enforced() -> None:
    with pytest.raises(ValueError, match="positive"):
        DeadLetterRetryPolicy(0)
    with pytest.raises(TypeError, match="integer"):
        DeadLetterRetryPolicy(True)  # type: ignore[arg-type]
    policy = DeadLetterRetryPolicy(3)
    reporting = request("Reporting", 15)
    assert policy.may_retry(SynchronizationAttempt(reporting, 1))
    assert policy.may_retry(SynchronizationAttempt(reporting, 2))
    assert not policy.may_retry(SynchronizationAttempt(reporting, 3))


def test_dead_letter_queue_preserves_insertion_order() -> None:
    queue = DeadLetterQueue()
    first = DeadLetterEntry(request("Reporting", 15), InventoryRevision(15), "first", 3)
    second = DeadLetterEntry(request("Archive", 16), InventoryRevision(16), "second", 3)
    queue.enqueue(first)
    queue.enqueue(second)
    assert queue.entries == (first, second)
    assert queue.depth == 2
    with pytest.raises(FrozenInstanceError):
        first.reason = "changed"  # type: ignore[misc]


def test_terminal_failure_is_dead_lettered_and_not_retried_again() -> None:
    result = run_dead_letter_scenario(maximum_attempts=3)
    reporting = tuple(
        completion
        for completion in result.completions
        if completion.attempt.request.system == "Reporting"
    )
    assert tuple(item.attempt.number for item in reporting) == (1, 2, 3)
    assert not any(item.succeeded for item in reporting)
    assert len(result.dead_letters) == 1
    assert result.dead_letters[0].request is result.requests[2]
    assert result.dead_letters[0].reason == MAXIMUM_ATTEMPTS_EXCEEDED
    assert result.dead_letters[0].revision == InventoryRevision(15)
    assert result.dead_letters[0].attempts == 3
    assert result.final_queue_depth == 0


def test_successful_work_continues_while_failure_is_isolated() -> None:
    result = run_dead_letter_scenario()
    assert tuple(item.system for item in result.successful_requests) == (
        "Storefront",
        "Warehouse",
    )
    assert result.retry_count == 3
    assert result.final_projections[0].state == result.authority.state
    assert result.final_projections[1].state == result.authority.state
    assert result.final_projections[2].state != result.authority.state
    assert run_dead_letter_scenario() == result
