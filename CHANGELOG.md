# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog (https://keepachangelog.com/en/1.1.0/)
and this project adheres to Semantic Versioning (https://semver.org/spec/v2.0.0.html).

Owner: GhostWeasel (Lead: doubletap-dave)

## [Unreleased]

### Added
- Placeholder for upcoming changes after v1.0.0.

### Changed
- README Quickstart aligned to M1: dev loop commands (ruff, black, mypy, pytest) and scaffolded layout.

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## [1.0.0] - 2025-08-06
First stable release of Meridian Runtime with a SemVer-committed API and complete documentation.

### Added
- Core primitives: Node, Edge, Subgraph, Scheduler, Message, PortSpec, Policies with bounded edges and explicit overflow policies (block, drop, latest, coalesce).
- Observability: structured logging and metrics interface; tracing adapter hooks.
- Utilities: ids, time, validation; scaffolding tools for generate_node.py and generate_subgraph.py.
- Documentation: Quickstart, API overview, Patterns, Troubleshooting, Observability, and Roadmap.
- Examples: hello_graph, pipeline_demo (control-plane priorities/backpressure), streaming_coalesce, minimal_hello.
- GitHub Pages site with Material for MkDocs; improved UX scripts and Meridian Halo initialization.
- CI: docs deploy workflow; release workflow for PyPI Trusted Publishing (OIDC) triggered on v* tags; post-publish smoke install.

### Changed
- Consolidated docs structure and navigation; fixed internal links and added robust client-side enhancements.

### Deprecated
- None.

### Removed
- Pre-1.0 placeholders and legacy planning docs superseded by roadmap.

### Fixed
- Deterministic scheduler edge cases; message header semantics; examples and documentation alignment.
- Broken nav/link warnings that previously blocked strict builds (deploy workflow relaxed to avoid blocking on warnings).

### Security
- Adopted PyPI Trusted Publisher (OIDC) for secretless releases; integrity checks (twine check) in release workflow.

--------------------------------------------------------------------------------

Release Entry Guidelines

- Group changes under one of: Added, Changed, Deprecated, Removed, Fixed, Security.
- Write user-focused, concise entries. Link to issues/PRs/Decision Records where helpful.
- Note migration steps for breaking or behavior-changing updates.
- Keep privacy posture explicit for any observability/diagnostics changes.

Versioning Notes

- Follow SemVer:
  - MAJOR: incompatible API changes
  - MINOR: backward-compatible functionality
  - PATCH: backward-compatible bug fixes
- Experimental APIs must be clearly marked and may change in MINOR releases.

References

- Governance and Overview (M0): docs/plan/M0-governance-and-overview.md
- Releasing Guide: docs/contributing/RELEASING.md
- Future Roadmap: docs/roadmap/future-roadmap.md
