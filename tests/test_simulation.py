import pytest

from inventory_sim import EventExecution, EventScheduler, VirtualClock


def test_clock_begins_at_zero_and_advances_forward_or_to_same_time() -> None:
    clock = VirtualClock()
    assert clock.now == 0
    clock.advance_to(5)
    clock.advance_to(5)
    assert clock.now == 5


@pytest.mark.parametrize("invalid", [True, 1.5, "1"])
def test_clock_rejects_non_integer_times(invalid: object) -> None:
    with pytest.raises(TypeError, match="time must be an integer"):
        VirtualClock().advance_to(invalid)  # type: ignore[arg-type]


def test_clock_rejects_negative_time_and_backward_movement() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        VirtualClock(-1)
    clock = VirtualClock(3)
    with pytest.raises(ValueError, match="cannot move backward"):
        clock.advance_to(2)


def test_scheduler_runs_chronologically_and_breaks_ties_by_insertion_order() -> None:
    clock = VirtualClock()
    scheduler = EventScheduler(clock)
    actions: list[str] = []
    scheduler.schedule(at=8, label="last", action=lambda: actions.append("last"))
    scheduler.schedule(at=5, label="first at five", action=lambda: actions.append("a"))
    scheduler.schedule(at=2, label="first", action=lambda: actions.append("first"))
    scheduler.schedule(at=5, label="second at five", action=lambda: actions.append("b"))

    executions = scheduler.run()

    assert actions == ["first", "a", "b", "last"]
    assert executions == (
        EventExecution(2, 3, "first"),
        EventExecution(5, 2, "first at five"),
        EventExecution(5, 4, "second at five"),
        EventExecution(8, 1, "last"),
    )
    assert clock.now == 8
    assert scheduler.run() == ()


def test_scheduler_allows_current_time_and_actions_may_schedule_actions() -> None:
    scheduler = EventScheduler()
    actions: list[str] = []

    def add_current_event() -> None:
        actions.append("creator")
        scheduler.schedule(
            at=scheduler.clock.now,
            label="new",
            action=lambda: actions.append("new"),
        )

    scheduler.schedule(at=0, label="creator", action=add_current_event)
    scheduler.schedule(
        at=0, label="already queued", action=lambda: actions.append("old")
    )
    scheduler.run()
    assert actions == ["creator", "old", "new"]


def test_each_action_runs_exactly_once() -> None:
    calls = 0

    def action() -> None:
        nonlocal calls
        calls += 1

    scheduler = EventScheduler()
    scheduler.schedule(at=1, label="once", action=action)
    scheduler.run()
    scheduler.run()
    assert calls == 1


def test_past_event_is_rejected() -> None:
    clock = VirtualClock(3)
    scheduler = EventScheduler(clock)
    with pytest.raises(ValueError, match="before the current clock time"):
        scheduler.schedule(at=2, label="past", action=lambda: None)


@pytest.mark.parametrize("invalid", [True, 1.5])
def test_scheduler_rejects_non_integer_event_times(invalid: object) -> None:
    with pytest.raises(TypeError, match="event time must be an integer"):
        EventScheduler().schedule(  # type: ignore[arg-type]
            at=invalid, label="invalid", action=lambda: None
        )


def test_scheduler_rejects_negative_event_time() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        EventScheduler().schedule(at=-1, label="invalid", action=lambda: None)


@pytest.mark.parametrize("label", ["", "   "])
def test_scheduler_rejects_blank_labels(label: str) -> None:
    with pytest.raises(ValueError, match="empty or whitespace"):
        EventScheduler().schedule(at=0, label=label, action=lambda: None)


def test_scheduler_rejects_non_string_label_and_non_callable_action() -> None:
    with pytest.raises(TypeError, match="label must be a string"):
        EventScheduler().schedule(at=0, label=3, action=lambda: None)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="action must be callable"):
        EventScheduler().schedule(at=0, label="bad", action=None)  # type: ignore[arg-type]


def test_scheduler_rejects_invalid_clock() -> None:
    with pytest.raises(TypeError, match="clock must be a VirtualClock"):
        EventScheduler(clock=object())  # type: ignore[arg-type]


def test_action_failure_stops_without_retry_or_advancing_further() -> None:
    scheduler = EventScheduler()
    calls = 0

    def fail() -> None:
        nonlocal calls
        calls += 1
        raise RuntimeError("action failed")

    scheduler.schedule(at=2, label="failure", action=fail)
    scheduler.schedule(at=5, label="later", action=lambda: None)
    with pytest.raises(RuntimeError, match="action failed"):
        scheduler.run()
    assert calls == 1
    assert scheduler.clock.now == 2


def test_simulation_module_does_not_import_real_time_or_sleep() -> None:
    import inventory_sim.simulation as simulation

    assert "time" not in simulation.__dict__
    assert "sleep" not in simulation.__dict__
