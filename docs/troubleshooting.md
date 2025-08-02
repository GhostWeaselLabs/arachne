# Troubleshooting

Common issues
- uv not installed: install uv, then initialize the environment:
  ```bash
  uv lock
  uv sync
  ```
- Import errors: run modules via uv and -m to ensure correct PYTHONPATH:
  ```bash
  uv run python -m examples.hello_graph.main
  ```
- Type mismatches: ensure PortSpec.schema matches Message.payload type. For example, if your port expects int, emit an int:
  ```python
  from arachne.core import Message, MessageType, PortSpec
  spec = PortSpec("in", int)
  # OK: payload is int
  msg_ok = Message(type=MessageType.DATA, payload=1)
  # Mismatch: payload is str (will fail validation on enqueue)
  msg_bad = Message(type=MessageType.DATA, payload="1")
  ```
- Queue full: increase capacity or use an overflow policy like Latest/Coalesce:
  ```python
  from arachne.core.policies import Latest, Coalesce
  # Increase capacity
  sg.connect(("producer","out"), ("consumer","in"), capacity=64)
  # Keep only newest when full
  sg.connect(("producer","out"), ("consumer","in"), capacity=16, policy=Latest())
  # Merge bursts using a function
  def combine(old, new): return new
  sg.connect(("producer","out"), ("consumer","in"), capacity=16, policy=Coalesce(combine))
  ```

Debugging
- Enable debug logs in observability config
- Use metrics to inspect edge depths and drops
- Use module execution for tests/examples to avoid path issues:
  ```bash
  uv run pytest
  uv run python -m examples.pipeline_demo.main
  ```
