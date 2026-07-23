# Release checklist

Use this checklist for `v1.0.0` and later releases. Run commands from a clean
checkout using Python 3.13 or the repository's Docker environment. Do not create
the tag until every applicable check passes.

- [ ] Start from a clean checkout of the intended commit; confirm `git status
      --short` has no output and review the complete diff since the last tag.
- [ ] Confirm `inventory_sim.__version__`, the planned tag, and release notes use
      the same semantic version.
- [ ] Run formatting: `docker compose run --rm lab ruff format --check .`.
- [ ] Run linting: `docker compose run --rm lab ruff check .`.
- [ ] Run tests and branch coverage: `docker compose run --rm lab pytest
      --cov=inventory_sim --cov-branch --cov-report=term-missing
      --cov-report=xml:coverage.xml`.
- [ ] Confirm the coverage report exists: `test -s coverage.xml`.
- [ ] Build the source and wheel distributions and validate their metadata:
      `rm -rf dist build && python -m build && python -m twine check dist/*`.
- [ ] Run `./scripts/validate-distributions.sh` to inspect the source archive,
      install the wheel and source distribution, compare installed metadata with
      the runtime version, and exercise the installed console script.
- [ ] Review README installation commands, links, release notes, and rendered
      documentation for the release version.
- [ ] From the verified commit, create an annotated tag: `git tag -a vX.Y.Z -m
      "Inventory Synchronization Laboratory vX.Y.Z"`, then push it with `git
      push origin vX.Y.Z`.
- [ ] Publish a GitHub Release from that tag, attach both files from `dist/`, and
      verify their names and checksums before announcing the release.

Tag creation and GitHub Release publication are release-day actions, not pull
request validation steps.
