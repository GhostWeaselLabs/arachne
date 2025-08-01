"""Validation issue data structure."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Issue:
    """Validation issue with severity and location context."""

    severity: str  # "error" | "warning"
    message: str
    location: str | tuple[str, ...]  # node, port, edge identifier

    def is_error(self) -> bool:
        """Check if this is an error-level issue."""
        return self.severity == "error"

    def is_warning(self) -> bool:
        """Check if this is a warning-level issue."""
        return self.severity == "warning"
