from __future__ import annotations

from arachne.core.edge import Edge
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

    v_out = PortSpec(name="out", schema=dict)
    t_in = PortSpec(name="in", schema=dict)
    t_out = PortSpec(name="out", schema=dict)
    s_in = PortSpec(name="in", schema=dict)
    c_out = PortSpec(name="out", schema=str)

    sg.connect(Edge(("validator", v_out), ("transformer", t_in), capacity=64, policy=block()))
    sg.connect(Edge(("transformer", t_out), ("sink", s_in), capacity=8, policy=latest()))
    sg.connect(
        Edge(("control", c_out), ("sink", s_in), capacity=1, policy=coalesce(lambda a, b: a))
    )

    sg.validate().raise_if_error()
    return sg, sink


def main() -> None:
    sg, sink = build_graph()

    sched = Scheduler(subgraph=sg)
    # In a real app we would feed inputs; here we only validate wiring and run a few ticks
    sched.run(ticks=5)


if __name__ == "__main__":
    main()
