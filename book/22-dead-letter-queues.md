# Chapter 22 — Dead Letter Queues

## Educational question

> What should the system do after repeated synchronization failures?

## Bounded retries and operational isolation

Not every synchronization request eventually succeeds. An unlimited retry loop
would repeatedly consume worker capacity and could prevent useful work from
making progress. This chapter adds a configurable maximum-attempt policy and the
smallest possible terminal destination: a deterministic in-memory
`DeadLetterQueue`.

When a request reaches its third failed attempt, the worker appends an immutable
entry containing the original request, attempt count, and reason. The active
queue never receives that request again. Dead-letter entries retain insertion
order and remain inspectable, while unrelated requests continue normally.

## Deterministic walkthrough

1. The `InventoryLedger` produces authoritative Revision 15.
2. `FanOutGenerator` creates immutable requests for Storefront, Warehouse, and
   Reporting, and a one-worker `WorkerPool` processes them through simulated
   `EventScheduler` time.
3. Storefront succeeds on its first attempt.
4. Warehouse fails once, returns to the FIFO work queue, and then succeeds.
5. Reporting deterministically fails attempts 1, 2, and 3.
6. The retry policy permits no fourth attempt, so Reporting is inserted into the
   dead-letter queue with reason `Maximum retry attempts exceeded`.
7. Storefront and Warehouse match authority; Reporting remains isolated and
   available for inspection.

There is no randomness, real waiting, networking, database, or concurrency.

## Chapter diagram

```text
Synchronization Request
        │
   Retry Policy
        │
 ┌──────┴────────┐
 ▼               ▼
Success      Retry Limit
                 │
                 ▼
      Dead Letter Queue
```

See the standalone [dead letter queue diagram](../diagrams/dead-letter-queues.md).
The important branch is operational isolation, not another recovery mechanism.

## Run the scenario

```bash
docker compose build
docker compose run --rm lab inventory-sim dead-letter
```

## Expected output

```text
Synchronization Summary

Storefront
Success

Warehouse
Succeeded after retry

Reporting
Retry 1 failed
Retry 2 failed
Retry 3 failed

Moved to Dead Letter Queue

Dead Letter Queue

Reporting
Revision 15
Reason:
Maximum retry attempts exceeded

Operational Summary

Successful requests: 2
Retries performed: 3
Dead-letter entries: 1
Terminal work is isolated; other synchronization continues.
```

## Relationship to Chapters 17–21

Chapter 17 established deterministic retry policies. Chapters 18 and 19 showed
duplicate delivery and idempotent effects. Chapters 20 and 21 explored
out-of-order delivery and monotonic projection updates. Those mechanisms make
delivery safer, but none answers what happens when every permitted attempt
fails. Chapter 22 bounds Chapter 17's retry behavior and isolates its terminal
outcome. It does not change duplicate, idempotency, or ordering rules.

Message replay, operator actions, and operator recovery are intentionally
deferred. The queue supports inspection only.

## Why this matters

Production systems often isolate permanently failing work so operators can
investigate without stopping the entire synchronization pipeline. A dead letter
queue makes terminal failures visible and preserves the throughput of healthy
work. This laboratory model captures that operational principle without adding
infrastructure or pretending to provide production recovery tooling.
