# Chapter 13 — Detecting Stale Synchronizations

## Educational question

> How can we recognize that a synchronization request is carrying an older inventory revision?

## Explanation

A request is stale when its captured revision is less than the current authoritative revision. `StaleDetection` is the smallest observation needed to state that fact: it records the request revision, authority revision, and Boolean result. It contains no instruction about what the worker should do.

Detection and policy are deliberately separate. A worker can know that its work is stale and still perform the same snapshot copy introduced earlier. This chapter observes; it does not reject, replace, or retry anything.

## Deterministic walkthrough

1. At time 1, Request A captures authority at Revision 2.
2. At time 2, authority advances to Revision 4.
3. At time 3, Request B captures Revision 4.
4. At time 4, two workers begin the queued requests in deterministic order.
5. Worker 1 compares 2 with 4 and observes that A is stale. Worker 2 compares 4 with 4 and observes that B is current.
6. Both workers continue. At time 6 both requests complete and update their projections from their captured snapshots.

The website receives Revision 2's quantity even though its request was identified as stale. Synchronization behavior has not changed.

## CLI instructions and expected output

Run the Docker-first demonstration:

```console
docker compose run --rm lab inventory-sim detect-stale
```

The central inspections are:

```text
Worker: worker-1

Request revision: 2
Authority revision: 4

Stale request: YES

Continuing synchronization...

Worker: worker-2

Request revision: 4
Authority revision: 4

Stale request: NO

Continuing synchronization...
```

The command then reports that both synchronizations complete. `YES` is an observation, not a refusal.

## Chapter diagram

See [the detecting-stale diagram](../diagrams/detecting-stale.md). Its final arrow is important: synchronization still proceeds after the stale observation.

## Relationship to Chapters 10–12

Chapter 10 demonstrated an old snapshot successfully updating a projection. Chapter 11 measured how long snapshots waited and aged. Chapter 12 introduced revisions as ordering information without classifying requests. Chapter 13 uses that ordering information for the first classification: an older request revision is stale. It still adds no processing policy.

## Limitations

This deterministic, in-memory model has one ledger, two workers, and fixed simulated service time. Revisions are local ledger positions. There are no databases, networks, real concurrency, random delays, global clocks, duplicate handling, optimistic concurrency, conflict resolution, retries, or rejection. Equality means only that the compared revisions match; it is not a general proof that distributed data is correct.

## Why this matters

Many distributed systems first detect stale work before deciding what action to take. Detection provides information; policy turns information into a decision. Keeping them separate makes both concepts visible and testable. The next chapter will finally introduce a policy decision.
