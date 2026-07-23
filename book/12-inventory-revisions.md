# Chapter 12 — Inventory Revisions

## Educational question

> How can two inventory states be placed into chronological order?

## Explanation

Quantity cannot answer that question reliably. Inventory can decrease and later
increase to a value seen before, and even identical operations can leave the same
quantity at several moments. A comparison of `available` values therefore says
nothing conclusive about which observation came first.

An **inventory revision** is the positive position of a state in ledger history.
This laboratory derives revisions deterministically from replay: the state after
the first event has Revision 1, the state after the second has Revision 2, and so
on. The immutable revision value expresses ordering independently of inventory
quantity. A greater revision is later in this one ledger's history; it is not a
claim that the state is correct or acceptable.

## Deterministic walkthrough

The scenario replays three ledger prefixes:

1. `Receive 10` produces available quantity 10 at Revision 1.
2. `Reserve 3` produces available quantity 7 at Revision 2.
3. `Receive 3` produces available quantity 10 at Revision 3.

Revision 1 and Revision 3 report identical available inventory. Their revisions,
not their quantities, reveal that Revision 3 is newer.

The scenario then creates an ordinary `SynchronizationRequest` for each observed
state and copies each snapshot to the website projection in order. Those requests
behave exactly as in earlier chapters. Revisions are observations alongside the
states: they do not cause acceptance, rejection, comparison, or retry.

## CLI instructions and expected output

Run the Docker-first demonstration:

```console
docker compose run --rm lab inventory-sim revisions
```

The deterministic table is:

```text
Revision    Available
---------------------
1           10
2           7
3           10
```

The command explains that Revision 3 is newer than Revision 1 even though both
report 10 available units. It deliberately does not label either state stale or
fresh and does not compare a revision with a projection.

## Chapter diagram

See [the inventory-revisions diagram](../diagrams/inventory-revisions.md). The
vertical path describes chronology rather than a synchronization decision.

## Relationship to Chapters 10 and 11

Chapter 10 showed that a request can copy an earlier snapshot after authority has
changed. Chapter 11 measured the age of such information using simulated time.
Chapter 12 adds a different fact: the relative order of states in ledger history.
Age and revision can both describe history, but neither establishes correctness
or supplies synchronization policy.

## Limitations

Revisions here are local positive ledger positions. The model has one in-memory
ledger and deterministic replay. It has no global identifiers, timestamps,
databases, networks, distributed clocks, version vectors, conflict resolution,
optimistic concurrency, retries, duplicate handling, or freshness validation.
Empty history has no revision because no inventory event has yet produced an
observation.

## Why this matters

Engineers often need ordering information because quantities alone cannot reveal
which inventory state is more recent. Revisions provide that information without
dictating policy. Future chapters will decide how the information is used; this
chapter only makes chronological order explicit.
