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

## 11. Check linting and formatting

Ruff performs two related jobs. Its linter finds selected correctness and consistency problems:

```bash
docker compose run --rm lab ruff check .
```

Its formatter check reports files whose layout differs from the project's standard, without changing them:

```bash
docker compose run --rm lab ruff format --check .
```

Contributors should run both checks and pytest before proposing a change. To format files deliberately, run `docker compose run --rm lab ruff format .` and review the edits.

## 12. Tour of the repository

```text
book/                 textbook chapters
diagrams/             future explanatory images
experiments/          future reproducible experiment definitions
results/              future reproducible outputs
src/inventory_sim/    the installable Python package and CLI
tests/                executable checks for current behavior
Dockerfile            recipe for the development image
compose.yaml          development service and source mount
pyproject.toml        package metadata, tools, and CLI entry point
README.md             project overview and quick start
CONTRIBUTING.md        contribution principles and checks
LICENSE                open-source license
```

The empty directories contain `.gitkeep` files because Git does not otherwise record empty directories. They reserve obvious homes for material only when later chapters introduce it.

## 13. How source mounting works

The image contains Python and installed tools. When Compose starts `lab`, this entry in `compose.yaml` maps the current host directory to `/workspace`:

```yaml
volumes:
  - .:/workspace
```

If you edit `src/inventory_sim/cli.py` on the host, the next container command immediately reads that edit. You generally do not need to rebuild for source or test changes. Rebuild when `Dockerfile` or project dependencies change. Files created inside `/workspace` can appear in your host checkout because it is the same mounted directory.

## 14. Common setup problems

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

For diagnosis, rerun `inventory-sim doctor` and retain its complete output along with `docker version` and `docker compose version` when asking for help.

## 15. Questions for the reader

1. Which tools remain installed on your host, and which are supplied by the image?
2. Why does `docker compose run --rm` suit short development checks?
3. When must you rebuild the image, and when is a source mount enough?
4. What does the `doctor` output prove? What intentionally remains outside its checks?
5. Why might implementing later concepts before their chapters make this textbook harder to learn from?

## 16. Chapter summary

You installed or verified the required host tools, cloned the repository, built a consistent Python environment, and ran its two foundational commands. You also learned how pytest and Ruff check the project, where its main files live, and how Compose exposes host edits to the container. The laboratory is ready, but it contains no inventory behavior yet.

## 17. What comes next in Chapter 1

Chapter 1 will introduce the first project concept and its vocabulary before any corresponding implementation is added. Stop here for now: Chapter 0's purpose is only to establish a trustworthy, repeatable workspace.
