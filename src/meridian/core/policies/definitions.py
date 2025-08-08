from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol, TypeVar, runtime_checkable

T_contra = TypeVar("T_contra", contravariant=True)


class PutResult(Enum):
    OK = auto()
    BLOCKED = auto()
    DROPPED = auto()
    REPLACED = auto()
    COALESCED = auto()


class Policy(Protocol[T_contra]):
    def on_enqueue(self, capacity: int, size: int, item: T_contra) -> PutResult: ...


class Block(Policy[object]):
    def on_enqueue(self, capacity: int, size: int, item: object) -> PutResult:
        return PutResult.BLOCKED if size >= capacity else PutResult.OK


class Drop(Policy[object]):
    def on_enqueue(self, capacity: int, size: int, item: object) -> PutResult:
        return PutResult.DROPPED if size >= capacity else PutResult.OK


class Latest(Policy[object]):
    def on_enqueue(self, capacity: int, size: int, item: object) -> PutResult:
        if size >= capacity:
            return PutResult.REPLACED
        return PutResult.OK


@dataclass(frozen=True, slots=True)
class Coalesce(Policy[object]):
    fn: Callable[[object, object], object]

    def on_enqueue(self, capacity: int, size: int, item: object) -> PutResult:
        if size >= capacity:
            return PutResult.COALESCED
        return PutResult.OK


def block() -> Block:
    return Block()


def drop() -> Drop:
    return Drop()


def latest() -> Latest:
    return Latest()


def coalesce(fn: Callable[[object, object], object]) -> Coalesce:
    return Coalesce(fn)


class RetryPolicy(Enum):
    NONE = 0
    SIMPLE = 1


class BackpressureStrategy(Enum):
    DROP = 0
    BLOCK = 1


@runtime_checkable
class Routable(Protocol):
    def route_key(self) -> str: ...


@dataclass(frozen=True, slots=True)
class RoutingPolicy:
    key: str = "default"

    def select(self, item: Routable | object) -> str:
        if isinstance(item, Routable):
            return item.route_key()
        return self.key
