# Contributing to Meridian Runtime {#contributing}

## Introduction

Thanks for your interest in Meridian Runtime! This document explains how to set up your environment, follow our standards, and propose changes. Meridian is a composable, asyncio-native, graph runtime created by *GhostWeasel*. We aim for clarity, predictability, and a strong developer experience.

!!! tip
    **New to Meridian?** Start with the [Getting Started Guide](../getting-started/guide.md) and [API Reference](../reference/api.md) to understand the core concepts before diving into development.

## Quick links

- [Governance and overview](../roadmap/governance-and-overview.md)
- [Milestones and plans](../roadmap/index.md)
- [How to report issues](../support/how-to-report-issues.md)
- [Troubleshooting](../support/troubleshooting.md)
- [CI triage and ownership](./CI-TRIAGE.md)
- [Docs style guide](./docs-conventions.md)

!!! note
    By contributing, you agree to follow our Code of Conduct (CoC) and project governance in M0.

---

## Project Goals and Principles {#goals}

- **Composable first**: nodes, edges, and subgraphs with clear boundaries
- **Async‑native**: Python 3.11+, asyncio‑friendly code
- **Predictable execution**: fairness, backpressure, bounded edges
- **Observability**: structured logs, metrics, optional tracing
- **Privacy‑first**: no payloads in errors by default; redaction hooks
- **Maintainability**: small, testable modules (~200 LOC/file guidance)
- **Platform‑agnostic**: no assumptions about specific hosting services
- **Docs‑as‑product**: plans, support docs, and examples are first‑class

---

## Prerequisites and Environment Setup {#environment}

### Environment

- **Python**: 3.11+
- **Package manager**: `uv`
- **Linting/formatting**: `ruff` + `black`
- **Type checking**: `mypy`
- **Tests**: `pytest` (+ coverage)

### Local setup

1. Install Python 3.11+.

2. Install `uv`:

    - See https://github.com/astral-sh/uv for installation instructions.

3. Clone the repository:

    ```bash
    git clone <repo-url>
    cd meridian-runtime
    ```

4. Create and activate a virtual environment

    - `uv` manages a venv automatically for most commands; manual activation is also fine.

5. Install dependencies (managed by `uv` via `pyproject.toml`):

    ```bash
    uv lock
    uv sync
    ```

6. Verify setup:

    ```bash
    uv --version
    uv run ruff --version
    uv run black --version
    uv run mypy --version
    uv run pytest --version
    ```

### Pre-commit (recommended)

1. Install pre-commit:

    ```bash
    uv run pip install pre-commit
    pre-commit install
    pre-commit install --hook-type pre-push
    ```

2. Run on all files once:

    ```bash
    pre-commit run --all-files
    ```

- Hooks configured:

    - `Ruff` (lint with autofix) + `Ruff` formatter
    - `Black`
    - EOF fixer, trailing whitespace, YAML/TOML checks
    - `markdownlint` (docs style)
    - docs: no bare code fences (fails on ```` with no language)
    - docs: visual separators — use only `---`; forbid `***` and `<hr>`
    - docs: link check (internal‑only via `lychee`)

This ensures consistent style locally and prevents CI churn.

### CI parity (run what CI runs)

```bash title="Run lint"
uv run ruff check .
```

```bash title="Run formatting check"
uv run black --check .
```

```bash title="Run type check"
uv run mypy src
```

```bash title="Run tests with coverage gate"
uv run pytest --cov=src --cov-fail-under=80
```

```bash title="Generate coverage XML (80% gate matches CI)"
uv run pytest --cov=src --cov-report=xml:coverage.xml --cov-fail-under=80
```

### Install lychee (optional)

```bash title="Install lychee (via cargo)"
# Using cargo (recommended)
cargo install lychee
# Verify
lychee --version
```

!!! note
    If `lychee` is not installed, the docs link‑check pre‑commit hook may fail locally; install it or skip with:

    ```bash title="Skip docs link check (local only)"
    SKIP=docs-lychee-internal pre-commit run --all-files
    ```

### Packaging (optional)

```bash title="Build package"
uv build
```

**Run a subset of tests:**

```bash title="Run a specific test"
uv run pytest -q tests/path::TestClass::test_method
```

!!! info
    Some commands may be wrapped by scripts in `scripts/` to ensure consistent options. Prefer those if present.

---

## Repository Layout {#layout}

- `src/meridian/*`: runtime and library code
- `tests/*`: unit, integration, and property‑based tests
- `examples/*`: runnable examples and recipes
- `docs/roadmap/*`: milestone plans and decision records
- `docs/contributing/*`: this guide and release process
- `docs/support/*`: issue reporting, troubleshooting, and templates
- `scripts/*`: helper scripts for lint/type‑check/test/release

---

## Development Standards {#standards}

### Language and APIs

- Target Python 3.11+ features only.
- Prefer explicitness over magic; avoid global mutable state.
- Keep modules small and cohesive; favor SRP (single responsibility).
- Keep public APIs minimal, consistent, and carefully named.
- Document public APIs with clear docstrings and examples where appropriate.

### Async and concurrency

- Prefer `async def` where applicable; avoid blocking calls in async contexts.
- If blocking is necessary, isolate and document it with appropriate adapters/executors.
- Enforce bounded edges and explicit backpressure policies (`Block`, `Drop`, `Latest`, `Coalesce`). See: [API Reference: Backpressure and Overflow](../reference/api.md#backpressure-and-overflow)
- Separate control plane operations from data plane work (control takes priority).

### Observability and privacy

- Use structured logging with stable keys. Avoid `print` in library code.
- Emit metrics via thin interfaces; keep adapters optional.
- Error events must not include payload contents by default.
- Support redaction hooks and scrub potential secrets/PII.

### Testing and quality

- Write tests alongside code changes (unit + integration where relevant).
- Aim for ≥ 80% coverage on critical modules and ≥ 70% overall (risk‑based exceptions documented).
- Keep tests deterministic; avoid sleeping where possible—use clocks/mocks/fakes.
- Add regression tests for bug fixes.
- Maintain type hints; pass `mypy` with the project configuration.
- Keep code formatted and linted; pass `ruff` and CI checks locally before opening a PR.

### Documentation

- Update docs for any user‑visible change.
- Provide examples or recipes when adding notable features.
- Keep `README` concise with pointers to deeper docs.

---

## Branching, Commits, and PRs {#workflow}

### Branching

- Use feature branches from the `main` branch.
- Keep changes scoped and reviewable. Split large work into logical commits and PRs.

### Commit messages

- Use clear, imperative tense: "Add X", "Fix Y", "Refactor Z".
- Reference issues or decision records where relevant.
- Include context in the body if the change is non‑trivial.

### Pull requests

- Describe the problem, solution, alternatives considered, and risk.
- Include tests and docs updates.
- Note any breaking change and migration notes.
- Ensure CI passes (lint, type, tests, packaging).
- For significant API changes, link to an RFC/Decision Record in `docs/roadmap/dr`.

### Review process

- Expect at least one maintainer review. For sensitive changes (scheduling, error handling, privacy), request an additional reviewer.
- Address comments via follow‑up commits; prefer small, targeted updates.
- Squash or rebase as needed to keep history clean.

---

## Decision Records and RFCs {#dr}

### When to write one

- Public API changes or deprecations
- Scheduler policies, fairness strategies, or performance‑sensitive modifications
- Error/diagnostics schema changes and redaction policies
- Persistence adapters, replay/log formats, visual inspector protocols

### What to include

- Motivation and scope
- Design options and trade‑offs
- Chosen approach and rationale
- Migration or compatibility notes
- Links to issues/PRs and related docs

### Location

- `docs/roadmap/dr/<YYYY-MM-DD>-short-title.md`

---

## Testing Guidance {#testing}

- **Unit tests**: Focus on behavior, boundaries, and edge/backpressure policies.
- **Integration tests**: Exercise realistic node/edge/scheduler flows.
- **Property‑based tests** (optional): Use where invariants are essential (e.g., fairness guarantees).
- **Fixtures**: Provide minimal, composable fixtures for runtime/scheduler setup.
- **Logging/metrics in tests**: Use structured assertions or capture context; avoid coupling to specific backends.
- **Performance checks**: Add micro‑benchmarks for hot paths where feasible (non‑blocking in CI).

---

## Security maintenance {#security}

### CodeQL

We run code scanning on PRs and `main`. If CodeQL flags an alert on your PR, review the alert details in the Security tab and fix or justify with a link to the relevant discussion/issue. 

Prefer fixing in the same PR when low‑risk; otherwise, open a follow‑up with a short timeline.

### Dependabot

Weekly PRs may update GitHub Actions, Python packages, or docs tooling. Review the changelog, ensure CI is green, and prefer merging patch/minor bumps. 

For major updates, open an issue or small PR to validate impact. Keep dependency PRs focused (one tool/stack at a time when possible).

---

## Observability, Errors, and Diagnostics {#observability}

### Log structure

- Prefer `event = "node_started"`, `node_id`, `graph_id`, etc.

### Metrics

- Stable names, low label cardinality, adapters optional.

### Errors

- Do not include payload contents by default; attach metadata only.

### Diagnostics

- A future CLI command `meridian diagnostics collect` will generate redacted bundles. Until then, follow [How to Report Issues](../support/how-to-report-issues.md) and [Troubleshooting](../support/troubleshooting.md) for safe data sharing.

---

## Privacy {#privacy}

- Never log secrets, tokens, or PII.
- Apply redaction hooks before emitting logs/diagnostics.
- Treat diagnostics bundles as sensitive; ensure anonymization and scrubbing where applicable.
- Follow the principle of least privilege for configuration and environment access.

---

## Releasing {#releasing}

- Follow [RELEASING.md](./RELEASING.md) for:
    - Versioning (SemVer)
    - Changelog updates
    - Tagging and packaging
    - Release verification (examples/tests)
- Any public API change must include release notes and migration steps.

---

## Getting Help {#help}

- For how to report issues and request features: [How to Report Issues](../support/how-to-report-issues.md)
- For common problems: [Troubleshooting](../support/troubleshooting.md)
- For templates: [Support Templates](../support/templates/)
- If you're blocked by a decision or unclear policy, open a discussion or small PR to propose a path forward and request maintainer guidance.

---

## Code of Conduct {#coc}

All contributors and maintainers must follow our CoC. Be respectful, constructive, and collaborative. Report violations through the project's designated channels.

---

## Checklist Before Opening a PR {#pr-checklist}

- [x] Code compiles and passes tests locally
- [x] `uv run ruff check .`
- [x] `uv run black --check .`
- [x] `uv run mypy src` passes (or narrow, justified suppressions)
- [x] `uv run pytest --cov=src --cov-fail-under=80` passes locally (coverage gate ≥80% overall)
- [x] Tests added/updated, including regression tests if fixing a bug
- [x] Docs updated (`README`, examples, or deeper docs as needed)
- [x] No payload contents in error events or logs; redaction applied where appropriate
- [x] Linked to issue(s) and/or Decision Record for significant changes
- [x] Scoped, reviewable commits with clear messages

---

## Awesome Contribution Ideas {#ideas}

Looking for inspiration? Here are some areas where contributions are especially welcome:

### High Impact, Low Complexity

- **Documentation improvements**: Fix typos, clarify examples, add missing sections
- **Test coverage**: Add tests for edge cases or improve existing test quality
- **Example enhancements**: Create new examples or improve existing ones
- **CI/CD improvements**: Optimize build times, add new checks, improve reliability

### Developer Experience

- **Error messages**: Make error messages more helpful and actionable
- **Debugging tools**: Add better debugging capabilities or observability features
- **CLI enhancements**: Improve the developer CLI experience
- **IDE support**: Add better IDE integration or tooling

### Performance & Reliability

- **Benchmarks**: Add performance benchmarks for critical paths
- **Memory optimization**: Identify and fix memory leaks or inefficiencies
- **Concurrency improvements**: Enhance fairness, reduce contention
- **Edge case handling**: Improve robustness for unusual scenarios

### Observability & Monitoring

- **Metrics**: Add new metrics for better monitoring
- **Logging**: Improve structured logging and error reporting
- **Tracing**: Enhance distributed tracing capabilities
- **Diagnostics**: Build better diagnostic tools

### Security & Privacy

- **Security audits**: Review code for security vulnerabilities
- **Privacy enhancements**: Improve data redaction and privacy features
- **Access control**: Add better access control mechanisms
- **Audit logging**: Enhance audit trail capabilities

!!! tip
    **Not sure where to start?** Check the [Issues](https://github.com/GhostWeaselLabs/meridian-runtime/issues) page for labeled "good first issue" or "help wanted" items, or ask in discussions!

---

**Thank you for helping build Meridian Runtime!** 🎉
