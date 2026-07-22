# Queues

Chapter 6 scheduled a direct synchronization. This chapter adds one idea:
synchronization work can wait in a queue before a worker performs it.

## 1. The problem: direct synchronization couples request and work

In Chapter 6, the scheduled action immediately copied the authoritative state
into the website projection. Requesting the refresh and performing the refresh
were effectively one action. That is easy to understand, but it gives us no way
to represent pending work when several systems need an update.

Suppose the website and marketplace both need the authoritative inventory. If
requests arrive before synchronization capacity is available, we need to record
that the work was requested without pretending it has already finished.

## 2. A real-world example

An inventory producer learns that the ledger now says 10 units are on hand and
3 are reserved. It requests refreshes for two sales channels. The website asks
first and the marketplace asks second. A synchronization worker is available
later, so the requests wait.

This example resembles production message processing, but deliberately omits
network transport, failures, retries, concurrency, and real waiting. Its only
purpose is to make pending work visible.

## 3. Requesting work versus performing work

Three beginner-friendly roles separate the two actions:

```text
Producer
    Requests synchronization.

Queue
    Holds pending requests.

Worker
    Performs synchronization.
```

The **producer** creates a request. The **queue** stores that request until it is
selected. The **worker** removes one request and refreshes its target projection.

### What enqueuing means

Enqueuing means adding a request to the queue. It does **not** update inventory.
The website remains stale after its time-2 request, and the marketplace remains
stale after its time-3 request. Only a worker action performs synchronization.

### FIFO ordering

This queue is first-in, first-out, or **FIFO**:

```text
Website request enters first.
Marketplace request enters second.

Worker processes website first.
Worker processes marketplace second.
```

FIFO makes this small lesson simple and deterministic. It is not a claim that
FIFO is always the best strategy for every production system.

### Queue depth

Queue depth is the number of requests waiting:

```text
Time 2: depth 1
Time 3: depth 2
Time 5: depth 1
Time 7: depth 0
```

Growing depth is an early signal that requests are arriving faster than the
available processing actions can remove them. We do not need a metrics framework
to observe that fact in this scenario.

### A single worker

The worker processes at most one request per scheduled action. That rule gives
the simulation deliberately limited capacity. Here, a worker is not a thread or
an operating-system process. It is an ordinary deterministic Python object. It
does not sleep, run concurrently, or perform asynchronous I/O.

### Snapshot semantics

Each request carries the authoritative `InventoryState` supplied when the
request is created:

```text
The worker processes the request's state snapshot.
It does not re-read authority during processing.
```

Thus, the time-2 request represents the authority known at time 2 even though
the worker uses it at time 5. The canonical authority does not change here, so
both projections end at the same current state. A later chapter can examine the
risk that a snapshot becomes old while waiting; this chapter does not solve it.

## 4. Diagrams

The [queued synchronization diagram](../diagrams/queued-synchronization.md)
shows the producer-to-queue-to-worker flow and the queue-depth timeline.

```text
Synchronization request -> FIFO queue -> Single worker -> Projection registry
```

No retry path, failure path, second worker, or network call is hidden in the
diagram.

## 5. The canonical scenario

The ledger contains `Receive(10)` followed by `Reserve(3)`, deriving 10 on hand,
3 reserved, and 7 available. Two projections begin stale:

| System | Available | Difference from authority |
| --- | ---: | ---: |
| website | 10 | +3 |
| marketplace | 9 | +2 |

The deterministic scheduler performs eight actions:

1. At time 1, inspect both initial projections.
2. At time 2, enqueue the website request; depth becomes 1.
3. At time 3, enqueue the marketplace request; depth becomes 2.
4. At time 4, inspect both stale projections and depth 2.
5. At time 5, process website; website matches and depth becomes 1.
6. At time 6, inspect: marketplace is still stale.
7. At time 7, process marketplace; both match and depth becomes 0.
8. At time 8, inspect both matching projections and the empty queue.

### Why stale data persists in the queue

From time 2 until time 5, the website request exists but has not been processed.
From time 3 until time 7, the marketplace waits even longer. A queue therefore
creates a visible delay between request and completion even though this model
has no network latency and performs no real waiting.

### Immutable values and mutable simulation structures

Requests are immutable snapshots, and projections are immutable copied values.
Refreshing returns a new projection rather than modifying the old one. The
registry replaces its reference to the current projection, leaving the original
available for inspection. The queue and registry themselves must be mutable:
requests enter and leave the queue, and the registry's current references change.
Neither exposes its mutable internal collection.

## 6. Code introduced

Chapter 7 lives in `src/inventory_sim/queues.py`.

### Synchronization request

The request has exactly a target and snapshot:

```python
@dataclass(frozen=True)
class SynchronizationRequest:
    system: str
    authoritative_state: InventoryState
```

Existing projection validation checks the system name and state type. There are
no IDs, timestamps, priorities, retry counts, or metadata.

### FIFO queue

`SynchronizationQueue` uses `collections.deque`. `enqueue()` validates and adds
to the back, `dequeue()` removes from the front, `depth` counts waiting requests,
and `is_empty` reports empty state. Dequeuing an empty queue raises `IndexError`.

```python
queue = SynchronizationQueue()
queue.enqueue(request)
oldest = queue.dequeue()
```

This is not `queue.Queue`; it has no locks, threads, or asynchronous primitives.

### Projection registry

`ProjectionRegistry` accepts a tuple of unique projections. `get(system)` finds
the current immutable value, `replace(projection)` replaces a known system, and
`projections` returns an immutable tuple snapshot. Unknown and duplicate systems
are rejected.

### Single worker and execution record

`SynchronizationWorker.process_next(time=...)` returns `None` if the queue is
empty. Otherwise it dequeues exactly one request, retrieves the target, calls
the existing `synchronize_directly`, replaces the registry value, and returns a
frozen `WorkerExecution`. The record contains simulated time, system, depth
before and after, projection before and after, and available differences before
and after. It has no worker ID, duration, attempt, or error field.

```python
execution = worker.process_next(time=5)
```

Critically, the call passes `request.authoritative_state`; the worker has no
authority dependency that it could re-read.

### Enqueue and inspection records

`QueueEnqueueExecution` records time, system, and resulting depth.
`QueueScenarioInspection` records time, depth, and immutable projection
inspections. These are lesson-specific records, not general metrics machinery.

### Scenario result and runner

`run_queue_synchronization_scenario()` constructs the canonical ledger,
projections, queue, registry, one worker, clock, and scheduler. Its immutable
`QueueSynchronizationResult` exposes the initial state, enqueue records,
inspections, worker executions, scheduler history, final projections, final
depth, and final time. It accepts no configuration.

## 7. Tests as part of the lesson

The queue tests verify FIFO order and exact depth changes. Registry tests verify
replacement and projection isolation. Worker tests prove one-request capacity,
empty-queue behavior, and that a supplied snapshot—not a fresh authority
lookup—is used. Scenario tests verify processing order, deterministic
repeatability, and preservation of the original immutable projections. CLI
tests verify that the educational explanation remains visible.

Because the scheduler advances a virtual integer clock, repeatability tests also
demonstrate the absence of wall-clock waiting. No `sleep`, thread, or async
primitive is necessary.

## 8. Running the scenario and manual exercises

Run:

```bash
docker compose run --rm lab inventory-sim sync-queue
```

Before running it, predict:

1. What is the queue depth at time 4?
2. Which system is processed at time 5?
3. Does marketplace match authority at time 6?
4. What is the final queue depth?

Then try these small source-level thought exercises without building a generic
configuration engine:

1. Reverse enqueue order and predict processing order.
2. Remove the time-7 worker action and predict final depth and projection state.
3. Add a third request and calculate depth after every action.
4. Explain why enqueuing alone cannot refresh a projection.
5. Explain the difference between queue waiting and network latency.
6. Predict what happens if a request snapshot becomes old while waiting.

## 9. Questions for the reader

1. Why separate requesting synchronization from performing it?
2. What does queue depth measure?
3. Why does website remain stale after time 2?
4. Why is marketplace still stale after time 5?
5. What makes this worker's capacity limited?
6. Why does FIFO matter for deterministic behavior?
7. What risk comes from carrying a state snapshot in a queued request?
8. What happens when requests arrive faster than the worker processes them?

## 10. Summary

- Synchronization requests enter a FIFO queue.
- Enqueuing records pending work; it does not update projections.
- A single deterministic worker processes one request per action.
- Queue depth rises as requests arrive and falls as work completes.
- Projections remain stale while their requests wait.
- Requests carry immutable creation-time authority snapshots.
- There are no failures, retries, parallel workers, network transport, variable
  service time, or real waiting in Chapter 7.

## 11. What comes next

Chapter 8 introduces worker capacity and service time. It will explore requests
arriving faster than they can be completed, workers needing simulated time to
finish work, and queue depth growing. Chapter 7 does not implement those ideas.
