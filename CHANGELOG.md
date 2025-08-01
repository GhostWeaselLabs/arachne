# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog (https://keepachangelog.com/en/1.1.0/)
and this project adheres to Semantic Versioning (https://semver.org/spec/v2.0.0.html).

Owner: GhostWeasel (Lead: doubletap-dave)

## [Unreleased] — 2025-08-01

### Added
- Smart .gitignore for Python/uv/tooling caches, editor settings, diagnostics bundles, and private notes patterns.
- Documentation guidance to keep public docs (plan/contributing/support) visible while excluding private notes under `Arachne/docs/private/`.
- Initial documentation scaffolding for governance (M0), roadmap, contributing, releasing, and support.
- Privacy‑first support materials and issue templates.

### Changed
- README now links to docs and SUPPORT policy with privacy‑first reporting.

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
- Post‑v1 Roadmap: docs/plan/post-v1-roadmap.md