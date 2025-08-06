# Architecture Decision Record (ADR) Template

Status
One of: proposed | accepted | rejected | superseded | deprecated | withdrawn

ADR ID and title
Use incremental numbering or date-based IDs plus a short, lowercase-kebab-case title.
Example: ADR-0007-prefer-async-io

Context
What is the problem we’re trying to solve and why now?
- Background and business/technical drivers
- Constraints and assumptions
- Related systems, components, or stakeholders
- Prior decisions this depends on

Decision
The decision we made, stated clearly and unambiguously.
- What we will do
- What we will not do
- Scope (what’s included/excluded)

Rationale
Why we chose this option over alternatives.
- Evaluation criteria (e.g., performance, complexity, risk, cost, operability)
- Trade-offs considered
- Links to benchmarks, experiments, prototypes

Alternatives considered
List serious options and why they were not chosen.
- Alternative A
  - Pros
  - Cons
  - Why not chosen
- Alternative B
  - Pros
  - Cons
  - Why not chosen

Consequences
What happens because of this decision.
- Positive outcomes (benefits, simplifications)
- Negative outcomes (costs, new risks, limitations)
- Impact on teams, processes, tooling
- Operational considerations (observability, performance, reliability)
- Security and privacy implications

Technical details
Concise but concrete technical notes to implement and operate the decision.
- Interfaces/APIs and schema impacts
- Migration approach (data, code, config)
- Backward/forward compatibility
- Tuning and capacity planning notes
- Testing strategy (unit, integration, performance)
- Rollout plan and safeguards (feature flags, canary, rollback)

Open questions and follow-ups
Known unknowns and tasks that must be done.
- Unresolved questions
- Follow-up ADRs expected
- Issues/tickets created

Decision owner and reviewers
- Owner: person or role accountable
- Reviewers: key stakeholders who approved
- Inputs from: optional contributors consulted

References
Links to relevant materials.
- Related ADRs
- Design docs, issues, PRs
- External references (standards, libraries, blog posts)

Changelog
Track notable updates to this ADR.
- YYYY-MM-DD: Short note about what changed

Metadata
- Created: YYYY-MM-DD
- Last updated: YYYY-MM-DD
- Status: proposed | accepted | rejected | superseded | deprecated | withdrawn
- Supersedes: ADR-XXXX-title (if applicable)
- Superseded by: ADR-YYYY-title (if applicable)
- Tags: [architecture, performance, security, observability, api, storage, ops]

Authoring guidance
- Be brief but complete—optimize for decision clarity, not exhaustive prose.
- Prefer diagrams when they clarify complex flows.
- Record the decision now; you can refine technical details as they stabilize.
- Keep titles and filenames in lowercase-kebab-case.
- One decision per ADR; compose via references if necessary.
- If this ADR changes user-facing behavior or public APIs, link to docs PRs and migration guides.
