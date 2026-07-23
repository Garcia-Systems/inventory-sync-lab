# Inventory Synchronization Laboratory

![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An executable engineering textbook for learning inventory synchronization and
distributed-systems correctness through small, deterministic Python models.
Volume I comprises Chapters 0–23 and is complete.

## What this project is

The laboratory pairs a written chapter with executable source, a CLI
demonstration, readable tests, and (where useful) a diagram. The prose introduces
one problem at a time; the code makes the claim inspectable; the tests make the
result repeatable. This is the project's **executable textbook** philosophy: do
not merely read about stale state, retries, or ordering—run a controlled example
and observe exactly why it behaves as described.

This project is for software engineers, technical students, educators, and
reviewers who want to build a precise mental model of inventory synchronization.
Basic command-line familiarity helps, but the book assumes neither distributed-
systems expertise nor prior knowledge of this repository.

## What this project is not

This is not a production inventory service, framework, benchmark, or reference
architecture. It deliberately has no networking, database, broker, operating-
system concurrency, or random failures. Those omissions isolate the idea being
taught and make every run reproducible. Read the dedicated [design philosophy](docs/design-philosophy.md)
before interpreting these models as production advice.

## Start here

1. Read [Setting Up Your Laboratory](book/00-setting-up-your-laboratory.md).
2. Build the environment and run the health check below.
3. Follow the [Volume I learning path](docs/learning-path.md) in chapter order.
4. Run each chapter's CLI demonstration as you read it.
5. Use the [documentation index](docs/README.md) whenever you need a map.

### Prerequisites

The supported, lowest-friction route requires Git, Docker, and the modern
`docker compose` plugin. It does **not** require Python on the host. A code editor
is useful for reading the Markdown and Python side by side. Docker may need
network access the first time it downloads the base image and dependencies.

### Install and verify with Docker

From a clone of this repository:

```bash
docker compose build
docker compose run --rm lab inventory-sim doctor
```

The final line from `doctor` should be `Laboratory environment is ready.` The
Compose service installs the package with its development dependencies and
mounts the checkout at `/workspace`.

If you intentionally prefer a host installation, use Python 3.13 or newer:

```bash
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install --editable '.[dev]'
inventory-sim doctor
```

Release artifacts provide the same `inventory-sim` command. To validate or use
a downloaded wheel from a release, install it in a fresh environment (replace
the filename if necessary):

```bash
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install inventory_sync_lab-1.0.0-py3-none-any.whl
inventory-sim doctor
inventory-sim inventory --on-hand 10 --reserved 3
```

The version reported by `doctor` and the distribution metadata both come from
`inventory_sim.__version__`; for the Volume I release they report `1.0.0`.

Docker remains the documented common environment for contributors and CI.

## Run the textbook

The CLI lists every demonstration and its chapter:

```bash
docker compose run --rm lab inventory-sim --help
```

For example, run the early inventory lesson and the Volume I capstone with:

```bash
docker compose run --rm lab inventory-sim inventory --on-hand 10 --reserved 3
docker compose run --rm lab inventory-sim laboratory
```

Every chapter includes its exact command. The complete command-to-chapter table
is in the [learning path](docs/learning-path.md).

## Run the checks

```bash
docker compose run --rm lab pytest
docker compose run --rm lab ruff check .
docker compose run --rm lab ruff format --check .
```

To reproduce CI's branch-coverage report:

```bash
docker compose run --rm lab pytest \
  --cov=inventory_sim \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml
```

Coverage reveals unexercised paths; it is not, by itself, proof of correctness.

## How Volume I progresses

Volume I is intentionally cumulative:

1. **Foundations (Chapters 0–9)** establish inventory, authority, immutable
   history and views, then deterministic time, queues, and worker capacity.
2. **Correctness (Chapters 10–15)** exposes stale observations and adds
   freshness, revisions, stale-update policies, and independent projections.
3. **Reliable Distribution (Chapters 16–22)** adds fan-out, retries, duplicate
   and out-of-order delivery, idempotency, ordering, and dead-letter queues.
4. **Integration (Chapter 23)** composes only the mechanisms already learned
   into one end-to-end operations laboratory.

See the [learning path](docs/learning-path.md) for the rationale, chapter links,
and runnable command for every step.

## Architecture at a glance

An immutable ledger is replayed into authoritative inventory. Immutable
synchronization requests carry revisioned snapshots through deterministic queues
and workers to projections. Retry, idempotency, monotonic ordering, and dead-
letter policies are layered onto that same pipeline one at a time. A virtual
clock and scheduler replace wall-clock timing, so outcomes never depend on
machine speed or scheduling luck.

The [architecture guide](docs/architecture.md) traces each concept to its chapter,
source module, and place in the end-to-end flow.

## Repository map

| Path | Purpose |
| --- | --- |
| [`book/`](book/00-setting-up-your-laboratory.md) | The 24 chapters; read these in order. |
| [`docs/`](docs/README.md) | Learning path, architecture, and project philosophy. |
| [`src/inventory_sim/`](src/inventory_sim/__init__.py) | The executable package and supported root API. |
| [`src/inventory_sim/cli/`](src/inventory_sim/cli/main.py) | CLI registration and chapter-oriented presentation. |
| [`tests/`](tests/test_package.py) | Behavioral and CLI checks written as executable examples. |
| [`diagrams/`](diagrams/end-to-end-operations-laboratory.md) | Focused diagrams linked from chapters and guides. |
| [`experiments/`](experiments/README.md) | Reserved experiment area and its reproducibility rules. |
| [`results/`](results/.gitkeep) | Reserved output area; generated results are not textbook claims. |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to extend the book without breaking its teaching model. |

## Supported Python API

Names exported from `inventory_sim` and listed in `inventory_sim.__all__` are the
supported Volume I Python API. Import core concepts from the package root:

```python
from inventory_sim import InventoryLedger, InventoryState, Receive
from inventory_sim import InventoryProjection, RevisionedProjection
from inventory_sim import EventScheduler, SynchronizationRequest, VirtualClock
```

Internal module paths, CLI implementation details, and future experiment code
are not stable public API. Use `inventory-sim` to invoke demonstrations.

## Contributing and license

Start with the [contributor guide](CONTRIBUTING.md). Changes must preserve the
book's concept order and deterministic learning environment. Garcia Systems may
publish material derived from this project, but this repository is a standalone
open-source educational project and is not part of its Laravel website.

Code and text are available under the [MIT License](LICENSE).
