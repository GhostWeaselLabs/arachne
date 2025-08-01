from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class RetryPolicy(Enum):
    NONE = 0
    SIMPLE = 1


class BackpressureStrategy(Enum):
    DROP = 0
    BLOCK = 1


class Routable(Protocol):
    def route_key(self) -> str:  # pragma: no cover - protocol
        ...


@dataclass(frozen=True, slots=True)
class RoutingPolicy:
    key: str = "default"

    def select(self, item: Routable | object) -> str:
        try:
            return item.route_key()  # type: ignore[no-any-return]
        except Exception:
            return self.key
