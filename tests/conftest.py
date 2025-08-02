# conftest.py
# Shared pytest fixtures and hooks for deterministic, observable test runs.

from __future__ import annotations

import os
import random
import sys
import time
from typing import Iterator

import pytest

# Ensure src is importable when running tests from repo root
ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# Observability imports (configured to be test-friendly)
from meridian.observability.config import (
    ObservabilityConfig,
    configure_observability,
    get_development_config,
)
from meridian.observability.logging import LogLevel
from meridian.observability.metrics import PrometheusConfig, PrometheusMetrics, configure_metrics


def _compute_seed() -> int:
    """
    Compute a stable default seed for this test session.

    Priority:
      1) MERIDIAN_TEST_SEED from env (int)
      2) Derive from current date (YYYYMMDD) to vary daily while being stable within a day
      3) Fallback to a fixed constant to avoid non-determinism
    """
    env_val = os.getenv("MERIDIAN_TEST_SEED")
    if env_val:
        try:
            return int(env_val)
        except ValueError:
            pass

    # Daily-stable seed (UTC date)
    t = time.gmtime()
    try:
        return int(f"{t.tm_year:04d}{t.tm_mon:02d}{t.tm_mday:02d}")
    except Exception:
        return 1337


def _seed_all(seed: int) -> None:
    """Seed Python's RNGs used in tests."""
    random.seed(seed)
    try:
        import numpy as np  # type: ignore[import-not-found]

        np.random.seed(seed)  # pragma: no cover - optional
    except Exception:
        # Numpy not installed or unavailable; ignore
        pass


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--seed",
        action="store",
        default=None,
        help="Deterministic seed for tests (overrides MERIDIAN_TEST_SEED).",
    )
    parser.addoption(
        "--enable-metrics",
        action="store_true",
        default=False,
        help="Enable in-memory metrics during tests.",
    )
    parser.addoption(
        "--log-json",
        action="store_true",
        default=False,
        help="Emit JSON logs to stderr during tests.",
    )


def pytest_configure(config: pytest.Config) -> None:
    # Determine seed precedence: CLI > env > daily > constant
    seed_opt = config.getoption("--seed")
    seed = int(seed_opt) if seed_opt is not None else _compute_seed()
    config._meridian_seed = seed  # type: ignore[attr-defined]
    _seed_all(seed)

    # Configure observability to a test-friendly baseline
    # Default: INFO logs, metrics off, tracing off
    obs: ObservabilityConfig = get_development_config()
    # Start from development, then constrain for tests
    obs.log_level = LogLevel.INFO
    obs.tracing_enabled = False

    # Metrics: enable only if requested, using in-memory Prometheus provider
    if config.getoption("--enable-metrics"):
        obs.metrics_enabled = True
        configure_metrics(PrometheusMetrics(PrometheusConfig(namespace="test")))
    else:
        obs.metrics_enabled = False

    # Logging output formatting
    obs.log_json = bool(config.getoption("--log-json"))

    # Bind to stderr explicitly to ensure CI capture
    obs.log_stream = sys.stderr

    configure_observability(obs)

    # Register custom markers in case pyproject lacks them (idempotent)
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "stress: stress tests")
    config.addinivalue_line("markers", "soak: long-running soak tests")
    config.addinivalue_line("markers", "benchmark: micro/macro benchmarks")


@pytest.fixture(scope="session")
def test_seed(pytestconfig: pytest.Config) -> int:
    """Expose the resolved deterministic seed for this session."""
    return getattr(pytestconfig, "_meridian_seed", _compute_seed())


@pytest.fixture(autouse=True)
def _seed_each_test(test_seed: int) -> Iterator[None]:
    """
    Re-seed at the start of each test for determinism and report seed
    as part of failure context.
    """
    _seed_all(test_seed)
    yield


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """
    Append the active test seed to the report for reproducibility
    whenever a test fails or is xfailed.
    """
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        seed = getattr(item.config, "_meridian_seed", None)
        if seed is not None:
            rep.longrepr = f"{rep.longrepr}\n[determinism] seed={seed}"
