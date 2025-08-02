# Patterns

Backpressure and overflow
- block: apply backpressure upstream; default
- drop: drop new messages when full
- latest: keep only newest beyond capacity
- coalesce: merge bursts via function

Control-plane priority
- Use higher priority edges for kill switches or coordination

Subgraph composition
- Expose input/output ports; validate wiring; ensure schema compatibility

Error handling
- Handle exceptions in node hooks; default policy is skip/continue; log structured errors
