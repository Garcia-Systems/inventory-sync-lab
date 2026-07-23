# Inventory Synchronization Laboratory v1.0.0 — Release Notes Draft

> **Release operator note:** Use this document as the GitHub Release
> description for tag `v1.0.0`. Remove this note when copying the body. Do not
> create the tag or publish the release until the [release checklist](release-checklist.md)
> is complete.

## Overview

Version 1.0.0 is the first public release of the Inventory Synchronization
Laboratory and completes Volume I (Chapters 0–23). It is an executable
engineering textbook: concise prose, small Python models, deterministic CLI
demonstrations, diagrams, and tests work together to explain why inventory
copies diverge and how explicit synchronization policies address that divergence.

The laboratory is intended for software engineers, technical students,
educators, and reviewers. It is a teaching environment—not a production
inventory service, framework, benchmark, or reference architecture.

## Educational Philosophy

Volume I introduces one problem at a time and makes each claim runnable.
Virtual time, stable ordering, fixed service times, and scripted failures keep
the examples reproducible. The models intentionally omit networking, databases,
brokers, threads, and randomness so infrastructure does not obscure the property
under study.

## Topics Covered

- Inventory state, business events, immutable ledgers, and authoritative truth
- Projections and direct or queued synchronization
- Virtual time, deterministic scheduling, worker capacity, and worker pools
- Snapshot freshness, monotonic revisions, and stale-update policies
- Multiple projections and fan-out distribution
- Retries, duplicate delivery, and idempotent processing
- Out-of-order delivery and ordering guarantees
- Bounded retries and dead-letter queues
- End-to-end composition and operational observations

## Major Concepts

The book distinguishes authoritative state from copied projections, then makes
the movement of revisioned snapshots explicit. Readers can observe queue wait,
service time, staleness, duplicate effects, reordering, retry exhaustion, and
failure isolation without relying on wall-clock timing. Chapter 23 combines
only previously introduced mechanisms into a complete, repeatable operations
laboratory.

## Installation

The recommended environment requires Git, Docker, and the modern Docker Compose
plugin. From a clone of the repository:

```bash
docker compose build
docker compose run --rm lab inventory-sim doctor
```

For a host installation, use Python 3.13 or newer:

```bash
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install --editable '.[dev]'
inventory-sim doctor
```

Published wheel and source archives contain the same `inventory-sim` console
command.

## Getting Started

Begin with [Chapter 0](../book/00-setting-up-your-laboratory.md), then follow the
[Volume I learning path](learning-path.md) in order. Every chapter gives the
exact CLI command for its demonstration. These two commands provide a quick
introduction and the final integrated trace:

```bash
docker compose run --rm lab inventory-sim inventory --on-hand 10 --reserved 3
docker compose run --rm lab inventory-sim laboratory
```

## Highlights of Volume I

- **Progressive:** Twenty-four chapters preserve context and motivate each new
  policy with an observable limitation in the preceding model.
- **Executable:** Every lesson connects prose to inspectable source, a named CLI
  demonstration, and automated tests.
- **Deterministic:** Identical inputs produce identical event order, output, and
  assertions across runs.
- **Navigable:** A learning path, architecture guide, focused diagrams, and
  chapter links provide distinct routes through the same material.
- **Distributable:** The project builds validated wheel and source archives and
  verifies installed-package metadata and console behavior.

## Future Roadmap: Volume II and Beyond

Volume I is intentionally complete at deterministic, in-memory simulation.
Future volumes may explore infrastructure and operational concerns that Volume I
deliberately excludes, but no specific topic, design, or schedule is promised by
this release. Any future work will preserve Volume I as a stable foundation and
introduce new concepts only when their educational motivation is clear.

## Acknowledgements

Thank you to the readers, reviewers, and contributors whose questions and
feedback helped make the explanations, examples, and release process clearer.
The project is maintained by Garcia Systems and released under the MIT License.

For the concise user-visible history, see the [changelog](../CHANGELOG.md).
