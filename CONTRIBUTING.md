# Contributing

Thank you for helping make the laboratory clearer and more useful. Begin with
the [documentation index](docs/README.md), [learning path](docs/learning-path.md),
and [design philosophy](docs/design-philosophy.md). They define the educational
contract that contributions must preserve.

## Principles

- **The guide drives the code.** Do not introduce a concept or abstraction before
  the relevant chapter explains why it exists.
- Teach **one concept per chapter** and keep pull requests similarly focused.
- Prefer straightforward, readable code over clever code; examples are teaching
  material, not merely implementation details.
- Preserve deterministic behavior: explicit inputs, virtual time, stable order,
  fixed service times, and scripted failures.
- Add simple automated tests with every new behavior or correction.
- Experiments and generated results must be reproducible. Never fabricate a
  metric, measurement, or observation.

## Adding a future chapter

Future chapters must extend the progression rather than revise Volume I history
to foreshadow them. Before proposing one:

1. State one educational question and explain why the previous chapter leaves it
   unanswered.
2. Add prose that introduces the concept before its implementation is required.
3. Model the smallest deterministic scenario that demonstrates the concept. Do
   not add networking, databases, brokers, `asyncio`, threads, or randomness as
   incidental realism.
4. Add a named CLI demonstration so readers can reproduce the lesson without
   writing a driver program.
5. Add readable automated tests for the model and representative CLI output.
6. Add or update a simple diagram only when it clarifies causality, ownership, or
   flow. Match existing labels and direction; avoid decorative artwork.
7. Update the learning path, architecture guide, documentation index if needed,
   and adjacent chapter links so the reader has a clear next step.
8. Run every command printed in the new prose and the complete validation suite.

If a proposed mechanism needs nondeterministic infrastructure to be meaningful,
it belongs in the future volume that teaches that infrastructure—not hidden in
an earlier example.

## Documentation and diagrams

Write for a reader with no repository context. Define a term before abbreviating
it, distinguish simulated behavior from production guarantees, and use relative
Markdown links. Avoid copying the same chapter list into multiple pages: the
[learning path](docs/learning-path.md) is the canonical chapter index, while the
[architecture guide](docs/architecture.md) is the canonical concept map.

Diagrams should express only what their chapter claims. Use a consistent
top-to-bottom or left-to-right flow, label policy branches, and include a short
paragraph stating what the diagram does *not* imply when ambiguity is possible.

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

Update prose alongside code and verify every command a reader is asked to run.
Use coverage to notice untested paths, not as a percentage to optimize blindly.

## Extending the command-line interface

The CLI follows the [four-part learning progression](docs/learning-path.md):

- `cli/foundations.py` presents Chapters 0–9;
- `cli/correctness.py` presents Chapters 10–15;
- `cli/reliability.py` presents Chapters 16–22;
- `cli/integration.py` presents Chapter 23;
- `cli/common.py` owns shared registration helpers; and
- `cli/main.py` composes the parser and executes handlers.

Put a future command's output handler in its educational area, then add one
declarative `CommandSpec` to `COMMANDS` in `main.py`. Register command arguments
near the other argument-bearing parsers in `build_parser`. Once published,
preserve names, help text, defaults, output, and exit codes. Keep simulation
logic in its chapter module rather than in the CLI layer.

## Pull request checklist

- [ ] The change has a stated purpose and stays within its educational or
      maintenance scope.
- [ ] Simulation inputs and ordering remain deterministic.
- [ ] The chapter, CLI demonstration, tests, and relevant docs agree.
- [ ] Any diagram supports the lesson without implying extra behavior.
- [ ] Relative documentation links resolve.
- [ ] All documented commands and development checks pass.

Return to the [README](README.md) for installation and repository navigation.
