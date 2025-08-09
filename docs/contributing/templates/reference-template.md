# Reference template

Summary
Provide a 1–2 sentence description of what this reference covers and who should use it. This page is the definitive, authoritative source for a specific surface area (API, CLI, configuration, schema, etc.). Keep it factual and exhaustive; move tutorials to guides.

Scope
- What’s included: brief bullets
- What’s not included: brief bullets (link to other references if applicable)

Versioning
- Since: vX.Y.Z
- Last updated: YYYY-MM-DD
- Stability: stable | experimental | deprecated

---

## Overview

A concise explanation of the component being documented (API surface, module, CLI, config). State core concepts the reader must know to understand the reference. Link to overview docs for deeper conceptual material.

Quick links
- How-to guide: ../guides/<related-guide>.md
- Concepts: ../concepts/<related-concept>.md
- Examples: ../examples/index.md (code in external `meridian-runtime-examples` repository)

---

## Usage at a glance

Short, copy-pasteable example(s) demonstrating common usage.

```bash
# Example: CLI invocation
meridian runtime --config config.toml --log-level info
```

```python
# Example: Python API
from meridian import Runtime, Node
rt = Runtime()
# ...
rt.start()
```

---

## Terminology

Define important terms as they are used in this reference.
- Term A: definition
- Term B: definition

---

## Specification

Provide the exhaustive, authoritative details. Prefer structured, scannable sections. Use stable ordering (alphabetical or logical).

### Endpoints / Commands / Objects

For each item, use the following pattern.

Name
A short, descriptive title (e.g., create_graph, runtime start, config.runtime).

Description
One or two sentences describing the behavior and purpose.

Signature
- Function/method signature or CLI syntax.
- HTTP method and path for REST, or fields for schemas.

Parameters/Options
List each parameter/flag with:
- Name (type) – required? default?
- Description
- Constraints (allowed values, ranges, regex, size)
- Notes (security, performance, side effects)

Request/Body (if applicable)
- Shape and example

Response/Output (if applicable)
- Shape and example
- Error conditions and codes

Examples
- Minimal working example
- A realistic example with comments

Notes
- Edge cases, caveats, ordering guarantees, idempotency, timeouts

Repeat this subsection per endpoint/command/object.

Example format:

#### runtime.start

Description
Starts the scheduler and all registered nodes, enabling message processing.

Signature
```python
Runtime.start(block: bool = False) -> None
```

Parameters
- block (bool) – optional, default: False
  - If True, blocks the current thread until shutdown.

Behavior
- Initializes nodes in dependency order.
- Fails fast if any node fails to initialize.

Errors
- RuntimeError – when already started
- NodeInitError – when any node fails to initialize

Example
```python
rt = Runtime()
rt.register_node(hello_node)
rt.start(block=False)
```

---

## Configuration reference

If this reference covers configuration, provide a single source of truth table with defaults.

Format: TOML/YAML/JSON example

```toml
[runtime]
log_level = "info"   # one of: trace, debug, info, warn, error
metrics_port = 8000  # 0 to disable
```

Settings
- runtime.log_level (string) – default: "info"
  - Allowed: trace|debug|info|warn|error
  - Notes: higher verbosity impacts performance
- runtime.metrics_port (int) – default: 8000
  - 0 disables metrics server

---

## Errors and diagnostics

List all errors with meanings and likely root causes. Include remediation guidance.

- NodeInitError
  - Meaning: Node failed during initialization
  - Causes: misconfiguration, missing dependency
  - Remediation: check node logs; verify required environment variables

- BackpressureTimeout
  - Meaning: Message enqueue timed out due to bounded queue
  - Remediation: adjust queue size or producer rate

---

## Performance characteristics

- Complexity: O(...) for critical operations
- Latency implications: startup, steady state
- Memory/CPU considerations
- Tuning knobs: which settings affect performance and how

---

## Security considerations

- Authentication/authorization requirements (if any)
- Sensitive data handling (PII, secrets)
- Logging guidelines (avoid payloads; prefer IDs/metadata)
- Network exposure and port usage

---

## Compatibility and constraints

- Supported platforms and versions
- Backward/forward compatibility guarantees
- Thread-safety and reentrancy
- Limits (max nodes, max edges, payload size)

---

## Deprecations

List deprecated items with:
- Since version
- Replacement
- Removal timeline
- Migration guidance

---

## Changelog

Capture notable changes to this surface (link to repo changelog for full history).
- vX.Y.Z: Short description
- vX.Y.(Z-1): Short description

---

## Appendix

- Schema definitions (if large)
- Type mappings
- Additional examples

---

Authoring guidance for maintainers
- Keep reference pages exhaustive but non-tutorial.
- Prefer stable ordering and consistent headings across items.
- Mark experimental features clearly and include stability notes.
- Update examples whenever signatures or outputs change.
- Keep examples runnable and minimal; link to guides for context.

Metadata
owner: docs@your-org
last_updated: YYYY-MM-DD
status: stable
tags: [reference]