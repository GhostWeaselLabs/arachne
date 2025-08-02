"""pipeline_demo example package.

Run:
  uv run python -m examples.pipeline_demo.main

Demonstrates:
  - validator → transformer → sink with backpressure
  - overflow policies: block, latest, coalesce
  - control-plane kill switch with priority preemption
"""
