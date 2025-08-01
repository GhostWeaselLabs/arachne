from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    DATA = "DATA"
    CONTROL = "CONTROL"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class Message:
    type: MessageType
    payload: Any
    metadata: Mapping[str, Any] | None = None

    def is_control(self) -> bool:
        return self.type == MessageType.CONTROL

    def is_error(self) -> bool:
        return self.type == MessageType.ERROR

    def is_data(self) -> bool:
        return self.type == MessageType.DATA
