from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TracingConfig:
    """
    Configuration for tracing behavior and provider selection.

    Attributes:
      enabled: When True, tracing spans are recorded via the configured provider.
      provider: "noop" | "inmemory" | "opentelemetry"
      sample_rate: 0.0–1.0 sampling fraction for OpenTelemetry.
    """

    enabled: bool = False
    provider: str = "noop"
    sample_rate: float = 0.0
