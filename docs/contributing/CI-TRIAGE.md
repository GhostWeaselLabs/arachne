# CI Triage and Ownership Guide

Status: Active
Owner: Core Maintainers
Last Updated: 2025-01-01

This guide explains how to triage and fix Continuous Integration (CI) failures quickly and with low churn. It complements CONTRIBUTING.md and documents the owners, common failures, and step-by-step remediation.

Quick Links
- CI dashboard: GitHub Actions → CI workflow
- Docs: MkDocs build logs under “Build MkDocs site”
- Link Checker: “Check links (lychee)”
- Snippet Smoke: “Validate docs commands”
- Build-and-Test: “Lint, Type, and Test (Python 3.11)”

Ownership and Escalation
Primary Owners
- CI Orchestration (workflow logic, caching, concurrency):
  - Lead: doubletap-dave
  - Backup: core-maintainer-2
- Linting & Formatting (ruff, black, pre-commit):
  - Lead: core-maintainer-1
  - Backup: core-maintainer-3
- Types (mypy):
  - Lead: core-maintainer-2
  - Backup: core-maintainer-1
- Tests & Coverage (pytest):
  - Lead: core-maintainer-3
  - Backup: core-maintainer-2
- Docs Build (MkDocs) & Snippets:
  - Lead: docs-maintainer-1
  - Backup: core-maintainer-1
- Link Check (lychee):
  - Lead: docs-maintainer-1
  - Backup: core-maintainer-3

Escalation
1) If you cannot fix within 1–2 commits, open an issue labeled ci-broken and assign the relevant owner.
2) If the failure blocks a critical PR, coordinate in the team channel and apply a minimal, reversible mitigation while working on a root-cause fix.
3) For flaky jobs, switch to non-blocking only as a short-term mitigation and track a follow-up issue with a deadline.

General Triage Workflow
1) Identify failing job(s)
- From the PR/commit page, open GitHub Actions logs.
- Note the first failure; ignore cascading errors.

2) Reproduce locally (CI parity)
- Sync dependencies with uv:
  - uv lock (if missing)
  - uv sync
- Run the failing tool locally:
  - Lint: uv run ruff check .
  - Format: uv run black --check .
  - Types: uv run mypy src
  - Tests: uv run pytest
  - Docs: mkdocs build --strict
  - Snippets: mimic the job’s uv run invocation
  - Links: run lychee locally or verify URLs by hand; respect .lycheeignore

3) Apply the smallest fix that unblocks CI
- Prefer a single focused commit.
- Avoid speculative changes; let linters/type-checkers guide fixes.
- If flakiness is external, add to .lycheeignore or apply limited retries with clear comments.

4) Verify and merge
- Push the fix; ensure CI is fully green on the PR.
- If a temporary relaxation was used, open a tracking issue to revert it and set a due date.

Common Failures and Fixes
Build-and-Test
- ruff lint failures:
  - Run: uv run ruff check .
  - Fix the reported rules; use # noqa only with justification.
  - Keep line length at 100 (aligned with black).
- black format check:
  - Run: uv run black .
  - Commit formatting changes.
- mypy type errors:
  - Prefer precise types and typed signatures over Any.
  - Add Protocols or TypedDict where interfaces are implied.
  - Avoid global Optional unless semantically required; prefer non-None invariants.
- pytest failures:
  - Run: uv run pytest -q --maxfail=1
  - Stabilize flaky tests (timeouts, sleeps). For integration-like tests, prefer deterministic stubs.
  - If coverage dips under threshold, add tests or adjust threshold temporarily with a tracked deadline.

Docs: MkDocs build
- mkdocs build --strict fails:
  - Missing pages in nav: update mkdocs.yml nav or links in docs.
  - Broken anchors or malformed Markdown (unterminated fences): fix formatting.
  - Ensure all code fences have language identifiers (bash, python, toml, yaml).
  - Replace “---” used as a visual separator with *** or <hr>.
- Locally reproduce: pip install mkdocs mkdocs-material mkdocs-git-revision-date-localized-plugin; then mkdocs build --strict.

Docs Snippet Validation
- “Validate docs commands” import errors:
  - Ensure invocations run via uv run python so package imports work.
  - Keep snippet scope deterministic, short, and side-effect free.
  - For unavoidable non-determinism, wrap in try/except and log non-fatal errors to stderr, but return non-zero on true failures.

Link Checker (lychee)
- Transient external failures:
  - Use .lycheeignore for known flaky domains.
  - Keep small retries: --max-retries 2, --retry-wait-time 2.
  - Exclude private or build-only assets: --exclude-all-private, --exclude-file .lycheeignore.
- Broken internal links:
  - Prefer local links that work in both GitHub and MkDocs (e.g., ./quickstart.md).
  - Avoid ../docs patterns in page bodies.

Caching and Concurrency
- Caching
  - actions/setup-python with cache: "pip" is enabled.
  - uv handles locking and environments; avoid mixing pip install for project deps (except tooling like mkdocs).
- Concurrency
  - Concurrency group ci-${{ github.workflow }}-${{ github.ref }} cancels in-progress runs on the same ref to reduce churn.

Promotion Policy: Link-Check to Required
- Keep link-check non-blocking until stable across 3–5 consecutive PRs on main.
- Monitor runtime and rate-limit behavior.
- When stable:
  - Remove continue-on-error: true from link-check job.
  - Set it as a required status check in repository settings.
  - Update this document and M99 plan status.

Temporary Relaxations and Deadlines
- Any relaxation (e.g., non-blocking link-check, coverage threshold dips) must:
  - Be documented in the relevant file (workflow, pyproject) with a TODO and issue link.
  - Have a tracking issue with an explicit deadline to restore the target.

Local Parity Quick Commands
- Setup:
  - uv lock (first time)
  - uv sync
- Lint/Format:
  - uv run ruff check .
  - uv run black --check .
- Types:
  - uv run mypy src
- Tests:
  - uv run pytest
- Coverage (local view):
  - uv run pytest --cov=src --cov-report=term-missing
- Docs:
  - pip install mkdocs mkdocs-material mkdocs-git-revision-date-localized-plugin
  - mkdocs build --strict

Commit Hygiene
- Keep CI fixes low-churn: one problem, one commit.
- Write clear commit messages: “ci(link-check): add retries and ignore flaky domain X”
- Avoid reformat-only commits mixed with logic changes; use pre-commit locally to prevent noise.

Appendix: When to Open an Issue vs. Commit Directly
- Commit directly when:
  - The fix is mechanical, low-risk, and reproducible locally.
- Open an issue when:
  - Flakiness persists after retries and ignores.
  - Types/test failures need design changes.
  - Docs IA or nav adjustments affect multiple pages.

Cross-Reference
- CONTRIBUTING.md: Setup, development workflow, pre-commit instructions.
- M99 Plan: Status and acceptance criteria for docs and CI stabilization.

Change Log (CI Triage Doc)
- 2025-01-01: Initial version documenting owners, triage flow, common fixes, and promotion policy for link-check.