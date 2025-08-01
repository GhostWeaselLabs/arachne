# Milestone M1: Project Bootstrap and CI

Status: Planned
Owner: Core Maintainers
Duration: 1–2 days

Overview
Establish the repository scaffold, development workflow, and CI guardrails to enable rapid, consistent iteration. This milestone sets conventions (SRP/DRY, ~200 LOC per file), pins toolchain versions, and ensures all contributors can build, lint, type-check, and test locally and in CI using uv.

Goals (EARS)
- The system shall be bootstrapped as a Python 3.11+ project managed by uv.
- The system shall provide a deterministic local dev loop: uv init → uv lock → uv sync → uv run.
- The system shall enforce code quality via linting and formatting checks.
- The system shall enforce typing via static analysis.
- The system shall run tests with coverage reports and thresholds.
- When code is pushed or a PR is opened, the CI shall run lint, type, and tests across supported Python versions (initially 3.11).
- If coverage thresholds are not met (≥90% core, ≥80% overall), the CI shall fail.
- The system shall publish a minimal README, LICENSE, and CHANGELOG skeletons.

Deliverables
- pyproject.toml configured for:
  - Python 3.11
  - uv-managed dependencies
  - ruff (lint), black (format), mypy (types), pytest + coverage (tests)
- Repo structure:
  - src/arachne/… (empty modules for now)
  - examples/ (placeholder)
  - tests/unit/, tests/integration/ (scaffolds)
  - docs/ (existing), docs/plan/ (this file)
  - .github/workflows/ci.yml (or alternative CI pipeline)
- Baseline configuration:
  - ruff.toml
  - mypy.ini
  - .editorconfig
  - .gitignore (Python + uv caches)
- Documentation:
  - README.md (quickstart, dev loop, contribution guidelines summary)
  - CHANGELOG.md (Keep a Changelog format, SemVer)
  - LICENSE (MIT or organization default)
- Verified CI run passing on main branch with the scaffold.

Scope and Tasks
1) Repository and tooling
- Create pyproject.toml:
  - Project metadata (name: arachne, version: 0.0.0, license: MIT)
  - Dependencies: none (runtime) for M1
  - Dev dependencies: ruff, black, mypy, pytest, pytest-cov, types-*
  - [tool.ruff], [tool.black], [tool.pytest.ini_options] sections
- Initialize uv workflow:
  - uv init, uv lock, uv sync
  - Doc quickstart commands in README

2) Codebase layout
- Create packages:
  - src/arachne/__init__.py
  - src/arachne/core/__init__.py
  - src/arachne/observability/__init__.py
  - src/arachne/utils/__init__.py
  - examples/__init__.py
- Add placeholder modules with TODO headers so imports resolve in tests.

3) Static checks and quality gates
- Configure ruff:
  - Enable common rule sets (E, F, I, UP, B)
  - Line length 100–120; exclude generated artifacts
- Configure black:
  - Line length consistent with ruff
- Configure mypy:
  - Python version 3.11
  - disallow_untyped_defs = True (at least in src/)
  - warn_unused_ignores = True
  - strict Optional handling
  - separate section for tests with relaxed rules
- Add EditorConfig and .gitignore:
  - Normalize whitespace, end-of-line, utf-8
  - Ignore .venv, .python-version, .mypy_cache, .ruff_cache, .pytest_cache, .coverage, dist, build

4) Testing scaffold
- tests/unit/test_smoke.py:
  - Verifies package import and versions
- tests/integration/test_examples_smoke.py:
  - Placeholder to run a no-op example
- Configure pytest.ini (inside pyproject):
  - testpaths = ["tests"]
  - addopts = "-q --cov=src --cov-report=term-missing --cov-fail-under=80"
  - markers for unit and integration

5) CI pipeline
- Workflow triggers: push and pull_request on main and feature branches
- Jobs:
  - setup: checkout, set up Python 3.11, install uv
  - deps: uv sync
  - lint: ruff check ., black --check .
  - type: mypy src
  - test: uv run pytest
- Cache:
  - Cache uv and pip artifacts if beneficial
- Artifacts:
  - Upload coverage xml (optional for codecov later)

6) Documentation updates
- README sections:
  - Quickstart (uv commands)
  - Development (lint, type, test)
  - Contributing conventions (SRP/DRY, ~200 LOC/file, typing)
- CHANGELOG.md initialized with Unreleased section
- LICENSE file added

Acceptance Criteria
- Running the following locally works without errors:
  - uv lock && uv sync
  - uv run ruff check .
  - uv run black --check .
  - uv run mypy src
  - uv run pytest
- CI runs the same checks and passes on a fresh clone.
- Coverage gate is enforced at ≥80% overall (temporary for M1); core modules will raise to ≥90% in later milestones.
- Repository contains README, LICENSE, CHANGELOG, and baseline scaffolds.

Risks and Mitigations
- Divergent local dev environments:
  - Mitigation: Use uv exclusively; document commands in README; provide .editorconfig.
- Slow CI feedback:
  - Mitigation: Cache uv artifacts; split jobs; run lint/type before tests to fail fast.
- Overly strict typing blocking progress:
  - Mitigation: Strict in src/, relaxed in tests/; allow per-file overrides with justification.

Out of Scope (future milestones)
- Core runtime modules (message, ports, edge, node, subgraph, scheduler)
- Observability exporters and tracing hooks
- Examples beyond smoke
- Release automation

Traceability
- Supports Implementation Plan M1 in the technical blueprint.
- Satisfies EARS operational requirements for bootstrap, dev loop, and CI quality gates.

Checklist
- [ ] pyproject.toml created and configured
- [ ] uv lock/sync completes cleanly
- [ ] ruff, black, mypy, pytest configs added
- [ ] src/, tests/, examples/ scaffolds exist
- [ ] CI workflow defined and passing
- [ ] README, LICENSE, CHANGELOG present
- [ ] Coverage threshold configured and enforced