<!-- CI trigger: harmless comment to regenerate logs for link-check dry run -->

# Meridian Runtime

Minimal, reusable graph runtime for Python. Build real-time, observable dataflows from small, single‑responsibility nodes connected by typed, bounded edges.

Meridian gives you:
- A tiny, composable runtime (nodes, edges, subgraphs, scheduler)
- Backpressure by default with configurable overflow policies
- Control‑plane priorities (e.g., kill switch) for predictable behavior under load
- First‑class observability (structured logs, metrics, trace hooks)
- A clean, SRP/DRY‑friendly codebase

Get the source: https://github.com/GhostWeaselLabs/meridian-runtime

For an overview of how this documentation is organized, see About these docs: ./ABOUT.md

***

## What can you build?

- Market/stream processing with strict backpressure
- Event enrichment and filtering pipelines
- Streaming ETL/log processing
- Control planes with prioritized signals
- Any real‑time graph that needs predictable flow control and visibility

***

## Quick start

Prereqs
- Python 3.11+
- uv (https://github.com/astral-sh/uv)

Initialize environment
```bash
uv lock
uv sync
```

Dev loop
```bash
# Lint
uv run ruff check .

# Format check (if black is configured locally)
uv run black --check .

# Type-check
uv run mypy src

# Tests with coverage
uv run pytest --cov=src --cov-fail-under=80
```

Run the examples
```bash
# Hello graph (minimal)
uv run python -m examples.hello_graph.main

# Sentiment pipeline (control-plane preemption, backpressure)
uv run python examples/sentiment/main.py --human --timeout-s 6.0

# Streaming coalesce (burst smoothing with deterministic merges)
uv run python examples/streaming_coalesce/main.py --human --timeout-s 5.0
```

***

## Core ideas in 30 seconds

- Node: single‑responsibility unit with typed inputs/outputs
- Edge: bounded queue with overflow policy (block, drop, latest, coalesce)
- Subgraph: reusable composition exposing its own inputs/outputs
- Scheduler: fairness + priorities; drives ticks and graceful shutdown
- Observability: logs, metrics, trace hooks embedded in the runtime

These primitives keep graphs explicit, testable, and easy to evolve.

***

## Next steps

Read the guides:
- Quickstart: ./quickstart.md
- API Reference: ./api.md
- Patterns: ./patterns.md
- Observability: ./observability.md
- Troubleshooting: ./troubleshooting.md

Contribute and plan:
- Contributing Guide: ./contributing/CONTRIBUTING.md
- Release Process: ./contributing/RELEASING.md
- Governance & Roadmaps: ./plan/

***

## Example layout

```text
src/meridian/
  core/           # nodes, edges, subgraphs, scheduler
  observability/  # logs, metrics, tracing hooks
  utils/          # shared utilities
examples/
  hello_graph/          # minimal runnable example
  sentiment/            # control-plane overrides and priorities
  streaming_coalesce/   # coalescing policy under burst pressure
tests/
  unit/           # unit tests
  integration/    # end-to-end graph tests
```

***

## Design principles

- Small, composable files (~200 lines target)
- Single responsibility, explicit contracts
- Backpressure first; overflow policies are explicit
- Prioritize control‑plane messages
- Observability is not an afterthought

***

## Links

- Repo: https://github.com/GhostWeaselLabs/meridian-runtime
- Issues: https://github.com/GhostWeaselLabs/meridian-runtime/issues
- Discussions: https://github.com/GhostWeaselLabs/meridian-runtime/discussions

Happy weaving.