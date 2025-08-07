
# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: Python 3
#     name: python3
# ---

# # Performance Analysis of Meridian Runtime Scheduler

# This notebook provides an interactive way to benchmark the Meridian Runtime scheduler's performance. It allows you to configure various parameters like the number of producers and consumers, edge capacity, and scheduler tick interval, then visualize the impact on scheduler loop latency.

# ## 1. Setup: Add Project to Python Path

# This cell adds the project's `src` directory to the Python path. This is necessary for the notebook to find and import the `meridian` module.

# +
import sys
import os

# Add the project's 'src' directory to the Python path
# This is necessary for the notebook to find the 'meridian' module
# We assume the notebook is run from the 'notebooks/research' directory.
src_path = os.path.abspath('../../src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    print(f"Added '{src_path}' to the Python path.")
# -

# ## 2. Imports and Configuration

# We'll import necessary modules and define a configuration class to hold our benchmark parameters.

# +
import json
import math
import random
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import ipywidgets as widgets
from IPython.display import display

from meridian.core import Node, Scheduler, SchedulerConfig, Subgraph, Message, MessageType
from meridian.core.ports import Port, PortDirection, PortSpec
from meridian.observability.metrics import (
    PrometheusMetrics,
    configure_metrics,
    get_metrics,
)

@dataclass
class BenchSchedConfig:
    seconds: float = 5.0
    producers: int = 2
    consumers: int = 2
    capacity: int = 1024
    tick_interval_ms: int = 1
    idle_sleep_ms: int = 0
    shutdown_timeout_s: float = 2.0
    fairness_ratio: Tuple[int, int, int] = (4, 2, 1)
    max_batch_per_node: int = 128
    seed: int = 8675309
# -

# ## 3. Helper Functions

# These functions are adapted from `bench_scheduler.py` to work within the notebook environment.

# +
def _percentile_from_histogram_cumulative(
    buckets: Dict[float, int], total: int, pct: float
) -> float:
    """
    Estimate percentile from a cumulative histogram mapping (upper_bound -> cumulative count).
    Includes +Inf as float('inf').
    """
    if total <= 0 or not buckets:
        return float("nan")
    if pct <= 0:
        # First non-zero bucket upper bound
        for ub in sorted(buckets.keys(), key=lambda x: float(x)):
            if buckets[ub] > 0:
                return float(ub)
        return float("nan")
    if pct >= 100:
        return float("inf")
    target = math.ceil((pct / 100.0) * total)
    for ub in sorted(buckets.keys(), key=lambda x: float(x)):
        if buckets[ub] >= target:
            return float(ub)
    # Fallback if not found
    return float("inf")


def _maybe_enable_prom_metrics() -> None:
    """
    Ensure PrometheusMetrics is enabled so the scheduler loop histogram is populated.
    """
    metrics = get_metrics()
    if not isinstance(metrics, PrometheusMetrics):
        configure_metrics(PrometheusMetrics())
# -

# ## 4. Workload Nodes

# These are the `Producer` and `Consumer` nodes used to generate and process messages, simulating a workload for the scheduler.

# +
class Producer(Node):
    """
    Producer emits increasing integers on each tick to generate message load.
    Emits Message(DATA, payload) via a declared output port, per runtime contract.
    """

    def __init__(self, name: str, out_port: Port, burst_max: int = 8) -> None:
        super().__init__(name)
        # Ensure Node has a matching output port name so Node.emit() can resolve it
        self.outputs = [out_port]
        self._out = out_port
        self._burst_max = max(1, burst_max)
        self._seq = 0

    def on_start(self) -> None:
        self._seq = 0

    def _handle_tick(self) -> None:
        # Emit a burst of messages to keep the scheduler busy
        burst = random.randint(1, self._burst_max)
        for _ in range(burst):
            msg = Message(MessageType.DATA, self._seq)
            self.emit(self._out.name, msg)
            self._seq += 1


class Consumer(Node):
    """
    Consumer counts messages; work is intentionally light to focus on scheduler loop behavior.
    Declares input port so scheduler can route messages by port name.
    """

    def __init__(self, name: str, in_port: Port, batch_max: int = 32) -> None:
        super().__init__(name)
        # Ensure Node declares the input port for routing
        self.inputs = [in_port]
        self._in = in_port
        self._batch_max = max(1, batch_max)
        self._processed = 0

    def on_start(self) -> None:
        self._processed = 0

    def on_message(self, port: Port, msg: Any) -> None:
        self._processed += 1

    def on_tick(self) -> None:
        # Tick present to participate in fairness, but primary work is message-driven
        pass

    @property
    def processed(self) -> int:
        return self._processed
# -

# ## 5. Topology Assembly

# This function builds the graph of producers and consumers based on the configuration.

# +
def _mk_ports(n: int = 4) -> Tuple[List[Port], List[Port]]:
    outs: List[Port] = []
    ins: List[Port] = []
    for i in range(n):
        outs.append(Port(f"o{i}", PortDirection.OUTPUT, PortSpec(f"o{i}", int)))
        ins.append(Port(f"i{i}", PortDirection.INPUT, PortSpec(f"i{i}", int)))
    return outs, ins


def _mk_subgraph(cfg: BenchSchedConfig) -> Tuple[Subgraph, List[Consumer]]:
    outs, ins = _mk_ports(max(cfg.producers, cfg.consumers))
    producers: List[Producer] = []
    consumers: List[Consumer] = []

    for p in range(cfg.producers):
        producers.append(Producer(f"prod{p}", outs[p % len(outs)], burst_max=8))
    for c in range(cfg.consumers):
        consumers.append(Consumer(f"cons{c}", ins[c % len(ins)], batch_max=32))

    # Build subgraph with nodes and explicitly wire producer outputs to consumer inputs
    g = Subgraph.from_nodes("bench_sched_topology", [*producers, *consumers])
    for p in producers:
        for c in consumers:
            g.connect((p.name, p._out.name), (c.name, c._in.name), capacity=cfg.capacity)
    return g, consumers
# -

# ## 6. Metrics Extraction

# This function extracts the scheduler loop latency histogram from the metrics system.

# +
def _get_scheduler_loop_hist() -> Tuple[float, int, Dict[float, int]]:
    """
    Returns (sum, count, buckets) for scheduler_loop_latency_seconds.
    """
    metrics = get_metrics()
    if not isinstance(metrics, PrometheusMetrics):
        return (0.0, 0, {})
    hists = metrics.get_all_histograms()
    for key, hist in hists.items():
        if key.endswith("scheduler_loop_latency_seconds"):
            return (hist.sum, hist.count, hist.buckets)
    return (0.0, 0, {})
# -

# ## 7. Benchmark Runner

# This function runs the scheduler for a specified duration and collects performance metrics.

# +
def _run_scheduler(cfg: BenchSchedConfig) -> Dict[str, Any]:
    # Deterministic randomness for repeatability
    random.seed(cfg.seed)

    # Ensure histogram is available
    _maybe_enable_prom_metrics()

    # Build topology and scheduler
    g, consumers = _mk_subgraph(cfg)
    s_cfg = SchedulerConfig(
        fairness_ratio=cfg.fairness_ratio,
        max_batch_per_node=cfg.max_batch_per_node,
        idle_sleep_ms=cfg.idle_sleep_ms,
        tick_interval_ms=cfg.tick_interval_ms,
        shutdown_timeout_s=cfg.shutdown_timeout_s,
    )
    sched = Scheduler(s_cfg)
    sched.register(g)

    # Run scheduler in background
    t = threading.Thread(target=sched.run, name="bench-scheduler", daemon=True)
    t.start()

    # Let it run for configured duration
    time.sleep(cfg.seconds)

    # Request shutdown and wait
    sched.shutdown()
    t.join(timeout=cfg.shutdown_timeout_s + 5.0)

    # Gather metrics
    h_sum, h_count, h_buckets = _get_scheduler_loop_hist()
    p50 = _percentile_from_histogram_cumulative(h_buckets, h_count, 50.0)
    p95 = _percentile_from_histogram_cumulative(h_buckets, h_count, 95.0)
    p99 = _percentile_from_histogram_cumulative(h_buckets, h_count, 99.0)

    total_processed = sum(c.processed for c in consumers)

    return {
        "name": "scheduler_loop",
        "version": 1,
        "env": {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform,
        },
        "config": {
            "seconds": cfg.seconds,
            "producers": cfg.producers,
            "consumers": cfg.consumers,
            "capacity": cfg.capacity,
            "tick_interval_ms": cfg.tick_interval_ms,
            "idle_sleep_ms": cfg.idle_sleep_ms,
            "shutdown_timeout_s": cfg.shutdown_timeout_s,
            "fairness_ratio": list(cfg.fairness_ratio),
            "max_batch_per_node": cfg.max_batch_per_node,
            "seed": cfg.seed,
        },
        "results": {
            "scheduler_loop_latency_seconds": {
                "sum": h_sum,
                "count": h_count,
                "p50_estimate_seconds": p50,
                "p95_estimate_seconds": p95,
                "p99_estimate_seconds": p99,
                "buckets": {str(k): int(v) for k, v in h_buckets.items()},
            },
            "total_processed": int(total_processed),
            "iterations_per_second_estimate": (
                (h_count / cfg.seconds) if (cfg.seconds > 0 and h_count > 0) else 0.0
            ),
        },
        "summary": {
            "loop_p95_ms": (p95 * 1000.0) if not math.isnan(p95) and not math.isinf(p95) else None,
            "loop_p99_ms": (p99 * 1000.0) if not math.isnan(p99) and not math.isinf(p99) else None,
            "processed": int(total_processed),
        },
    }
# -

# ## 8. Interactive Benchmark Execution

# Use the widgets below to configure and run the scheduler benchmark. The results will be displayed below.

# +
# Create widgets for benchmark parameters
seconds_slider = widgets.FloatSlider(value=5.0, min=1.0, max=30.0, step=1.0, description='Duration (s):')
producers_slider = widgets.IntSlider(value=2, min=1, max=10, step=1, description='Producers:')
consumers_slider = widgets.IntSlider(value=2, min=1, max=10, step=1, description='Consumers:')
capacity_slider = widgets.IntSlider(value=1024, min=16, max=4096, step=16, description='Edge Capacity:')
tick_ms_slider = widgets.IntSlider(value=1, min=1, max=100, step=1, description='Tick Interval (ms):')
idle_sleep_ms_slider = widgets.IntSlider(value=0, min=0, max=10, step=1, description='Idle Sleep (ms):')
shutdown_timeout_s_slider = widgets.FloatSlider(value=2.0, min=1.0, max=10.0, step=1.0, description='Shutdown Timeout (s):')
fairness_ratio_text = widgets.Text(value='4,2,1', description='Fairness Ratio (ctl,high,norm):')
max_batch_per_node_slider = widgets.IntSlider(value=128, min=1, max=512, step=1, description='Max Batch Per Node:')
seed_text = widgets.IntText(value=8675309, description='Random Seed:')

run_benchmark_button = widgets.Button(description='Run Benchmark')
benchmark_output = widgets.Output()

def on_run_benchmark_button_clicked(b):
    with benchmark_output:
        benchmark_output.clear_output()
        print("Running benchmark...")

        cfg = BenchSchedConfig(
            seconds=seconds_slider.value,
            producers=producers_slider.value,
            consumers=consumers_slider.value,
            capacity=capacity_slider.value,
            tick_interval_ms=tick_ms_slider.value,
            idle_sleep_ms=idle_sleep_ms_slider.value,
            shutdown_timeout_s=shutdown_timeout_s_slider.value,
            fairness_ratio=tuple(int(x) for x in fairness_ratio_text.value.split(',')),
            max_batch_per_node=max_batch_per_node_slider.value,
            seed=seed_text.value,
        )

        results = _run_scheduler(cfg)
        print(json.dumps(results, indent=2))

run_benchmark_button.on_click(on_run_benchmark_button_clicked)

display(
    seconds_slider,
    producers_slider,
    consumers_slider,
    capacity_slider,
    tick_ms_slider,
    idle_sleep_ms_slider,
    shutdown_timeout_s_slider,
    fairness_ratio_text,
    max_batch_per_node_slider,
    seed_text,
    run_benchmark_button,
    benchmark_output
)
# -
