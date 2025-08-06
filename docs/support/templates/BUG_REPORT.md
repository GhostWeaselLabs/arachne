# Meridian Runtime Bug Report Template (Privacy‑First)
# Owner: GhostWeasel (Lead: doubletap-dave)
# Purpose: Help you file actionable bug reports while protecting sensitive data.

## 1) Summary
<!-- 1–3 sentences describing the bug at a high level. Avoid payload contents and sensitive data. -->

## 2) Environment
<!-- Do NOT include secrets, tokens, or PII. -->
- OS: (e.g., macOS 14.5 / Ubuntu 22.04 / Windows 11)
- Python: 3.11.x
- Meridian Runtime: x.y.z
- Install/Tooling: (e.g., `uv` version, `ruff`/`mypy`/`pytest` versions)
- How installed: (`pip`/`uv`/source)

## 3) Reproduction Steps
<!-- Provide the smallest reproduction you can. Keep it sanitized—no payload contents. -->
1) …
2) …
3) …

### Minimal Repro (Sanitized)
<!-- Replace data with placeholders. Share shapes/schemas, not values. -->
- Graph summary: number of nodes/edges, relevant edges' bounds and overflow policies (`block`/`drop`/`latest`/`coalesce`).
- Relevant node lifecycle hooks: `on_start` / `on_message` / `on_tick` / `on_stop`.
- Validation in use (optional): `TypedDict` / `Pydantic` (schema names only).

Example (conceptual, no real data):
- Edge E_A: `bound=10`, `policy="drop"`
- Node N_input -> Edge E_A -> Node N_worker

## 4) Observed Behavior
<!-- What actually happened. Include redacted logs/errors. -->
- Behavior:
  - …
- Redacted errors/stack traces (if any):
  - …
- Relevant structured logs (redacted values, keep keys):
  - `event="edge_overflow", edge_id="E_A", policy="drop", dropped=123`
  - `event="node_error", node_id="N_worker", error_type="ValueError", message="<REDACTED>"`

## 5) Expected Behavior
<!-- What you expected to happen instead. Be specific. -->
- …

## 6) Additional Technical Detail (Optional, Redacted)
<!-- Keep it privacy‑safe. Never share payload contents, secrets, or PII. -->
- Metrics snapshot (numbers only; avoid PII in labels):
  - `queue_depth=`, `overflow_count=`, `processed_total=`, `error_total=`
- Config highlights (redacted):
  - Relevant keys and enum/boolean values; replace secrets with `<REDACTED>` or `CHECKSUM(...)`
- Timing/frequency:
  - Intermittent vs consistent; began after version/change
- Workarounds tried:
  - …

## 7) Impact
<!-- Who/what is affected? Severity? -->
- (e.g., Blocks release; production impact; affects one workflow; minor inconvenience)

## 8) Attachments (Optional, Sanitized)
<!-- If a diagnostics bundle is available, attach the sanitized archive.
     Until an automated collector exists, include a manual set of:
       - Environment details (no secrets)
       - Redacted logs (last 200–500 lines)
       - Topology snapshot (counts, bounds, overflow policies)
       - Minimal repro script (sanitized) -->
- Attached: yes/no
- Notes on redaction: …

## 9) Maintainer Questions (Optional)
<!-- If you have specific questions for maintainers, list them here. -->
- …

## 10) Redaction Guidance (Strongly Enforced)
MUST remove or replace:
- Secrets: API keys, tokens, passwords, private URLs.
- PII: names, emails, phone numbers, addresses, IDs.
- Payload contents: message/body data, records; share only schemas/field names if necessary.
- Hostnames/IPs: replace with `HOST_A` or `203.0.113.10`.
- Internal IDs: replace with opaque placeholders (`ID_123` → `ID_A`).

Best practices:
- Prefer schemas over data (example: `{user_id: str, balance_cents: int}`).
- Keep log structure and keys; replace values with `<REDACTED>` or representative shapes.
- For configs, include only relevant keys and non-sensitive values; mask secrets entirely.
- If you must differentiate distinct secret/config values without exposing them, use checksums:
  - `DB_PASSWORD: CHECKSUM(sha256:abcd...)`

What not to share:
- Raw payloads or domain data
- Credentials or tokens
- Proprietary identifiers without anonymization

## 11) Checklist
- [ ] Removed payload contents, secrets, tokens, and PII
- [ ] Included OS/Python/Meridian Runtime versions and install method
- [ ] Added minimal, sanitized reproduction steps
- [ ] Provided redacted logs/errors and metrics snapshots if relevant
- [ ] Described observed vs expected behavior

## References
- Troubleshooting: `docs/support/troubleshooting.md`
- How to Report Issues: `docs/support/HOW-TO-REPORT-ISSUES.md`
- Governance and Overview: `docs/roadmap/governance-and-overview.md`
- Contributing Guide: `docs/contributing/guide.md`