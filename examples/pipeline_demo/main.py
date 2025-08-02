from __future__ import annotations

from arachne.core.policies import block, coalesce, latest
from arachne.core.ports import PortSpec
from arachne.core.scheduler import Scheduler
from arachne.core.subgraph import Subgraph

from .control import KillSwitch
from .sink import SlowSink
from .transformer import Transformer
from .validator import Validator


def build_graph() -> tuple[Subgraph, SlowSink]:
    sg = Subgraph(name="pipeline_demo")

    validator = Validator()
    transformer = Transformer()
    sink = SlowSink(delay_s=0.01)
    control = KillSwitch()

    sg.add_node(validator, name="validator")
    sg.add_node(transformer, name="transformer")
    sg.add_node(sink, name="sink")
    sg.add_node(control, name="control")

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
