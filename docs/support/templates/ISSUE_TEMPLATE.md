# Meridian Runtime Issue Template (Generic)
# Owner: GhostWeasel (Lead: doubletap-dave)
# Audience: Users and contributors
# Purpose: Provide a concise, privacy‑first structure for reporting any issue (bug, question, usability concern, docs gap, etc.)

## 1) Issue Type
<!-- Choose one; keep only the relevant line -->
- [ ] Bug
- [ ] Question
- [ ] Feature request
- [ ] Documentation
- [ ] Performance
- [ ] Usability / DX
- [ ] Other (describe below)

## 2) Summary
<!-- 1–3 sentences describing the issue or request in plain language. -->

## 3) Environment
<!-- Do NOT include secrets, tokens, or PII. -->
- OS: (e.g., macOS 14.5 / Ubuntu 22.04 / Windows 11)
- Python: 3.11.x
- Meridian Runtime version: x.y.z
- Tooling (if relevant): `uv` version, `ruff`/`mypy`/`pytest` versions
- Installation method: (e.g., `pip`/`uv`/local build)

## 4) Reproduction / Context
<!-- Keep it minimal and privacy‑safe. Use sanitized examples and no payload contents. -->
- Steps to reproduce:
  1.
  2.
  3.
- Minimal repro snippet (sanitized; schemas or field names only, no real data):
  - Node/edge definitions, bounds, overflow policy (`block`/`drop`/`latest`/`coalesce`)
  - Any relevant lifecycle hooks (`on_start`/`on_message`/`on_tick`/`on_stop`)

## 5) Observed vs Expected
- Observed:
  - What happened, including any redacted stack traces or error summaries.
  - Example structured logs (redact values; keep keys):
    - `event="edge_overflow", edge_id="EDGE_A", policy="drop", dropped=123`
    - `event="node_error", node_id="NODE_X", error_type="ValueError", message="<REDACTED>"`
- Expected:
  - What you expected to happen instead.

## 6) Additional Details (Optional)
<!-- Include only privacy‑safe artifacts; redact all sensitive data. -->
- Metrics snapshot (counters/gauges; avoid PII in labels):
  - `queue_depth_example=`, `overflow_count_example=`
- Config highlights (redacted):
  - Relevant keys and enum/boolean values only. Replace secrets with `<REDACTED>` or `CHECKSUM(...)`.
- Frequency/timing:
  - Intermittent/consistent; started after `<version/change>`.
- Workarounds tried:
  - What you attempted and results.

## 7) Impact
<!-- Briefly describe severity and who is affected (e.g., blocks release, affects single workflow, minor inconvenience). -->

## 8) Attachments (Optional)
<!-- If a diagnostics bundle is available, attach the sanitized archive.
     Until the CLI exists, include a manual, redacted bundle: environment details, redacted logs (last 200–500 lines), graph topology snapshot (counts, bounds/policies), minimal repro. -->

## 9) Proposed Next Steps (Optional)
<!-- Suggestions for fixes, docs improvements, or clarifying questions for maintainers. -->

## Checklist
- [ ] I removed payload contents, secrets, tokens, PII, and proprietary identifiers.
- [ ] I provided a minimal reproduction or the smallest set of redacted artifacts possible.
- [ ] I included OS/Python/Meridian Runtime versions and relevant tooling info.
- [ ] I clearly described observed vs expected behavior.

# References
- Troubleshooting: `docs/support/TROUBLESHOOTING.md`
- How to Report Issues: `docs/support/HOW-TO-REPORT-ISSUES.md`
- Governance and Overview: `docs/roadmap/governance-and-overview.md`
- Contributing Guide: `docs/contributing/guide.md`