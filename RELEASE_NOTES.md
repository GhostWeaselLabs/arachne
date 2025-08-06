# Meridian Runtime v1.0.0 — Release Notes

Date: 2025-08-06
Tag: v1.0.0
Package: meridian-runtime

Meridian Runtime delivers a minimal, reusable, and observable graph runtime for Python with bounded edges, fairness, and clear operational semantics. This is the first stable release with a SemVer‑committed API surface.

## Highlights

- Core primitives (`Node`, `Edge`, `Subgraph`, `Scheduler`, `Message`, `PortSpec`, `Policies`)
- Bounded edges with explicit overflow policies (`block`, `drop`, `latest`, `coalesce`) and backpressure by default
- Control‑plane priorities and fair scheduling for predictable behavior under load
- First‑class observability (structured logs, metrics hooks, tracing adapter hooks)
- Utilities (`ids`, `time`, `validation`) and scaffolding (`generate_node.py`, `generate_subgraph.py`)
- Examples: `hello_graph`, `pipeline_demo`, `streaming_coalesce`, `minimal_hello`
- Docs site (Material for MkDocs) with improved UX and Halo initialization
- CI: Docs deploy and PyPI release via Trusted Publisher (OIDC), with post‑publish smoke install

## What’s new in v1.0.0

### Added
- Stable public API surfaces:
  - Core: `Node`, `Edge`, `Subgraph`, `Scheduler`, `Message`, `PortSpec`, `Policies`
  - Observability: logging, metrics interface (extensible), tracing adapter hooks
  - Utils: `ids`, `time`, `validation`
  - Scaffolding: `generate_node.py`, `generate_subgraph.py`
- Deterministic, fair scheduling with control‑plane priorities (e.g., kill switch preemption)
- Bounded edges with explicit overflow policies and backpressure semantics
- Documentation set:
  - Getting started (Guide, Quickstart)
  - Concepts (Architecture, Patterns, Observability, Glossary)
  - Reference (API)
  - Guides and Examples
- Examples demonstrating:
  - Minimal graph wiring
  - Control‑plane priorities and preemption (`pipeline_demo`)
  - Streaming coalesce (burst smoothing with deterministic merges)
- Release pipeline:
  - GitHub Pages deploy for docs
  - PyPI publish via Trusted Publisher (OIDC) on `v*` tags
  - Post‑publish smoke install to validate distribution integrity

### Changed
- Consolidated documentation structure and navigation; normalized internal links
- Robust front‑end extras (smooth anchors, keyboard shortcuts, safe link handling)
- Relaxed docs deploy to not fail on warnings (link checking enforced on PRs)

### Fixed
- Scheduler and message header edge cases under load
- Example consistency across docs and codebase
- Intermittent link/navigation issues that previously triggered strict build failures

### Security
- Adopted PyPI Trusted Publisher (OIDC) for secretless releases
- Integrity checks (`twine check`) in the release workflow
- No secrets committed; CI uses ephemeral OIDC tokens

## Upgrade Guide

- Requirement: Python 3.11+
- Install/Upgrade:
  - `pip install -U meridian-runtime`
- Example verification (optional, using uv):
  - `uv run python -m examples.hello_graph.main`
  - `uv run python examples/pipeline_demo/main.py --human --timeout-s 6.0`
  - `uv run python examples/streaming_coalesce/main.py --human --timeout-s 5.0`
- Observability:
  - Logging/metrics hooks are no‑op by default; enable adapters as needed
- API Stability:
  - The listed public surfaces follow SemVer from v1.0.0 onward
  - Avoid importing from private/underscored modules

## Deprecations

- None introduced in v1.0.0
- Deprecation policy:
  - Deprecations will be announced in a `MINOR` release and remain for at least one subsequent `MINOR` before removal
  - Documented in release notes and API docs

## Known Issues

- Tracing adapter is provided as hooks/extensions and may require optional dependencies
- Distributed/multiprocess execution is out of scope for v1.0.0 (see roadmap for future plans)

## Release Process (Summary)

- Tagging: push `v1.0.0` on main
- CI gates (recommended): lint, type, tests/coverage (configurable), then build sdist/wheels
- Publish: PyPI via Trusted Publisher (OIDC)
- Docs: GitHub Pages deploy on main push
- Post‑publish smoke: fresh env, install exact version, import and run example

## Links

- Docs: https://ghostweasellabs.github.io/meridian-runtime/
- Repository: https://github.com/ghostweasellabs/meridian-runtime
- Issues: https://github.com/ghostweasellabs/meridian-runtime/issues
- Discussions: https://github.com/ghostweasellabs/meridian-runtime/discussions

## Thanks

Thanks to contributors and testers who helped shape the API, examples, and documentation. Your feedback on performance, ergonomics, and observability guided the v1.0.0 cut.

---