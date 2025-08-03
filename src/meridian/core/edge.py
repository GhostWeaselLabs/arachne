from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import time
from typing import Generic, TypeVar

from ..observability.logging import get_logger, with_context
from ..observability.metrics import Metrics, get_metrics
from .message import Message
from .policies import Coalesce, Latest, Policy, PutResult
from .ports import Port, PortSpec

T = TypeVar("T")


@dataclass
class Edge(Generic[T]):
    """
    Bounded, in-memory channel between a source node/port and a target node/port.

    Semantics
    - Capacity-bounded FIFO queue with policy-controlled behavior on overflow.
    - Accepts Message payloads or raw values; when a PortSpec is provided, values are
      validated via PortSpec.validate before enqueue.
    - Enqueue behavior is governed by a Policy (Block, Drop, Latest, Coalesce). If no
      policy is provided on try_put(), Latest is used by default or the configured default_policy
      if present.

    Metrics and Observability
    - edge_enqueued_total: count of successful enqueues (including replace/coalesce cases)
    - edge_dequeued_total: count of dequeues
    - edge_dropped_total: count of dropped items due to capacity/policy
    - edge_queue_depth: current queue depth gauge
    - edge_blocked_time_seconds: time spent in BLOCKED outcomes (cooperative backpressure)
    - All metrics are labeled by a stable edge_id: "src_node:src_port->dst_node:dst_port"

    Threading/Performance
    - Intended for cooperative, single-threaded scheduling; avoid blocking calls.
    - Coalescing functions should be fast and exception-safe; on coalesce failure, the new
      item is appended to preserve forward progress.

    Attributes
    - source_node/source_port: origin of items
    - target_node/target_port: destination for items
    - capacity: maximum number of items permitted
    - spec: optional PortSpec used to validate payload types
    - default_policy: optional Policy used when none is provided at try_put() time

    """

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
        """Initialize metric instruments and labels after construction."""
        self._init_metrics()

    def _init_metrics(self) -> None:
        """Create counters, gauges, and histograms labeled by a stable edge_id."""
        edge_id = (
            f"{self.source_node}:{self.source_port.name}->"
            f"{self.target_node}:{self.target_port.name}"
        )
        edge_labels = {"edge_id": edge_id}

        self._enq = self._metrics.counter("edge_enqueued_total", edge_labels)
        self._deq = self._metrics.counter("edge_dequeued_total", edge_labels)
        self._drops = self._metrics.counter("edge_dropped_total", edge_labels)
        self._depth = self._metrics.gauge("edge_queue_depth", edge_labels)
        self._blocked_time = self._metrics.histogram("edge_blocked_time_seconds", edge_labels)

    def depth(self) -> int:
        """
        Return the current queue depth and update the depth gauge.

        Returns:
            Current number of items in the edge queue.
        """
        d = len(self._q)
        if self._depth:
            self._depth.set(d)
        return d

    def _edge_id(self) -> str:
        """Return the stable identifier for this edge."""
        return (
            f"{self.source_node}:{self.source_port.name}->"
            f"{self.target_node}:{self.target_port.name}"
        )

    def _coalesce(self, fn: Coalesce, new_item: T) -> None:
        """
        Merge the newest item with the most recent queued item using the provided function.

        Behavior:
            - If the queue has an existing item, pop it and apply fn(old, new).
              On success, append the merged result; on exception, fall back to
              appending the new item to maintain progress.
            - If the queue is empty, simply append the new item.

        Observability:
            - Logs success and errors with the current edge_id context.
        """
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
        """
        Attempt to enqueue an item under a backpressure policy.

        Parameters:
            item: Value to enqueue. If a Message, its payload is validated against PortSpec.
            policy: Backpressure Policy to apply. Defaults to Latest() if not provided.

        Returns:
            PutResult indicating OK, BLOCKED, DROPPED, REPLACED, or COALESCED.

        Raises:
            TypeError: If a PortSpec is present and the item (or Message payload) fails validation.

        Behavior:
            - Validates against spec when provided.
            - Applies the selected policy’s on_enqueue to decide overflow handling.
            - Updates metrics for enqueues, drops, coalesces, and blocked durations.
            - Updates depth gauge after the operation.

        Notes:
            - BLOCKED currently records blocked time; cooperative yielding is planned for future.
        """
        logger = get_logger()
        start_time = time.perf_counter()

        # Validate payload type against spec (Message payload or raw value)
        value = item.payload if isinstance(item, Message) else item
        if self.spec and not self.spec.validate(value):
            with with_context(edge_id=self._edge_id()):
                logger.warn("edge.validation_failed", "Item does not conform to PortSpec schema")
            raise TypeError("item does not conform to PortSpec schema")

        # Choose policy: explicit > default_policy > Latest()
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
        """
        Attempt to dequeue a single item if available.

        Returns:
            The next queued item, or None if the queue is empty.

        Side effects:
            - Increments dequeue counter on success.
            - Logs the operation and updates the depth gauge.
        """
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
        """Return True if the queue is empty."""
        return len(self._q) == 0

    def is_full(self) -> bool:
        """Return True if the queue has reached or exceeded capacity."""
        return len(self._q) >= self.capacity
