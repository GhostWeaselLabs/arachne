# How to Report Issues (Privacy‑First)

Owner: GhostWeasel (Lead: doubletap-dave)
Audience: Users and contributors
Status: Stable

This guide explains how to file effective bug reports and feature requests for Arachne while protecting sensitive information. It provides step‑by‑step instructions, redaction guidance, and copy‑paste templates.

Key principles
- Safety by default: avoid sharing secrets, tokens, PII, or domain data payloads.
- Reproducibility: provide enough context (versions, platform, steps) to reproduce.
- Precision: include observed vs expected behavior and the smallest failing example you can.
- Optional diagnostics: prefer anonymized, redacted bundles when sharing runtime context.

-------------------------------------------------------------------------------

1) Before You File

1. Check the docs
   - README and docs/plan/ for intended behavior.
   - docs/support/TROUBLESHOOTING.md for known issues and fixes.

2. Search existing issues/discussions
   - Your issue may be known, have a workaround, or be in progress.

3. Prepare a minimal reproduction
   - Reduce your graph to the smallest example that still fails.
   - Use fake or anonymized data. Do not include payload contents.

-------------------------------------------------------------------------------

2) Information to Include

Required
- Summary: 1–3 sentences describing the issue or request.
- Environment: OS, Python version (3.11+), Arachne version.
- Reproduction: clear steps and minimal, anonymized example (no payload contents).
- Observed vs Expected: what happened vs what you expected.
- Logs/errors (redacted): structured logs or error messages with sensitive data removed.

Helpful
- Scheduler/graph details: edge bounds and overflow policy, node lifecycle hooks in use.
- Configuration snippets: anonymized and redacted, or checksums if content is sensitive.
- Metrics snapshots: counts/gauges/histograms as numbers; avoid labels with PII.
- Timeline: when the problem started, whether it’s intermittent or consistent.
- Workarounds tried: what you’ve already tested.

Out of scope for reports
- Secrets, tokens, credentials, PII, or raw domain payloads.
- Production‑only identifiers (use placeholders).

-------------------------------------------------------------------------------

3) Redaction Guidance

Always remove or replace:
- Secrets: API keys, tokens, passwords, private URLs.
- PII: names, emails, phone numbers, addresses, IDs.
- Payloads: message bodies and data records. If necessary, share schema or field names only.
- Hostnames and IPs: replace with HOST_A, 203.0.113.10, etc.
- Internal IDs: replace with opaque placeholders (ID_123 → ID_A).

Best practices:
- Prefer schemas over data. Example: {user_id: str, balance_cents: int}.
- For logs, keep structure and keys; replace values with <REDACTED> or representative shapes.
- For configs, show only relevant keys; mask secrets entirely.

-------------------------------------------------------------------------------

4) Optional: Diagnostics Bundle (Planned CLI)

Planned command: arachne diagnostics collect
- Purpose: gather anonymized runtime metadata, environment info, config checksums, recent logs, and a redacted graph/scheduler snapshot.
- Default posture: privacy‑first. Payload contents are not included by default; sensitive fields are scrubbed.
- Output: a timestamped archive that you can attach to your issue.

Until the CLI is available:
- Provide a manual bundle with:
  - Environment: OS, Python, Arachne version.
  - Graph topology snapshot: node/edge counts, edge bounds and overflow policy (no payload schemas required).
  - Logs: last 200–500 lines of structured logs, redacted.
  - Config: relevant settings as key names and boolean/enum values; omit secrets or replace with CHECKSUM(...) if you need to show distinct values without exposing them.
  - Minimal repro: a small, sanitized script or snippet demonstrating the issue.

-------------------------------------------------------------------------------

5) Templates

Bug Report
Title: [Bug] Short description

Summary
A concise summary of the problem (1–3 sentences).

Environment
- OS: macOS/Linux/Windows (version)
- Python: 3.11.x
- Arachne: x.y.z
- Install/Tooling: uv version (if applicable)

Reproduction Steps
1) …
2) …
3) …

Minimal Repro Snippet (sanitized; no payload contents)
- Show relevant node/edge definitions, edge bounds, overflow policies, lifecycle hooks.
- Provide fake schemas or placeholder field names only.

Observed Behavior
- What happened, including any redacted stack traces or error codes.
- Relevant structured logs (redacted):
  - event="edge_overflow", edge_id="EDGE_A", policy="drop", count=123
  - event="node_error", node_id="NODE_X", error_type="ValueError", message="<REDACTED>"

Expected Behavior
- What you expected to happen.

Additional Context (optional)
- Metrics counters/gauges (no sensitive labels)
- Workarounds tried
- Frequency and timing


Feature Request
Title: [Feature] Short description

Summary
- What problem this would solve and for whom.

Motivation and Use Cases
- Context and examples (sanitized).

Proposed Behavior
- High‑level API or runtime behavior.
- Defaults and opt‑in/opt‑out expectations.

Alternatives Considered
- Other approaches and trade‑offs.

Impact and Scope
- Affected modules (runtime, scheduler, observability, CLI).
- Backward compatibility considerations.

-------------------------------------------------------------------------------

6) Examples of Good vs Poor Reports

Good
- Includes versions, OS, and tooling.
- Provides a minimal repro with redacted logs.
- Specifies observed vs expected behavior.
- Avoids payload contents and sensitive details.

Poor
- “It doesn’t work” without a repro or environment info.
- Shares raw production data or secrets.
- Vague expectations or no description of the failure mode.

-------------------------------------------------------------------------------

7) Where and How to Submit

- Use your organization’s chosen issue tracker or discussion forum.
- If a private channel exists for sensitive cases, prefer it for sharing any diagnostics bundle.
- If you email or chat, paste the template with redacted content and attach the sanitized bundle.

-------------------------------------------------------------------------------

8) Maintainer Process (What to Expect)

- Triage: confirm receipt, label, and request missing info if needed.
- Reproduce: attempt to reproduce with your minimal example.
- Diagnose: share findings; may ask for additional sanitized logs or metrics.
- Fix/Decision: propose a fix, workaround, or an RFC/DR for larger changes.
- Verify: ask you to validate a patch or a pre‑release build when applicable.

-------------------------------------------------------------------------------

9) FAQ

Q: Can I share payload data if it seems harmless?
A: No. Share schemas or field names only. Keep values redacted.

Q: I can’t create a minimal repro. What should I do?
A: Provide the smallest set of sanitized logs, graph configuration details (edge bounds/policies), and environment info you can. Maintainers may suggest a narrowed test based on your description.

Q: What if the issue is security‑sensitive?
A: Use a private reporting channel if available. Do not share details publicly. Briefly describe impact and request a secure handoff.

Q: Will maintainers sign NDAs?
A: The project is designed to avoid the need for sensitive data. We strongly prefer anonymized, redacted artifacts.

-------------------------------------------------------------------------------

10) Quick Checklist

- [ ] Read TROUBLESHOOTING and search existing issues
- [ ] Collected environment details (OS, Python, Arachne version)
- [ ] Prepared minimal, sanitized reproduction
- [ ] Redacted logs and configs (no secrets, no payload contents)
- [ ] Wrote clear observed vs expected behavior
- [ ] Attached optional sanitized diagnostics bundle (manual for now)

Thank you for helping improve Arachne while keeping your data safe.
