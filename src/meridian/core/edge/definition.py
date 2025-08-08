from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import time
from typing import Generic, TypeVar

from ...observability.logging import get_logger, with_context
from ...observability.metrics import Metrics, get_metrics
from ..message import Message
from ..policies import Coalesce, Latest, Policy, PutResult
from ..ports import Port, PortSpec

T = TypeVar("T")


@dataclass
class Edge(Generic[T]):
    source_node: str
    source_port: Port
    target_node: str
    target_port: Port
    capacity: int = 1024
    spec: PortSpec | None = None
    default_policy: Policy[T] | None = None
    _q: deque[T] = field(default_factory=deque, init=False, repr=False)
    _metrics: Metrics = field(default_factory=lambda: get_metrics(), init=False, repr=False)
    _enq = None
    _deq = None
    _drops = None
    _depth = None
    _blocked_time = None

    def __post_init__(self) -> None:
        self._init_metrics()

    def _init_metrics(self) -> None:
        edge_id = f"{self.source_node}:{self.source_port.name}->{self.target_node}:{self.target_port.name}"
        edge_labels = {"edge_id": edge_id}
        self._enq = self._metrics.counter("edge_enqueued_total", edge_labels)
        self._deq = self._metrics.counter("edge_dequeued_total", edge_labels)
        self._drops = self._metrics.counter("edge_dropped_total", edge_labels)
        self._depth = self._metrics.gauge("edge_queue_depth", edge_labels)
        self._blocked_time = self._metrics.histogram("edge_blocked_time_seconds", edge_labels)

    def depth(self) -> int:
        d = len(self._q)
        if self._depth:
            self._depth.set(d)
        return d

    def _edge_id(self) -> str:
        return f"{self.source_node}:{self.source_port.name}->{self.target_node}:{self.target_port.name}"

    def _coalesce(self, fn: Coalesce, new_item: T) -> None:
        logger = get_logger()
        if self._q:
            old = self._q.pop()
            try:
                merged = fn.fn(old, new_item)
                self._q.append(merged)  # type: ignore[arg-type]
                with with_context(edge_id=self._edge_id()):
                    logger.debug("edge.coalesce", "Messages coalesced successfully")
            except Exception as e:
                with with_context(edge_id=self._edge_id()):
                    logger.error("edge.coalesce_error", f"Coalesce function failed: {e}")
                self._q.append(new_item)
        else:
            self._q.append(new_item)

    def try_put(self, item: T, policy: Policy[T] | None = None) -> PutResult:
        logger = get_logger()
        start_time = time.perf_counter()
        value = item.payload if isinstance(item, Message) else item
        if self.spec and not self.spec.validate(value):
            with with_context(edge_id=self._edge_id()):
                logger.warn("edge.validation_failed", "Item does not conform to PortSpec schema")
            raise TypeError("item does not conform to PortSpec schema")
        pol = policy or self.default_policy or Latest()
        res = pol.on_enqueue(self.capacity, len(self._q), item)
        with with_context(edge_id=self._edge_id()):
            if res == PutResult.OK:
                self._q.append(item)
                if self._enq:
                    self._enq.inc(1)
                logger.debug("edge.enqueue", f"Item enqueued, depth={len(self._q)}")
            elif res == PutResult.REPLACED:
                if self._q:
                    self._q.pop()
                self._q.append(item)
                if self._enq:
                    self._enq.inc(1)
                logger.debug("edge.replace", f"Item replaced, depth={len(self._q)}")
            elif res == PutResult.DROPPED:
                if self._drops:
                    self._drops.inc(1)
                logger.debug("edge.drop", "Item dropped due to capacity limit")
            elif res == PutResult.COALESCED and isinstance(pol, Coalesce):
                self._coalesce(pol, item)
                if self._enq:
                    self._enq.inc(1)
                logger.debug("edge.coalesce", f"Item coalesced, depth={len(self._q)}")
            elif res == PutResult.BLOCKED:
                blocked_duration = time.perf_counter() - start_time
                if self._blocked_time:
                    self._blocked_time.observe(blocked_duration)
                logger.debug("edge.blocked", f"Put blocked, duration={blocked_duration:.6f}s")
        self.depth()
        return res

    def try_get(self) -> T | None:
        logger = get_logger()
        if not self._q:
            return None
        item = self._q.popleft()
        if self._deq:
            self._deq.inc(1)
        with with_context(edge_id=self._edge_id()):
            logger.debug("edge.dequeue", f"Item dequeued, depth={len(self._q)}")
        self.depth()
        return item

    def is_empty(self) -> bool:
        return len(self._q) == 0

    def is_full(self) -> bool:
        return len(self._q) >= self.capacity
