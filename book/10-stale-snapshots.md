# Stale Snapshots

## Educational question

> What happens when authoritative inventory changes while an earlier
> synchronization request is waiting in the queue?

It can produce a successful but obsolete projection. A synchronization request
captures an immutable `InventoryState`; it does not continuously point at the
ledger. Queue delay creates time in which ordinary business activity can change
the state derived from that ledger.

## Deterministic walkthrough

The scenario begins by replaying `Receive 10` and `Reserve 3`. Authority is 10
on hand, 3 reserved, and 7 available. At simulated time 0, the single worker
starts an earlier warehouse request. That deliberately occupies its fixed
three-tick capacity.

At time 1, a website `SynchronizationRequest` captures the authority's
7-available state and enters `CapacityQueue`. It cannot start yet. At time 2,
the immutable ledger is extended with `Receive 5` and replayed. Current
authority is now 15 on hand, 3 reserved, and 12 available. The queued request
still carries 7 available, because that was the valid snapshot at creation.

At time 3 the earlier work completes and the website request starts. At time 6,
`WorkerState` completes it and `ProjectionRegistry` receives a new immutable
website projection. The worker correctly copied 7 available from the request.
The projection therefore equals the request snapshot but differs from current
authority's 12 available.

Nothing failed. FIFO ordering, fixed service time, ledger replay, and projection
replacement all behaved exactly as designed. Correctness relative to a request
is not necessarily correctness relative to the current world.

See the [chapter timeline](../diagrams/stale-snapshots.md).

## Run the scenario

Use the Docker-first command:

```bash
docker compose run --rm lab inventory-sim stale-snapshots
```

Expected output includes:

```text
Time 1 — Website request created and queued
  Request snapshot available: 7

Time 2 — Authority changes: Receive 5
  Current authority available: 12
  Queued request snapshot remains: 7

Time 6 — Worker finishes
  Synchronization succeeded; projection updated from the request.
  Request snapshot available: 7
  Resulting projection available: 7
  Current authority available: 12

The projection matches the request snapshot: MATCH.
The projection differs from current authority: STALE.
```

All times, events, queue choices, and service durations are fixed. Repeated runs
produce the same records without sleeping, networking, threads, or randomness.

## Relationship to Chapters 7–9

Chapter 7 established that a request carries authority through a FIFO queue.
Chapter 8 made waiting visible by giving a worker fixed capacity and service
time. Chapter 9 showed that more workers can overlap simulated work while
preserving deterministic assignment. Those chapters held authority constant.

Chapter 10 changes only that assumption. The existing request, work item,
capacity queue, worker, scheduler, registry, projection, ledger, and inventory
state naturally expose the consequence. Capacity may shorten a delay, but it
does not make the captured information change while waiting.

## Why synchronization alone is insufficient

Synchronization answers, “Was this snapshot copied?” It does not answer, “Is
this snapshot still an accurate description of authority now?” Here the answer
to the first question is yes and the answer to the second is no. Merely moving
data reliably cannot guarantee that the world did not change during transit.

## Limitations intentionally deferred

This chapter demonstrates the problem rather than solving it. It adds no
freshness validation, versions, sequence numbers, retries, rejection rules,
optimistic concurrency, idempotency, persistence, database, network, HTTP,
threads, or asynchronous execution. The labels `MATCH` and `STALE` are
post-scenario observations for readers; they do not control processing.

## Why this matters

Distributed systems often fail because information becomes old before it
arrives—not because software crashes. A queue and worker can execute perfectly
and still publish a view the authoritative world has already left behind.

The next chapters will explore measuring and eventually preventing stale
updates. This chapter intentionally supplies neither mechanism; it establishes
why they become necessary.
