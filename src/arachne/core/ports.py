from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PortDirection(str, Enum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"


@dataclass(frozen=True, slots=True)
class Port:
    name: str
    direction: PortDirection
    index: Optional[int] = None

    def is_input(self) -> bool:
        return self.direction == PortDirection.INPUT

    def is_output(self) -> bool:
        return self.direction == PortDirection.OUTPUT
