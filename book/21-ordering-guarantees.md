# Chapter 21 — Ordering Guarantees

## Educational question

> How can a projection avoid moving backward when older synchronization requests arrive later?

## Compare before updating

Before a worker updates a projection, it compares the request revision with the
projection's current revision. A strictly newer request advances the projection.
An older request is skipped. An equal revision also leaves the projection
unchanged, preserving the idempotent behavior introduced in Chapter 19.

This ordering policy is independent of retries and duplicate detection. It is a
small, deterministic rule, not a production ordering protocol.

## Deterministic walkthrough

1. The `InventoryLedger` creates Revision 13 and then Revision 14.
2. Immutable `SynchronizationRequest` values are delivered in reverse order.
3. The `EventScheduler` and one-worker `WorkerPool` process Revision 14 first.
4. Revision 14 is newer than the projection, so the `ProjectionRegistry` is updated.
5. Revision 13 then arrives and compares older than projection Revision 14.
6. Its update is skipped, so projection Revision 14 still matches authority.

No buffering or request reordering occurs. The observed delivery order remains
14 then 13; only the permission to overwrite the projection is conditional.

## Chapter diagram

```text
Revision 14
    ↓
Projection Revision 14
    ↓
Revision 13 arrives
    ↓
Revision comparison
    ↓
Update skipped
    ↓
Projection remains Revision 14
```

See the standalone [ordering guarantees diagram](../diagrams/ordering-guarantees.md).

## Run the scenario

```bash
docker compose build
docker compose run --rm lab inventory-sim ordering
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

Revision 14

Projection updated

Projection revision: 14

Revision 13

Older than current projection

Update skipped

Projection revision: 14

Final authority revision: 14

Final projection revision: 14

The projection never moves backward.
```

## Relationship to Chapter 20

Chapter 20 intentionally allowed both distinct requests to overwrite the
projection and ended incorrectly on Revision 13. This chapter reuses that same
reversed delivery. Revision comparison supplies the missing ordering guarantee:
the older request still completes, but cannot replace newer projected state.

## Why this matters

Many production systems maintain correctness by ensuring state progresses
monotonically rather than allowing older information to overwrite newer
information. More sophisticated ordering mechanisms exist, but the educational
rule introduced here captures the essential idea: compare revisions and advance
only toward newer state.

Buffering, distributed clocks, vector or Lamport clocks, consensus algorithms,
networking, databases, randomness, and concurrency remain intentionally deferred.
