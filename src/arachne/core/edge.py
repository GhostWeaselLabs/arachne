from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from ..observability.metrics import Metrics, NoopMetrics
from .policies import Coalesce, Latest, Policy, PutResult
from .ports import Port, PortSpec

T = TypeVar("T")


@dataclass
class Edge(Generic[T]):
    source_node: str
    source_port: Port
    target_node: str
    target_port: Port
    capacity: int = 1024
    spec: PortSpec | None = None
    _q: deque[T] = field(default_factory=deque, init=False, repr=False)
    _metrics: Metrics = field(default_factory=NoopMetrics, init=False, repr=False)
    _enq = None
    _deq = None
    _drops = None
    _depth = None

    def depth(self) -> int:
        d = len(self._q)
        if self._depth is None:
            edge_lbl = {
                "edge": f"{self.source_node}:{self.source_port.name}->"
                f"{self.target_node}:{self.target_port.name}"
            }
            self._depth = self._metrics.gauge("queue_depth", edge_lbl)
        self._depth.set(d)
        return d

    def _coalesce(self, fn: Coalesce, new_item: T) -> None:
        if self._q:
            old = self._q.pop()
            merged = fn.fn(old, new_item)
            self._q.append(merged)  # type: ignore[arg-type]
        else:
            self._q.append(new_item)

    def try_put(self, item: T, policy: Policy[T] | None = None) -> PutResult:
        if self.spec and not self.spec.validate(item):
            raise TypeError("item does not conform to PortSpec schema")
        pol = policy or Latest()  # default to non-blocking behavior for now
        res = pol.on_enqueue(self.capacity, len(self._q), item)
        if self._enq is None:
            edge_lbl = {
                "edge": f"{self.source_node}:{self.source_port.name}->"
                f"{self.target_node}:{self.target_port.name}"
            }
            self._enq = self._metrics.counter("enqueued_total", edge_lbl)
        if self._deq is None:
            edge_lbl = {
                "edge": f"{self.source_node}:{self.source_port.name}->"
                f"{self.target_node}:{self.target_port.name}"
            }
            self._deq = self._metrics.counter("dequeued_total", edge_lbl)
        if self._drops is None:
            edge_lbl = {
                "edge": f"{self.source_node}:{self.source_port.name}->"
                f"{self.target_node}:{self.target_port.name}"
            }
            self._drops = self._metrics.counter("drops_total", edge_lbl)
        if res == PutResult.OK:
            self._q.append(item)
            self._enq.inc(1)
        elif res == PutResult.REPLACED:
            if self._q:
                self._q.pop()
            self._q.append(item)
            self._enq.inc(1)
        elif res == PutResult.DROPPED:
            self._drops.inc(1)
        elif res == PutResult.COALESCED and isinstance(pol, Coalesce):
            self._coalesce(pol, item)
            self._enq.inc(1)
        return res

    def try_get(self) -> T | None:
        if not self._q:
            return None
        return self._q.popleft()
