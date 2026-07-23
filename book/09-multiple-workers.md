# Chapter 9: Multiple Workers

## 1. The problem: one worker is a capacity limit

Chapter 8 gave every request the same three-tick service time, but forced every
request through one worker. Separate requests could not be processed during the
same simulated interval, so later arrivals waited longer.

Consider four stale sales-channel projections. The ledger records `Receive 10`
and `Reserve 3`, so authority is 10 on hand, 3 reserved, and 7 available.
Website has 10 available, marketplace 9, storefront 8, and partner 9. Their
available differences are therefore +3, +2, +1, and +2.

## 2. A real-world example: adding capacity

A worker pool is **a fixed collection of workers that can process different
queued requests at the same simulated time**. Our pool contains `worker-1` and
`worker-2`. Each is still individually limited to one request and each request
still needs three ticks. Worker count is a capacity decision, not a correctness
rule.

One worker makes requests wait behind one another. With two workers, two
requests may be in progress at once. Capacity helps only when work exists to use
it; an idle third worker would not make an already-running request faster.

## 3. The engineering concept: simulated concurrency

Website and marketplace are both in progress from time 1 through time 4.
Python does not run two threads. A deterministic scheduler merely records two
future completion events. This overlapping *simulated* work needs no processes,
locks, asynchronous I/O, or wall-clock waiting.

Assignment has two explicit rules:

1. Give the oldest FIFO request work first.
2. Give that request to the lowest-numbered idle worker first.

Thus website goes to `worker-1` and marketplace to `worker-2`; at time 4,
storefront goes to `worker-1` and partner to `worker-2`. Explicit tie-breaking
prevents object identity, container ordering, or platform behavior from changing
the lesson.

### Same-time arrivals and completions

At time 1, the scheduler enqueues website, then marketplace, then runs one
assignment event. Both requests are visible to the assignment round.

At time 4, completion events execute in scheduling order: worker-1 then
worker-2. The first completion schedules one coordination event at the same
time. Because it is inserted behind the already-scheduled completion, both
workers complete and become idle before coordination assigns more work. The
coordination event then walks workers by number and requests by FIFO order.
This is a precise event ordering, not physically simultaneous execution.

## 4. Diagrams and the scenario timeline

See the [two worker lanes and queue evolution](../diagrams/multiple-workers.md).

Queue depth after each assignment boundary is:

```text
Time 1: 0
Time 2: 1  [storefront]
Time 3: 2  [storefront, partner]
Time 4: 0
```

Four requests arrive before either first-round request completes, so a queue can
still grow even with two workers. At time 3, queue depth is 2, busy workers is 2,
and total unfinished work is 4. At time 5, queue depth is 0, busy workers is 2,
and total unfinished work is 2. Queue depth counts only work waiting to start.

The resulting waits are website 0, marketplace 0, storefront 2, and partner 1.
Partner arrives later but both workers become free at time 4, so both waiting
requests start in that assignment round. Average wait is `(0 + 0 + 2 + 1) / 4 =
0.75` ticks; maximum wait is 2.

Service time never changes: every completion is exactly three ticks after its
start. Website and marketplace update only at time 4; storefront and partner
remain stale until their time-7 completions.

Across the time-0-to-time-8 observation window each worker is busy for six
ticks. Pool utilization is total busy worker-ticks divided by available
worker-ticks: `12 / (2 * 8) = 75%`. This differs from merely asking whether at
least one worker was busy.

## 5. Code introduced

`WorkerState` now has a validated stable `name`, and start and completion records
carry `worker_name`. `WorkerPool` creates an ordered immutable tuple of workers,
reports busy and idle counts, looks workers up by name, and rejects invalid
counts and duplicate names.

`assign_available` walks idle workers in tuple order and dequeues FIFO work until
either workers or requests run out. It schedules a completion for each start but
does not update a projection. `complete` performs that update and makes exactly
one worker idle. Immutable `WorkerInspection`, `MultipleWorkersInspection`, and
`MultipleWorkersResult` make pool behavior directly testable.

`run_multiple_workers_scenario()` constructs only this chapter's canonical
two-worker scenario. It records arrivals, starts, completions, inspections at
times 3, 5, and 8, scheduler history, and simple wait summaries. It is not a
generic experiment framework.

## 6. Tests are part of the lesson

The tests verify FIFO request order, stable worker order, one active request per
worker, completion-event insertion order, the coordinated time-4 reassignment,
completion-only projection visibility, reduced waits, and repeatability. They
also preserve Chapter 8's single-worker result. No test needs a thread, process,
sleep, async operation, failure, retry, or random number.

## 7. Run it and try manual exercises

Before running, predict each assignment, depth at time 3, matches at time 5,
final completion time, and average wait:

```bash
docker compose run --rm lab inventory-sim multiple-workers
```

Then work these on paper (the CLI intentionally is not configurable):

1. Predict all waits with one worker, then with three workers.
2. Reverse the two time-1 enqueue events and apply both ordering rules.
3. Recalculate partner's wait if it arrives at time 5.
4. Explain why every service time remains three ticks.
5. Calculate queue depth after each event time.
6. Identify intervals in which a third worker would remain unused.

## 8. Questions for the reader

1. How do two workers increase capacity?
2. Does a second worker make one request complete faster?
3. Why is deterministic worker ordering necessary?
4. What in-progress work does queue depth omit?
5. Why do storefront and partner both start at time 4?
6. Why does partner wait only one tick?
7. When would an extra worker remain idle?
8. What new problem appears if authority changes while requests wait?

## 9. Summary

Multiple workers allow overlapping simulated processing, while each worker
still handles only one request. FIFO requests and numbered workers make every
assignment deterministic. Additional capacity reduces waiting and queue depth,
but it does not shorten fixed service time and helps only when pending work
exists. Projections update at completion. There are no real threads, failures,
retries, autoscaling, or random timing.

## 10. What comes next

Chapter 10 introduces authority changing after a request snapshot is created.
An older queued snapshot may then arrive after newer state exists, leaving a
projection outdated even after successful processing. That chapter will reason
about freshness and ordering; Chapter 9 does not implement them.
