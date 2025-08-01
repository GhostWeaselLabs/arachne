from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Generic, Optional, TypeVar

from .message import Message
from .policies import Coalesce, Latest, Policy, PutResult
from .ports import Port, PortSpec

T = TypeVar("T")


@dataclass(slots=True)
class Edge(Generic[T]):
    source_node: str
    source_port: Port
    target_node: str
    target_port: Port
    capacity: int = 1024
    spec: Optional[PortSpec] = None
    _q: Deque[T] = field(default_factory=deque, init=False, repr=False)

    def depth(self) -> int:
        return len(self._q)

    def _coalesce(self, fn: Coalesce[T], new_item: T) -> None:
        if self._q:
            old = self._q.pop()
            merged = fn.fn(old, new_item)
            self._q.append(merged)
        else:
            self._q.append(new_item)

    def try_put(self, item: T, policy: Policy[T] | None = None) -> PutResult:
        if self.spec and not self.spec.validate(item):
            raise TypeError("item does not conform to PortSpec schema")
        pol = policy or Latest()  # default to non-blocking behavior for now
        res = pol.on_enqueue(self.capacity, len(self._q), item)
        if res == PutResult.OK:
            self._q.append(item)
        elif res == PutResult.REPLACED:
            if self._q:
                self._q.pop()
            self._q.append(item)
        elif res == PutResult.COALESCED and isinstance(pol, Coalesce):
            self._coalesce(pol, item)
        return res

    def try_get(self) -> Optional[T]:
        if not self._q:
            return None
        return self._q.popleft()
