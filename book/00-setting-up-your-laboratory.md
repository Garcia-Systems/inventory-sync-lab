# Setting Up Your Laboratory

This chapter prepares a consistent place to read, run examples, and check your work. You do not need prior Docker or Python experience. We will verify the tools carefully before later chapters add any subject-matter code.

## 1. The purpose of the laboratory

Engineering ideas become easier to understand when you can run them, change them, and observe the result. This repository pairs a written textbook with Python examples and automated checks. The laboratory is the development environment in which those parts run together.

For now, the goal is deliberately modest: start the environment and prove that its Python package and command-line program work. There is no inventory simulator in Chapter 0.

## 2. What you will build

Over the course of the book, you will grow a small, executable teaching project. Future chapters will introduce concepts one at a time, explain why they are needed, implement them in plain Python, and verify them with tests and reproducible observations.

The guide drives the code. We will not build future mechanisms early, even as empty abstractions. This keeps each code change connected to an explanation you have already read.

## 3. Why this project uses Docker

A Python program depends on more than source code: it also depends on a Python version and development tools. Installing those directly on every reader's computer can produce different behavior and difficult setup instructions.

Docker builds a project-specific image from the repository's `Dockerfile`. Docker Compose gives that image the short service name `lab` and supplies the development settings. The same commands therefore work on Linux, macOS, and Windows systems supported by Docker.

## 4. What Docker does—and does not do

Docker provides the Python interpreter, installs the package and development tools, and runs commands in an isolated container. Compose mounts your checkout into `/workspace`, so the container sees edits made in your editor.

Docker does **not** provide a database, message broker, external API, or background service here. It does not hide the source in the image during development, and it does not replace Git or your editor. The Chapter 0 commands require no internet after the image has been built.

## 5. Required host tools

Install these tools on your computer:

- **Git**, to obtain and update the repository;
- **Docker**, to build and run the environment;
- **Docker Compose**, available as the `docker compose` command in current Docker installations; and
- a **code editor**, to read and change Markdown and Python files.

You do not need host Python, `pip`, pytest, or Ruff. Confirm the essential command-line tools before continuing:

```bash
git --version
docker --version
docker compose version
```

Each command should print a version. If Docker reports that its daemon is unavailable, start Docker Desktop or your system's Docker service.

## 6. Clone the repository

Cloning asks Git to make a local copy. Replace `<repository-url>` with the HTTPS or SSH URL provided by the project host, then enter the new directory:

```bash
git clone <repository-url> inventory-sync-lab
cd inventory-sync-lab
```

Run all remaining commands from this repository root—the directory containing `compose.yaml`.

## 7. Build the container

The build reads `Dockerfile`, downloads the Python base image if necessary, and installs the project with its testing and formatting tools. The first build may take a little time and requires network access:

```bash
docker compose build
```

Later builds reuse cached work when their inputs have not changed. Rebuild after changing dependency or image configuration.

## 8. Check the laboratory

The `doctor` subcommand imports the package and prints the Python and package versions. It performs local checks only. `docker compose run` creates a temporary container for the `lab` service, while `--rm` removes that container when the command finishes:

```bash
docker compose run --rm lab inventory-sim doctor
```

Successful output ends with:

```text
Laboratory environment is ready.
```

The command's success exit status also allows scripts and automated systems to use the check.

## 9. Run the demonstration

The `demo` subcommand is a harmless Chapter 0 smoke test. It proves that a second CLI command can run, but intentionally performs no simulation:

```bash
docker compose run --rm lab inventory-sim demo
```

The message confirms the environment is functioning and clearly says that the simulator has not yet been implemented.

## 10. Run the tests

pytest discovers readable test functions under `tests/`. These checks import the package, call both commands, and invoke the package through Python's `-m` entry point:

```bash
docker compose run --rm lab pytest
```

A passing run ends with a count of passed tests. A failure includes the test name and the differing result so you can investigate it.

## 11. Run tests with coverage locally

Coverage records which application code the tests exercise. Run the same coverage
command used by continuous integration:

```bash
docker compose run --rm lab pytest \
  --cov=inventory_sim \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml
```

**Statement coverage** describes how many measured statements ran. **Branch
coverage** also checks the different outcomes of decisions, such as both the true
and false paths of an `if`. The `term-missing` report prints uncovered line numbers
in the terminal. `coverage.xml` contains the same measurements in a structured
format that reporting tools can read.

The Compose source mount writes `coverage.xml` into the host checkout. It is a
transient result, so Git ignores it: each test run should generate a fresh report
instead of committing a machine-generated snapshot. To explore a browsable local
report explicitly, replace or supplement the XML option with
`--cov-report=html`; open `htmlcov/index.html` after the run.

## 12. GitHub Actions

GitHub Actions runs the same Docker-based checks whenever code is pushed to
`main`, a pull request targets `main`, or an owner starts the workflow manually.
The workflow builds the development image, then verifies formatting, linting,
tests, coverage generation, and the health of both CLI commands. A failing command
stops the job and clearly marks the check as failed.

Running the checks in Docker matters: contributors and CI use the environment
defined by this repository rather than relying on different host Python setups.

## 13. What Codecov does

Codecov does **not** run this project's tests. GitHub Actions runs pytest and
creates `coverage.xml`; Codecov receives that report, stores coverage history, and
presents coverage changes on commits and pull requests.

A coverage percentage does not prove that software is correct. It only says which
measured statements and branches were exercised. Useful tests check meaningful
behavior rather than chasing a percentage.

## 14. Required Codecov setup for the repository owner

The committed configuration cannot create or reveal a repository token. An owner
must complete these steps:

1. Install or authorize the Codecov GitHub App for this repository.
2. Add or activate the repository in Codecov.
3. Copy the repository upload token from Codecov.
4. Open the repository on GitHub.
5. Go to **Settings → Secrets and variables → Actions**.
6. Create a repository secret named `CODECOV_TOKEN`.
7. Paste the upload token as the secret value.
8. Push a commit or manually run the **Continuous Integration** workflow.
9. Verify the upload in both the GitHub Actions log and Codecov.

GitHub masks secret values in logs. Masking is a safety feature, not permission to
share a token: never put the token in source code, documentation, command output,
or a commit. Forked pull requests normally cannot access repository secrets, so
their project checks run but their Codecov upload is intentionally skipped.

## 15. Check linting and formatting

Ruff performs two related jobs. Its linter finds selected correctness and consistency problems:

```bash
docker compose run --rm lab ruff check .
```

Its formatter check reports files whose layout differs from the project's standard, without changing them:

```bash
docker compose run --rm lab ruff format --check .
```

Contributors should run both checks and pytest before proposing a change. To format files deliberately, run `docker compose run --rm lab ruff format .` and review the edits.

## 16. Tour of the repository

```text
book/                 textbook chapters
diagrams/             future explanatory images
experiments/          future reproducible experiment definitions
results/              future reproducible outputs
src/inventory_sim/    the installable Python package and CLI
tests/                executable checks for current behavior
.github/workflows/    GitHub Actions workflow definitions
Dockerfile            recipe for the development image
compose.yaml          development service and source mount
pyproject.toml        package metadata, tools, and CLI entry point
codecov.yml            Codecov status and comment policy
README.md             project overview and quick start
CONTRIBUTING.md        contribution principles and checks
LICENSE                open-source license
```

The empty directories contain `.gitkeep` files because Git does not otherwise record empty directories. They reserve obvious homes for material only when later chapters introduce it.

## 17. How source mounting works

The image contains Python and installed tools. When Compose starts `lab`, this entry in `compose.yaml` maps the current host directory to `/workspace`:

```yaml
volumes:
  - .:/workspace
```

If you edit `src/inventory_sim/cli.py` on the host, the next container command immediately reads that edit. You generally do not need to rebuild for source or test changes. Rebuild when `Dockerfile` or project dependencies change. Files created inside `/workspace` can appear in your host checkout because it is the same mounted directory.

Development tools keep their disposable caches under the container's temporary
directory rather than in the mounted checkout. Compose uses the host user and group
IDs when they are provided, so generated outputs such as `coverage.xml` remain
writable on Linux and in CI without running the container as root.

## 18. Common setup and CI problems

### `docker: command not found`

Docker is not installed or is not on your shell's path. Install a current Docker distribution, open a new terminal, and retry `docker --version`.

### Cannot connect to the Docker daemon

The Docker client is present but the engine is not running. Start Docker Desktop or the Docker service. On Linux, also follow Docker's official post-install guidance if your account lacks permission to use Docker.

### `docker compose` is not recognized

Your installation may be old or may lack the Compose plugin. Install the current Compose plugin. This book uses `docker compose` (with a space), not the legacy `docker-compose` command.

### The image cannot download packages

The initial build needs network access to fetch the base image and development packages. Check connectivity, proxy configuration, and registry access, then rerun `docker compose build`.

### A command cannot find `compose.yaml`

Check your location with `pwd` (or `cd` without arguments as appropriate for your shell) and change into the repository root before running Compose.

### Source edits do not appear

Confirm you used `docker compose run --rm lab ...`, not an unrelated container, and that the checkout is permitted in Docker Desktop's file-sharing settings. The Compose mount should map the repository to `/workspace`.

### Generated files have awkward ownership

The image uses a non-root user with a common user ID. Host configurations vary, particularly on Linux. Remove an unwanted generated file from the host, or adjust the development user mapping locally; do not run broad permission-changing commands without understanding their effect.

### `coverage.xml` was not created

Run the complete coverage command from the repository root and include
`--cov-report=xml:coverage.xml`. Check that pytest succeeded; a failed test command
may not produce a usable report.

### The Codecov step was skipped or the token is missing

The upload runs only when the `CODECOV_TOKEN` repository secret is nonempty. An
owner should complete the manual setup above. A forked pull request cannot normally
receive this secret, so a skipped upload there is expected and does not skip the
project checks.

### Codecov reports “no coverage reports found”

Check that the pytest step created a nonempty `coverage.xml` in the repository root
and that the workflow still uploads `./coverage.xml`. The workflow has a separate
file check to make this problem visible before upload.

### CI passes but no Codecov status appears

Confirm that an authenticated upload actually ran and succeeded. Codecov may have
nothing to display before the first successful upload; also verify that the
repository is active in Codecov and that the Codecov GitHub App is authorized for
it.

### The Codecov GitHub App has not been authorized

Ask a repository owner to install or authorize the app for this repository, then
rerun CI. A token upload alone does not guarantee that Codecov can publish GitHub
checks and pull-request information.

### Local tests pass but Docker-based CI fails

Rebuild and run the documented `docker compose` checks locally. Host Python can
have different versions or dependencies; the container result matches the
repository's CI environment more closely. Compare the Docker and Compose versions
printed near the start of the Actions log as well.

For diagnosis, rerun `inventory-sim doctor` and retain its complete output along with `docker version` and `docker compose version` when asking for help.

## 19. Questions for the reader

1. Which tools remain installed on your host, and which are supplied by the image?
2. Why does `docker compose run --rm` suit short development checks?
3. When must you rebuild the image, and when is a source mount enough?
4. What does the `doctor` output prove? What intentionally remains outside its checks?
5. Why might implementing later concepts before their chapters make this textbook harder to learn from?
6. Why can high coverage coexist with incorrect behavior?
7. Which system runs tests, and which system records their coverage history?

## 20. Chapter summary

You installed or verified the required host tools, cloned the repository, built a
consistent Python environment, and ran its foundational commands. You also learned
how pytest, coverage, Ruff, GitHub Actions, and Codecov support the project, where
its main files live, and how Compose exposes host edits to the container. The
laboratory is ready, but it contains no inventory behavior yet.

## 21. What comes next in Chapter 1

Chapter 1 will introduce the first project concept and its vocabulary before any corresponding implementation is added. Stop here for now: Chapter 0's purpose is only to establish a trustworthy, repeatable workspace.
