from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol, TypeVar, runtime_checkable

T_contra = TypeVar("T_contra", contravariant=True)


class PutResult(Enum):
    """
    Result of attempting to enqueue an item into a bounded buffer/edge.

    OK:
      Item enqueued successfully; no capacity constraint impacted the operation.

    BLOCKED:
      Enqueue would exceed capacity; producer should block or yield cooperatively.

    DROPPED:
      Item was intentionally not enqueued due to capacity limits (lossy behavior).

    REPLACED:
      Latest item replaced an older one to keep only the most recent value (single-slot semantics).

    COALESCED:
      Item merged with an existing one via a coalescing function to reduce queue pressure.
    """

    OK = auto()
    BLOCKED = auto()
    DROPPED = auto()
    REPLACED = auto()
    COALESCED = auto()


class Policy(Protocol[T_contra]):
    """
    Backpressure policy protocol for bounded queues.

    on_enqueue(capacity, size, item) -> PutResult
      Decide how to handle a new item given the queue capacity and current size.

    Parameters:
      capacity: Maximum allowed items in the queue.
      size: Current number of items in the queue.
      item: The item to be enqueued (type contravariant).

    Returns:
      PutResult indicating whether to enqueue, block, drop, replace, or coalesce.
    """

    def on_enqueue(self, capacity: int, size: int, item: T_contra) -> PutResult: ...


class Block(Policy[object]):
    """
    Blocking policy: producers should block/yield when capacity is reached.

    Semantics:
      - If size >= capacity: return BLOCKED (cooperative backpressure).
      - Otherwise: return OK.

    Suitable when lossless delivery is required and producers can wait.
    """

    def on_enqueue(self, capacity: int, size: int, item: object) -> PutResult:
        return PutResult.BLOCKED if size >= capacity else PutResult.OK


class Drop(Policy[object]):
    """
    Dropping policy: excess items are discarded once capacity is reached.

    Semantics:
      - If size >= capacity: return DROPPED (lossy).
      - Otherwise: return OK.

    Suitable for telemetry or low-importance streams where freshness matters
    but occasional loss is acceptable.
    """

    def on_enqueue(self, capacity: int, size: int, item: object) -> PutResult:
        return PutResult.DROPPED if size >= capacity else PutResult.OK


class Latest(Policy[object]):
    """
    Latest-wins policy: keep only the most recent item when at capacity.

    Semantics:
      - If size >= capacity: return REPLACED (drop older value, keep the latest).
      - Otherwise: return OK.

    Suitable for single-slot state or UI-like consumers that only need the newest value.
    """

    def on_enqueue(self, capacity: int, size: int, item: object) -> PutResult:
        if size >= capacity:
            return PutResult.REPLACED
        return PutResult.OK


@dataclass(frozen=True, slots=True)
class Coalesce(Policy[object]):
    """
    Coalescing policy: merge items when at capacity using a user-provided function.

    Attributes:
      fn: Callable that merges two items into one (e.g., aggregates, reduces, or batches).

    Semantics:
      - If size >= capacity: return COALESCED (runtime should call fn to merge).
      - Otherwise: return OK.

    Suitable for batchable workloads where combining items mitigates pressure.
    """

    fn: Callable[[object, object], object]

    def on_enqueue(self, capacity: int, size: int, item: object) -> PutResult:
        if size >= capacity:
            return PutResult.COALESCED
        return PutResult.OK


# Convenience factory functions expected by examples


def block() -> Block:
    """Factory: create a Block policy."""
    return Block()


def drop() -> Drop:
    """Factory: create a Drop policy."""
    return Drop()


def latest() -> Latest:
    """Factory: create a Latest policy."""
    return Latest()


def coalesce(fn: Callable[[object, object], object]) -> Coalesce:
    """Factory: create a Coalesce policy with a merge function."""
    return Coalesce(fn)


class RetryPolicy(Enum):
    """
    Retry behavior for operations that can be retried on failure.

    NONE:
      Do not retry.

    SIMPLE:
      Apply a simple retry strategy (implementation-defined by the runtime).
    """

    NONE = 0
    SIMPLE = 1


class BackpressureStrategy(Enum):
    """
    High-level backpressure strategies used by the runtime.

    DROP:
      Prefer dropping items when capacity is reached.

    BLOCK:
      Prefer blocking/yielding the producer when capacity is reached.
    """

    DROP = 0
    BLOCK = 1


@runtime_checkable
class Routable(Protocol):
    """
    Protocol for items that can provide a routing key.

    route_key() -> str
      Returns a string used for partitioning or consistent routing.
    """

    def route_key(self) -> str: ...


@dataclass(frozen=True, slots=True)
class RoutingPolicy:
    """
    Policy for selecting a routing key for items.

    Attributes:
      key:
        Default routing key used when the item does not implement Routable.

    Behavior:
      - If the item implements Routable, its route_key() is used.
      - Otherwise, the default key is returned.
    """

    key: str = "default"

    def select(self, item: Routable | object) -> str:
        if isinstance(item, Routable):
            return item.route_key()
        return self.key
