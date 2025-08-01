# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog (https://keepachangelog.com/en/1.1.0/)
and this project adheres to Semantic Versioning (https://semver.org/spec/v2.0.0.html).

Owner: GhostWeasel (Lead: doubletap-dave)

## [Unreleased]

### Added
- M1 scaffold: `pyproject.toml` with uv-managed workflow; tooling configs for ruff, black, mypy, pytest/coverage.
- Repository layout: `src/arachne/` package skeletons, `tests/unit` and `tests/integration` smoke tests, `examples/` package placeholder.
- CI: GitHub Actions workflow to run lint, format check, type check, and tests with coverage gate (≥80%).
- Documentation updates in README for dev loop with uv; BSD 3-Clause `LICENSE`.

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

## [0.0.0] - YYYY-MM-DD
Bootstrap version placeholder. Replace with the first tagged release entry.

### Added
- Project skeleton and documentation map in README.

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

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
- Post‑v1 Roadmap: docs/plan/99-post-v1-roadmap.md