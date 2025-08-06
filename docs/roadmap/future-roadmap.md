# Meridian Runtime Future Roadmap

## Purpose

This roadmap captures high‑value initiatives considered out of scope for v1.0.0 but aligned with Meridian's mission: a composable, asyncio‑native graph runtime with strong observability, predictable scheduling, and privacy‑first error handling. It is organized by time horizon and includes requirements framed with EARS to ensure clarity and testability.

## Guiding Themes

- Composability and portability over bespoke integrations
- Predictable performance and graceful backpressure
- Operational transparency with privacy‑safe diagnostics
- Ergonomic developer experience (DX) and API stability
- Incremental, opt‑in features to avoid core bloat

---

## Horizon 1: Near‑Term (v1.x series)

### 1) CLI Enhancements and Diagnostics

**Event-driven:**

- When a user runs `meridian diagnostics collect`, the CLI shall gather anonymized runtime metadata, environment info (OS, Python version), configuration checksums, and recent logs into a bundle.
- When a diagnostics bundle is created, the CLI shall apply redaction rules to scrub secrets, tokens, PII, and payload contents by default.

**Ubiquitous:**

- The CLI shall support subcommands for graph validation, linting, and quick profiling (e.g., edge depths, queue sizes).
- The CLI shall support exporting a machine‑readable snapshot of node/edge schemas and runtime topology.

### 2) Rust Fast Path Extensions (PyO3)

**Ubiquitous:**

- The system shall provide an optional `meridian_fast` extension backed by Rust (via PyO3/maturin) implementing:
    - A bounded ring buffer for edges with `block`/`drop`/`latest`/`coalesce` policies.
    - Policy handlers as zero‑copy operations over indices and lengths.
    - Scheduler ready‑queue band selection and dispatch primitives.
- When `meridian_fast` is installed, the runtime shall auto‑detect and use the Rust implementations; otherwise, it shall fall back to pure Python.

**Unwanted:**

- If the Rust extension is unavailable or fails to load, the system shall degrade gracefully with no behavior change.

**Notes:**

- Package as an optional extra: `pip install meridian-runtime[fast]`.
- Keep the public API identical; optimize internal data structures and loops.

### 3) CPU Topology Awareness and Affinity

**Event-driven:**

- At startup, the runtime shall detect logical CPU count and affinity mask, log them, and expose metrics (e.g., `runtime_cpu_visible`, `runtime_cpu_affinity_count`).
- When `MERIDIAN_SET_CPU_AFFINITY=1` is set on Linux, the process shall set its CPU affinity to the full visible set and log the result.

**Unwanted:**

- Affinity setting shall be opt‑in and never cause startup failure if the platform doesn't support it.

### 4) Deterministic Metrics Overhead Minimization

**Ubiquitous:**

- The metrics subsystem shall provide a zero‑overhead stub when disabled and batch increments when enabled to keep overhead ≤10% versus no metrics.

**Notes:**

- Preserve budget checks in CI; validate with microbenchmarks.

### 5) Nightly Profiling Artifacts

**Event-driven:**

- When profiling mode is enabled (`MERIDIAN_PROF=1`), CI shall capture sampling profiles (`py‑spy`/`perf`) during stress tests and upload flamegraphs.

**Unwanted:**

- Profiling mode shall not be enabled by default in PR CI to avoid noise.

### 6) Graph Inspector (Text/Terminal)

**Ubiquitous:**

- The system shall provide a TUI inspector enabling overview of nodes, edges, queue states, and lifecycle statuses with refresh intervals.
- The inspector shall remain opt‑in and run without impacting runtime performance beyond nominal observation overhead.

### 7) Runtime Introspection API

**Ubiquitous:**

- The runtime shall expose an introspection surface to enumerate nodes, edge policies, and recent error events with redacted metadata.
- The runtime shall provide structured metrics readers for exporting counters/gauges/histograms to common backends via adapters.

### 8) Schema and Validation Ergonomics

**Ubiquitous:**

- The system shall offer optional validators (`TypedDict`/`Pydantic`) with a consistent adapter interface.
- The system shall include validation error mapping to structured runtime error events (no payloads by default).

### 9) Scheduler Profiling and Fairness Tuning

**Event-driven:**

- When profiling mode is enabled, the scheduler shall record scheduling latencies, runnable queue lengths, and per‑node execution times with constant‑factor overhead.

**State-driven:**

- While steady‑state, the scheduler shall support configurable fairness strategies (e.g., round‑robin, weighted) selectable via policy.

### 10) Persistence‑Friendly Hooks

**Ubiquitous:**

- The system shall provide extension points for durable inbox/outbox adapters (e.g., SQLite, file‑backed) without making persistence mandatory.
- The system shall document at‑least‑once and at‑most‑once semantics for adapters that opt into persistence.

### 11) Examples and Recipes Expansion

**Ubiquitous:**

- The repository shall include curated examples demonstrating backpressure policies, redaction strategies, and controlled shutdown.
- The examples shall include "debug mode" scripts that set up structured logs and quick metrics sinks.

---

## Horizon 2: Mid‑Term (v2.x series)

### 1) Visual Graph Inspector (Local/Web)

**Ubiquitous:**

- The system shall provide an optional web or local visual inspector for graph topology exploration, node status, and basic metrics overlays.

**Unwanted:**

- If the visual inspector is enabled, it shall never expose payload contents by default; sensitive fields shall be masked or omitted.

### 2) Pluggable Storage for Edges (Advanced)

**Ubiquitous:**

- The system shall allow edge queues to use pluggable storage (memory, mmap, local DB) with consistent overflow policies (`block`, `drop`, `latest`, `coalesce`).
- The system shall document performance and durability trade‑offs for each adapter.

### 3) Extended Backpressure Strategies

**Ubiquitous:**

- The system shall support advanced backpressure configurations (e.g., watermarks, adaptive coalescing) that can be selected per edge.

### 4) Graph Versioning and Migration Aids

**Event-driven:**

- When loading a graph with a prior schema version, the system shall support mapping/migration strategies to upgrade definitions with clear errors on incompatibilities.

### 5) Replay and Time‑Travel Debugging (Local)

**Ubiquitous:**

- The system shall provide opt‑in, local‑only replay from persisted event logs to reproduce behavior, with strong redaction guarantees.

### 6) Policy‑Driven Error Handling

**Ubiquitous:**

- The system shall offer configurable error policies (e.g., retry with backoff, circuit breaker, quarantine node) expressible in graph definitions.

### 7) Structured Configuration Layer

**Ubiquitous:**

- The system shall offer a structured config loader (e.g., from TOML/YAML) with strict key validation and environment overrides, remaining optional.

---

## Horizon 3: Long‑Term (v3.x+)

### 1) Multi‑Process/Distributed Execution (Rust Bridges)

**Ubiquitous:**

- The runtime shall support partitioned execution across processes or hosts with clear delivery guarantees and robust health checks.
- Bridge edges shall be backed by shared memory or lock‑free queues implemented in Rust, with a `DistributedEngine` composing multiple schedulers.

**Unwanted:**

- If a partition becomes isolated, the system shall degrade gracefully with backpressure, clear error events, and recovery paths.

### 2) Adaptive Scheduling and QoS

**State-driven:**

- While under sustained load, the scheduler shall adapt priorities based on configured QoS classes, queue depth, and SLIs.

### 3) Formal Verification Aids

**Ubiquitous:**

- The system shall provide optional formal models/specs for critical components (e.g., edge policies) to support verification and model‑checking.

### 4) Pluggable Security Posture

**Ubiquitous:**

- The system shall support policy modules for encryption at rest for persistent edges, signed configuration bundles, and policy‑as‑code redaction rules.

### 5) Remote Control Plane

**Event-driven:**

- When enabled, a remote control plane shall allow safe operations (pause/resume nodes, swap subgraphs, drain edges) with strict auth and audit logs.

---

## Cross‑Cutting Concerns

### Observability

- The system shall continue to prioritize structured logs, metrics, and optional tracing, with stable keys and label cardinality guidance.
- Adapters shall be provided for common metrics backends (Prometheus, OpenTelemetry exporters) without hard dependencies.
- Profiling: provide nightly sampling profiles and flamegraphs for stress runs; keep off by default in PR CI.

### Privacy and Redaction

- Redaction hooks shall be consistently applied across logs, diagnostics, inspector tools, and replay facilities.
- Default posture remains "no payloads in errors" with opt‑in, policy‑driven exposure.

### Performance

- Benchmarks and micro‑profiling suites shall accompany major changes (scheduler, edges, validators).
- Clear SLOs: baseline latency envelopes for node execution and enqueue/dequeue operations under reference workloads.
- Rust fast paths: optional acceleration layer (`meridian_fast`) for ring buffers, policies, and scheduler dispatch with behavior parity tests.
- CPU topology awareness: metrics for visible CPUs and affinity; optional process pinning via `MERIDIAN_SET_CPU_AFFINITY`.

### API Stability

- Semantic versioning applies to public APIs; deprecations shall include migration notes and timelines.
- Experimental APIs shall be clearly marked with upgrade expectations.
- Fast‑path implementations must preserve public API semantics and be fully covered by conformance tests against the Python reference.

---

## Candidate RFC/Decision Record Topics

- Diagnostics bundle schema and redaction policy vocabulary
- Scheduler pluggability and fairness strategies
- Edge storage adapters and durability semantics
- Visual inspector transport and privacy posture
- Replay/log formats and time‑travel debugging guarantees
- Multi‑process partitioning model and delivery guarantees
- Rust fast‑path FFI surface and conformance testing approach
- Scheduler core replacement plan and callback adapter interface

---

## Milestone Selection Guidance

- Prefer features that increase reliability, debuggability, and clarity of behavior.
- Keep the core small; ship optional adapters and inspectors as add‑ons.
- Ensure each feature includes tests, examples, and docs updates.
- Validate user benefit with examples and realistic load tests before default enablement.

---

## Changelog and Tracking

This document is updated as items land or are re‑scoped. Each substantial item should be linked to an RFC/DR and issue(s) for planning and status.