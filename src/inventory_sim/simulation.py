"""Deterministic simulated time and scheduled actions."""

import heapq
from collections.abc import Callable
from dataclasses import dataclass, field


def _validate_time(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} cannot be negative")
    return value


class VirtualClock:
    """A mutable integer clock controlled only by the simulation."""

    def __init__(self, start: int = 0) -> None:
        self._now = _validate_time(start, name="start time")

    @property
    def now(self) -> int:
        """Return the current simulated time."""
        return self._now

    def advance_to(self, time: int) -> None:
        """Advance to a later or equal simulated time."""
        validated = _validate_time(time, name="time")
        if validated < self._now:
            raise ValueError("time cannot move backward")
        self._now = validated


@dataclass(frozen=True)
class EventExecution:
    """An immutable record of one successfully executed action."""

    time: int
    order: int
    label: str


@dataclass(order=True)
class _ScheduledEvent:
    time: int
    order: int
    label: str = field(compare=False)
    action: Callable[[], object] = field(compare=False, repr=False)


class EventScheduler:
    """Run scheduled actions by time and then by insertion order."""

    def __init__(self, clock: VirtualClock | None = None) -> None:
        if clock is not None and not isinstance(clock, VirtualClock):
            raise TypeError("clock must be a VirtualClock")
        self.clock = clock if clock is not None else VirtualClock()
        self._events: list[_ScheduledEvent] = []
        self._next_order = 1

    def schedule(self, *, at: int, label: str, action: Callable[[], object]) -> None:
        """Schedule a zero-argument action at a valid simulated time."""
        scheduled_time = _validate_time(at, name="event time")
        if scheduled_time < self.clock.now:
            raise ValueError("event time cannot be before the current clock time")
        if not isinstance(label, str):
            raise TypeError("event label must be a string")
        if not label.strip():
            raise ValueError("event label cannot be empty or whitespace")
        if not callable(action):
            raise TypeError("event action must be callable")

        heapq.heappush(
            self._events,
            _ScheduledEvent(scheduled_time, self._next_order, label, action),
        )
        self._next_order += 1

    def run(self) -> tuple[EventExecution, ...]:
        """Run all queued actions, returning records of successful executions."""
        executions: list[EventExecution] = []
        while self._events:
            event = heapq.heappop(self._events)
            self.clock.advance_to(event.time)
            event.action()
            executions.append(EventExecution(event.time, event.order, event.label))
        return tuple(executions)
