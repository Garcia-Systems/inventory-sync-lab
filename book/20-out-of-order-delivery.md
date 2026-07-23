# Chapter 20: Out-of-Order Delivery

## Educational question

> What happens when newer inventory arrives before older inventory?

## Processing order is not creation order

Reliable delivery does not promise chronological delivery. Revisions describe
the authority's intended order even when requests are observed in another
order. An idempotent handler recognizes repeated request identities, but two
different requests are not duplicates: it may successfully apply each exactly
once and still finish with the wrong snapshot.

This chapter deliberately exposes that failure. It adds no stale-request
rejection, buffering, sorting, or reordering.

## Deterministic walkthrough

1. An `InventoryLedger` produces Revision 13 and then Revision 14.
2. One immutable `SynchronizationRequest` is created for each snapshot.
3. The `EventScheduler` delivers Revision 14 first and Revision 13 second.
4. A one-worker `WorkerPool` applies both requests successfully and exactly once.
5. The `ProjectionRegistry` therefore holds Revision 14 briefly, then follows
   delivery order backward to Revision 13.
6. Authority remains at Revision 14. The final projection is behind it.

The run is deterministic and has no retry, duplicate delivery, randomness,
network, database, thread, or real waiting.

## Chapter diagram

```text
Creation order                 Delivery and processing order

Revision 13                    Revision 14 → Projection 14
    ↓                              ↓
Revision 14                    Revision 13 → Projection 13

Authority: 14                 Final projection: 13
```

See the standalone [out-of-order delivery diagram](../diagrams/out-of-order-delivery.md).

## Run the scenario

```bash
docker compose build
docker compose run --rm lab inventory-sim out-of-order
```

## Expected output

```text
Authority

Revision 13 created

Revision 14 created

Delivery order

Revision 14

Revision 13

Processing

Revision 14 applied

Projection revision: 14

Revision 13 applied

Projection revision: 13

Final authority revision: 14

Final projection revision: 13

Projection is behind authority.

No retries occurred. No duplicate deliveries occurred.
Every request succeeded and was processed exactly once.
Ordering alone caused the incorrect result.
```

## Relationship to Chapters 17–19

Chapter 17 retried a failed delivery. Chapter 18 delivered one request twice.
Chapter 19 used stable request identities to make those repeated deliveries
idempotent. Chapter 20 delivers two distinct, successful requests once each, so
idempotency has nothing to suppress. Their reversed arrival order alone makes
the projection incorrect.

## Why this matters

Reliable delivery and idempotent processing do not guarantee correct ordering.
Many distributed systems require additional mechanisms to preserve or restore
ordering. Those mechanisms are intentionally beyond the scope of this chapter;
this scenario must remain incorrect so the consequence is visible.
