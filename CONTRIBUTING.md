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
docker compose run --rm lab ruff check .
docker compose run --rm lab ruff format --check .
docker compose run --rm lab pytest \
  --cov=inventory_sim \
  --cov-branch \
  --cov-report=term-missing
```

Update the relevant prose alongside code, and verify every command a reader is asked to run.

New functionality should normally include tests that check its behavior. Use
coverage to notice untested paths, not as a percentage to optimize blindly. Review
coverage changes in context, and justify any exclusion based on behavior that
cannot usefully be measured—not merely because the exclusion raises the reported
percentage.
