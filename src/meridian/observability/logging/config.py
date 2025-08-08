from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TextIO
import sys


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass
class LogConfig:
    level: LogLevel = LogLevel.INFO
    json: bool = True
    stream: TextIO = field(default_factory=lambda: sys.stderr)
    extra_fields: dict[str, Any] = field(default_factory=dict)
