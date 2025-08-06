# Milestone M99: Quality Pass (Code Comments, Docs Fixes, CI Docs Checks)

**Status**: In Progress  
**Owner**: Core Maintainers (Lead: `doubletap-dave`)  
**Duration**: 2–4 days  
**Branch**: `main` (merged via PR #13 from `feature/m99-quality-pass`)

## 1) Purpose

Elevate overall project quality before the next milestone by ensuring:

- Public code surfaces are properly documented with clear, typed docstrings and inline comments where helpful.
- Documentation renders correctly on both GitHub and the GitHub Pages site (MkDocs Material).
- Documentation is sufficiently detailed, cohesive, and discoverable.
- CI validates docs build, checks links, and optionally validates code snippets where feasible.

## 2) Standards and Scope

### Standards (EARS: Ubiquitous)

- The project shall follow SRP/DRY and ~200 LOC/file guidance for maintainability.
- The codebase shall expose discoverable, typed public APIs with module/class/function docstrings and usage notes.
- The documentation shall render without layout/formatting surprises on both GitHub (Markdown viewer) and MkDocs (Material theme).
- CI shall validate docs build and perform link checks, and optionally verify example/snippet execution where reasonable.

### Scope

- `src/`: docstrings and comments for public APIs and complex logic.
- `docs/`: formatting fixes, readability polish, navigation sanity.
- `examples/`: light commentary to guide new users.
- CI: add docs build + link checking, optional snippet validation, and verification that all workflows are green (lint, type, tests, packaging, pages deploy).

### Out of Scope (for M99)

- Feature work or API changes beyond documentation clarifications.
- New examples beyond small snippet adjustments.
- Heavy redesign of the docs site IA—only iterative improvements.

---

## 3) EARS Requirements

### Documentation Rendering & Structure

- **Ubiquitous**: The documentation shall render correctly on GitHub and on the MkDocs site with the Material theme.
- **Event-driven**: When documentation contains visual separators, the content shall avoid bare YAML front-matter delimiters (`---` at top of file or isolated lines) that cause rendering ambiguity; use `***` or `<hr>` instead.
- **Unwanted**: If a Markdown page references another page, links shall be valid for both GitHub preview and MkDocs navigation (prefer root-relative in MkDocs or local paths without `../docs`).
- **State-driven**: While using fenced code blocks, the docs shall specify language identifiers (`bash`, `python`, `toml`, `yaml`, etc.) for proper highlighting and readability.

### Documentation Completeness & Clarity

- **Ubiquitous**: The docs shall include clear Quickstart, API overview, Patterns, Observability, and Troubleshooting pages with navigable links from the homepage.
- **Event-driven**: When an example is introduced, the docs shall include concise, copy‑paste commands to run it (`uv` commands).
- **Unwanted**: If a concept is introduced (e.g., "latest" policy), the docs shall cross-link to the API definitions or Patterns section where the behavior is documented, avoiding duplication.
- **State-driven**: While the docs evolve, each page shall retain a "last updated" indicator (plugin-backed), and broken links shall be flagged in CI.

### Code Comments & Docstrings

- **Ubiquitous**: The `src/meridian` package shall provide docstrings for public classes, functions, and modules that describe contracts, parameters, return types, and error/side-effects semantics.
- **Event-driven**: When code includes non-obvious decisions or performance-sensitive logic, the code shall include short comments explaining rationale and expected complexity trade-offs.
- **Unwanted**: If a public symbol lacks docstrings, the linter/checker shall fail (or at minimum surface warnings) during CI for M99.
- **State-driven**: While maintaining small files, docstrings shall be concise yet sufficient—favor references to API sections in docs for deeper narratives.

### CI Docs Checks

- **Ubiquitous**: The CI shall build MkDocs and publish artifacts only if docs build succeeds for main and PRs.
- **Event-driven**: When CI runs for PRs, it shall run a link checker against the built site or Markdown corpus and fail on broken links.
- **Unwanted**: If docs contain malformed Markdown (e.g., unterminated fences), CI shall fail and provide actionable error output.
- **Complex**: Where feasible, CI shall validate selected code snippets (shell/python) using a lightweight snippet checker or example execution smoke (best-effort, non-flaky).

### CI Workflow Health (All Jobs Green)

- **Ubiquitous**: All GitHub Actions workflows (lint, format check, type-check, tests with coverage, packaging, and GitHub Pages deploy) shall complete successfully on main and PRs.
- **Event-driven**: When a workflow fails, the project shall triage and fix the failure prior to merge; flaky jobs shall be stabilized or quarantined with clear tracking.
- **Unwanted**: If a job is intermittently flaky, CI shall apply retries only as a temporary mitigation while a root-cause fix is implemented and documented.
- **State-driven**: While coverage targets are enforced, thresholds shall be explicit and documented; any temporary relaxations shall be tracked and time-bounded.

---

## 4) Deliverables

### Code Documentation

- Pass across `src/meridian/core/*`, `src/meridian/observability/*`, `src/meridian/utils/*` to ensure public classes/functions have docstrings with:
    - Purpose and contracts
    - Parameters and types
    - Return values and types
    - Exceptions and side effects
    - Notes on performance or hot-path constraints (where relevant)

### Docs Rendering Fixes

- Replace problematic horizontal rule markers (`---` used as separators) with `***` or HTML `<hr>`.
- Ensure code fences specify languages consistently.
- Normalize relative links to be valid in both GitHub and MkDocs (avoid `../docs` patterns).
- Confirm nav entries correspond to real files; adjust headings where it improves page structure.

### Docs Completeness

- Align homepage references (Quickstart, API, Patterns, Observability, Troubleshooting) and ensure they are consistent and discoverable.
- Add clarifying examples where minimal, and cross-link to deeper documentation.

### CI Enhancements (docs-specific)

- Job to build MkDocs site.
- Link check job (Markdown or built site).
- Optional snippet verification job for small example blocks or end-to-end example smoke run.

### CI Workflow Health

- Ensure existing jobs (lint, format, type-check, tests with coverage, packaging) are green.
- Ensure Pages deploy workflow is green and publishes the site successfully.
- Add failure triage guidance and ownership for broken or flaky jobs.

---

## 5) Work Breakdown

### Task Group A: Code Docstrings and Comments

- **A1**: Inventory public surfaces in `src/meridian/core/` and add or refine docstrings.
- **A2**: Inventory `src/meridian/observability/` and document adapters and configuration flows.
- **A3**: Inventory `src/meridian/utils/` and add examples to docstrings where helpful.
- **A4**: Add rationale comments for performance-sensitive or non-obvious logic.

### Task Group B: Docs Formatting and Links

- **B1**: Replace bare `---` separators in docs with `***` or `<hr>` where used as visual separators.
- **B2**: Add language identifiers to code blocks (`bash`, `python`, `toml`, `yaml`).
- **B3**: Normalize internal links:
    - Homepage → `quickstart`/`api`/`patterns`/`observability`/`troubleshooting`
    - Remove `../docs` pathing in Markdown links; prefer local MkDocs-friendly paths.
- **B4**: Validate headings and page structure for readability and consistent navigation.

### Task Group C: Docs Completeness

- **C1**: Tighten Quickstart commands; ensure `uv`-based steps are copy-paste-able.
- **C2**: API overview alignment: ensure section titles map to public API and reference core docs.
- **C3**: Patterns: ensure short examples and cross-links to API semantics (`block`/`drop`/`latest`/`coalesce`).
- **C4**: Observability: confirm metric names align with docs; add sample configuration snippet.
- **C5**: Troubleshooting: add clearer remediation steps for common miswiring/type issues.

### Task Group D: CI Docs Checks

- **D1**: Add job to build the MkDocs site (PR and main).
- **D2**: Add link-check job (Markdown or built site).
- **D3**: Optional: snippet execution checks or example smoke runs for docs examples (best-effort).
- **D4**: Cache dependencies appropriately for speed.

### Task Group E: CI Workflow Health (All Jobs Green)

- **E1**: Audit all workflows (lint, format, type-check, tests, coverage, packaging, Pages deploy) for current failures and flakiness.
- **E2**: Fix failing jobs (tool pinning, cache keys, step ordering, permissions, concurrency) and stabilize flaky steps.
- **E3**: Enforce required checks on PRs; document ownership and escalation for CI failures.
- **E4**: Record coverage thresholds and ensure reporting; revisit temporary relaxations and set timelines to restore targets.
- **E5**: Add code scanning (CodeQL) and enable weekly scans; update ruleset to require code scanning results after first successful run.
- **E6**: Add Dependabot for GitHub Actions and Python packages (including docs tooling) with weekly cadence and minimal churn.

---

## 6) Acceptance Criteria

### Documentation

- All Markdown pages render correctly on both GitHub and the MkDocs site.
- No broken links in CI's link-check job.
- Code fences include proper language identifiers.
- Homepage and README consistently link to Quickstart, API, Patterns, Observability, and Troubleshooting.

### Code Docstrings

- All public classes, functions, and modules in `src/meridian` have typed docstrings with contracts and side effects where applicable.
- Comments exist for non-obvious logic and performance-sensitive sections.

### CI

- CI builds docs and fails on errors. **Status**: Implemented and green.
- Link-check job passes; broken links fail PRs. **Status**: Running but currently non-blocking pending stability.
- Optional snippet/execution checks pass or are quarantined with clear skip rationale. **Status**: "Validate docs commands" using `uv` is passing.
- All workflows (lint, format, type-check, tests with coverage, packaging, Pages deploy) pass on PRs and main; any temporary skips or relaxations are documented and time-bounded. **Status**: Green on main; badge reflects passing.

---

## 7) Risks and Mitigations

### Risk: CI flakiness in link checking/snippet execution

**Mitigation**: Start with deterministic link checking; add snippet checks selectively; mark unstable checks as optional or nightly until stable.

### Risk: Overly heavy docstrings or duplicated narratives across code and docs

**Mitigation**: Keep docstrings concise and link to docs for deeper narratives; avoid duplication.

### Risk: Formatting differences between GitHub and MkDocs causing surprises

**Mitigation**: Use robust Markdown practices (language fences, avoid front-matter markers as separators, prefer simple relative links).

### Risk: Docs build time increase

**Mitigation**: Cache dependency installs; skip analytics/extras in CI builds.

---

## 8) Implementation Notes and Conventions

### Docstrings

- Use concise summaries (first line), followed by parameter/return type details.
- Capture error semantics and side effects (e.g., scheduling, I/O, metrics emission).
- Reference corresponding sections in docs with stable page anchors where helpful.

### Markdown Practices

- Replace horizontal rules `---` used as visual separators with `***` or `<hr>` (avoid YAML front-matter ambiguity).
- Prefer short, local relative links in Markdown (e.g., `./quickstart.md`) that MkDocs resolves to `/quickstart/`.
- Always specify language for code fences: ````bash`, ````python`, ````toml`, ````yaml`, etc.
- Keep commands copy-paste friendly; avoid prompts (`$`).

### CI

- Build docs as part of PR checks.
- Run link-checker against the built site or `.md` files.
- Gate merges on docs build + link checks.
- Optionally run a quick snippet or example smoke to catch drift.

---

## 9) CI Checklist (High-Level)

- [x] Docs build job added to CI (PR + main). **Notes**: MkDocs build job is green and runs on PRs and main.
- [x] Link-checking job added and green. **Notes**: Link-check runs with retries and caching; promotion to "required" is a manual branch protection step after observing stability on main.
- [x] Optional snippet execution or example smoke job (allowed to fail initially, then promote to required). **Notes**: "Validate docs commands" fixed via `uv`; runs successfully.
- [x] All workflow jobs green on PRs and main: lint, format, type-check, tests with coverage, packaging, and Pages deploy. **Notes**: CI badge reflects passing; flaky link checks quarantined.
- [x] Coverage thresholds enforced and documented; relaxations (if any) tracked with a deadline to restore targets.
- [ ] Ownership and on-failure triage guidance documented.

---

## 10) Execution Checklist

### Code Documentation

- [x] `src/meridian/core/*` docstrings complete and typed — Completed across Node, Message, Ports, Policies, Edge, Priority Queue, Runtime Plan, Subgraph, and module init. Includes parameters, returns, exceptions, and side‑effects.
- [x] `src/meridian/observability/*` docstrings complete and typed — Completed for logging, metrics, tracing, and unified config; includes usage and configuration semantics.
- [x] `src/meridian/utils/*` docstrings complete and typed — Completed for ids, time, and validation helpers; clarified legacy aliases and shallow vs. runtime validations.
- [x] Non-obvious logic annotated with short clarifying comments — Added notes on backpressure, fairness model, coalescing behavior, and timing utilities.

### Docs Rendering and Structure

- [x] Replace `---` separators with `***` or `<hr>` where used visually — Completed in docs sweep (PR #13)
- [x] Add language identifiers to all fenced code blocks — Completed in docs sweep (PR #13)
- [x] Normalize internal links (no `../docs` in page body) — Completed in docs sweep (PR #13)
- [x] Validate headings and section structure for scanability — Completed primary pass (Quickstart, Patterns). Further polish optional.

### Docs Completeness

- [x] Quickstart commands are consistent and copy‑paste ready — Updated and verified (PR #13)
- [x] API overview aligned with public classes and semantics — Verified anchors and examples; incremental fixes applied (PR #13)
- [x] Patterns include small examples; cross-link to API — Examples fixed; anchors normalized (PR #13)
- [x] Observability metrics and configuration confirmed and exemplified — Example confirmed; no changes required in sweep
- [x] Troubleshooting includes clear remediation steps — Filled code fences and commands (PR #13)

### CI Docs Checks

- [x] MkDocs build job added and green — Site build verified on PRs and main.
- [x] Link-check job added and green — Stabilized with caching and retries; promotion to "required" is a manual branch protection change once main has clean passes.
- [x] Optional snippet/execution checks configured or queued for nightly — "Validate docs commands" fixed using `uv` and passing.

### CI Workflow Health

- [x] All jobs green on PRs and main (lint, format, type-check, tests with coverage, packaging, Pages deploy) — CI badge now passing.
- [x] Flaky jobs identified with a mitigation plan and owner — Link-check flakiness mitigated via ignores and non-blocking status.
- [x] Coverage thresholds enforced; relaxations documented and time-bounded — Gate set via `pytest --cov-fail-under` in CI; documented thresholds and restoration timelines captured in CONTRIBUTING and M99 notes.
- [x] Code scanning added and scheduled — CodeQL workflow runs on PRs, main, and weekly; "Require code scanning results" enabled in the main ruleset (CodeQL).
- [x] Dependency automation added — Dependabot configured for GitHub Actions, Python packages, and docs tooling with weekly updates.

---

## 11) Traceability

- Aligns with M0 governance (SRP/DRY, small modules, docs-as-product).
- Supports M6 documentation outcomes by ensuring consistent rendering and completeness.
- Prepares for M7/M8 by preventing documentation regressions and ensuring code/API are discoverable via docstrings.

---

## 12) Change Management

- Update CHANGELOG with a Quality section noting documentation and CI improvements. — Next PR
- Review PRs for docstring quality and Markdown formatting alignment. — Ongoing
- Enforce docs build and link checks as required PR gates after proving stability. — Promotion of link-check to "required" occurs via a manual branch protection setting after stability on main. Code scanning requirement enabled: "Require code scanning results" (CodeQL) is active in the main ruleset.

---

## 13) Acceptance Sign-off

- **Owner**: Lead maintainer validates CI additions, rendering fixes, and docstring completeness.
- **Criteria**: Docs sweep merged in PR #13; CI green; proceed to promote link-check to required after stability; finalize coverage thresholds and triage ownership notes.
