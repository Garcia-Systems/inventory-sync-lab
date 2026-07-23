# Documentation Index

This index is the shortest route into the Inventory Synchronization Laboratory.
The [project README](../README.md) explains what the project is and how to install
it; this directory explains how to study and interpret it.

## Read in this order

1. **[Learning path](learning-path.md)** — the recommended Volume I progression,
   with every chapter and CLI command.
2. **[Design philosophy](design-philosophy.md)** — why the laboratory uses plain,
   deterministic simulations instead of production infrastructure.
3. **[Architecture](architecture.md)** — how the ledger, authority, projections,
   delivery mechanisms, and correctness policies accumulate.
4. **[Chapter 0](../book/00-setting-up-your-laboratory.md)** — set up the common
   Docker environment, then begin reading.

## Find a project area

- [Book chapters](../book/00-setting-up-your-laboratory.md)
- [Diagrams](../diagrams/end-to-end-operations-laboratory.md)
- [Source package](../src/inventory_sim/__init__.py)
- [CLI implementation](../src/inventory_sim/cli/main.py)
- [Tests](../tests/test_package.py)
- [Experiments policy](../experiments/README.md)
- [Contributor guide](../CONTRIBUTING.md)
- [Release notes for v1.0.0](release-notes-v1.0.0.md)
- [Changelog](../CHANGELOG.md)
- [Release checklist](release-checklist.md)

After the architecture overview, continue to the [end-to-end laboratory](../book/23-end-to-end-operations-laboratory.md)
to see the complete Volume I model run.
