# Chapter 23: End-to-End Operations Laboratory

## Educational question

> What does a complete deterministic inventory synchronization system look like
> when all of its components work together?

## Overview

This capstone introduces no synchronization mechanism. Instead, it places the
immutable domain values and deterministic infrastructure from Chapters 1–22 in
one observable run. The result is a compact operations exercise: every outcome
comes from fixed inputs, simulated integer time, FIFO queueing, and stable worker
assignment. Running it repeatedly produces the same result.

The complete architecture is shown in the [end-to-end diagram](../diagrams/end-to-end-operations-laboratory.md).

## Walkthrough

1. An `InventoryLedger` records 16 alternating Receive and Reserve events.
2. Replaying its first 15 events creates authority Revision 15; replaying every
   event creates Revision 16.
3. Storefront, Warehouse, and Reporting are registered as independent
   projections.
4. Fan-out creates one immutable synchronization request for every projection at
   each authority revision. One separately delayed Revision 15 request represents
   work already in transit.
5. A `CapacityQueue` holds work while a deterministic two-worker `WorkerPool`
   processes it in simulated time.
6. Warehouse Revision 15 fails once, then the same request succeeds on retry.
7. Reporting Revision 15 fails three times and is isolated in the dead letter
   queue. Reporting Revision 16 later succeeds, showing that terminal old work
   does not stop healthy new work.
8. Storefront Revision 16 is deliberately delivered twice. The applied-request
   registry recognizes the second delivery, so idempotency skips its effect.
9. Warehouse Revision 15 is deliberately delivered after Revision 16. The
   monotonic ordering comparison skips it rather than moving Warehouse backward.
10. All three final projections match authority Revision 16. The old Reporting
    failure remains available for operational inspection in the dead letter
    queue.

These are scripted failures and deliveries, not random faults or operating-system
concurrency. That constraint makes the lesson reproducible.

## Run the CLI

Docker remains the supported default:

```bash
docker compose build
docker compose run --rm lab inventory-sim laboratory
```

The command narrates the run chronologically under these sections:

```text
=== Ledger ===
=== Authority ===
=== Fan-Out ===
=== Queue ===
=== Worker Pool ===
=== Retry ===
=== Duplicate Delivery ===
=== Ordering ===
=== Dead Letter Queue ===
=== Final Summary ===
```

## Expected operational dashboard

The detailed worker lines precede this deterministic summary:

```text
Authority Revision: 16
Registered Projections: 3
Synchronization Requests: 7
Successful Synchronizations: 5
Retries: 3
Duplicate Deliveries: 1
Idempotent Skips: 1
Rejected Stale Updates: 1
Ordering Skips: 1
Dead Letter Entries: 1

Final Projection Revisions

Storefront 16
Warehouse 16
Reporting 16
```

“Synchronization Requests” counts the six requests created by fan-out plus the
delayed older request.
“Successful Synchronizations” counts projection applications, not retry attempts
or policy skips. The stale rejection and ordering skip describe the same old
delivery from two operational viewpoints: it was rejected because the ordering
policy determined that it could not advance the projection.

## How Volume I fits together

- Chapters 1–4 define inventory, authority, ledger replay, and projections.
- Chapters 5–9 add deterministic time, direct and queued synchronization,
  capacity, and worker pools.
- Chapters 10–14 make stale snapshots measurable with revisions and rejection.
- Chapters 15–16 register multiple projections and fan authority changes out.
- Chapters 17–19 demonstrate retry, duplicate delivery, and idempotency.
- Chapters 20–21 expose out-of-order delivery and enforce monotonic ordering.
- Chapter 22 isolates permanently failing work in a dead letter queue.
- Chapter 23 orchestrates those existing pieces and reports their combined
  operational behavior.

## Volume I Complete

Volume I began with a small immutable inventory state and progressively made the
path between authority and projections explicit. Readers learned that a ledger
can rebuild authority; a snapshot can become stale while queued; finite workers
create waiting; revisions express causality that quantities cannot; fan-out
creates independent work; retry can cause duplicate delivery; idempotency makes
repetition harmless; ordering prevents regression; and a dead letter queue
isolates work that cannot succeed.

The capstone shows why those ideas belong together. Correct projection state is
not supplied by one clever algorithm. It emerges from clear immutable inputs,
deterministic orchestration, and small policies whose decisions are observable
and testable. No new synchronization concept is hidden in this chapter: the
laboratory is the assembled Volume I architecture.
