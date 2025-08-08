---
title: Deprecation policy
icon: material/alert-decagram
---

# Deprecation policy

We follow Semantic Versioning (SemVer): MAJOR.MINOR.PATCH.

- Breaking changes only in MAJOR versions.
- MINOR versions may add features and deprecate APIs.
- PATCH versions include bug fixes and internal-only changes.

## Deprecation process

1. Mark API as deprecated with clear warnings in docs and code (where applicable).
2. Maintain the deprecated API for at least one MINOR release after the deprecation is announced.
3. Remove the deprecated API in the next MAJOR release.

## Guidance

- Prefer additive changes when possible.
- Provide migration notes and examples in the release notes.
- Emit non-intrusive warnings (logging/doc) rather than raising errors.

## Compatibility guarantees

- Built-in nodes aim for forward-compatible configuration defaults.
- Node behavior changes will be documented and versioned with clear guidance.
