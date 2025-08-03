# Getting Started

Welcome to Meridian Runtime — a minimal, reusable graph runtime for Python. This guide gets you from zero to a running example, and shows you where to go next.

If you’re familiar with dataflow systems (nodes/edges/graphs), you’ll feel at home. Meridian emphasizes predictability under load, strong observability, and clean composition.

---

## Prerequisites

- Python 3.11+
- uv (fast Python package manager): https://github.com/astral-sh/uv
- macOS/Linux recommended (Windows should work via WSL)

Optional but recommended:
- make
- gh (GitHub CLI) if you plan to contribute

---

## Install and Setup

Clone the repository:
```text
git clone https://github.com/GhostWeaselLabs/meridian-runtime.git
cd meridian-runtime
```

Create and sync the environment with uv:
```text
uv lock
uv sync
```

You can now run any commands in a reproducible environment using:
```text
uv run <command>
```

---

## Your First Run: Verify The Runtime

We provide a one-shot verification script that runs smoke, integration, and stress tests with coverage thresholds.

```text
uv run bash scripts/verify.sh
```

What this does:
- Executes the test suite (including stress tests)
- Enforces coverage gates (core ≥ 90%, overall ≥ 80%)
- Produces a single PASS/FAIL signal

If the script passes, your local environment is healthy and ready for development.

---

## Development Loop

The typical loop is: lint -> type-check -> test -> run examples.

```text
# Lint
uv run ruff check .

# Type-check
uv run mypy src

# Tests with coverage
uv run pytest --cov=src --cov-fail-under=80
```

If you prefer make targets, you may see convenient shortcuts in the repository’s Makefile, such as:
```text
make demo-sentiment
make demo-coalesce
```

---

## Run Examples

Meridian ships with runnable examples that demonstrate realistic behavior: control-plane priorities, overflow policies, coalescing, and graceful shutdown.

From the project root:

Sentiment pipeline (control-plane priority, mixed overflow policies):
```text
uv run python examples/sentiment/main.py --human --timeout-s 6.0
```

Streaming coalesce (high-rate stream with deterministic coalescing under pressure):
```text
uv run python examples/streaming_coalesce/main.py --human --timeout-s 5.0
```

Tip: use --help on any example for supported flags.

---

## Core Concepts

Meridian exposes a small set of primitives:
- Node: a single-responsibility processing unit (on_start/on_tick/on_stop)
- Edge: a bounded queue between nodes with a configurable overflow policy
- Subgraph: a reusable composition of nodes/edges with typed ingress/egress
- Scheduler: fairness and priority-aware execution
- Observability: structured logs, metrics, and trace hooks

Overflow policies include:
- Block: producers wait when the queue is full
- Drop: new messages are dropped under pressure
- Latest: keep only the most recent payload(s)
- Coalesce: merge incoming messages deterministically

Control-plane priorities let you signal urgent messages (e.g., shutdown, flush, reconfigure) that preempt standard traffic.

---

## Example Index

Use these to explore specific features:

1. Sentiment (examples/sentiment)
   - Demonstrates:
     - Control-plane preemption (e.g., FLUSH, QUIET/VERBOSE)
     - Mixed overflow policies per edge
     - Priority fairness and graceful shutdown
     - Runtime observability and logging

   Run:
   ```text
   uv run python examples/sentiment/main.py --human --timeout-s 6.0
   ```

2. Streaming Coalesce (examples/streaming_coalesce)
   - Demonstrates:
     - Coalesce policy for high-rate aggregation
     - Deterministic merging under pressure
     - Per-edge default policy configuration

   Run:
   ```text
   uv run python examples/streaming_coalesce/main.py --human --timeout-s 5.0
   ```

Future examples to look for:
- Hello Graph (minimal dataflow with a couple of nodes and edges)
- Backpressure E2E demo (block/drop/latest/coalesce comparison)
- Observability cookbook (logs, metrics, traces)

---

## Project Layout

```text
src/meridian/
  core/           # nodes, edges, subgraphs, scheduler, policies
  observability/  # logging/metrics/tracing hooks
examples/
  sentiment/
  streaming_coalesce/
tests/
  unit/
  integration/
  soak/
scripts/
  verify.sh       # one-shot verification gate (tests + coverage)
```

---

## Troubleshooting

- Tests flaky or slow?
  - Ensure nothing else is consuming heavy CPU in the background.
  - Run `uv run pytest -q` to see minimal output.
- Coverage below threshold?
  - Run subsets: `uv run pytest tests/unit -q`
  - Check reports and add targeted unit tests.
- Example hangs?
  - Use shorter `--timeout-s` values.
  - Enable human-friendly output (`--human`) to see pipeline state.

---

## Contributing

We welcome issues, PRs, and discussions:
- Issues: https://github.com/GhostWeaselLabs/meridian-runtime/issues
- Discussions: https://github.com/GhostWeaselLabs/meridian-runtime/discussions

Before submitting, please:
- Run the full verification: `uv run bash scripts/verify.sh`
- Ensure linters and type checks pass
- Follow patterns used in existing nodes/edges for clarity and observability

If you plan to contribute regularly, check out:
- CONTRIBUTING guidelines
- Release and versioning notes
- Docs on examples and patterns

---

## What’s Next?

- Read the Concepts and Patterns guide for deeper usage
- Explore the API Reference for node/edge/subgraph contracts
- Try extending an example (e.g., add a control-plane message or a new edge policy)
- Add observability hooks and inspect logs/metrics under load

Happy weaving.