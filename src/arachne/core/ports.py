from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Protocol, TypeGuard


class PortDirection(str, Enum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"


class SchemaValidator(Protocol):
    def __call__(self, value: Any) -> bool: ...


@dataclass(frozen=True, slots=True)
class PortSpec:
    name: str
    schema: type[Any] | tuple[type[Any], ...] | None = None
    policy: str | None = None

    def validate(self, value: Any) -> bool:
        if self.schema is None:
            return True
        if isinstance(self.schema, tuple):
            return isinstance(value, self.schema)
        return isinstance(value, self.schema)


@dataclass(frozen=True, slots=True)
class Port:
    name: str
    direction: PortDirection
    index: Optional[int] = None
    spec: Optional[PortSpec] = None

    def is_input(self) -> bool:
        return self.direction == PortDirection.INPUT

    def is_output(self) -> bool:
        return self.direction == PortDirection.OUTPUT
