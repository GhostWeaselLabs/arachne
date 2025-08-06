---
title: Glossary
description: Comprehensive glossary of terms and concepts used throughout Meridian Runtime documentation and codebase, with links to relevant reference pages and examples.
tags:
  - glossary
  - terminology
  - concepts
  - reference
---

# Glossary

A comprehensive vocabulary for Meridian Runtime concepts, patterns, and terminology. This glossary provides clear definitions and links to relevant documentation sections for deeper understanding.

!!! info "See Also"
    - [API Reference](../reference/api.md) for detailed API documentation
    - [Patterns](../concepts/patterns.md) for common usage patterns
    - [Architecture](../concepts/architecture.md) for system design concepts
    - [Observability](../concepts/observability.md) for monitoring and debugging

---

## A

**Agent**
A long-lived process or service that hosts the runtime and executes graphs. Often responsible for lifecycle, configuration, and observability endpoints. See [Architecture: Core Components](../concepts/architecture.md#core-components).

**API (Application Programming Interface)**
The public surface exposed by Meridian (Python types, functions, and CLI) for building, running, and observing graphs. See [API Reference](../reference/api.md) for complete documentation.

**Admonition**
A callout box used in documentation to highlight important information, warnings, or tips. Uses `!!!` syntax in Markdown.

**Annotation**
A numbered reference in code examples that links to explanatory text. See [Patterns](../concepts/patterns.md) for examples with code annotations.

---

## B

**Backpressure**
A flow-control mechanism that slows or stops producers when consumers can't keep up. Implemented via bounded queues and enqueue policies. See [Patterns: Backpressure and Overflow](../concepts/patterns.md#how-to-backpressure-and-overflow).

**Backpressure Strategy**
High-level approach to handling overflow conditions. Options include `DROP` (prefer dropping items) and `BLOCK` (prefer blocking producers). See [API: Policies](../reference/api.md#backpressure-and-overflow).

**Bounded Edge/Queue**
A queue with a fixed capacity connecting nodes. When full, enqueue behavior follows a configured policy (e.g., block, drop, coalesce). See [Architecture: Edge](../concepts/architecture.md#edge).

**Batch Processing**
Processing multiple messages together for efficiency. See [Patterns: Coalesce Policy](../concepts/patterns.md#coalesce-deterministic-merge-under-pressure).

---

## C

**Control Message**
A message used for runtime coordination (e.g., shutdown, health check) that may be scheduled with higher priority than data messages. See [Patterns: Control-plane Priority](../concepts/patterns.md#how-to-control-plane-priority).

**Coalescing**
A drop strategy that merges or replaces older queued items with newer ones to bound memory while retaining the most relevant state. See [API: Coalesce Policy](../reference/api.md#backpressure-and-overflow).

**Composable Node**
A node that is designed to be reused and nested into subgraphs without side effects beyond its declared inputs/outputs. See [Patterns: Subgraph Composition](../concepts/patterns.md#reference-subgraph-composition-and-reuse).

**Context**
Additional information attached to logs, metrics, or traces to provide operational context. See [Observability: Contextual Logging](../concepts/observability.md#contextual-logging).

**Counter**
A monotonically increasing metric type for counting events. See [Observability: Metric Types](../concepts/observability.md#counter).

---

## D

**Dataflow**
An application structure where data moves through a directed graph of nodes via typed edges. Each node transforms or routes the data. See [Architecture: Message Flow](../concepts/architecture.md#message-flow).

**Dead Letter**
A message that cannot be processed (e.g., due to validation errors) and is routed to a diagnostic or quarantine path. See [Patterns: Error Handling](../concepts/patterns.md#how-to-error-handling).

**Drain**
A shutdown phase where nodes finish processing in-flight messages and flush outputs before stopping. See [API: Scheduler Examples](../reference/api.md#scheduler-examples).

**Drop Policy**
An overflow policy that discards new messages when the queue is full. See [Patterns: Drop Policy](../concepts/patterns.md#drop-lossy-prefer-freshness).

**Distributed Tracing**
A technique for tracking request flow across multiple nodes and services. See [Observability: Distributed Tracing](../concepts/observability.md#how-to-distributed-tracing).

---

## E

**Edge**
A directed, typed connection between nodes with a bounded queue. Responsible for backpressure and overflow policy. See [Architecture: Edge](../concepts/architecture.md#edge).

**Enqueue Policy**
Behavior when an edge's bounded queue is full. Examples: block (apply backpressure), drop-oldest, drop-newest, coalesce, timeout. See [API: Policy Semantics](../reference/api.md#backpressure-and-overflow).

**Event**
A unit of data processed by nodes. May be generic (payload + metadata) or strongly typed. See [API: Message](../reference/api.md#message).

**Error Message**
A message type used for structured error reporting. See [Patterns: Error Handling](../concepts/patterns.md#how-to-error-handling).

---

## F

**Flow Control**
Mechanisms that regulate throughput and stability (backpressure, priorities, rate limits). See [Patterns: Backpressure and Overflow](../concepts/patterns.md#how-to-backpressure-and-overflow).

**Fairness**
Scheduling property ensuring all nodes get execution time proportional to their priority. See [API: Scheduler Examples](../reference/api.md#scheduler-examples).

**Factory Function**
A function that creates and returns instances of classes or objects. See [Patterns: Policy Factories](../concepts/patterns.md#how-to-backpressure-and-overflow).

---

## G

**Graph**
A directed acyclic (or cyclic with care) network of nodes and edges representing your pipeline. Can be nested through subgraphs. See [Architecture: Composition and Subgraphs](../concepts/architecture.md#composition-and-subgraphs).

**Gauge**
A metric type representing the current value of a measurement. See [Observability: Metric Types](../concepts/observability.md#gauge).

**Graceful Shutdown**
A termination mode where the runtime stops accepting new work, drains in-flight messages, and cleans up resources. See [API: Scheduler Examples](../reference/api.md#scheduler-examples).

---

## H

**Health Check**
A lightweight status probe to determine liveness/readiness of the runtime or nodes. See [Patterns: Control Messages](../concepts/patterns.md#how-to-control-plane-priority).

**Histogram**
A metric type for recording observations into buckets, commonly used for latency distributions. See [Observability: Metric Types](../concepts/observability.md#histogram).

**High Priority**
A scheduling priority level for control messages and critical operations. See [Patterns: Control-plane Priority](../concepts/patterns.md#how-to-control-plane-priority).

---

## I

**Idempotency**
A property where processing the same message multiple times yields the same result. Important for retries and failure recovery. See [Patterns: Error Handling](../concepts/patterns.md#how-to-error-handling).

**Ingress / Egress**
Ingress: entry points where data enters the graph. Egress: exit points where results leave the graph or are persisted. See [Architecture: Message Flow](../concepts/architecture.md#message-flow).

**Instrumentation**
Adding observability code to measure performance and behavior. See [Observability: Performance Monitoring](../concepts/observability.md#performance-monitoring).

---

## L

**Latency Budget**
The maximum expected end-to-end time from message ingress to egress under normal load. See [Observability: Performance Considerations](../concepts/observability.md#performance-considerations).

**Latest Policy**
An overflow policy that keeps only the newest item when the queue is full. See [Patterns: Latest Policy](../concepts/patterns.md#latest-replace-older-with-newest).

**Lifecycle Hook**
A method called by the runtime at specific points in a node's execution (start, message, tick, stop). See [Patterns: Scheduler Lifecycle](../concepts/patterns.md#reference-scheduler-configuration-and-lifecycle).

**Log Level**
The minimum severity level for log messages (DEBUG, INFO, WARN, ERROR). See [Observability: Log Levels](../concepts/observability.md#log-levels).

---

## M

**Metric**
A numeric time-series signal used for observability (counters, gauges, histograms) emitted by the runtime and nodes. See [Observability: Metrics Collection](../concepts/observability.md#how-to-metrics-collection).

**Message**
An envelope carrying a payload and metadata (e.g., timestamps, keys, trace IDs) across edges. See [API: Message](../reference/api.md#message).

**Message Type**
Classification of messages as DATA, CONTROL, or ERROR. See [API: Message](../reference/api.md#message).

**Middleware**
Software that provides services to applications beyond those available from the operating system.

---

## N

**Node**
A single-responsibility processing unit that consumes and produces messages. The core building block of graphs. See [Architecture: Node](../concepts/architecture.md#node).

**Namespace**
A prefix applied to metric names to organize and group related metrics. See [Observability: Configuration](../concepts/observability.md#basic-configuration).

**Normal Priority**
The default scheduling priority for data messages. See [Patterns: Control-plane Priority](../concepts/patterns.md#how-to-control-plane-priority).

---

## O

**Observability**
Capabilities for understanding internal state and behavior through logs, metrics, and traces. See [Observability](../concepts/observability.md).

**Overflow**
A queue-full condition on an edge that triggers the configured enqueue policy. See [Patterns: Backpressure and Overflow](../concepts/patterns.md#how-to-backpressure-and-overflow).

**Overflow Policy**
The behavior applied when an edge's queue is full. See [API: Policy Semantics](../reference/api.md#backpressure-and-overflow).

---

## P

**Priority**
A scheduling attribute that influences the execution order of messages or tasks (e.g., control messages may have higher priority). See [Patterns: Control-plane Priority](../concepts/patterns.md#how-to-control-plane-priority).

**Producer / Consumer**
Producer: emits messages onto an edge. Consumer: receives messages from an edge. Nodes are often both. See [Architecture: Message Flow](../concepts/architecture.md#message-flow).

**Port**
A named input or output connection point on a node. See [API: Ports and PortSpec](../reference/api.md#ports-and-portspec).

**Policy**
A configuration object that defines behavior for edges, routing, or retries. See [API: Policies](../reference/api.md#backpressure-and-overflow).

**Payload**
The actual data content of a message. See [API: Message Fields](../reference/api.md#message-fields).

---

## Q

**Queue**
The internal buffer on an edge that decouples producers and consumers. Bounded by design. See [Architecture: Edge](../concepts/architecture.md#edge).

**Queue Depth**
The current number of messages waiting in a queue. See [Observability: Built-in Metrics](../concepts/observability.md#edge-metrics).

---

## R

**Retry**
A strategy to attempt processing again after transient failures. Often paired with idempotency and backoff policies. See [API: RetryPolicy](../reference/api.md#backpressure-and-overflow).

**Runtime**
The scheduler and orchestration engine that executes nodes, enforces priorities, and provides observability. See [Architecture: Core Components](../concepts/architecture.md#core-components).

**Routing**
The process of directing messages to specific paths based on content or policy. See [Patterns: Routing](../concepts/patterns.md#reference-routing).

**Routable**
A protocol that allows objects to provide a routing key. See [API: Routing](../reference/api.md#routing).

---

## S

**Scheduler**
Component that decides execution order of work items based on priorities, readiness, and backpressure signals. See [Architecture: Scheduler](../concepts/architecture.md#scheduler).

**Shutdown (Graceful)**
A termination mode where the runtime stops accepting new work, drains in-flight messages, and cleans up resources. See [API: Scheduler Examples](../reference/api.md#scheduler-examples).

**Subgraph**
A reusable composite of nodes and edges treated as a single unit within a larger graph. See [Patterns: Subgraph Composition](../concepts/patterns.md#reference-subgraph-composition-and-reuse).

**Span**
A unit of work in distributed tracing that represents an operation or function call. See [Observability: Distributed Tracing](../concepts/observability.md#how-to-distributed-tracing).

**Structured Logging**
Logging that uses consistent, machine-readable formats with structured fields. See [Observability: Structured Logging](../concepts/observability.md#how-to-structured-logging).

**Sample Rate**
The fraction of operations that are traced (0.0 to 1.0). See [Observability: Configuration](../concepts/observability.md#basic-configuration).

---

## T

**Trace**
A correlated record of events across nodes/edges that captures causality for a single request or message journey. See [Observability: Distributed Tracing](../concepts/observability.md#how-to-distributed-tracing).

**Throughput**
The rate at which messages are processed (e.g., messages/sec). Balanced with latency and resource usage. See [Observability: Performance Considerations](../concepts/observability.md#performance-considerations).

**Typed Edge**
An edge that enforces a payload schema or type for messages, enabling validation and safety. See [API: Ports and PortSpec](../reference/api.md#ports-and-portspec).

**Tick**
A periodic execution cycle for nodes that need time-based processing. See [Patterns: Scheduler Lifecycle](../concepts/patterns.md#reference-scheduler-configuration-and-lifecycle).

**Trace ID**
A unique identifier that correlates all operations within a single request or message flow. See [Observability: Trace Context Management](../concepts/observability.md#trace-context-management).

---

## U

**Upstream / Downstream**
Upstream: components that produce inputs to a node. Downstream: components that consume outputs from a node. See [Architecture: Message Flow](../concepts/architecture.md#message-flow).

**Unbounded**
A queue or buffer without size limits (not used in Meridian Runtime by design).

---

## V

**Validation**
The process of ensuring message payloads conform to expected schemas or invariants before processing. See [Patterns: Error Handling](../concepts/patterns.md#how-to-error-handling).

**Version**
A release identifier for the runtime or application components.

---

## W

**Watermark**
A progress indicator that denotes that all messages up to a certain event-time or sequence have been observed/processed.

**Worker**
A node that performs computational work on messages.

---

## Z

**Zero-downtime Deploy**
A deployment strategy that avoids service interruption via techniques like blue/green, canary, or rolling updates with graceful handover.

**Zero-cost**
A property where features have no performance impact when disabled. See [Observability: Performance Considerations](../concepts/observability.md#performance-considerations).

---

## Conventions

### Documentation Standards
- Use **bold** for glossary terms when first defined
- Use lowercase-kebab-case for filenames and directories
- Use sentence case for headings; retain canonical capitalization for proper nouns
- Prefer precise, unambiguous definitions with links to reference pages

### Code Standards
- Use snake_case for Python functions and variables
- Use PascalCase for Python classes
- Use UPPER_CASE for constants
- Use descriptive names that reflect purpose and behavior

### Cross-references
- Link to relevant API documentation sections
- Reference specific patterns and examples
- Include links to architecture concepts
- Connect related terms within the glossary

### Change Requests
- Propose additions/edits via PRs referencing the term's first usage in code/docs
- Include examples and cross-links to relevant guides or reference pages
- Ensure new terms follow established conventions
- Update related documentation when adding new terms 