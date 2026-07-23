from inventory_sim.duplicate_delivery import run_duplicate_delivery_scenario


def test_duplicate_delivery_is_deterministic() -> None:
    assert run_duplicate_delivery_scenario() == run_duplicate_delivery_scenario()


def test_exact_same_request_is_delivered_twice() -> None:
    result = run_duplicate_delivery_scenario()

    assert len(result.business_events) == 1
    assert len(result.deliveries) == 2
    assert all(delivery.request is result.request for delivery in result.deliveries)


def test_both_deliveries_update_the_projection() -> None:
    result = run_duplicate_delivery_scenario()

    assert result.authority.revision.value == 11
    assert result.projection_update_count == 2
    assert all(
        delivery.completion.projection_after.state == result.authority.state
        for delivery in result.deliveries
    )
    assert result.final_projection.state == result.authority.state
    assert result.final_queue_depth == 0
