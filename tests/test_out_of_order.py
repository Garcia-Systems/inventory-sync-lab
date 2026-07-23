from inventory_sim.out_of_order import run_out_of_order_scenario


def test_reversed_delivery_is_deterministic() -> None:
    assert run_out_of_order_scenario() == run_out_of_order_scenario()


def test_projection_follows_delivery_instead_of_creation_order() -> None:
    result = run_out_of_order_scenario()

    assert tuple(item.revision.value for item in result.created_revisions) == (13, 14)
    assert tuple(item.revision.value for item in result.deliveries) == (14, 13)
    assert result.final_projection.state == result.created_revisions[0].state
    assert result.final_projection_revision.value == 13


def test_authority_remains_newer_after_every_request_succeeds_once() -> None:
    result = run_out_of_order_scenario()

    assert result.authority.revision.value == 14
    assert result.authority.state != result.final_projection.state
    assert result.processed_request_ids == (14, 13)
    assert len(set(result.processed_request_ids)) == len(result.requests) == 2
    assert all(
        delivery.completion.projection_after.state
        == delivery.request.authoritative_state
        for delivery in result.deliveries
    )
    assert result.final_queue_depth == 0
