# Chapter 8: Workers and Capacity

Chapter 7 separated requesting synchronization from performing it, but each
scheduled worker action completed a request instantly. That hides a fundamental
constraint: a worker cannot finish unlimited work at one moment. Chapter 8 adds
only the simulated time required to perform work.

## 1. The problem: instantaneous worker actions hide capacity

The Chapter 7 worker removed and completed one request whenever an action ran.
Nothing represented the interval during which it was occupied. Consequently we
could not ask whether a worker was busy, when work would finish, or how long a
request waited. A real inventory channel offers the motivating example: three
refresh requests arrive close together, while the adapter can update only one
channel at a time. Later arrivals must wait.

## 2. Service time

**Service time is the simulated time a worker needs to complete one request
after starting it.** Every request in this lesson takes exactly three integer
ticks. Fixed time isolates the capacity lesson; variable and random timing would
add uncertainty before the state transitions are understood.

## 3. Arrival, start, and completion

These are three distinct moments:

```text
Arrival     The request enters the system.
Start       The worker begins processing it.
Completion  The projection is updated and the request is finished.
```

Website arrives and starts at time 1, then completes at time 4. Marketplace
arrives at 2 but cannot start until 4. Storefront arrives at 3 and starts at 7.

## 4. Waiting time

```text
Waiting time = Start time - Arrival time

Website:     1 - 1 = 0
Marketplace: 4 - 2 = 2
Storefront:  7 - 3 = 4
```

The service time stays constant, but waits grow because each later request finds
the worker occupied by earlier work.

## 5. Total time in the system

```text
Total time = Completion time - Arrival time
Total time = Waiting time + Service time

Website:     4 - 1 = 3 = 0 + 3
Marketplace: 7 - 2 = 5 = 2 + 3
Storefront: 10 - 3 = 7 = 4 + 3
```

Service and waiting are therefore different parts of the time a request spends
in the system.

## 6. Busy and idle workers

```text
IDLE  No request is being processed.
BUSY  One request is being processed until a scheduled completion time.
```

This worker is an ordinary mutable Python simulation object, not an operating-
system thread or process. It never sleeps and does not run concurrently.

## 7. Queue depth versus work in progress

Queue depth counts requests **waiting to start**. Work in progress is the one
request currently held by the worker. At time 3, website is in progress while
marketplace and storefront wait: queue depth is 2, work in progress is website,
and total unfinished work is 3. Removing work at start keeps this distinction
visible.

![The single worker timeline](../diagrams/worker-capacity.md)

## 8. Starting work immediately

An arrival starts immediately when the worker is idle. Website therefore leaves
the queue at time 1 and has zero wait. Its projection does not change yet.

## 9. Arriving while busy

Marketplace and storefront arrive while website is busy. FIFO order keeps them
queued. A projection remains stale both while its request waits and while its
request is being processed.

## 10. Updating at completion

Starting is not completing. Only the completion callback copies the request's
authoritative snapshot into the registry. This makes stale duration accurate:
website remains stale until time 4, marketplace until 7, and storefront until 10.

## 11. Completion starts the next request

Time 4 has a deterministic transition:

1. website completes;
2. website's projection updates;
3. marketplace starts;
4. marketplace completion is scheduled for time 7.

Starting marketplace at time 4 does not complete it then. Its own three ticks
must elapse. The same sequence starts storefront when marketplace completes.

## 12. Dynamic event scheduling

Arrival actions do not manually predetermine every completion. When work starts,
the worker computes `start + service_time` and the action schedules that future
completion. An executing scheduler action may add an event at the current or a
future simulated time, never in the past. Newly added same-time work follows
already queued same-time events, preserving insertion order.

## 13. Capacity and queue growth

Three requests arrive in three ticks, but one worker needs three ticks for each.
At time 3 it is still processing website, so two requests wait. This is limited
throughput without yet introducing queueing-theory formulas. Across the fixed
observation window 0 through 11, it is busy for 9 ticks, so the illustrative
utilization is `9 / 11`, about 81.8%. Instantaneous callbacks add no busy time.

## 14. Snapshot semantics remain

`SynchronizationWorkItem` wraps the Chapter 7 `SynchronizationRequest` and its
arrival time. The request still carries the authoritative state captured at
creation; completion uses that snapshot rather than rereading the ledger.
Authority does not change in this chapter. A future lesson can examine changes
that occur while work waits.

## 15. The Python implementation

The immutable timed envelope is intentionally small:

```python
@dataclass(frozen=True)
class SynchronizationWorkItem:
    request: SynchronizationRequest
    arrived_at: int
```

`WorkerState(service_time=3)` exposes `is_idle`, `is_busy`, `current`,
`started_at`, and `completes_at`. `start_next` removes one FIFO item and returns
an immutable `WorkerProcessingStart` containing system, arrival, start,
scheduled completion, depth after start, and wait. It rejects a second start
while busy. `complete` refreshes the registry and returns `WorkerCompletion`
with timing, before/after projections, and differences before becoming idle.

`CapacityScenarioInspection` records time, worker status, current system and
completion, waiting depth, and each projection's status and available
difference. `run_worker_capacity_scenario()` wires arrival callbacks,
dynamically created completion callbacks, and inspections together. Its
immutable result exposes the records, event history, final state, and the simple
canonical utilization calculation.

## 16. Running the scenario

Before running it, predict the time-3 depth, marketplace start, storefront wait,
matching projections at time 8, and final worker state. Then run:

```bash
docker compose run --rm lab inventory-sim worker-capacity
```

The command shows arrival, start, and completion separately. It uses virtual
ticks: there is no real waiting.

## 17. Tests are part of the lesson

The tests verify immutable work items, fixed-time validation, idle/busy state
transitions, FIFO depth, exact completion times, increasing waits, updates only
at completion, and deterministic dynamically scheduled events. They also guard
the earlier timelines and ensure no wall-clock sleep influences the result.

## 18. Manual exercises

1. Calculate the waits if service time were two ticks (without changing code).
2. Predict queue depth if storefront arrived at time 8.
3. Explain what changes if marketplace arrives at time 5.
4. Recalculate total time for all three requests from their timestamps.
5. Identify exactly when each projection becomes current.
6. Explain why queue depth excludes current work.
7. Predict worker and projection state if final inspection occurred at time 9.

These are paper experiments, not requests for a configuration engine.

## 19. Questions for the reader

- Why is starting work different from completing it?
- Why does website have zero wait time?
- Why does storefront wait longer than marketplace?
- When does a projection become current?
- What does queue depth omit?
- Why does the worker schedule a completion event?
- What happens if requests continue arriving every tick?
- How could additional workers change the result?

## 20. Summary

Processing now consumes deterministic simulated time. One worker handles one
request at a time; depth grows when arrivals exceed its capacity. Waiting time
and service time are distinct, and their sum is total time in the system.
Projections update at completion, not start. There are still no failures,
retries, multiple workers, random timing, concurrency, or real sleeping.

## 21. What comes next

Chapter 9 introduces multiple workers. It will explore parallel processing
capacity, assignment, reduced waits, deterministic tie-breaking when workers
are simultaneously available, and the limits of adding workers. None of those
ideas is implemented here.
