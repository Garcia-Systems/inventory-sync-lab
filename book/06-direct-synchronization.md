# Chapter 6: Direct Synchronization

## 1. The problem: from manual refresh to scheduled synchronization

Chapter 4 refreshed a projection manually, outside simulated time. Chapter 5
gave us a clock and a scheduler, but its actions only printed descriptions. We
can now combine those lessons: schedule the same essential copy operation for a
specific simulated time.

The website may be stale even while the authority is correct. We need to see
both that stale interval and the moment at which the copied view changes.

## 2. A real-world example

Imagine an inventory ledger used as the official record and a website that has
an older copy. The ledger contains `Receive(10)` followed by `Reserve(3)`, so the
authority has 10 on hand, 3 reserved, and 7 available. The website still has 10
on hand, 0 reserved, and 10 available. Its available difference is therefore
`+3`.

The website remains stale until its refresh action runs. This laboratory is a
teaching model, not a production integration.

## 3. The engineering concept: what direct synchronization means

> At the scheduled time, copy the current authoritative state directly into the
> projection.

“Direct” means that the scheduled action performs the update itself. This model
skips transport, queues, workers, retries, and network latency. Scheduling an
action does not create a queue in the inventory-synchronization sense.

The canonical timeline is:

* time 0: authority available is 7; website available is 10;
* time 4: inspect the stale website;
* time 6: directly refresh the website;
* time 8: inspect the matching website.

## 4. Diagram and observing before and after

See the [direct synchronization diagram](../diagrams/direct-synchronization.md).
The time-4 inspection proves the projection does not change merely because a
future refresh is scheduled. The time-8 inspection proves that the time-6 action
replaced the simulation's current value. Integer simulated time lets us inspect
both sides without sleeping.

## 5. Code introduced

### Immutable values inside mutable simulation state

`InventoryProjection` remains a frozen domain value. A private, named
`_ProjectionSlot` holds the current value for this one simulation:

```python
class _ProjectionSlot:
    def __init__(self, current: InventoryProjection) -> None:
        self.current = current

    def replace(self, projection: InventoryProjection) -> None:
        self.current = projection
```

The distinction is important:

```text
Projection value
    Immutable.

Current projection reference in the simulation
    Can be replaced as simulated time advances.
```

We do not edit the old object. Replacing a reference preserves a trustworthy
before value for inspection and makes the transition explicit.

### Reusing manual refresh

The direct operation validates its two inputs and delegates to Chapter 4's
`refresh_from` method:

```python
def synchronize_directly(
    *, projection: InventoryProjection, authoritative_state: InventoryState
) -> InventoryProjection:
    if not isinstance(projection, InventoryProjection):
        raise TypeError("projection must be an InventoryProjection")
    if not isinstance(authoritative_state, InventoryState):
        raise TypeError("authoritative_state must be an InventoryState")
    return projection.refresh_from(authoritative_state)
```

The copying rule is not new. The new concept is deciding *when* it runs. This
pure operation neither schedules an event nor waits.

### Inspection and execution records

`ProjectionInspection` records simulated time, system, state, available
difference, and whether it matches. `DirectSynchronizationExecution` records
time, system, the immutable before and after projections, and their available
differences. Both are frozen dataclasses. Differences come from the existing
projection comparison rather than a second formula.

`DirectSynchronizationResult` collects authority, initial projection,
inspections, synchronization execution, scheduler history, final projection,
and final time. It gives tests a structured result without parsing terminal
text.

### The scheduled synchronization action

The scenario schedules three actions. When the scheduler reaches time 6, the
action:

1. reads the slot's current projection;
2. compares it with authority;
3. creates a refreshed projection from authority;
4. replaces the slot's current reference;
5. records the completed synchronization.

The scheduler still owns timing. Its chronological history is 4, 6, 8, and each
action runs once.

## 6. No intermediate transport and tight coupling

No object travels between systems, and no queue waits to be processed. This is
easy to follow, but it cannot represent limited processing capacity or delayed
delivery. Direct synchronization also couples the action to the authoritative
state, projection being updated, and refresh operation. That is appropriate for
this small model; it may become limiting when work must be buffered or many
updates must be processed. Tight coupling is a tradeoff, not universally bad.

## 7. Running the scenario

Before running it, predict the status at times 4 and 8. Then execute:

```bash
docker compose run --rm lab inventory-sim sync-direct
```

Time 4 reports website available 10, difference `+3`, and `STALE`. Time 6
records the direct copy from available 10 to 7. Time 8 reports available 7,
difference `+0`, and `MATCH`. The clock ends at 8. No real waiting or transport
delay is modeled.

## 8. Tests as part of the lesson

The tests check before-and-after states, execution at simulated time 6,
projection immutability, deterministic repeatability, and the scheduler's
4–6–8 order. They also verify that the comparison reaches zero through existing
authority-comparison behavior and that no wall-clock sleep is needed. Input
validation tests keep errors clear while existing Chapter 5 tests protect the
scheduler lesson.

## 9. Manual exercises

1. Predict the complete time-4 inspection before running the command.
2. Predict the observations if synchronization occurred at time 3 instead.
3. Explain what the time-8 inspection would show with no synchronization event.
4. Explain why the old projection object still contains available 10.
5. Name a missing mechanism that could delay an update requested at time 6.
6. Compare Chapter 4's manual refresh with this scheduled direct refresh.

These are reasoning exercises; Chapter 6 intentionally has no configurable
experiment runner.

## 10. Questions for the reader

* What makes this synchronization “direct”?
* Which record remains authoritative?
* Why is the projection stale before time 6?
* Does scheduling a refresh create an inventory queue?
* Why hold a replaceable reference to an immutable projection?
* What happens conceptually if many projections need updates at the same time?
* What mechanism could separate requesting an update from performing it?

## 11. Summary

The ledger replay produces authoritative inventory. The website projection
begins stale. At simulated time 6, the scheduler runs a direct operation that
copies authority into a new projection and replaces the simulation's current
reference. The later inspection matches. There is still no queue, worker, retry,
failure, or latency model.

## 12. What comes next

Chapter 7 introduces queues. It will separate:

```text
Requesting synchronization
```

from:

```text
Performing synchronization
```

That mechanism is deliberately not implemented in this chapter.
