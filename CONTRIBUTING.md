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

## Extending the command-line interface

The CLI is organized by the educational progression rather than as one module:

- `inventory_sim/cli/foundations.py` presents Chapters 0–9: environment setup,
  inventory fundamentals, deterministic time, queues, and workers.
- `inventory_sim/cli/correctness.py` presents Chapters 10–15: freshness,
  revisions, stale-work policy, and independent projections.
- `inventory_sim/cli/reliability.py` presents Chapters 16–22: distribution,
  retries, duplicate and out-of-order delivery, idempotency, ordering, and the
  dead-letter queue.
- `inventory_sim/cli/integration.py` presents the Chapter 23 end-to-end
  laboratory.
- `inventory_sim/cli/common.py` owns shared registration types and helpers, and
  `inventory_sim/cli/main.py` composes the parser and executes handlers.

When a future volume adds a command, put its output handler in the module for
that educational area, then add one declarative `CommandSpec` to `COMMANDS` in
`main.py`. Commands with arguments should register those arguments next to the
other argument-bearing parsers in `build_parser`. Preserve command names, help
text, defaults, output, and exit codes once published. Add a CLI test that
checks registration and representative lesson output; keep simulation logic in
its chapter module rather than in the CLI layer.
