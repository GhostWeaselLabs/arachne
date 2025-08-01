from __future__ import annotations

from dataclasses import dataclass
from time import monotonic, sleep

from .message import Message, MessageType
from .node import Node
from .subgraph import Subgraph


@dataclass(slots=True)
class SchedulerConfig:
    tick_interval_ms: int = 50
    fairness_ratio: tuple[int, int, int] = (4, 2, 1)  # control, high, normal
    max_batch_per_node: int = 8
    idle_sleep_ms: int = 1
    shutdown_timeout_s: float = 2.0


class Scheduler:
    def __init__(self, config: SchedulerConfig | None = None) -> None:
        self._cfg = config or SchedulerConfig()
        self._graphs: list[Subgraph] = []
        self._running = False
        self._shutdown = False
        self._last_tick: dict[str, float] = {}

    def register(self, unit: Node | Subgraph) -> None:
        if isinstance(unit, Node):
            g = Subgraph.from_nodes(unit.name, [unit])
            self._graphs.append(g)
        else:
            self._graphs.append(unit)

    def run(self) -> None:
        if self._running:
            return
        self._running = True
        try:
            for g in self._graphs:
                for n in g.nodes.values():
                    n.on_start()
                    self._last_tick[n.name] = monotonic()
            loop_start = monotonic()
            while not self._shutdown:
                did_work = False
                for g in self._graphs:
                    for n in g.nodes.values():
                        inputs = g.inputs_of(n.name)
                        for port, edge in inputs.items():
                            msg = edge.try_get()
                            if msg is not None:
                                n.on_message(port, Message(MessageType.DATA, msg))
                                did_work = True
                                break
                        if did_work:
                            continue
                        now = monotonic()
                        last = self._last_tick.get(n.name, 0.0)
                        if (now - last) * 1000.0 >= self._cfg.tick_interval_ms:
                            n.on_tick()
                            self._last_tick[n.name] = now
                            did_work = True
                if not did_work:
                    if (monotonic() - loop_start) > 0:
                        break
                    sleep(self._cfg.idle_sleep_ms / 1000.0)
        finally:
            for g in self._graphs:
                for n in reversed(list(g.nodes.values())):
                    n.on_stop()
            self._running = False

    def shutdown(self) -> None:
        self._shutdown = True

    # Stubs for M3 API; implemented incrementally later
    def set_priority(self, edge_id: str, priority: int) -> None:  # pragma: no cover
        _ = (edge_id, priority)

    def set_capacity(self, edge_id: str, capacity: int) -> None:  # pragma: no cover
        _ = (edge_id, capacity)
