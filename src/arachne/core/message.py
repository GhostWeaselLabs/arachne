from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional


class MessageType(str, Enum):
    DATA = "DATA"
    CONTROL = "CONTROL"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class Message:
    type: MessageType
    payload: Any
    metadata: Optional[Mapping[str, Any]] = None

    def is_control(self) -> bool:
        return self.type == MessageType.CONTROL

    def is_error(self) -> bool:
        return self.type == MessageType.ERROR

    def is_data(self) -> bool:
        return self.type == MessageType.DATA
