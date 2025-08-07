
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

# # Sentiment Analysis Pipeline (Interactive)

# This notebook demonstrates a real-time sentiment analysis pipeline built with Meridian Runtime. It showcases:
# - Ingesting streaming text data.
# - Tokenizing text.
# - Computing a naive sentiment score.
# - Using control-plane messages to alter node behavior.
# - Observing the pipeline's output.

# ## 1. Setup: Add Project to Python Path

# This cell adds the project's `src` directory to the Python path. This is necessary for the notebook to find and import the `meridian` module.

# +
import sys
import os

# Add the project's 'src' directory to the Python path
# This is necessary for the notebook to find the 'meridian' module
# We assume the notebook is run from the 'notebooks/examples' directory.
src_path = os.path.abspath('../../src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    print(f"Added '{src_path}' to the Python path.")
# -

# ## 2. Domain Helpers

# These helper functions are used for tokenization and naive sentiment calculation.

# +
import random
import threading
import time
from typing import Iterable, List, Tuple, Any

POSITIVE_WORDS = {"good", "great", "awesome", "excellent", "love", "like", "win", "nice"}
NEGATIVE_WORDS = {"bad", "terrible", "awful", "hate", "dislike", "lose", "worse", "nope"}

def tokenize(text: str) -> List[str]:
    return [w.strip(".,!?;:").lower() for w in text.split() if w.strip()]

def naive_sentiment(words: Iterable[str]) -> float:
    p = sum(1 for w in words if w in POSITIVE_WORDS)
    n = sum(1 for w in words if w in NEGATIVE_WORDS)
    if p == n == 0:
        return 0.0
    return (p - n) / max(1, (p + n))
# -

# ## 3. Pipeline Nodes

# Here are the definitions for the nodes that make up our sentiment analysis pipeline:

# *   **IngestNode**: Simulates a streaming data source.
# *   **TokenizeNode**: Breaks text into individual words.
# *   **SentimentNode**: Calculates a sentiment score.
# *   **SinkNode**: Collects and displays results.
# *   **ControlNode**: Sends control messages to other nodes.

# +
from meridian.core import (
    Edge,
    Message,
    MessageType,
    Node,
    Port,
    PortDirection,
    PortSpec,
    Scheduler,
    SchedulerConfig,
    Subgraph,
)
from meridian.core.policies import Block, Latest
from meridian.observability.config import (
    ObservabilityConfig,
    configure_observability,
)
from meridian.observability.logging import get_logger, with_context


class IngestNode(Node):
    """
    Emits DATA messages containing raw text.
    A separate thread feeds samples into an internal buffer to simulate streaming.
    """

    def __init__(self, name: str = "ingest", rate_hz: float = 10.0) -> None:
        super().__init__(
            name=name,
            inputs=[],
            outputs=[Port("text", PortDirection.OUTPUT, spec=PortSpec("text", str))],
        )
        self._buf: list[str] = []
        self._stop = False
        self._rate_hz = rate_hz
        self._producer_t: threading.Thread | None = None
        self._samples = [
            "I love this product, it is awesome!",
            "This is bad, I dislike the changes",
            "What a great day to win and feel excellent",
            "Awful behavior and terrible support",
            "Nice work, really like the new UI",
            "Nope, this is worse than before",
        ]

    def on_start(self) -> None:
        super().on_start()
        self._stop = False
        self._producer_t = threading.Thread(target=self._feeder, daemon=True)
        self._producer_t.start()

    def on_stop(self) -> None:
        self._stop = True
        if self._producer_t and self._producer_t.is_alive():
            self._producer_t.join(timeout=1.0)
        super().on_stop()

    def _feeder(self) -> None:
        rng = random.Random(42)
        while not self._stop:
            s = rng.choice(self._samples)
            self._buf.append(s)
            time.sleep(1.0 / max(1e-6, self._rate_hz))

    def _handle_tick(self) -> None:
        # Emit one item per tick if available
        if self._buf:
            s = self._buf.pop(0)
            self.emit("text", Message(MessageType.DATA, s))


class TokenizeNode(Node):
    """Converts raw text to a list of tokens."""

    def __init__(self, name: str = "tokenize") -> None:
        super().__init__(
            name=name,
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", str))],
            outputs=[Port("out", PortDirection.OUTPUT, spec=PortSpec("out", list))],
        )

    def _handle_message(self, port: str, msg: Message) -> None:
        tokens = tokenize(str(msg.payload))
        self.emit("out", Message(MessageType.DATA, tokens))


class SentimentNode(Node):
    """Computes a naive sentiment score from tokens. Supports CONTROL to change mode."""

    def __init__(self, name: str = "sentiment") -> None:
        super().__init__(
            name=name,
            inputs=[
                Port("in", PortDirection.INPUT, spec=PortSpec("in", list)),
                Port("ctl", PortDirection.INPUT, spec=PortSpec("ctl", str)),
            ],
            outputs=[
                Port("scored", PortDirection.OUTPUT, spec=PortSpec("scored", tuple)),
            ],
        )
        # modes: "avg" or "binary"
        self._mode = "avg"

    def _handle_message(self, port: str, msg: Message) -> None:
        if port == "ctl":
            # CONTROL messages can switch mode
            cmd = str(msg.payload).strip().lower()
            if cmd in {"avg", "binary"}:
                self._mode = cmd
            return

        words = msg.payload
        if not isinstance(words, list):
            return

        score = naive_sentiment(words)
        if self._mode == "binary":
            score = 1.0 if score > 0 else (-1.0 if score < 0 else 0.0)
        self.emit("scored", Message(MessageType.DATA, (words, score)))


class SinkNode(Node):
    """Renders the latest N results; CONTROL can flush or toggle verbosity."""

    def __init__(self, name: str = "sink", keep: int = 10, verbose: bool = True) -> None:
        super().__init__(
            name=name,
            inputs=[
                Port("in", PortDirection.INPUT, spec=PortSpec("in", tuple)),
                Port("ctl", PortDirection.INPUT, spec=PortSpec("ctl", str)),
            ],
            outputs=[],
        )
        self._keep = keep
        self._verbose = verbose
        self._buffer: list[Tuple[List[str], float]] = []

    def _handle_message(self, port: str, msg: Message) -> None:
        logger = get_logger()
        if port == "ctl":
            cmd = str(msg.payload).strip().lower()
            if cmd == "flush":
                with with_context(node=self.name):
                    logger.info("sink.flush", "Flushing buffer")
                self._buffer.clear()
            elif cmd == "quiet":
                self._verbose = False
            elif cmd == "verbose":
                self._verbose = True
            return

        words, score = msg.payload
        self._buffer.append((words, score))
        if len(self._buffer) > self._keep:
            self._buffer.pop(0)

        if self._verbose:
            text = " ".join(words)
            with with_context(node=self.name):
                logger.info(
                    "sink.item",
                    f"[{score:+.2f}] {text}",
                    score=score,
                    len=len(words),
                )

    def _handle_tick(self) -> None:
        # periodic summary
        if not self._buffer:
            return
        avg = sum(s for _, s in self._buffer) / len(self._buffer)
        logger = get_logger()
        with with_context(node=self.name):
            logger.info("sink.summary", f"buffer={len(self._buffer)} avg={avg:+.2f}", avg=avg)


class ControlNode(Node):
    """Emits CONTROL messages periodically to demonstrate preemption."""

    def __init__(self, name: str = "control", period_s: float = 5.0) -> None:
        super().__init__(
            name=name,
            inputs=[],
            outputs=[Port("ctl", PortDirection.OUTPUT, spec=PortSpec("ctl", str))],
        )
        self._period_s = period_s
        self._last = 0.0
        self._ops = ["avg", "binary", "flush", "quiet", "verbose"]
        self._i = 0

    def _handle_tick(self) -> None:
        now = time.monotonic()
        if now - self._last >= self._period_s:
            self._last = now
            cmd = self._ops[self._i % len(self._ops)]
            self._i += 1
            self.emit("ctl", Message(MessageType.CONTROL, cmd))
# -

# ## 4. Interactive Controls and Running the Pipeline

# Use the widgets below to configure and run the sentiment analysis pipeline.

# +
import ipywidgets as widgets
from IPython.display import display

# Configure observability for the notebook
configure_observability(
    ObservabilityConfig(
        log_level="INFO",
        log_json=False,  # Human-readable logs for notebook
        metrics_enabled=False,
        tracing_enabled=False,
    )
)

# Create widgets for pipeline parameters
rate_hz_slider = widgets.FloatSlider(value=8.0, min=1.0, max=20.0, step=1.0, description='Ingest Rate (Hz):')
control_period_slider = widgets.FloatSlider(value=4.0, min=1.0, max=10.0, step=1.0, description='Control Period (s):')
keep_slider = widgets.IntSlider(value=10, min=1, max=50, step=1, description='Sink Buffer Size:')
quiet_checkbox = widgets.Checkbox(value=False, description='Quiet Sink (summary only)')
tick_ms_slider = widgets.IntSlider(value=25, min=10, max=100, step=5, description='Scheduler Tick (ms):')
max_batch_slider = widgets.IntSlider(value=8, min=1, max=32, step=1, description='Max Batch Size:')
timeout_s_slider = widgets.FloatSlider(value=6.0, min=1.0, max=20.0, step=1.0, description='Shutdown Timeout (s):')
cap_text_slider = widgets.IntSlider(value=64, min=16, max=256, step=16, description='Capacity: Text Edge:')
cap_tokens_slider = widgets.IntSlider(value=64, min=16, max=256, step=16, description='Capacity: Tokens Edge:')
cap_scored_slider = widgets.IntSlider(value=128, min=32, max=512, step=32, description='Capacity: Scored Edge:')
cap_control_slider = widgets.IntSlider(value=8, min=1, max=32, step=1, description='Capacity: Control Edges:')

run_button = widgets.Button(description='Run Sentiment Pipeline')
output_area = widgets.Output()

def run_sentiment_pipeline(b):
    with output_area:
        output_area.clear_output()
        print("=== Starting Sentiment Pipeline Demo ===")

        ingest = IngestNode(rate_hz=rate_hz_slider.value)
        tok = TokenizeNode()
        sent = SentimentNode()
        ctrl = ControlNode(period_s=control_period_slider.value)
        sink = SinkNode(keep=keep_slider.value, verbose=not quiet_checkbox.value)

        g = Subgraph.from_nodes("sentiment_pipeline", [ingest, tok, sent, ctrl, sink])

        # Wiring:
        # ingest(text) -> tokenize(in) -> sentiment(in) -> sink(in)
        # control(ctl) -> sentiment(ctl) [CONTROL priority], and to sink(ctl)
        g.connect((ingest.name, "text"), (tok.name, "in"), capacity=cap_text_slider.value)
        g.connect((tok.name, "out"), (sent.name, "in"), capacity=cap_tokens_slider.value)
        g.connect((sent.name, "scored"), (sink.name, "in"), capacity=cap_scored_slider.value)

        # Control lines: keep capacity small; impose Block for CONTROL in scheduler
        g.connect((ctrl.name, "ctl"), (sent.name, "ctl"), capacity=cap_control_slider.value)
        g.connect((ctrl.name, "ctl"), (sink.name, "ctl"), capacity=cap_control_slider.value)

        sched = Scheduler(
            SchedulerConfig(
                tick_interval_ms=tick_ms_slider.value,
                fairness_ratio=(4, 2, 1),
                max_batch_per_node=max_batch_slider.value,
                idle_sleep_ms=1,
                shutdown_timeout_s=timeout_s_slider.value,
            )
        )

        sched.register(g)

        logger = get_logger()
        with with_context(node="driver"):
            logger.info("demo.start", "Starting sentiment pipeline demo")

        # Run in a separate thread to keep notebook interactive
        pipeline_thread = threading.Thread(target=sched.run)
        pipeline_thread.start()
        pipeline_thread.join() # Wait for pipeline to complete

        with with_context(node="driver"):
            logger.info("demo.stop", "Sentiment pipeline stopped")

        print("=== Sentiment Pipeline Demo Finished ===")

run_button.on_click(run_sentiment_pipeline)

display(
    rate_hz_slider,
    control_period_slider,
    keep_slider,
    quiet_checkbox,
    tick_ms_slider,
    max_batch_slider,
    timeout_s_slider,
    cap_text_slider,
    cap_tokens_slider,
    cap_scored_slider,
    cap_control_slider,
    run_button,
    output_area
)
# -
