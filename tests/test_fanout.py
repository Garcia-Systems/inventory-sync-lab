from dataclasses import FrozenInstanceError

import pytest

from inventory_sim.fanout import FanOutGenerator, run_fanout_scenario
from inventory_sim.inventory import InventoryState
from inventory_sim.projections import InventoryProjection
from inventory_sim.queues import ProjectionRegistry
from inventory_sim.revisions import InventoryRevision, RevisionedInventoryState


def _registry() -> ProjectionRegistry:
    return ProjectionRegistry(
        tuple(
            InventoryProjection(system, InventoryState(0, 0))
            for system in ("Storefront", "Warehouse", "Reporting")
        )
    )


def test_fanout_generates_one_request_per_projection_in_registry_order() -> None:
    authority = RevisionedInventoryState(InventoryRevision(8), InventoryState(20, 5))
    requests = FanOutGenerator(_registry()).generate(authority)

    assert tuple(request.system for request in requests) == (
        "Storefront",
        "Warehouse",
        "Reporting",
    )
    assert len(requests) == 3
    assert all(request.authoritative_state is authority.state for request in requests)


def test_generated_requests_are_immutable() -> None:
    authority = RevisionedInventoryState(InventoryRevision(8), InventoryState(20, 5))
    request = FanOutGenerator(_registry()).generate(authority)[0]

    with pytest.raises(FrozenInstanceError):
        request.system = "Changed"  # type: ignore[misc]


def test_fanout_scenario_is_deterministic_and_updates_every_projection() -> None:
    first = run_fanout_scenario()
    second = run_fanout_scenario()

    assert first == second
    assert first.authority.revision == InventoryRevision(8)
    assert len(first.requests) == 3
    assert tuple(item.projection.system for item in first.final_projections) == (
        "Storefront",
        "Warehouse",
        "Reporting",
    )
    assert {item.revision for item in first.final_projections} == {InventoryRevision(8)}
    assert all(
        item.projection.state == first.authority.state
        for item in first.final_projections
    )
    assert len(first.completions) == 3
    assert first.final_queue_depth == 0


def test_fanout_validates_inputs() -> None:
    with pytest.raises(TypeError, match="ProjectionRegistry"):
        FanOutGenerator(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="RevisionedInventoryState"):
        FanOutGenerator(_registry()).generate(object())  # type: ignore[arg-type]
