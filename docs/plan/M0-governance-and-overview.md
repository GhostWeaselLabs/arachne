# M0 — Governance and Overview (EARS)

Owner: GhostWeasel (Lead: doubletap-dave)
Status: Draft
Audience: Contributors, maintainers, and stakeholders preparing to implement Arachne Milestones M1–M8.

Purpose
This document establishes the governance model, scope boundaries, quality bar, and operational practices for the Arachne runtime. It also sets non-functional requirements, decision processes, and artifact expectations that apply to all subsequent milestones.

Guiding Principles
- Composable first: graphs, subgraphs, and clear boundaries.
- Async-friendly: Python 3.11+, asyncio-native.
- Predictable execution: fairness, backpressure, bounded edges.
- Observability by default: structured logs, metrics, optional tracing.
- Safety and privacy: no payloads in errors by default, redaction hooks.
- Maintainability: small, testable modules (~200 LOC/file guidance).
- Platform-agnostic: no host-specific assumptions (e.g., not GitHub-only).
- Docs-as-product: plans, support docs, and examples are first-class.

Non-Functional Requirements (EARS: Ubiquitous)
- The system shall be implemented in Python 3.11+ and be asyncio-friendly.
- The system shall avoid global mutable state and prefer explicit dependency injection at boundaries.
- The system shall provide deterministic resource cleanup for nodes and the scheduler.
- The system shall enforce bounded edges with configurable overflow policies.
- The system shall produce structured logs with stable keys and provide a metrics interface with consistent naming conventions.
- The system shall keep core packages dependency-light, with optional extras for validators and tracing.
- The system shall publish a clear public API with semantic versioning and a stability policy.
- The system shall maintain a baseline of type coverage (mypy), style (ruff), and automated tests (pytest).
- The system shall include user-facing documentation and examples demonstrating typical runtime patterns.
- The system shall separate control plane operations from data-plane work, with priority for control.

Out of Scope (EARS: State-driven “whenever building v1”)
- The system shall not include vendor-specific observability backends; it will expose generic interfaces and adapters.
- The system shall not ship a full-featured UI/dashboard in v1; it may provide CLI-based inspectors and structured outputs that other tools can consume.
- The system shall not implement distributed graph execution in v1; single-process, multi-task concurrency is in scope.
- The system shall not require a schema system; validation is optional via Pydantic or TypedDict where desirable.
- The system shall not embed secrets management or cloud-specific key stores; integration hooks are acceptable.

Governance Model (EARS: Ubiquitous)
- The project shall be owned by GhostWeasel, with Dave as lead maintainer.
- The project shall accept contributor changes via a documented contribution process, including code review and CI checks.
- The project shall prioritize API stability and backward compatibility within a major version.
- The project shall record major decisions via lightweight Decision Records (DRs) in docs/plan/dr/.
- The project shall adhere to a transparent, milestone-based roadmap that is documented and updated as necessary.
- The project shall apply a Code of Conduct (CoC) and enforce it consistently across all communication channels.
- The project shall maintain clear ownership for subsystems (runtime, scheduler, observability, CLI, docs) and rotate reviewers to spread knowledge.

Decision Process (EARS: Event-driven)
- When a contributor proposes a significant API change, the maintainers shall require an RFC or DR covering motivation, alternatives, migration plan, and impact.
- When interfaces or behaviors affect user data handling, the maintainers shall require a privacy and redaction review.
- When a release branch is cut, the lead maintainer shall define a freeze policy covering allowed changes, documentation finalization, and release notes.

Quality Bar (EARS: Ubiquitous)
- The system shall maintain CI checks for: lint (ruff), type-check (mypy), tests (pytest), and packaging (uv).
- The system shall maintain ≥ 80% code coverage in critical modules and ≥ 70% overall by M7, with risk-based exemptions documented.
- The system shall include structured logging via a minimal logging façade; no direct stdout prints in production code.
- The system shall provide meaningful error types and messages with contextual metadata and without sensitive payloads by default.
- The system shall provide reproducible examples with pinned versions and scripts to run locally.

Operational Practices (EARS: Ubiquitous)
- The project shall maintain a CONTRIBUTING document describing environment setup (uv), coding standards, branching, and commit conventions.
- The project shall maintain RELEASING documentation describing versioning, tagging, changelog, and post-release verification.
- The project shall maintain support documentation describing how users report issues, provide diagnostics bundles, and request features.
- The project shall prefer minimal, composable modules with single-responsibility orientation and explicit dependencies.
- The project shall ensure that blocking operations are isolated and documented, with async adapters where needed.

Security and Privacy (EARS: Unwanted)
- If a node attempts to log user-provided payloads, the logger shall redact sensitive fields by default where configured.
- If diagnostics bundles are generated, the bundle shall omit secrets, auth tokens, and personally identifiable information (PII) by default.
- If a graph contains validation failures, the runtime shall emit structured error events without including payload contents, unless explicitly enabled by the user with a redaction policy.
- If an unhandled exception occurs in a node, the runtime shall capture the exception, emit a structured error event, stop the node cleanly, and preserve the scheduler’s stability.

Compatibility and Versioning (EARS: Ubiquitous)
- The system shall follow SemVer for the public API, with clear documentation of what constitutes public versus private interfaces.
- The system shall target Python 3.11+ and keep language features within that baseline for v1.
- The system shall provide migration notes for any breaking changes, including code examples and find/replace suggestions where feasible.

Documentation Standards (EARS: Ubiquitous)
- The project shall maintain milestone plans under docs/plan with EARS framing for requirements.
- The project shall provide example graphs and recipes under examples/ with runnable instructions.
- The project shall keep support docs under docs/support and contributor docs under docs/contributing.
- The project shall ensure that README provides a concise overview, quickstart, and links to deeper docs.
- The project shall maintain an up-to-date post-v1 roadmap capturing near-term and longer-term work.

Scheduler and Runtime Policy (EARS: State-driven)
- While the runtime is starting, the scheduler shall prioritize control-plane tasks to ensure clean initialization and graph admission.
- While the runtime is steady-state, the scheduler shall enforce fairness across runnable tasks while respecting bounded edges and backpressure.
- While the runtime is shutting down, the scheduler shall drain in-flight work according to policy and guarantee on_stop hooks are called for nodes.

Observability Policy (EARS: Event-driven)
- When nodes transition lifecycle states, the runtime shall emit structured events and metrics with stable labels.
- When edges overflow their bounds, the runtime shall emit a structured event with policy details (block, drop, latest, coalesce).
- When tracing is enabled, spans shall capture node execution, scheduling, and edge operations with minimal overhead and no sensitive data by default.

Support and Issue Reporting (EARS: Event-driven)
- When a user requests help, the project shall provide templates for bug reports, feature requests, and general issues under docs/support/templates.
- When a user opts into a diagnostics bundle, the CLI shall collect logs, config snippets, and an anonymized snapshot of the graph and scheduler state.
- When an issue is submitted with a diagnostics bundle, maintainers shall use the anonymized snapshot to reproduce and triage without requiring user data.

Change Control (EARS: Event-driven)
- When a pull request is opened, CI shall run and block merging on failure.
- When a maintainer approves a PR that changes public APIs, the maintainer shall update changelogs and migration notes before merging.
- When a release candidate is tagged, the project shall perform smoke tests on examples and verify packaging integrity.

Risk Management (EARS: Unwanted)
- If a design proposal introduces unbounded queues or uncoordinated concurrency, the maintainers shall require mitigation or rejection with rationale.
- If an implementation would cause excessive coupling or hidden side effects, the maintainers shall require refactoring to restore SRP and composability.
- If observability features leak sensitive data by default, the maintainers shall mandate redaction policies and opt-in surfaces.

Deliverables in M0
- Governance and overview document (this file).
- Contributor guide: setup, standards, review process, commit/branch patterns, code of conduct reference.
- Releasing guide: SemVer policy, tagging, changelog process, publishing steps, support windows.
- Support docs: how to report issues, troubleshooting, templates for bug/feature/general requests.
- Decision Records directory and template for future significant changes.

Success Criteria for M0
- The governance model is documented and unambiguous.
- The quality bar and non-functional requirements are explicit and testable.
- Support and contributor documentation exists and is discoverable from README.
- Decision Records directory and template are ready for use.
- All subsequent milestones (M1–M8) can reference this document for process and policy alignment.

Appendix A: EARS Patterns Used
- Ubiquitous: “The system shall …” for cross-cutting requirements.
- Event-driven: “When <event>, the system shall …” for trigger-driven behaviors.
- State-driven: “While <state>, the system shall …” for lifecycle policies.
- Unwanted: “If <failure/undesired condition>, the system shall …” for error/resilience.
- Complex: Used sparingly; decompose into Ubiquitous/Event/State/Unwanted where possible.

Appendix B: Roles and Responsibilities
- Lead Maintainer (Dave): final arbiter on technical decisions, release management, roadmap ownership.
- Maintainers: code review, subsystem ownership, triage rotation, quality enforcement.
- Contributors: feature/bugfix implementation, doc improvements, tests, RFCs/DRs for major changes.
- Users: issue reporting, diagnostics bundle opt-in, feedback on APIs and examples.

Appendix C: Repository Conventions
- src/arachne/* for runtime packages.
- examples/* for runnable examples and recipes.
- docs/* for plans, support, contributing, and architecture notes.
- tests/* for unit, integration, and property-based tests where appropriate.
- scripts/* for helper tools (lint, type-check, release tasks).
- Keep files small and cohesive; prefer explicit imports and narrow module APIs.

End of M0