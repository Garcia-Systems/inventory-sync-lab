# Chapter 18 — Duplicate Delivery

## Educational question

> What happens when the same synchronization request is processed more than once?

## One event, two deliveries

Reliable delivery commonly means that a sender tries again when it cannot know
whether earlier work completed. Consequently, a synchronization request may be
delivered more than once. This is different from two business events: the
authority advances only once, to Revision 11, and Request 42 carries that one
unchanged snapshot on both deliveries.

This chapter intentionally updates the projection twice. It does not label the
second update as an error, discard it, or make processing idempotent. Those
policies would hide the behavior this lesson is intended to expose.

## Chapter diagram

```text
Business Event
      │
      ▼
Synchronization Request
      │
 ┌────┴────┐
 ▼         ▼
Delivery 1 Delivery 2
 └────┬────┘
      ▼
Projection Updated Twice
```

See the standalone [duplicate-delivery diagram](../diagrams/duplicate-delivery.md).

## Walkthrough

1. A single inventory event advances the authoritative inventory to Revision 11.
2. The simulator creates immutable Synchronization Request 42 for that snapshot.
3. The queue receives two work items that both reference the exact same request.
4. A one-worker `WorkerPool` processes Delivery 1 and updates the projection.
5. The deterministic `EventScheduler` assigns Delivery 2 next.
6. The worker processes the unchanged request again and repeats the projection
   update to Revision 11.
7. The result records one business event, two request deliveries, and two
   projection updates.

There is no networking, database, randomness, real-time waiting, thread, or
asynchronous runtime. Every run has the same ordering and result.

## Run the scenario

```bash
docker compose build
docker compose run --rm lab inventory-sim duplicate-delivery
```

## Expected output

```text
Authority Revision 11

Synchronization Request 42

Delivery 1
Projection updated to Revision 11

Delivery 2
Projection updated to Revision 11

Business events: 1
Request deliveries: 2
Projection updates: 2

Duplicate delivery is expected in many reliable messaging systems; this scenario intentionally performs both updates.
```

## Why this matters

Duplicate delivery is often the price paid for reliable delivery. A producer may
prefer delivering a request again over risking that it never arrives. Consumers
must therefore be designed with repeated execution in mind, even when the
underlying business event occurred only once.

This chapter shows the consequence without solving it. Readers should naturally
ask:

> How can processing the same request twice produce the correct outcome?

That question is answered in the next chapter.
