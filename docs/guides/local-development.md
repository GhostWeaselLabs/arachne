# Local development

## Summary
This guide helps you set up a productive local development environment for Meridian Runtime, run tests, lint and format code, and iterate quickly on examples and docs.

### Audience
Developers contributing to the project or building against the runtime locally.

### Goals

- Install and configure local tooling (Python, uv, Make, pre-commit).
- Run the test suite and linters.
- Execute examples and iterate on code with fast feedback.
- Build and preview documentation locally.

### Non-goals

- Production deployment.
- Deep-dive into the scheduler or performance tuning.

---

## Prerequisites

- Python 3.11+ installed
- uv installed (recommended) or pip
- Make (optional but used by provided targets)
- Git
- On macOS: Xcode command line tools (for compilers) — xcode-select --install

Optional but recommended:
- direnv for automatic environment loading
- A modern editor with Python support (VS Code, PyCharm, etc.)

---

## Repository setup

Clone and install dependencies:

```bash
git clone https://github.com/GhostWeaselLabs/meridian-runtime.git
cd meridian-runtime

# Create a virtual environment and install dependencies with uv (preferred)
uv sync

# Alternatively, using pip:
# python -m venv .venv
# source .venv/bin/activate
# pip install -U pip
# pip install -e ".[dev]"
```

Enable pre-commit hooks (formatting, linting, hygiene checks):

```bash
# Automated setup (recommended)
./scripts/dev-setup.sh

# Manual setup
uv tool install pre-commit
pre-commit install
pre-commit install --hook-type pre-push
# Run against all files once:
pre-commit run --all-files
```

!!! note
    The `dev-setup.sh` script automatically installs pre-commit, lychee (link checker), and configures hooks.

Common make targets (optional, convenience):

```bash
make help
make demo-minimal        # run minimal hello world demo
make demo-sentiment      # run sentiment pipeline demo
make demo-coalesce       # run streaming coalesce demo
make docs-serve          # serve docs locally
make docs-build          # build docs to ./site
make docs-check-links    # check links in docs
```

---

## Running tests

Run all tests:

```bash
uv run pytest -q
```

Run a subset (by keyword or path):

```bash
# Run tests matching a keyword
uv run pytest -k "scheduler and not slow" -q

# Run tests in a specific file
uv run pytest tests/test_scheduler.py -q
```

Generate a coverage report:

```bash
uv run pytest --cov=src --cov-report=term-missing
```

!!! tip
    - Keep unit tests fast; mark slow tests with pytest markers.
    - Prefer deterministic tests; avoid sleeps where possible—use timeouts and events.

---

## Linting, typing, and formatting

Run the full lint suite:

```bash
# Using uvx (recommended)
uvx ruff check .
uvx ruff format .
uvx mypy

# Or using uv run
uv run ruff check .
uv run ruff format .
uv run mypy
```

Guidance:

- Ruff handles both linting and formatting (see pyproject.toml configuration).
- MyPy enforces strict typing (disallow_untyped_defs, strict_equality, etc.).
- Coverage requirement: 80% minimum enforced in CI.
- If you must ignore a rule, prefer the narrowest scope and document why.

!!! warning
    **Coverage Requirements**: The project enforces 80% test coverage. Local runs omit coverage flags for convenience, but CI will fail if coverage drops below 80%.

---

## Running examples

List available examples:

```bash
ls examples/
```

Run an example:

```bash
# Direct execution
python examples/minimal_hello/main.py
python examples/hello_graph/main.py
python examples/sentiment/main.py --human --timeout-s 6.0
python examples/streaming_coalesce/main.py --human --timeout-s 5.0
python examples/pipeline_demo/main.py

# Using make targets (with configurable parameters)
make demo-minimal
make demo-sentiment
make demo-coalesce
```

Troubleshooting examples:

- If imports fail, ensure your virtualenv is active and the project is installed in editable mode (uv sync already does this).
- For long-running examples, add structured logging or increase log verbosity as needed.

!!! tip
    **Make Target Parameters**: Override demo parameters with environment variables:
    ```bash
    RATE_HZ=20 TICK_MS=10 make demo-sentiment
    COAL_RATE_HZ=600 CAP_AGG_TO_SINK=8 make demo-coalesce
    ```

---

## Local observability

Enable structured logs (if configurable via env or config):

```bash
export MERIDIAN_LOG_LEVEL=info
uv run python -m examples.hello_graph.main
```

Metrics (if exposed locally):

- Default port can be set via env or config (e.g., MERIDIAN_METRICS_PORT=8000).
- Verify with:
```bash
curl -s localhost:8000/metrics | head
```

See also:

- [Concepts overview](../concepts/about.md)
- [Observability details](../concepts/observability.md)
- [API reference](../reference/api.md)

---

## Docs: build and preview

Serve docs locally with live reload:

```bash
make docs-serve
# or if you prefer direct command:
mkdocs serve -a 127.0.0.1:8000
```

Build docs:

```bash
uv run mkdocs build
```

Docs conventions and templates:

- [Conventions](../contributing/docs-conventions.md)
- [Guide template](../contributing/templates/guide-template.md)
- [Reference template](../contributing/templates/reference-template.md)
- [ADR template](../contributing/templates/adr-template.md)

---

## Developer workflow

1. Create a feature branch:
```bash
git checkout -b feat/short-description
```

2. Iterate locally:
```bash
uvx ruff format .
uvx ruff check .
uvx mypy
uvx pytest -q
```

3. Update docs if behavior or public APIs change:
    - Add or edit pages under docs/.
    - Update mkdocs.yml navigation if you add new pages.
    - Verify with mkdocs serve.

4. Commit with a clear message:
```bash
git add -A
git commit -m "feat: add X to scheduler (docs: update quickstart and api reference)"
```

5. Push and open a PR:
```bash
git push -u origin feat/short-description
```

Ensure the PR checklist includes:

- [x] Tests added/updated
- [x] Docs added/updated and linked from index or section pages
- [x] Lint/format/type checks pass

---

## Troubleshooting

Virtual environment issues

- Symptom: ModuleNotFoundError for project modules.
- Fix: Re-run uv sync; verify that .venv is active; confirm editable install.

Mypy false positives

- Narrow ignores with `# type: ignore[code]` and add a comment. Prefer fixing types over ignoring.
- Project uses strict MyPy configuration; expect type errors for untyped code.

Ruff disagreements

- Use `uvx ruff format` to resolve style issues. For rule exceptions, add inline `# noqa: RULE` sparingly with justification.
- Line length is 100 characters (see pyproject.toml).

Coverage failures

- CI enforces 80% coverage minimum. Run `uvx pytest --cov=src --cov-report=term-missing` locally.
- Add tests for new code to maintain coverage.

Docs build failures

- Check mkdocs.yml paths after moving/renaming docs.
- Run `make docs-check-links` to verify internal links.
- Lychee link checker is installed via dev-setup.sh.

---

## Useful commands

```bash
# Run a single test with verbose output
uvx pytest tests/test_scheduler.py::test_basic --maxfail=1 -vv

# Profile a test module (example approach; integrate your profiler of choice)
uvx pytest tests/test_scheduler.py -q

# Run only changed files (pre-commit)
pre-commit run --from-ref origin/main --to-ref HEAD

# Check coverage locally
uvx pytest --cov=src --cov-report=term-missing
```

---

## Next steps

- [Quickstart](../getting-started/quickstart.md)
- [Examples](../examples/index.md)
- [Patterns](../concepts/patterns.md)
- [API reference](../reference/api.md)
- [Contributing guide](../contributing/guide.md)