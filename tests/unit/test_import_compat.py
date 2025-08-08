from __future__ import annotations

# Import compatibility smoke tests for modularization

def test_core_imports() -> None:
    from meridian.core import Edge, Node, Scheduler, SchedulerConfig, Subgraph  # noqa: F401


def test_priority_queue_imports() -> None:
    from meridian.core.priority_queue import (  # noqa: F401
        NodeProcessor,
        PriorityQueueConfig,
        PrioritySchedulingQueue,
    )


def test_runtime_plan_imports() -> None:
    from meridian.core.runtime_plan import PriorityBand, RuntimePlan  # noqa: F401


def test_policies_imports() -> None:
    from meridian.core.policies import (  # noqa: F401
        BackpressureStrategy,
        Block,
        Coalesce,
        Drop,
        Latest,
        PutResult,
        RetryPolicy,
        RoutingPolicy,
    )


def test_observability_tracing_imports() -> None:
    from meridian.observability.tracing import (  # noqa: F401
        InMemoryTracer,
        TracingConfig,
        get_tracer,
        start_span,
    )


def test_observability_metrics_imports() -> None:
    from meridian.observability.metrics import (  # noqa: F401
        PrometheusConfig,
        PrometheusMetrics,
        get_metrics,
        time_block,
    )


def test_observability_logging_imports() -> None:
    from meridian.observability.logging import (  # noqa: F401
        LogConfig,
        Logger,
        LogLevel,
        get_logger,
        with_context,
    )
