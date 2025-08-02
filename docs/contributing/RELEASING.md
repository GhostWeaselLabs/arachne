# Releasing Meridian Runtime

Owner: GhostWeasel (Lead: doubletap-dave)
Audience: Maintainers and release managers
Status: Stable

This guide describes the end-to-end process for preparing, tagging, verifying, and publishing a release of Arachne. It follows Semantic Versioning (SemVer) and emphasizes reliability, privacy, and reproducibility.

-------------------------------------------------------------------------------

1) Versioning Policy (SemVer)

We follow semantic versioning for all public APIs:

- MAJOR (X.y.z): incompatible API changes
- MINOR (x.Y.z): backward-compatible functionality
- PATCH (x.y.Z): backward-compatible bug fixes

Public API scope:
- Anything documented in README and docs, public classes/functions/types in primary packages, and command-line interface behaviors.
- Experimental APIs must be marked clearly and may change across minor versions.

Breaking changes:
- Require an RFC/Decision Record (DR), migration notes, and explicit changelog entries.
- Avoid breaking changes in MINOR and PATCH releases.

-------------------------------------------------------------------------------

2) Pre-Flight Checklist

Ensure the following before cutting a release:

- Roadmap and DRs
  - Any release-defining DRs merged and linked.
  - M0 governance and policies still accurate or updated.

- Quality gates
  - Lint: clean
  - Types: clean
  - Tests: all pass locally and in CI
  - Coverage targets: ≥ 80% critical modules, ≥ 70% overall (exceptions documented)
  - Packaging sanity: build succeeds and artifacts import cleanly

- Documentation
  - README: current quickstart, status, links to docs
  - docs/plan: updated if scope changed
  - docs/support: updated troubleshooting if necessary
  - examples/: runnable with pinned deps (or uv) and instructions

- Observability and privacy posture
  - No payload contents in error events/logs by default
  - Redaction hooks tested where applicable
  - Diagnostics instructions current

- Dependency review
  - Minimal, vetted runtime dependencies
  - No accidental dev-only packages leaking into runtime
  - License compatibility ok

-------------------------------------------------------------------------------

3) Determine Next Version

Decide the version bump type based on changes since the last release:

- PATCH: bug fixes, performance improvements without API changes, documentation-only changes that don’t alter published APIs, test infra
- MINOR: new features, optional adapters, new CLI subcommands that are backward compatible
- MAJOR: breaking changes, removed/renamed public APIs, incompatible behavior changes

Record the rationale:
- In the changelog’s “Unreleased → <version>” section
- In any relevant DRs

-------------------------------------------------------------------------------

4) Changelog Management

Location: CHANGELOG.md (or equivalent in the repository root)

Structure:
- Unreleased
- <version> — YYYY-MM-DD
  - Added
  - Changed
  - Deprecated
  - Removed
  - Fixed
  - Security

Guidelines:
- Use terse, user-focused entries.
- Link to PRs/issues/DRs for context.
- Include migration notes for any behavior or API changes.
- Call out privacy/observability behavior changes explicitly.

Process:
1. Move items from Unreleased to a new section for the version.
2. Ensure every entry is clear and actionable for users.
3. Leave an empty Unreleased section for future work.

-------------------------------------------------------------------------------

5) Update Version and Metadata

- Update the package version (pyproject.toml or version module).
- Update any version strings in documentation if necessary.
- Verify dependency pins for examples and lockfiles for tools (e.g., uv).

Version consistency checks:
- Build artifact shows the intended version.
- Importing the package yields the same version (e.g., arachne.__version__ if present).
- CLI reports the same version when applicable.

-------------------------------------------------------------------------------

6) Build and Sanity Check

Local build:
- Build source and wheel artifacts using the project’s standard tooling.
- Confirm artifacts are small and do not include unnecessary files.

Sanity tests:
- Create a clean virtual environment.
- Install the local artifact(s).
- Import key modules; run a small example or smoke tests.
- Run ruff, mypy, and pytest in a controlled environment to confirm no packaging regressions.

-------------------------------------------------------------------------------

7) Verification Suite

Run smoke and integration checks:
- Examples: run the primary examples end-to-end
- Scheduler: verify fairness basic invariants and clean shutdown
- Bounded edges: verify overflow policies (block, drop, latest, coalesce)
- Observability: verify structured logs appear with expected keys
- Error handling: ensure no payload contents in error events by default
- Type-check and lint: clean
- Tests: full suite green

Performance sanity:
- Run lightweight micro-benchmarks or repeatable load scripts (if present)
- Compare results to previous release ranges (no significant regressions)

-------------------------------------------------------------------------------

8) Tagging and Signing

Create a release commit:
- Include:
  - Version bump
  - Updated CHANGELOG.md
  - Any migration notes in docs
  - Any updated example pins
- Ensure CI is green on the release commit.

Tagging:
- Use annotated tags: vX.Y.Z
- Include a concise message with highlights and links to the changelog
- If applicable, sign the tag using your standard signing key

Example:
- git tag -a vX.Y.Z -m "Arachne vX.Y.Z — highlights: <short summary>"
- git push origin vX.Y.Z

-------------------------------------------------------------------------------

9) Publish Artifacts

- Push build artifacts to the designated package registry.
- Verify the artifacts are present and downloadable.
- Confirm installation from the registry in a clean environment:
  - New venv
  - Install from registry
  - Import, run quick sample, verify version

-------------------------------------------------------------------------------

10) Post-Release Verification

- Re-run quickstart from README against the published package.
- Validate that examples work with the released version (not local artifacts).
- Open and track a “Post-release verification” issue with:
  - Release version
  - Verification steps completed
  - Any anomalies and follow-ups

-------------------------------------------------------------------------------

11) Communications

- Update release notes: copy highlights from the changelog with any additional context (e.g., migration notes).
- Broadcast to the project’s communication channels (e.g., mailing list, forums, or chat) in a concise announcement:
  - What changed
  - Why it matters
  - How to upgrade
  - Links to docs, issues, and examples

-------------------------------------------------------------------------------

12) Hotfixes

When a critical issue is found post-release:

- Create a hotfix branch from the release tag.
- Apply minimal, surgical fixes with tests.
- Repeat verification and packaging steps.
- Bump PATCH version.
- Update changelog under “Fixed”.
- Tag and publish the hotfix release.

-------------------------------------------------------------------------------

13) Backport Policy

- Backport only critical bug fixes and security patches to previous minor versions still within support.
- Document supported versions and timelines in M0 or a SUPPORT policy file.
- Clearly note backports in changelog sections corresponding to older lines.

-------------------------------------------------------------------------------

14) Release Roles and Sign-Off

Recommended roles:
- Release Manager: coordinates the process, final sign-off
- Build/Packaging Owner: prepares and validates artifacts
- QA/Verification Owner: runs verification suite and examples
- Docs Owner: updates changelog and user docs

Sign-off checklist:
- [ ] Version bump and changelog updates are correct
- [ ] CI green on release commit
- [ ] Artifacts built and validated locally
- [ ] Artifacts published to registry
- [ ] Clean install from registry verified
- [ ] Examples and smoke tests pass on published bits
- [ ] Announcement ready and posted
- [ ] Post-release verification issue filed

-------------------------------------------------------------------------------

15) Troubleshooting

Common issues:
- Missing files in wheel/sdist: review MANIFEST or tooling configuration
- Version mismatch between package and docs: search/replace version strings, centralize version if possible
- Dependency leakage: isolate dev-only dependencies; confirm minimal runtime deps
- Observability regressions: ensure structured logging keys remain stable; update docs/tests where needed
- Privacy concerns: re-check redaction paths; audit error events and diagnostics instructions

-------------------------------------------------------------------------------

16) Checklists

Minimal Release Checklist
- [ ] Decide version bump (MAJOR/MINOR/PATCH)
- [ ] Update version metadata
- [ ] Update CHANGELOG.md and docs as needed
- [ ] Lint, type-check, test locally and in CI
- [ ] Build artifacts and perform clean install test
- [ ] Tag release and push tag
- [ ] Publish artifacts to registry
- [ ] Verify published package with examples
- [ ] Announce and open post-release verification issue

Breaking Change Checklist (Major releases)
- [ ] DR for the breaking changes merged
- [ ] Migration notes in changelog and docs
- [ ] Examples updated
- [ ] Clear communications  about impact and upgrade path

-------------------------------------------------------------------------------

Appendix A: References
- Governance and overview: docs/plan/M0-governance-and-overview.md
- Milestones and plans: docs/plan/
- Support and troubleshooting: docs/support/
- Decision Records: docs/plan/dr/

End of document.