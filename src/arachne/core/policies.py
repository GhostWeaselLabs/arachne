from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol, TypeVar

T = TypeVar("T")


class PutResult(Enum):
    OK = auto()
    BLOCKED = auto()
    DROPPED = auto()
    REPLACED = auto()
    COALESCED = auto()


class Policy(Protocol[T]):
    def on_enqueue(self, capacity: int, size: int, item: T) -> PutResult: ...


class Block:
    def on_enqueue(self, capacity: int, size: int, item: T) -> PutResult:
        return PutResult.BLOCKED if size >= capacity else PutResult.OK


class Drop:
    def on_enqueue(self, capacity: int, size: int, item: T) -> PutResult:
        return PutResult.DROPPED if size >= capacity else PutResult.OK


class Latest:
    def on_enqueue(self, capacity: int, size: int, item: T) -> PutResult:
        if size >= capacity:
            return PutResult.REPLACED
        return PutResult.OK


@dataclass(frozen=True, slots=True)
class Coalesce:
    fn: callable[[T, T], T]

    def on_enqueue(self, capacity: int, size: int, item: T) -> PutResult:
        if size >= capacity:
            return PutResult.COALESCED
        return PutResult.OK


class RetryPolicy(Enum):
    NONE = 0
    SIMPLE = 1


class BackpressureStrategy(Enum):
    DROP = 0
    BLOCK = 1


class Routable(Protocol):
    def route_key(self) -> str: ...


@dataclass(frozen=True, slots=True)
class RoutingPolicy:
    key: str = "default"

    def select(self, item: Routable | object) -> str:
        try:
            return item.route_key()  # type: ignore[no-any-return]
        except Exception:
            return self.key
