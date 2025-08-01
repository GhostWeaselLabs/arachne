# Decision Record: <Short, Descriptive Title>

Status: Proposed | Accepted | Rejected | Superseded by <DR-ID>  
Date: <YYYY-MM-DD>  
Authors: <Name(s)>  
Owners: GhostWeasel (Lead: doubletap-dave)

Summary
Concise overview (2–4 sentences) describing the decision, context, and impact.

Context and Problem Statement
Describe the problem this decision addresses and why it matters. Include relevant constraints, goals, and non-goals.

Goals (What this decision should achieve)
- …
- …

Non-Goals (What this decision does not cover)
- …
- …

Decision
State the decision clearly and unambiguously. If there are multiple parts, number them.

Rationale
Explain why this approach was chosen over alternatives. Include key trade-offs, guiding principles (e.g., composability, privacy-first, observability), and expected benefits.

Alternatives Considered
1) Alternative A
   - Pros:
   - Cons:
2) Alternative B
   - Pros:
   - Cons:
3) Do Nothing
   - Pros:
   - Cons:

EARS-Style Acceptance Criteria
Use clear, testable statements.
- Ubiquitous: “The system shall …”
- Event-driven: “When <event>, the system shall …”
- State-driven: “While <state>, the system shall …”
- Unwanted: “If <failure/undesired condition>, the system shall …”

Impact
API changes, compatibility considerations, and migration needs. Note implications to:
- Public APIs (SemVer)
- Scheduler/runtime behavior
- Observability (logs/metrics/traces)
- Privacy posture (no payloads in errors by default; redaction)
- Performance and resource usage
- Developer experience and documentation

Security and Privacy Considerations
Identify risks (data exposure, elevated permissions, sensitive logging) and mitigations (redaction, least privilege, opt-in surfaces).

Operational Considerations
Deployment, configuration, failure modes, rollback strategies, monitoring, and alerting implications.

Testing Strategy
- Unit tests:
- Integration tests:
- Regression tests:
- Performance/benchmark checks (if applicable):

Documentation Plan
- README updates
- docs/plan updates and cross-references
- Examples/recipes
- Support and troubleshooting notes

Rollout Plan
- Phasing/feature flags/opt-in defaults
- Backward compatibility measures
- Migration steps for users (code snippets, find/replace guidance)
- Deprecation timeline (if any)

Open Questions
- Q1:
- Q2:

References
- Related issues/PRs:
- Related DRs:
- External references/RFCs:

Changelog
Summarize what will appear in release notes if accepted.

Appendix (Optional)
Supporting diagrams, schemas (structure only—no payload contents), or extended analysis.