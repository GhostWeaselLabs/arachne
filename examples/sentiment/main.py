from __future__ import annotations

import argparse
import random
import threading
import time
from typing import Iterable, List, Tuple

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


# ---------------------------
# Domain helpers
# ---------------------------


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


# ---------------------------
# Nodes
# ---------------------------


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

    def _feeder(self) -> None:
        rng = random.Random(42)
        while not self._stop:
            s = rng.choice(self._samples)
            self._buf.append(s)
            time.sleep(1.0 / max(1e-6, self._rate_hz))

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


# ---------------------------
# Build graph and run
# ---------------------------


def build_graph(args: argparse.Namespace) -> Subgraph:
    ingest = IngestNode(rate_hz=args.rate_hz)
    tok = TokenizeNode()
    sent = SentimentNode()
    ctrl = ControlNode(period_s=args.control_period)
    sink = SinkNode(keep=args.keep, verbose=not args.quiet)

    g = Subgraph.from_nodes("sentiment_pipeline", [ingest, tok, sent, ctrl, sink])

    # Wiring:
    # ingest(text) -> tokenize(in) -> sentiment(in) -> sink(in)
    # control(ctl) -> sentiment(ctl) [CONTROL priority], and to sink(ctl)
    g.connect((ingest.name, "text"), (tok.name, "in"), capacity=args.cap_text)
    g.connect((tok.name, "out"), (sent.name, "in"), capacity=args.cap_tokens)
    g.connect((sent.name, "scored"), (sink.name, "in"), capacity=args.cap_scored)

    # Control lines: keep capacity small; impose Block for CONTROL in scheduler
    g.connect((ctrl.name, "ctl"), (sent.name, "ctl"), capacity=args.cap_control)
    g.connect((ctrl.name, "ctl"), (sink.name, "ctl"), capacity=args.cap_control)

    return g


def configure_obs(args: argparse.Namespace) -> None:
    cfg = ObservabilityConfig(
        log_level="INFO" if not args.debug else "DEBUG",
        log_json=not args.human,
        metrics_enabled=False,
        tracing_enabled=False,
    )
    configure_observability(cfg)


def run(args: argparse.Namespace) -> None:
    configure_obs(args)

    sched = Scheduler(
        SchedulerConfig(
            tick_interval_ms=args.tick_ms,
            fairness_ratio=(4, 2, 1),
            max_batch_per_node=args.max_batch,
            idle_sleep_ms=1,
            shutdown_timeout_s=args.timeout_s,
        )
    )

    sched.register(build_graph(args))

    # Demonstrate policy behavior by filling an edge using Latest (freshness)
    # and Block on the data pipeline (controlled by scheduler for CONTROL msgs).
    # Note: Edge policies on emit are handled by scheduler; Latest used by default on puts.
    logger = get_logger()
    with with_context(node="driver"):
        logger.info("demo.start", "Starting sentiment pipeline demo")

    sched.run()

    with with_context(node="driver"):
        logger.info("demo.stop", "Sentiment pipeline stopped")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Meridian sentiment demo")
    p.add_argument("--rate-hz", type=float, default=8.0, help="Ingest rate (items/sec)")
    p.add_argument("--control-period", type=float, default=4.0, help="CONTROL message period (sec)")
    p.add_argument("--keep", type=int, default=10, help="Sink buffer size")
    p.add_argument("--quiet", action="store_true", help="Sink prints summary only")
    p.add_argument("--tick-ms", type=int, default=25, help="Scheduler tick interval (ms)")
    p.add_argument("--max-batch", type=int, default=8, help="Max messages per node per slice")
    p.add_argument("--timeout-s", type=float, default=6.0, help="Shutdown timeout when idle (s)")
    p.add_argument("--cap-text", type=int, default=64, help="Capacity: text edge")
    p.add_argument("--cap-tokens", type=int, default=64, help="Capacity: tokens edge")
    p.add_argument("--cap-scored", type=int, default=128, help="Capacity: scored edge")
    p.add_argument("--cap-control", type=int, default=8, help="Capacity: control edges")
    p.add_argument("--human", action="store_true", help="Human-readable logs")
    p.add_argument("--debug", action="store_true", help="Enable debug logs")
    return p.parse_args()


if __name__ == "__main__":
    run(parse_args())
