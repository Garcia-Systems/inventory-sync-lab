# Chapter 19: Idempotent Synchronization

## Educational question

> How can a synchronization request be safely processed more than once?

## Duplicate delivery without duplicate effects

Duplicate delivery is expected in reliable systems. Preventing every duplicate
would require machinery outside this laboratory and would also work against the
retry behavior introduced in Chapter 17. Instead, the handler makes applying a
request **idempotent**: executing it repeatedly has the same final projection
state as executing it once.

An immutable synchronization request now has a deterministic positive request
identifier. Each projection has an in-memory `AppliedRequestRegistry`. Before a
worker applies a request, the registry checks that request identifier for that
target projection. The first successful application records the identifier.
Later deliveries are still received and processed, but their projection update
is skipped. This small teaching mechanism deliberately uses no database,
network, distributed lock, or global message store.

## Chapter diagram

```text
Synchronization Request 57
           │
    ┌──────┼──────┐
    ▼      ▼      ▼
Delivery Delivery Delivery
   1        2        3
   │        │        │
   ▼        ▼        ▼
 Update   Ignore   Ignore

     Projection changed once
```

See the standalone [idempotent-synchronization diagram](../diagrams/idempotent-synchronization.md).

## Deterministic walkthrough

1. Twelve ledger events advance the authority to Revision 12.
2. The simulator creates immutable Synchronization Request 57.
3. Three FIFO work items carry the exact same request object.
4. The `EventScheduler` and one-worker `WorkerPool` process all three deliveries.
5. Delivery 1 is not in the applied-request registry, so it updates the
   projection and records Request 57.
6. Deliveries 2 and 3 find Request 57 already recorded. Both complete normally,
   while the projection object and state remain unchanged.
7. The final counts are three received and processed deliveries, but one
   projection update. Repeating the scenario always produces the same result.

The authoritative inventory changes only during the ledger setup. Duplicate
delivery never creates another business event and never advances the authority.

## Run the scenario

```bash
docker compose build
docker compose run --rm lab inventory-sim idempotency
```

## Expected output

```text
Authority Revision 12

Synchronization Request 57

Delivery 1

Result:
Projection updated.

Delivery 2

Result:
Already applied.

Projection unchanged.

Delivery 3

Result:
Already applied.

Projection unchanged.

Summary

Deliveries: 3

Projection updates: 1
```

## Relationship to Chapters 17–18

Chapter 17 showed why retries reuse the same immutable request. Chapter 18 then
made duplicate delivery visible by applying one request twice, producing two
effects. This chapter retains both properties: retries and duplicate deliveries
remain allowed, and every delivery is processed. The new applied-request check
removes only the repeated effect.

## Why this matters

Many reliable distributed systems intentionally allow duplicate delivery
because idempotent handlers make repeated execution safe. A sender can retry
when an outcome is uncertain rather than risk losing work. The consumer may see
the request again, but recognizing its stable identity ensures that the desired
projection state is produced once and remains correct after every repetition.
