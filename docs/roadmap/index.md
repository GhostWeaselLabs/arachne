# Roadmap

This directory contains the Meridian Runtime roadmap: a sequenced set of milestones that communicate priorities, expected order of work, and scope at a glance.

## Purpose

- Provide a clear, incremental path from foundation to stable releases.
- Make trade-offs and sequencing explicit so contributors can align efforts.
- Keep a historical record of planning assumptions as they evolve.

## How It's Organized

- Milestones are organized to preserve logical order and make sequencing obvious:
  - `00-...`: upstream requirements and architecture inputs
  - Sequential milestones: major development phases leading to v1 and quality passes
- Each file is a focused, self-contained plan for a milestone with:
  - Goals and non-goals (what's in/out)
  - Deliverables and acceptance criteria
  - Dependencies and risks
  - Rough timelines or checkpoints (if applicable)
  - Links to issues/PRs as the plan progresses

## Reading Order (Recommended)

1. [EARS Requirements and Architecture](00-ears-requirements-and-architecture.md)
   Context and upstream requirements that influence early decisions.

2. [Governance and Overview](governance-and-overview.md)
   Project structure, governance, and high-level vision.

3. [Bootstrap & CI](bootstrap-and-ci.md) → [Release v1.0.0](release-v1.0.0.md)
   Sequential execution from core bootstrapping to stable release.

4. [Quality Pass](quality-pass.md)
   Hardening, polish, and quality improvements that require broad coverage.

5. [Future Roadmap](future-roadmap.md)
   Post-v1.0.0 initiatives and long-term planning for future releases.

## FAQ

See our [FAQ page](../support/faq.md) for answers to common questions about the roadmap and contributing.

## Contributing to the Roadmap

### Small Edits to an Existing Milestone

Make a PR that:
- Clearly states the change (scope adjustment, acceptance criteria, dependency update).
- Links to evidence (benchmarks, incidents, prototypes) when changing scope or risk.

### New Milestone Proposal

1. Copy the template below into a new `milestone-title.md` (use descriptive names that indicate the milestone's purpose).
2. Open a PR and request review from maintainers.

### Renumbering or Resequencing

- Avoid churn. If order must change, prefer updating dependencies and "Order of operations" instead of renaming files.
- If a rename is necessary, include redirect notes in docs (if external links exist) and update references across the repo.

## Milestone Template

Copy this into a new file and fill in the sections. Keep it tight and actionable.

```yaml
---
title: milestone-concise-title
status: proposed | accepted | in-progress | done | deferred
owner: maintainer-or-team
last_updated: YYYY-MM-DD
dependencies: [previous-milestone, external-reqs]
---
```

### Summary

One paragraph: what this milestone achieves and why it's important now.

### Goals

- Concrete, testable outcomes
- User-visible improvements and/or technical capabilities

### Non-goals

- Explicitly out-of-scope items to prevent scope creep

### Deliverables

- Features and artifacts (docs, examples, APIs, tooling)
- Acceptance criteria (how we know we're done)

### Order of Operations

1. Step or sub-workstream with rationale
2. Step or sub-workstream
3. Step or sub-workstream

### Risks and Mitigations

- **Risk**: description
  - **Mitigation**: approach
- **Risk**: description
  - **Mitigation**: approach

### Validation

- Tests (unit/integration/perf) and benchmarks
- Dogfooding plan or example(s)
- Observability criteria (metrics/logs/traces to watch)

### Links

- Tracking issue(s)
- Related ADRs/design docs
- Dependent issues/PRs

---

## Maintainer Guidance

- Prefer additive edits over file renames to reduce churn.
- Keep milestone content focused on outcomes and criteria; link to detailed design docs or ADRs rather than embedding them here.
- When a milestone completes, add a short "post-mortem" note: what changed vs. plan, lessons learned, follow-ups.

## Questions or Proposals

- Open a discussion or PR with your suggested changes.
- For larger changes, draft an ADR and link it from the affected milestones.
