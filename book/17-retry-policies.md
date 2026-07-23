# Chapter 17: Retry Policies

## Educational question

> What should happen when a synchronization attempt does not complete successfully?

## Requests, attempts, and completion

A synchronization request says which projection should receive an immutable
authoritative snapshot. An attempt is one try to deliver that request. Keeping
the two concepts separate lets delivery fail without changing inventory business
logic or constructing a different snapshot.

This chapter adds a deliberately small retry policy. It deterministically fails
Warehouse's first attempt and allows its second attempt to succeed. Storefront
and Reporting succeed on their first attempts. No clock time, random value,
network, or external service controls these outcomes, so every run is identical.

Retries improve the chance of delivery, but each extra attempt also creates the
possibility that work will be performed more than once. A successful retry does
not by itself prove that repeated processing is safe.

## Chapter diagram

```text
Revision → Synchronization Request → Attempt 1 → Failure
                                              ↓
                         Success ← Attempt 2 ← Retry
```

See the standalone [retry-policy diagram](../diagrams/retry-policies.md).

## Walkthrough

1. The ledger produces authoritative Revision 10.
2. Fan-out creates one request each for Storefront, Warehouse, and Reporting.
3. The worker performs Storefront Attempt 1 and succeeds.
4. Warehouse Attempt 1 fails as prescribed by the fixed retry policy. Its
   projection is not updated.
5. The scheduler enqueues the **same Warehouse request** again. Reporting's
   already-queued request remains ahead of it in FIFO order.
6. Reporting Attempt 1 succeeds, followed by Warehouse Attempt 2.
7. All projections hold the unchanged Revision 10 snapshot.

The displayed CLI output groups attempts by request so each request's delivery
story is easy to read. The simulator's inspectable event history retains actual
FIFO execution order.

## Run the scenario

```bash
docker compose build
docker compose run --rm lab inventory-sim retries
```

## Expected output

```text
Retry Policies

Revision 10

Storefront
Attempt 1
Success

Warehouse
Attempt 1
Failed

Retry scheduled

Attempt 2
Success

Reporting
Attempt 1
Success

Summary
Requests created: 3
Attempts performed: 4
Retries required: 1
Successful synchronizations: 3
```

## What retries do not solve

This lesson contains no duplicate detection or idempotency. It demonstrates
delivery reliability only: requests remain immutable, attempts are explicit,
and a deterministic policy schedules another attempt after failure.

The resulting challenge belongs to the next chapter:

> How can a system safely process the same request more than once?
