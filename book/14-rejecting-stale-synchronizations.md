# Chapter 14 — Rejecting Stale Synchronizations

## Educational question

> Should an older inventory snapshot overwrite a newer projection?

No. Once a worker can detect stale work, the system can adopt a policy that
prevents that work from changing a projection. Detection remains an observation;
rejection is the deliberate response chosen in this chapter.

## The rejection policy

When a worker begins a request, it compares the request's immutable
`InventoryRevision` with the current authoritative revision. A smaller revision
is stale. The worker records a rejection and later completes normally without
replacing the projection. An equal revision is accepted and follows the existing
projection-update path.

Only the update is conditional. Starting still removes the request from the FIFO
queue, completion still occurs after the fixed service time, and each worker
becomes idle. This makes an important outcome explicit: successful worker
execution need not imply that data was written.

The immutable inspection record contains the simulated time, worker, request and
authority revisions, stale flag, projection-update decision, and—only for a
rejection—a short reason. It contains no retry or delivery metadata.

## Deterministic walkthrough

The scenario starts with authoritative Revision 4. The website projection
already reflects Revision 4, while the marketplace projection is older.

1. At time 1, Request A arrives with the Revision 2 snapshot.
2. At time 2, the timeline states that authority has advanced to Revision 4.
3. At time 3, Request B arrives with the Revision 4 snapshot.
4. At time 4, deterministic worker assignment gives A to `worker-1` and B to
   `worker-2`.
5. Worker 1 observes `2 < 4`, rejects A, and leaves the current website
   projection untouched.
6. Worker 2 observes `4 == 4`, accepts B, and refreshes marketplace.
7. At time 6 both workers complete and the queue is empty.

The ordering, assignment, comparison, and final states are identical on every
run. See the [chapter diagram](../diagrams/rejecting-stale.md).

## Run the simulation

Docker remains the default environment:

```bash
docker compose run --rm lab inventory-sim reject-stale
```

## Expected output

```text
Rejecting Stale Synchronizations

Time 1 — Request A captures Revision 2.
Time 2 — Authority advances to Revision 4.
Time 3 — Request B captures Revision 4.
Time 4 — Workers begin processing.

Worker: worker-1

Request revision: 2
Authority revision: 4

Result: REJECTED

Reason: request revision is older than authority.
Projection unchanged.

Worker: worker-2

Request revision: 4
Authority revision: 4

Result: ACCEPTED

Projection updated.

Time 6 — Both workers complete normally.

Summary
Accepted requests: 1
Rejected requests: 1
Final authoritative revision: 4
Final projection revision: 4
```

## Relationship to Chapters 10–13

- Chapter 10 showed that a queued snapshot can become obsolete.
- Chapter 11 measured the time that allows freshness to decay.
- Chapter 12 introduced revisions so state can be ordered independently of its
  quantities.
- Chapter 13 compared revisions and reported staleness, but intentionally
  updated every projection.
- Chapter 14 keeps that detection and adds one policy: stale requests do not
  update projections.

## Limitations

This laboratory still has no database, network, random timing, threads,
`asyncio`, failures, retries, duplicate-delivery handling, idempotency,
optimistic concurrency, locks, or distributed coordination. The authority is
fixed at the comparison boundary, revisions are totally ordered, and the policy
handles only revisions older than authority. These constraints keep one concept
visible; they are not a complete production design.

## Why this matters

Many production synchronization systems avoid overwriting newer information
with obsolete snapshots. Discarding work can preserve freshness more reliably
than faithfully applying every request.

The policy here is intentionally simple. It establishes that detection and
response are separate decisions and prepares readers for future chapters about
retries, duplicate delivery, and idempotency.
