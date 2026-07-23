# Chapter 11 — Measuring Freshness

## Educational question

> Once a synchronization request becomes stale, how can we describe *how stale* it is?

## Explanation

Chapter 10 showed a successful request copying an obsolete snapshot. This chapter
adds observation without changing that behavior. An immutable freshness observation
records request creation and completion times, current simulated time, queue wait,
worker service time, whether authority changed after capture, and snapshot age.

Here, **snapshot age** is the elapsed simulated time from the first authority change
missed by the captured snapshot until synchronization completion. If no authority
change was missed, its age is zero. This is a timing measurement, not an assessment
of whether the result is acceptable. Freshness and correctness answer different
questions: a faithfully copied snapshot can be correct relative to its request and
still be old relative to current authority.

## Deterministic walkthrough

All three requests capture immutable inventory states and use one worker with a
three-tick service time:

1. At time 0, A is captured and starts. It completes at time 3 before authority
   changes, so its measured age is 0.
2. At time 1, B and C are captured and queued.
3. At time 4, authority changes. B completes at time 6 after waiting two ticks;
   the first missed change is two ticks old.
4. At time 7, authority changes again. C completes at time 9 after waiting five
   ticks. Its snapshot has missed changes since time 4, so its age is five ticks.

The scheduler, queue, worker, registry, requests, work items, ledger, and inventory
states are the same deterministic building blocks used in earlier chapters.

## CLI instructions and expected output

Run the Docker-first demonstration:

```console
docker compose run --rm lab inventory-sim freshness
```

The chronological narration ends with values produced by the simulation:

```text
Request    Wait    Service    Snapshot Age
-------------------------------------------
A          0       3          0
B          2       3          2
C          5       3          5
```

Increasing queue delay gives later work more opportunity to miss authority changes.
It does not guarantee staleness: only the deterministic authority timeline determines
whether a particular snapshot actually becomes stale. Worker service time also
contributes because authority can change during processing.

## Chapter diagram

See [the measuring-freshness diagram](../diagrams/measuring-freshness.md). It follows
capture through waiting and processing to completion, then adds an observation. It
contains no decision or enforcement step.

## Relationship to Chapter 10

Chapter 10 establishes that successful synchronization can use obsolete input.
Chapter 11 leaves that pipeline intact and quantifies how long the input has been
outdated when completion occurs. Nothing rejects or modifies a request.

## Limitations

This laboratory uses virtual integer ticks, a fixed service time, one in-memory
authority, and predetermined events. It has no networking, database, randomness,
threads, policies, retries, validation, or corrective behavior. The observation
describes only this simulated timeline.

## Why this matters

Production monitoring systems often measure latency, queue time, and age of
information before implementing mechanisms to reduce them. The first step toward
improving a distributed system is learning how to observe it. Later chapters can
build on these measurements; this chapter only makes them visible.
