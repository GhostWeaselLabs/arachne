"""
Backward-compatible shim to preserve public imports.

This module re-exports the modularized scheduler API from
`meridian.core.scheduler` package so existing imports continue to work:

    from meridian.core.scheduler import Scheduler, SchedulerConfig

"""
from __future__ import annotations

from .scheduler import Scheduler, SchedulerConfig  # type: ignore  # re-export

__all__ = ["Scheduler", "SchedulerConfig"]
