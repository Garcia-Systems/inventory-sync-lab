# Contributing

Thank you for helping make the laboratory clearer and more useful.

## Principles

- **The guide drives the code.** Do not introduce a concept or supporting abstraction before the relevant chapter explains it.
- Prefer straightforward, readable code over clever code. Examples are teaching material.
- Add simple tests with every new behavior or correction.
- Keep each pull request focused on one chapter or one concept.
- Experiments and generated results must be reproducible. Never fabricate a metric, measurement, or observation.

## Development checks

Use the documented Docker environment rather than relying on host Python tools:

```bash
docker compose build
docker compose run --rm lab pytest
docker compose run --rm lab ruff check .
docker compose run --rm lab ruff format --check .
```

Update the relevant prose alongside code, and verify every command a reader is asked to run.
