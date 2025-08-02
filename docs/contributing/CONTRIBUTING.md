# Contributing to Meridian Runtime

Thanks for your interest in Meridian Runtime! This document explains how to set up your environment, follow our standards, and propose changes. Meridian is a composable, asyncio-native, graph runtime created by GhostWeasel (Lead: doubletap-dave). We aim for clarity, predictability, and a strong developer experience.

Quick links
- Governance and overview: ../plan/M0-governance-and-overview.md
- Milestones and plans: ../plan/
- Support/how to report issues: ../support/HOW-TO-REPORT-ISSUES.md
- Troubleshooting: ../support/TROUBLESHOOTING.md
- CI triage and ownership: ./CI-TRIAGE.md
- Docs style guide: ./DOCS_STYLE.md

Note: By contributing, you agree to follow our Code of Conduct (CoC) and project governance in M0.

***

1) Project Goals and Principles

- Composable first: nodes, edges, and subgraphs with clear boundaries
- Async-native: Python 3.11+, asyncio-friendly code
- Predictable execution: fairness, backpressure, bounded edges
- Observability: structured logs, metrics, optional tracing
- Privacy-first: no payloads in errors by default; redaction hooks
- Maintainability: small, testable modules (~200 LOC/file guidance)
- Platform-agnostic: no assumptions about specific hosting services
- Docs-as-product: plans, support docs, and examples are first-class

***

2) Prerequisites and Environment Setup

We use:
- Python: 3.11+
- Package manager: uv
- Linting/formatting: ruff + black
- Type checking: mypy
- Tests: pytest (+ coverage)

Local setup
1. Install Python 3.11+.
2. Install uv:
   - See https://github.com/astral-sh/uv for installation instructions.
3. Clone the repository:
   - git clone <repo-url>
   - cd meridian-runtime
4. Create and activate a virtual environment (uv will manage it automatically for most commands, but you can also do it yourself if preferred).
5. Install dependencies (managed by uv via pyproject.toml):
   - uv lock
   - uv sync
6. Verify setup:
   - uv --version
   - uv run ruff --version
   - uv run black --version
   - uv run mypy --version
   - uv run pytest --version

Pre-commit (recommended)
- Install pre-commit:
  - uv run pip install pre-commit
  - pre-commit install
  - pre-commit install --hook-type pre-push
- Run on all files once:
  - pre-commit run --all-files
```bash
pre-commit run --all-files
```
- Hooks configured:
  - Ruff (lint with autofix) + Ruff formatter
  - Black
  - EOF fixer, trailing whitespace, YAML/TOML checks
  - markdownlint (docs style)
  - docs: no bare code fences (fails on ``` with no language)
  - docs: forbid '---' as visual separators (use *** or <hr> instead)
  - docs: link check (internal-only via lychee)
This ensures consistent style locally and prevents CI churn.

CI parity (run what CI runs)
- Lint:
  ```bash
  uv run ruff check .
  ```
- Format check:
  ```bash
  uv run black --check .
  ```
- Type-check:
  ```bash
  uv run mypy src
  ```
- Tests (with coverage gates):
  ```bash
  uv run pytest --cov=src --cov-fail-under=80
  ```
- Build coverage XML like CI (80% gate matches CI):
  ```bash
  uv run pytest --cov=src --cov-report=xml:coverage.xml --cov-fail-under=80
  ```
- Optional: install lychee locally for pre-commit docs link checks:
  ```bash
  # Using cargo (recommended)
  cargo install lychee
  # Verify
  lychee --version
  ```
  If lychee is not installed, the docs link-check pre-commit hook may fail locally; install it or skip with:
  ```bash
  SKIP=docs-lychee-internal pre-commit run --all-files
  ```
- Packaging (optional):
  ```bash
  uv build
  ```
- Run a subset of tests:
  ```bash
  uv run pytest -q tests/path::TestClass::test_method
  ```

Note: Some commands may be wrapped by scripts in scripts/ to ensure consistent options. Prefer those if present.

***

3) Repository Layout

- src/meridian/*: runtime and library code
- tests/*: unit, integration, and property-based tests
- examples/*: runnable examples and recipes
- docs/plan/*: milestone plans and decision records
- docs/contributing/*: this guide and release process
- docs/support/*: issue reporting, troubleshooting, and templates
- scripts/*: helper scripts for lint/type-check/test/release

***

4) Development Standards

Language and APIs
- Target Python 3.11+ features only.
- Prefer explicitness over magic; avoid global mutable state.
- Keep modules small and cohesive; favor SRP (single responsibility).
- Keep public APIs minimal, consistent, and carefully named.
- Document public APIs with clear docstrings and examples where appropriate.

Async and concurrency
- Prefer async def where applicable; avoid blocking calls in async contexts.
- If blocking is necessary, isolate and document it with appropriate adapters/executors.
- Enforce bounded edges and explicit overflow policies (block, drop, latest, coalesce).
- Separate control plane operations from data plane work (control takes priority).

Observability and privacy
- Use structured logging with stable keys. Avoid print in library code.
- Emit metrics via thin interfaces; keep adapters optional.
- Error events must not include payload contents by default.
- Support redaction hooks and scrub potential secrets/PII.

Testing and quality
- Write tests alongside code changes (unit + integration where relevant).
- Aim for ≥ 80% coverage on critical modules and ≥ 70% overall (risk-based exceptions documented).
- Keep tests deterministic; avoid sleeping where possible—use clocks/mocks/fakes.
- Add regression tests for bug fixes.
- Maintain type hints; pass mypy with the project configuration.
- Keep code formatted and linted; pass ruff and CI checks locally before opening a PR.

Documentation
- Update docs for any user-visible change.
- Provide examples or recipes when adding notable features.
- Keep README concise with pointers to deeper docs.

***

5) Branching, Commits, and PRs

Branching
- Use feature branches from the main branch.
- Keep changes scoped and reviewable. Split large work into logical commits and PRs.

Commit messages
- Use clear, imperative tense: “Add X”, “Fix Y”, “Refactor Z”.
- Reference issues or decision records where relevant.
- Include context in the body if the change is non-trivial.

Pull requests
- Describe the problem, solution, alternatives considered, and risk.
- Include tests and docs updates.
- Note any breaking change and migration notes.
- Ensure CI passes (lint, type, tests, packaging).
- For significant API changes, link to an RFC/Decision Record in docs/plan/dr.

Review process
- Expect at least one maintainer review. For sensitive changes (scheduling, error handling, privacy), request an additional reviewer.
- Address comments via follow-up commits; prefer small, targeted updates.
- Squash or rebase as needed to keep history clean.

***

6) Decision Records and RFCs

When to write one
- Public API changes or deprecations
- Scheduler policies, fairness strategies, or performance-sensitive modifications
- Error/diagnostics schema changes and redaction policies
- Persistence adapters, replay/log formats, visual inspector protocols

What to include
- Motivation and scope
- Design options and trade-offs
- Chosen approach and rationale
- Migration or compatibility notes
- Links to issues/PRs and related docs

Location
- docs/plan/dr/<YYYY-MM-DD>-short-title.md

-------------------------------------------------------------------------------

7) Testing Guidance

- Unit tests: Focus on behavior, boundaries, and edge policies.
- Integration tests: Exercise realistic node/edge/scheduler flows.
- Property-based tests (optional): Use where invariants are essential (e.g., fairness guarantees).
- Fixtures: Provide minimal, composable fixtures for runtime/scheduler setup.
- Logging/metrics in tests: Use structured assertions or capture context; avoid coupling to specific backends.
- Performance checks: Add micro-benchmarks for hot paths where feasible (non-blocking in CI).

***

Security maintenance (CodeQL & Dependabot)
- CodeQL: We run code scanning on PRs and main. If CodeQL flags an alert on your PR, review the alert details in the Security tab and fix or justify with a link to the relevant discussion/issue. Prefer fixing in the same PR when low-risk; otherwise, open a follow-up with a short timeline.
- Dependabot: Weekly PRs may update GitHub Actions, Python packages, or docs tooling. Review the changelog, ensure CI is green, and prefer merging patch/minor bumps. For major updates, open an issue or small PR to validate impact. Keep dependency PRs focused (one tool/stack at a time when possible).


8) Observability, Errors, and Diagnostics

- Log structure: prefer event = "node_started", node_id, graph_id, etc.
- Metrics: stable names, low label cardinality, adapters optional.
- Errors: do not include payload contents by default; attach metadata only.
- Diagnostics: future CLI command meridian diagnostics collect will generate redacted bundles. Until then, follow docs/support/HOW-TO-REPORT-ISSUES.md for safe data sharing.

-------------------------------------------------------------------------------

9) Security and Privacy

- Never log secrets, tokens, or PII.
- Apply redaction hooks before emitting logs/diagnostics.
- Treat diagnostics bundles as sensitive; ensure anonymization and scrubbing where applicable.
- Follow the principle of least privilege for configuration and environment access.

***

10) Releasing

- Follow docs/contributing/RELEASING.md for:
  - Versioning (SemVer)
  - Changelog updates
  - Tagging and packaging
  - Release verification (examples/tests)
- Any public API change must include release notes and migration steps.

***

11) Getting Help

- For how to report issues and request features: docs/support/HOW-TO-REPORT-ISSUES.md
- For common problems: docs/support/TROUBLESHOOTING.md
- For templates: docs/support/templates/
- If you’re blocked by a decision or unclear policy, open a discussion or small PR to propose a path forward and request maintainer guidance.

***

12) Code of Conduct

All contributors and maintainers must follow our CoC. Be respectful, constructive, and collaborative. Report violations through the project’s designated channels.

***

Checklist Before Opening a PR

- [ ] Code compiles and passes tests locally
- [ ] uv run ruff check .
- [ ] uv run black --check .
- [ ] uv run mypy src passes (or narrow, justified suppressions)
- [ ] uv run pytest --cov=src --cov-fail-under=80 passes locally (coverage gate ≥80% overall)
- [ ] Tests added/updated, including regression tests if fixing a bug
- [ ] Docs updated (README, examples, or deeper docs as needed)
- [ ] No payload contents in error events or logs; redaction applied where appropriate
- [ ] Linked to issue(s) and/or Decision Record for significant changes
- [ ] Scoped, reviewable commits with clear messages

Thank you for helping build Meridian Runtime!