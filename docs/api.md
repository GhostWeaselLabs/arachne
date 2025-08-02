# API Overview

Install and import
- Prereqs: Python 3.11+, uv
- Install dev tools: uv lock; uv sync
- Import: from arachne.core import Message, Node, Subgraph, Scheduler, SchedulerConfig, PortSpec
- Policies: from arachne.core.policies import Block, Drop, Latest, Coalesce
- Observability: from arachne.observability.metrics import configure_metrics, PrometheusMetrics

Core types
- Message: data container with headers; supports get_trace_id(), with_headers(...)
- PortSpec: name, schema/type tuple or type; validate(value) checks payloads
- Policies: Block, Drop, Latest, Coalesce(fn)
- Edge: bounded, typed queue with capacity, try_put/try_get, metrics
- Node: lifecycle on_start/on_message/on_tick/on_stop; emit(port, Message)
- Subgraph: from_nodes(name, [nodes]); add_node(node[, name]); connect((src_node, src_port), (dst_node, dst_port), capacity, spec, priority)
- Scheduler: run(); shutdown(); set_priority(edge_id, band); set_capacity(edge_id, n); get_stats()

Lifecycle overview
- Node.on_start(): initialize resources
- Node.on_message(port, msg): process data; call emit() to forward
- Node.on_tick(): periodic work; cadence via scheduler tick_interval_ms
- Node.on_stop(): cleanup

Priorities and bands
- PriorityBand: CONTROL > HIGH > NORMAL; control-plane edges preempt
- Scheduler fairness_ratio: default (4,2,1); max_batch_per_node: default 8

Observability
- Logging: structured events via arachne.observability.logging
- Metrics: Noop by default; configure with PrometheusMetrics(); counters/gauges/histograms names include arachne_* prefix
- Tracing: context propagation via trace_id; spans around node and scheduler operations

Validation
- Edge validates Message.payload (or raw value) against PortSpec.schema on enqueue
- Subgraph validates unique names, ports, capacities, and schemas on build

Edge identifiers
- Format: source:out_port->target:in_port; used by set_priority/set_capacity

Example: minimal pipeline
```python
from arachne.core import Message, Node, Subgraph, Scheduler, SchedulerConfig, PortSpec
from arachne.core.policies import Latest

class Producer(Node):
    def __init__(self):
        super().__init__("producer", outputs=[PortSpec("out")])
    def _handle_tick(self):
        self.emit("out", Message.data(time.time()))

class Consumer(Node):
    def __init__(self):
        super().__init__("consumer", inputs=[PortSpec("in")])
    def _handle_message(self, port, msg):
        print("got", msg.payload)

sg = Subgraph.from_nodes("hello", [Producer(), Consumer()])
sg.connect(("producer","out"), ("consumer","in"), capacity=16, spec=PortSpec("in", float), policy=Latest())
Scheduler(SchedulerConfig()).register(sg)
Scheduler().run()
```
