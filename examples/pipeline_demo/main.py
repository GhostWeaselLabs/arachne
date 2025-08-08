from __future__ import annotations

from meridian.core import Scheduler, Subgraph

from .control import KillSwitch
from .sink import SlowSink
from .transformer import Transformer
from .validator import Validator


def build_graph() -> tuple[Subgraph, SlowSink]:
    sink = SlowSink(delay_s=0.01)
    sg = Subgraph.from_nodes("pipeline_demo", [Validator(), Transformer(), sink, KillSwitch()])

    # Wire nodes by port names (policies applied in scheduler/edge layer)
    sg.connect(("validator", "out"), ("transformer", "in"), capacity=64)
    sg.connect(("transformer", "out"), ("sink", "in"), capacity=8)
    sg.connect(("control", "out"), ("sink", "control"), capacity=1)

    return sg, sink


def main() -> None:
    sg, sink = build_graph()

    sched = Scheduler()
    sched.register(sg)
    # In a real app we would feed inputs; here we only validate wiring and run a few ticks
    sched.run()


if __name__ == "__main__":
    main()
