# Chapter 5: Time and Events

Chapter 4 required a person to refresh a projection. Before deciding how a
future simulation triggers such work, we need a repeatable answer to **when**
generic actions run. Chapter 5 adds only simulated time and scheduling; none of
its descriptive actions synchronize inventory.

## 1. The problem: why real time makes experiments difficult

A program that waits on the wall clock can run slowly, depend on operating-system
scheduling, become harder to test, and sometimes behave differently between
runs. Real-time systems can be tested, but doing so requires complexity this
laboratory does not need yet.

```text
Real program time
    Depends on operating-system timing and actual waiting.

Simulated time
    Advances only when the simulation decides to advance it.
```

## 2. A real-world example

Our teaching timeline begins at 0, inspects inventory at 2, describes website
and marketplace refresh actions at 5, and inspects again at 8. The labels make
the scenario familiar; the callbacks deliberately do nothing. The lesson is
ordering, not synchronization.

## 3. The engineering concept: simulated time

Simulated time is an integer controlled by the program. Moving from tick 0 to
tick 5 does not wait five seconds. Integers avoid floating-point ambiguity and
make examples easy to compare.

## 4. Diagram

[The Chapter 5 timeline](../diagrams/deterministic-timeline.md) shows the direct
jumps and the two events sharing tick 5.

## 5. The virtual clock

```text
Clock starts at 0.
Next event is at 5.
Clock advances directly to 5.
```

Unless the model schedules something between those values, there is nothing to
process there. `VirtualClock` contains explicit, local mutation: `now` exposes
the current tick and `advance_to` moves forward. Moving to the current tick is
allowed, which is useful for equal-time events. Negative, Boolean, non-integer,
and backward times are rejected. There is no global clock.

## 6. Scheduled events

A scheduled simulation event is a zero-argument action assigned a simulated
time and a readable, nonblank label. Its return value is ignored because the
action is run for its effects.

Do not confuse two meanings of “event”:

```text
Inventory ledger event
    A business fact such as receiving stock.

Scheduled simulation event
    An action the simulator plans to execute at a simulated time.
```

The latter does not become a ledger fact.

## 7. Chronological and equal-time ordering

Earlier times execute first even if scheduling calls occur in another order.
Schedule tick 8 and then tick 2, and tick 2 still runs first. For two events at
tick 5, time alone cannot decide. The scheduler assigns an increasing insertion
order and compares `(time, order)`, so website runs before marketplace when it
was scheduled first. This explicit tie-breaker avoids incidental object or
memory-address ordering.

Actions may schedule new actions because the same small heap loop naturally
supports it. Normal rules still apply. A new current-time action receives a
later insertion order, so it runs after current-time actions already waiting.

## 8. No real sleeping and the event loop

The scheduler never calls `sleep`. An eight-tick timeline can finish immediately:

1. Find the next event.
2. Advance the virtual clock to its time.
3. Execute its action.
4. Record what ran.
5. Repeat until no events remain.

This is a small deterministic scheduler, not an asynchronous or operating-system
event loop.

## 9. Failure behavior

If an action raises, that exception escapes and stops `run()`. The failed event
is not retried or recorded as successful, and the clock remains at its scheduled
time rather than advancing to later work. Recovery and retries are intentionally
deferred.

## 10. Code introduced

The public implementation is in `src/inventory_sim/simulation.py`:

```python
clock = VirtualClock()
scheduler = EventScheduler(clock)
scheduler.schedule(at=5, label="first", action=lambda: None)
executions = scheduler.run()
```

`VirtualClock` stores one integer. Internally, an ordered scheduled record holds
time and insertion order before its label and callback; only the first two fields
participate in heap comparison. `EventExecution` is an immutable public record
of scheduled time, original insertion order, and label. `run()` returns a tuple
of these records and ignores callback return values. Internal heap entries and
the counter are not public package interfaces.

## 11. Running the timeline

Before running it, predict both the chronological order and the tick-5 order:

```bash
docker compose run --rm lab inventory-sim timeline
```

The command prints the clock at 0, the four scheduling calls, their execution at
2, 5, 5, and 8, and the final clock at 8. It explicitly says no real waiting
occurred and that the labels did not synchronize inventory.

## 12. Tests as part of the lesson

`tests/test_simulation.py` verifies chronological and insertion order, invalid
times, forward and equal clock movement, local exactly-once callback execution,
action failure, and the absence of real-time sleeping. Here “exactly once” means
one action is invoked once in one local scheduler run. It makes no claim about
distributed message delivery. CLI tests verify the readable teaching scenario.

## 13. Manual exercises

1. Reorder the scheduling calls and predict execution order.
2. Add two events at one tick and predict their tie-break order.
3. Try to move a clock backward and explain the error.
4. Schedule an action at the current tick.
5. Change the last event and predict the final clock value.
6. Explain why wall-clock sleep is unnecessary.

## 14. Questions for the reader

- Why is integer time useful here?
- Why can the clock skip directly from 2 to 5?
- What should happen when two events share a time?
- How is a scheduled event different from a ledger event?
- Why should the scheduler reject past events?
- What future mechanism could use this scheduler to refresh projections?

## 15. Summary

The program controls simulated integer time without real waiting. Scheduled
actions execute chronologically, and insertion order deterministically resolves
equal-time ties. Execution records make the result inspectable. Automatic
inventory synchronization still does not exist.

## 16. What comes next

Chapter 6 introduces direct synchronization. It will use deterministic events
to represent when a projection refresh occurs, while still avoiding queues and
workers. Chapter 5 stops before implementing any of that synchronization.
