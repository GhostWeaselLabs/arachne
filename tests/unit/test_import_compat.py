from __future__ import annotations

# Import compatibility smoke tests for modularization

def test_core_imports() -> None:
    from meridian.core import Node, Edge, Subgraph, Scheduler, SchedulerConfig  # noqa: F401


def test_priority_queue_imports() -> None:
    from meridian.core.priority_queue import (  # noqa: F401
        PriorityQueueConfig,
        PrioritySchedulingQueue,
        NodeProcessor,
    )


def test_runtime_plan_imports() -> None:
    from meridian.core.runtime_plan import PriorityBand, RuntimePlan  # noqa: F401


def test_policies_imports() -> None:
    from meridian.core.policies import (  # noqa: F401
        BackpressureStrategy,
        RetryPolicy,
        RoutingPolicy,
        PutResult,
        Block,
        Drop,
        Latest,
        Coalesce,
    )


def test_observability_tracing_imports() -> None:
    from meridian.observability.tracing import (  # noqa: F401
        TracingConfig,
        InMemoryTracer,
        get_tracer,
        start_span,
    )


def test_observability_metrics_imports() -> None:
    from meridian.observability.metrics import (  # noqa: F401
        PrometheusMetrics,
        PrometheusConfig,
        get_metrics,
        time_block,
    )


def test_observability_logging_imports() -> None:
    from meridian.observability.logging import (  # noqa: F401
        Logger,
        LogConfig,
        LogLevel,
        get_logger,
        with_context,
    )
