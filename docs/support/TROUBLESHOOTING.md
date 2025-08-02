# Meridian Runtime Troubleshooting Guide (Privacy‑First)

Owner: GhostWeasel (Lead: doubletap-dave)
Audience: Users and contributors
Status: Stable

This guide helps you diagnose common issues with the Meridian runtime while protecting sensitive information. It emphasizes minimal, reproducible steps and privacy‑respecting artifacts.

Key principles
- Keep it minimal: reduce to the smallest failing example.
- Keep it safe: do not share payload contents, secrets, or PII.
- Keep it structured: use clear steps, observed vs expected, and redacted logs.

-------------------------------------------------------------------------------

1) Quick Checklist

- [ ] Verify environment
  - Python 3.11+, toolchain installed as documented.
  - Meridian version and dependency versions noted.
- [ ] Reproduce with a minimal example
  - Simplify the graph: few nodes, clear edge bounds/policies.
  - Replace real data with dummy values; remove payload contents.
- [ ] Collect redacted artifacts
  - Structured logs: redact values; keep keys, counts, and policy names.
  - Config snippets: include only relevant keys; mask secrets.
  - Metrics snapshots: numeric values; avoid PII in labels.
- [ ] Compare observed vs expected
  - Write down what actually happens vs what you expect.
- [ ] Consult docs
  - Review README, milestone docs (especially M0), and How to Report Issues.

-------------------------------------------------------------------------------

2) Common Issues and Fixes

A) Edge Overflow or Backpressure Surprises
Symptoms
- Messages appear to stall or are being dropped.
- Logs show “edge overflow” or queue depth near bounds.
- Throughput lower than expected.

Likely Causes
- Edge bounds too small for bursty workloads.
- Overflow policy not aligned with workload (e.g., drop vs block vs latest vs coalesce).
- Upstream/downstream rate mismatch or blocking operations in critical paths.

What To Try
1) Inspect edge configuration:
   - Increase bounds for bursty edges.
   - Switch to “block” if you need strict delivery (with awareness of backpressure).
   - Use “latest” or “coalesce” for high‑frequency updates where only the latest state matters.
2) Balance node workloads:
   - Move blocking I/O to async or dedicated executors.
   - Batch processing where appropriate.
3) Add lightweight metrics/logs:
   - Track enqueue/dequeue counts and overflow events per edge.
4) Validate fairness:
   - Ensure scheduler policies aren’t starving a node.

What to Collect (Redacted)
- Edge definitions with bounds and policy names (no payload schemas required).
- Logs:
  - event="edge_overflow", edge_id="E_X", policy="drop", dropped=123
- Metrics snapshot: queue_depth, overflow_count.

B) Scheduler Starvation or Unfairness
Symptoms
- Certain nodes rarely run or lag behind others.
- Control-plane tasks take too long to apply.

Likely Causes
- Misconfigured fairness or long‑running tasks monopolizing execution.
- Blocking operations in async contexts causing event loop stalls.
- High contention on shared resources.

What To Try
1) Audit node work:
   - Break long tasks into smaller units.
   - Use asyncio-friendly APIs; offload blocking calls.
2) Verify control-plane prioritization:
   - Ensure control operations have clear priority.
3) Tune fairness strategy:
   - If available, try round‑robin vs weighted fairness; adjust weights.

What to Collect (Redacted)
- Summary of node durations (ranges).
- Structured logs around scheduling decisions (no payloads).
- Minimal graph snapshot: node names, edge topology (no secrets).

C) Shutdown Hangs or Unclean Teardown
Symptoms
- Runtime fails to exit promptly.
- Nodes’ on_stop hooks not called or appear stuck.
- In‑flight work not draining.

Likely Causes
- Blocking operations in shutdown paths.
- Pending tasks waiting on unbounded or stuck conditions.
- Missing timeouts or cancellation guards.

What To Try
1) Add timeouts to on_stop and drain operations.
2) Ensure idempotent on_stop; avoid new work on shutdown.
3) Emit logs for lifecycle transitions:
   - on_stop start/end markers.
4) Use policies to drain or drop remaining work per edge.

What to Collect (Redacted)
- Logs:
  - event="shutdown_initiated"
  - event="node_stopping", node_id=...
  - event="node_stopped", node_id=...
- Note any tasks still pending after timeout.

D) Validation Errors or Unexpected Payload Handling
Symptoms
- Frequent validation failures.
- Error events contain too little or too much detail.

Likely Causes
- Mismatched schema vs runtime data shape.
- Validation placed at incorrect boundary.
- Error policy not configured as intended.

What To Try
1) Validate at boundaries:
   - Apply TypedDict/Pydantic validators at ingress/egress points.
2) Tighten/loosen schema choices:
   - Optional fields vs required fields in evolving systems.
3) Confirm privacy posture:
   - Verify “no payloads in error events” is enforced; attach only metadata.

What to Collect (Redacted)
- Schema shape (names and types only; no values).
- Error logs without payload contents:
  - event="validation_error", node_id="N_A", error_type="SchemaMismatch"

E) Logging/Tracing Too Verbose or Too Sparse
Symptoms
- High log volume impacting performance.
- Not enough information to diagnose issues.

Likely Causes
- Inappropriate log levels or missing event coverage.
- Excessive debug logs in hot paths.

What To Try
1) Right-size log levels:
   - INFO for lifecycle, WARN/ERROR for anomalies, DEBUG sparingly.
2) Adopt key conventions:
   - event, node_id, edge_id, policy, counts, durations.
3) Sampling:
   - Apply sampling for repetitive debug events.

What to Collect (Redacted)
- A short sequence (last 200–500 lines) with structured entries.
- Note which events are missing for diagnosis.

F) Performance Regressions
Symptoms
- Increased latency or reduced throughput vs previous runs.
- Hot CPU or I/O saturation.

Likely Causes
- New blocking paths introduced.
- Higher cardinality in metric labels or verbose logging.
- Insufficient edge bounds or inefficient coalescing.

What To Try
1) Revert to known-good settings:
   - Compare metrics before/after a change.
2) Profile hot paths (locally):
   - Identify blocking calls; offload or batch.
3) Reduce label cardinality:
   - Keep metrics labels low and stable.

What to Collect (Redacted)
- Before/after metrics: throughput, queue_depth, overflow_count, latency percentiles (if available).
- Configuration diffs: policy names, bounds.

-------------------------------------------------------------------------------

3) Minimal Reproduction Strategy

1) Start small:
   - One or two nodes, one edge, a single message type.
2) Replace data:
   - Use “shape‑equivalent” dummy values; avoid real payloads.
3) Fix the seed:
   - Avoid non‑determinism in tests unless necessary.
4) Log only essentials:
   - Lifecycle transitions, scheduling decisions, edge overflows, error summaries.

Example structure (sanitized, conceptual)
- Configure an edge with bound=10 and policy="drop".
- Send 100 synthetic messages; confirm overflow events.
- Observe metrics counts and expected behavior.

-------------------------------------------------------------------------------

4) Safe Artifacts for Triage

- Environment
  - OS, Python, Meridian versions; tooling versions.
- Graph topology snapshot
  - Node/edge names, bounds, policies; no payload schemas required.
- Logs (redacted)
  - Keep keys; redact values: “<REDACTED>”.
- Metrics
  - Numeric counters/gauges/histograms; avoid PII in labels.
- Config differences
  - Show changed keys and enum/boolean values; mask secrets or replace with CHECKSUM(...) or PLACEHOLDER.

Never include
- Secrets, tokens, credentials.
- PII or business data payloads.
- Proprietary identifiers without anonymization.

-------------------------------------------------------------------------------

5) When to Escalate

Escalate with a request for help if:
- You cannot produce a minimal repro.
- The runtime hangs or corrupts state even after simplification.
- You suspect a scheduler fairness bug or data loss contradictory to policy.

Provide:
- Short, sanitized repro or script.
- Redacted logs (last 200–500 lines).
- Environment details and exact versions.
- Observed vs expected behavior.

-------------------------------------------------------------------------------

6) FAQs

Q: How do I check if I’m hitting edge bounds?
- Enable structured logs for enqueue/dequeue and overflow events. Inspect queue depth metrics if available.

Q: Should I include payload schemas in a report?
- Prefer not to. If necessary, share only field names and types—no values.

Q: What if my logs contain sensitive info?
- Redact values. Keep structure, keys, and counts. Replace sensitive strings with <REDACTED> or placeholders.

Q: How do I handle blocking I/O?
- Use async variants or run in an executor. Ensure on_stop has timeouts and is idempotent.

-------------------------------------------------------------------------------

7) Related Documents

- How to Report Issues: docs/support/HOW-TO-REPORT-ISSUES.md
- Governance and Overview (M0): docs/plan/M0-governance-and-overview.md
- Milestones and Plans: docs/plan/
- Contributing Guide: docs/contributing/CONTRIBUTING.md

End of document.