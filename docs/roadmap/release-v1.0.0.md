# Milestone M8: Release v1.0.0

## EARS Tasks and Git Workflow

**Branch name**: `feature/m8-release-1-0-0`

**EARS loop**

- Explore: finalize scope, gates, and release workflow
- Analyze: verify docs/examples, changelog, versioning, policies
- Implement: release CI, packaging, signing, notes, migration guide
- Specify checks: dry-run to test index; post-publish smoke; downstream compatibility
- Commit after each major step

**Git commands**

```bash
git checkout -b feature/m8-release-1-0-0
git add -A && git commit -m "chore(release): bump version and finalize pyproject metadata"
git add -A && git commit -m "chore(release): CI workflow for build, test, and publish on tag"
git add -A && git commit -m "docs(release): changelog, release notes, migration and deprecation policy"
git add -A && git commit -m "chore(release): signing and integrity checks; test publish flow"
git add -A && git commit -m "chore(release): downstream smoke and docs link validation"
git push -u origin feature/m8-release-1-0-0
```

Open PR early; keep commits small and focused

**Status**: Planned  
**Owner**: Core Maintainers  
**Duration**: 2–4 days

---

## Overview

This milestone delivers the first stable release of Arachne's graph runtime with a SemVer-committed API. It finalizes documentation, artifacts, and release processes, validates compatibility with downstreams, and publishes packages. It also sets the project's maintenance and deprecation policies to ensure dependable adoption.

## EARS Requirements

- The system shall be versioned following Semantic Versioning, starting at `v1.0.0`.
- The system shall publish artifacts to a package registry (e.g., PyPI) with signed distributions and reproducible builds.
- The system shall provide a `CHANGELOG` entry summarizing user-facing changes since the last pre-1.0 milestone.
- The system shall tag the release in VCS and attach release notes with upgrade guidance, compatibility guarantees, and known issues.
- When the release workflow runs on the main branch with a version tag, it shall build wheels and source distributions, run checks (lint, type, tests), and then publish upon success.
- If any gate (lint, type, tests, coverage) fails, the workflow shall abort without publishing.
- The system shall provide a migration guide for any changes since RC or beta, including deprecated APIs.
- The system shall validate that examples run with `uv` and that documentation links are correct at release time.
- The system shall define and document a deprecation policy for future changes.
- The system shall verify downstream compatibility by running a smoke CI against an integration repository or a minimal consumer project.

---

## Release Scope (What's Included)

- **Public APIs stabilized for**:
    - `core`: `Node`, `Edge`, `Subgraph`, `Scheduler`, `Message`, `PortSpec`, `Policies`
    - `observability`: logging, metrics interface (no-op + Prometheus adapter), tracing adapter (optional)
    - `utils`: `ids`, `time`, `validation`
    - `scaffolding`: `generate_node.py`, `generate_subgraph.py`
- **Documentation**:
    - Quickstart, API overview, Patterns, Troubleshooting, Observability
    - Release notes and migration guide
- **Examples**:
    - `hello_graph`, `pipeline_demo` (priority/backpressure demonstrations)

---

## Non-Goals

- Distributed/multi-process runtime
- Async-native scheduler API (adapter may arrive post-1.0)
- Vendor-specific observability integrations beyond documented adapters

---

## Versioning and Policy

- **Semantic Versioning**:
    - `MAJOR`: breaking changes to public API
    - `MINOR`: new backward-compatible features
    - `PATCH`: bug fixes and internal improvements
- **Deprecation**:
    - Mark deprecated APIs with warnings and docstrings
    - Minimum deprecation window: one `MINOR` release before removal
    - Document deprecations in `CHANGELOG` and API docs
- **Support**:
    - Maintain latest `MINOR` and previous `MINOR` for critical fixes (best-effort)

---

## Pre-Release Checklist

### Source and API

- [ ] All public APIs reviewed; docstrings updated; typing consistent and explicit
- [ ] SRP/DRY and ~200 lines/file guidance verified; split where needed
- [ ] Optional dependencies (Pydantic, OTEL, Prometheus) guarded and documented
- [ ] Example code imports from public API surfaces only

### Quality Gates

- [ ] Lint: ruff passes; formatting consistent
- [ ] Type: mypy (and/or pyright) passes on `src`
- [ ] Tests: pytest suites pass; coverage:
    - core ≥ 90%
    - overall ≥ 80%
- [ ] Benchmarks: no regressions beyond budget thresholds
- [ ] Stress/soak: nightly passing; no unbounded memory growth

### Docs and Examples

- [ ] `README` updated with final quickstart and links
- [ ] Docs: quickstart, api, patterns, troubleshooting, observability complete
- [ ] Metric catalog verified against code
- [ ] Examples: `hello_graph` and `pipeline_demo` validated via `uv run`
- [ ] Docs links validated (no broken references)

### Security and Compliance

- [ ] No secrets in repo; example configs do not include credentials
- [ ] License headers present; `LICENSE` file correct
- [ ] Supply-chain:
    - Reproducible builds (pinning, hashes)
    - Hash-checking enabled in lock files
- [ ] Optional: generate SBOM (best-effort) and attach to release

### Distribution

- [ ] `pyproject` configured with project metadata (name, summary, authors, classifiers)
- [ ] Build: sdist and manylinux/macOS wheels built via PEP 517 backend
- [ ] Sign artifacts (GPG) and/or use trusted publisher flow
- [ ] Test publish to staging/test index (if available)
- [ ] Final publish to PyPI
- [ ] Verify install: fresh virtual env, `uv sync`, import smoke, example run

### Downstream Readiness

- [ ] Update integration guide for downstream (e.g., Kraken) to pin `v1.0.0`
- [ ] Run compatibility smoke in downstream repo or a minimal consumer
- [ ] Capture upgrade notes and any breaking changes since RC/beta

---

## Release Workflow (CI)

**Trigger**: tag `v1.0.0` on main

**Steps**:

1. Checkout; set up Python; install build toolchain
2. `uv sync` (locked)
3. Quality gates: ruff, mypy, pytest with coverage
4. Build artifacts: sdist, wheels
5. Integrity checks: twine check; optional GPG signing
6. Publish to registry (conditional on all prior steps passing)
7. Create VCS release with notes, changelog excerpt, and artifact links
8. Post-publish smoke: create fresh env and install from registry; run `hello_graph`

---

## Release Notes Template

**Title**: Arachne `v1.0.0` — Minimal, Reusable Graph Runtime for Python

**Summary**:

- Core primitives (`Node`, `Edge`, `Subgraph`, `Scheduler`, `Message`, `PortSpec`)
- Bounded edges with `block`/`drop`/`latest`/`coalesce` policies and backpressure
- Control-plane priorities; fair cooperative scheduler
- First-class observability (logs, metrics hooks, tracing adapter)
- Utilities (`ids`, `time`, `validation`) and scaffolding generators

**Highlights**:

- Performance and fairness under load; priority preemption for kill switch
- Strong typing, SRP/DRY-friendly structure (~200 lines/file)
- `uv`-native dev workflow and examples

**Breaking Changes**:

- N/A for `v1.0.0` compared to last RC (list if any)

**Deprecations**:

- None in `v1.0.0` (list if any were declared)

**Upgrade Guide**:

- Pin `meridian-runtime>=1.0.0`
- Re-run examples with `uv`; verify observability config flags

**Known Issues**:

- Tracing disabled by default; enable only with optional dependency
- No distributed edges in v1; roadmap outlines future plans

**Thanks**:

- Acknowledge contributors and testers

---

## Post-Release Tasks

- [ ] Announce release (`README` badge, repo release, internal comms)
- [ ] Open `v1.x` milestone; triage backlog into minor/patch candidates
- [ ] Create docs for deprecation policy and contribution guidelines update
- [ ] Establish version pinning recommendations for downstreams
- [ ] Schedule periodic performance regression runs and publish dashboards

---

## Risk and Mitigations

- **Failed publish or partial artifacts**:
    - Mitigation: Dry-run to test index; atomic CI workflow; sig verification
- **API inconsistencies**:
    - Mitigation: API review checklist; examples import from public API only; type-check docs/examples
- **Performance regressions**:
    - Mitigation: Benchmarks with budgets in CI; rollback plan (yank release if critical)
- **Documentation drift**:
    - Mitigation: Link validation in CI; docs owners assigned; examples as living tests

---

## Acceptance Criteria

- `v1.0.0` tag created; artifacts published and signed; release notes available
- CI pipeline green on tag; post-publish install smoke passes on clean env
- Examples runnable; docs complete and cross-linked
- Downstream smoke green with `v1.0.0` pin
- `CHANGELOG` updated; deprecation and support policies documented