# Meridian Runtime Support Policy

Owner: GhostWeasel (Lead: doubletap-dave)  
Status: Stable  
Audience: Users and contributors

Meridian Runtime is built to be operable and supportable with a strong bias toward privacy and safety. This document describes how to get help, how to report issues, and what to expect from maintainers.

-------------------------------------------------------------------------------

## Getting Help

1) Start with the docs
- Governance and Overview (M0): docs/plan/M0-governance-and-overview.md
- Post‑v1 Roadmap: docs/plan/post-v1-roadmap.md
- Contributing: docs/contributing/CONTRIBUTING.md
- Releasing: docs/contributing/RELEASING.md

2) Diagnosis and self‑serve support
- Troubleshooting Guide (privacy‑first): docs/support/TROUBLESHOOTING.md
- How to Report Issues (privacy‑first): docs/support/HOW-TO-REPORT-ISSUES.md
- Templates for filing issues:
  - General Issue: docs/support/templates/ISSUE_TEMPLATE.md
  - Bug Report: docs/support/templates/BUG_REPORT.md
  - Feature Request: docs/support/templates/FEATURE_REQUEST.md

3) Discussions and questions
- Use your organization’s preferred channels (issue tracker, discussions, or forum) to ask questions or propose ideas.
- For sensitive or security‑related topics, use a private channel if available (see “Security and Sensitive Reports”).

-------------------------------------------------------------------------------

## Privacy‑First Support

Meridian’s support process intentionally avoids collecting sensitive information. Please do not share:
- Secrets: API keys, tokens, passwords, private URLs
- PII: names, emails, phone numbers, addresses, IDs
- Payload contents: message bodies or domain data
- Proprietary identifiers: share only anonymized placeholders

Preferred artifacts:
- Environment summaries (OS, Python, Meridian version)
- Redacted structured logs (keep keys; redact values with <REDACTED>)
- Graph topology summaries (node/edge counts, bounds, overflow policies)
- Metrics snapshots (numeric counters/gauges; avoid PII in labels)
- Minimal, sanitized reproductions (schemas/names only; no real data)

Until diagnostics tooling is available, follow the manual bundle guidance in:
- docs/support/HOW-TO-REPORT-ISSUES.md

-------------------------------------------------------------------------------

## Filing an Issue

1) Before filing
- Read the Troubleshooting Guide: docs/support/TROUBLESHOOTING.md
- Search existing issues to avoid duplicates

2) What to include (sanitized)
- Summary: short description of the problem or request
- Environment: OS, Python (3.11+), Meridian version, install/tooling details
- Reproduction: minimal steps and small sanitized snippet (no payload contents)
- Observed vs Expected: describe what happened vs what you expected
- Logs/Metrics: include redacted structured logs and numeric metrics snapshots
- Workarounds: note anything you’ve tried

3) Use a template
- Bug reports: docs/support/templates/BUG_REPORT.md
- Feature requests: docs/support/templates/FEATURE_REQUEST.md
- General issues: docs/support/templates/ISSUE_TEMPLATE.md

-------------------------------------------------------------------------------

## Maintainer Process (What to Expect)

1) Triage
- Label and prioritize issues
- Request missing information if necessary (always privacy‑first)

2) Reproduction and analysis
- Attempt to reproduce with your minimal, sanitized example
- Ask for additional redacted artifacts if needed

3) Resolution
- Provide a fix, workaround, or RFC/Decision Record for larger changes
- Confirm with the reporter when feasible (e.g., pre‑release builds)

4) Closure
- Close when addressed, with notes on remediation and versions affected

-------------------------------------------------------------------------------

## Security and Sensitive Reports

- Do not share secrets, PII, or payload contents publicly.
- Use private channels if available within your organization to coordinate a secure handoff.
- Provide high‑level impact and sanitized details.
- Maintainers prioritize triage for security‑sensitive issues.

-------------------------------------------------------------------------------

## Service Expectations

- Best‑effort support by maintainers
- Clear communication on status, scope, and next steps
- Preference for fixes that improve reliability, debuggability, and privacy posture
- Changes follow SemVer and are documented in the changelog and release notes

-------------------------------------------------------------------------------

## References

- Governance and Overview (M0): docs/plan/M0-governance-and-overview.md
- Post‑v1 Roadmap: docs/plan/post-v1-roadmap.md
- Contributing: docs/contributing/CONTRIBUTING.md
- Releasing: docs/contributing/RELEASING.md
- Troubleshooting: docs/support/TROUBLESHOOTING.md
- How to Report Issues: docs/support/HOW-TO-REPORT-ISSUES.md
- Issue Templates:
  - docs/support/templates/ISSUE_TEMPLATE.md
  - docs/support/templates/BUG_REPORT.md
  - docs/support/templates/FEATURE_REQUEST.md

Thank you for helping improve Meridian Runtime—privacy‑first, composable, and observable by design.