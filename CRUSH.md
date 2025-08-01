# CRUSH.md — Fast ref for agents in Arachne (Python 3.11, uv)

Build/lint/type/test
- Env: uv lock; uv sync
- Lint: uv run ruff check .
- Format check: uv run black --check .
- Autoformat: uv run black .
- Types (src only): uv run mypy src
- Tests (quiet + coverage): uv run pytest
- If tools missing: uv add --dev ruff black mypy pytest pytest-cov
- Run single test file:: uv run pytest tests/unit/test_smoke.py::test_import_arachne_package -q
- Run single test node: uv run pytest -k "name" -q
- Coverage XML (CI parity): uv run pytest --cov=src --cov-report=xml:coverage.xml

Project layout
- src/arachne/* (core, observability, utils); tests/{unit,integration}; examples/; pyproject.toml
- Tools configured in pyproject.toml, ruff.toml, mypy.ini, .editorconfig

Code style (summarized)
- Formatting: Black (LL=100), keep imports sorted by Ruff isort rules
- Imports: first stdlib, then third‑party, then first‑party (arachne); combine "as" imports; force sort within sections
- Typing: MyPy strict in src (no untyped defs, no implicit optional, disallow any generics); relaxed in tests; prefer precise types and TypedDict/Protocols over Any
- Naming: snake_case for functions/vars; PascalCase for classes; UPPER_SNAKE for consts; module names are lowercase
- Errors: handle locally when possible; raise descriptive exceptions; avoid bare except; prefer explicit exception types; no logging of secrets
- Docs: concise docstrings on public APIs; keep files ~200 LOC; SRP/DRY
- Observability: structured logs, metrics hooks; keep tracing optional

Testing
- Pytest configured via [tool.pytest.ini_options]; testpaths=tests; markers: unit, integration
- Use -m "unit" or -m "integration" to filter; prefer small, deterministic tests

CI parity
- Workflow runs ruff, black --check, mypy src, pytest, and coverage XML; keep local commands identical

Notes
- Packaging via setuptools; build: uv run python -m build (optional)
- Python >=3.11 only
