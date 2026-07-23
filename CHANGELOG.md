# Changelog

This file records user-visible changes to the Inventory Synchronization
Laboratory. The project follows [Semantic Versioning](https://semver.org/).

## 1.0.0 — 2026-07-23

The first public release completes Volume I, an executable textbook comprising
Chapters 0–23.

### Highlights

- A cumulative learning path from inventory fundamentals and authoritative
  state through deterministic queues, workers, and synchronization.
- Correctness lessons covering stale snapshots, freshness, revisions, stale
  update policies, and multiple projections.
- Reliable-delivery models for fan-out, retries, duplicate and out-of-order
  delivery, idempotency, ordering guarantees, and dead-letter queues.
- An end-to-end operations laboratory that composes the Volume I mechanisms in
  one deterministic trace.
- A chapter-oriented `inventory-sim` CLI, supported Python API, diagrams, and
  readable automated tests for exploring every lesson.
- Reproducible Docker development, Python package distributions, branch
  coverage, and release-candidate validation.
