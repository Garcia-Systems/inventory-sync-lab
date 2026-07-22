# Inventory Synchronization Laboratory

![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An executable engineering textbook for learning deterministic inventory synchronization.

This repository is **education-first**: the written guide introduces each idea before code implements it. Explanations, small Python programs, tests, and eventually reproducible experiments will work together so readers can inspect every claim.

## Current status

- Chapter 0: Laboratory setup — **complete**
- Chapter 1: What is inventory? — **complete**
- Chapter 2: Authoritative source of truth — **complete**
- Chapter 3: The inventory ledger — **complete**
- Chapter 4: Inventory projections — **complete**
- Chapter 5: Time and Events — **complete**

Next: **Chapter 6 — Direct Synchronization**

The laboratory now records inventory events and derives current inventory by
replaying an immutable ledger. Projections can be compared with that authority
and manually refreshed, but refreshes are not automatic. Deterministic integer
time and generic event scheduling now exist without real waiting. Automatic
inventory synchronization, queues, workers, retries, and failures are not
implemented. Start with
[Setting Up Your Laboratory](book/00-setting-up-your-laboratory.md), continue to
[What Is Inventory?](book/01-what-is-inventory.md), and then read
[The Authoritative Source of Truth](book/02-authoritative-source-of-truth.md).
Then read [The Inventory Ledger](book/03-the-inventory-ledger.md) and
[Inventory Projections](book/04-projections.md), followed by
[Time and Events](book/05-time-and-events.md).

## Quick start

Docker is the default development environment. From the repository root:

```bash
docker compose build
docker compose run --rm lab inventory-sim doctor
docker compose run --rm lab inventory-sim demo
docker compose run --rm lab inventory-sim inventory \
  --on-hand 10 \
  --reserved 3
docker compose run --rm lab inventory-sim authority
docker compose run --rm lab inventory-sim ledger
docker compose run --rm lab inventory-sim projections
docker compose run --rm lab inventory-sim timeline
docker compose run --rm lab pytest
docker compose run --rm lab pytest \
  --cov=inventory_sim \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml
docker compose run --rm lab ruff check .
docker compose run --rm lab ruff format --check .
```

pytest measures coverage of the application package; the report shows what the
current tests exercised without claiming that the test suite is complete. CI runs
these checks through Docker on pushes and pull requests. Codecov requires the
repository owner to add one `CODECOV_TOKEN` Actions secret and may show no result
until the first successful CI upload.

## Repository map

- `book/` contains the chapters that drive development.
- `src/inventory_sim/` contains executable Python introduced by the book.
- `tests/` contains readable checks for the examples and CLI.
- `diagrams/` holds explanatory diagrams.
- `experiments/` and `results/` are reserved for later, reproducible work.

## Education and contributions

Keep changes focused, readable, tested, and aligned with the chapter that introduces them. See [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change.

Garcia Systems may publish material derived from this project. This repository is nevertheless a standalone open-source educational project; it is not part of the Garcia Systems Laravel website.

## License

The code and text in this repository are available under the [MIT License](LICENSE).
