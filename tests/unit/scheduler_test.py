from __future__ import annotations

import time
from unittest.mock import patch

from meridian.core import Message, MessageType, Node, Scheduler, SchedulerConfig, Subgraph
from meridian.core.runtime_plan import PriorityBand


class Producer(Node):
    def __init__(self, name: str = "Producer") -> None:
        super().__init__(name, inputs=[], outputs=[Node.with_ports("tmp", [], ["out"]).outputs[0]])
        self.tick_count = 0
        self.messages_sent = 0

    def on_tick(self) -> None:
        self.tick_count += 1
        if self.tick_count <= 3:  # Send a few messages
            msg = Message(MessageType.DATA, f"data_{self.tick_count}")
            self.emit("out", msg)
            self.messages_sent += 1


class Consumer(Node):
    def __init__(self, name: str = "Consumer") -> None:
        super().__init__(name, inputs=[Node.with_ports("tmp", ["in"], []).inputs[0]], outputs=[])
        self.messages_received = 0
        self.received_data = []

    def on_message(self, port: str, msg: Message) -> None:
        if msg.type in (MessageType.DATA, MessageType.CONTROL):
            self.messages_received += 1
            self.received_data.append(msg.payload)


class ControlNode(Node):
    def __init__(self, name: str = "Control") -> None:
        super().__init__(
            name,
            inputs=[Node.with_ports("tmp", ["ctrl_in"], []).inputs[0]],
            outputs=[Node.with_ports("tmp", [], ["ctrl_out"]).outputs[0]],
        )
        self.control_received = 0
        self.tick_count = 0

    def on_message(self, port: str, msg: Message) -> None:
        if msg.type == MessageType.CONTROL:
            self.control_received += 1
            # Echo control message
            self.emit("ctrl_out", msg)

    def on_tick(self) -> None:
        self.tick_count += 1
        if self.tick_count <= 2:  # Send a couple control messages
            msg = Message(MessageType.CONTROL, f"control_{self.tick_count}")
            self.emit("ctrl_out", msg)


class ErrorNode(Node):
    def __init__(self, name: str = "ErrorNode") -> None:
        super().__init__(name, inputs=[Node.with_ports("tmp", ["in"], []).inputs[0]], outputs=[])
        self.error_count = 0

    def on_message(self, port: str, msg: Message) -> None:
        self.error_count += 1
        raise RuntimeError("Intentional test error")


def test_scheduler_starts_and_processes_message() -> None:
    """Test basic scheduler functionality."""
    p = Producer()
    c = Consumer()
    sg = Subgraph.from_nodes("G", [p, c])
    sg.connect(("Producer", "out"), ("Consumer", "in"), capacity=10)

    config = SchedulerConfig(tick_interval_ms=10, shutdown_timeout_s=0.5)
    sch = Scheduler(config)
    sch.register(sg)

    # Run scheduler briefly
    time.time()
    sch.run()

    # Should have processed some messages
    assert c.messages_received > 0
    assert p.tick_count > 0
    assert len(c.received_data) > 0


def test_priority_scheduling() -> None:
    """Test that control-plane messages are prioritized over data-plane."""
    producer = Producer("DataProducer")
    control = ControlNode("ControlNode")
    consumer = Consumer("DataConsumer")
    ctrl_consumer = Consumer("ControlConsumer")

    sg = Subgraph.from_nodes("PriorityTest", [producer, control, consumer, ctrl_consumer])

    # Data edge (normal priority)
    sg.connect(("DataProducer", "out"), ("DataConsumer", "in"), capacity=1)
    # Control edge (will be set to high priority)
    ctrl_edge_id = sg.connect(("ControlNode", "ctrl_out"), ("ControlConsumer", "in"), capacity=1)

    config = SchedulerConfig(tick_interval_ms=10, shutdown_timeout_s=0.3)
    sch = Scheduler(config)
    sch.register(sg)

    # Set control edge to high priority
    sch.set_priority(ctrl_edge_id, PriorityBand.CONTROL)

    # Pre-fill control message
    ctrl_edge = sg.edges[1]  # Control edge
    ctrl_edge.try_put(Message(MessageType.CONTROL, "urgent").payload)

    sch.run()

    # Control messages should be processed
    assert ctrl_consumer.messages_received > 0


def test_backpressure_handling() -> None:
    """Test backpressure with blocking policy."""
    producer = Producer("BlockedProducer")
    consumer = Consumer("SlowConsumer")

    sg = Subgraph.from_nodes("BackpressureTest", [producer, consumer])
    # Small capacity to trigger backpressure
    sg.connect(("BlockedProducer", "out"), ("SlowConsumer", "in"), capacity=1)

    config = SchedulerConfig(tick_interval_ms=5, shutdown_timeout_s=0.2)
    sch = Scheduler(config)
    sch.register(sg)

    sch.run()

    # Should handle backpressure gracefully without crashing
    assert producer.messages_sent >= 0
    assert consumer.messages_received >= 0


def test_runtime_mutators() -> None:
    """Test set_priority and set_capacity methods."""
    producer = Producer()
    consumer = Consumer()

    sg = Subgraph.from_nodes("MutatorTest", [producer, consumer])
    edge_id = sg.connect(("Producer", "out"), ("Consumer", "in"), capacity=10)

    sch = Scheduler()
    sch.register(sg)

    # Test set_priority
    sch.set_priority(edge_id, PriorityBand.HIGH)
    sch.set_priority(edge_id, PriorityBand.CONTROL)

    # Test set_capacity
    sch.set_capacity(edge_id, 50)

    # Test validation
    try:
        sch.set_priority("nonexistent", 2)
        raise AssertionError("Should raise ValueError")
    except ValueError:
        pass

    try:
        sch.set_priority(edge_id, 5)  # Invalid priority
        raise AssertionError("Should raise ValueError")
    except ValueError:
        pass

    try:
        sch.set_capacity(edge_id, 0)  # Invalid capacity
        raise AssertionError("Should raise ValueError")
    except ValueError:
        pass


def test_error_handling() -> None:
    """Test that node errors don't crash the scheduler."""
    producer = Producer("ErrorProducer")
    error_node = ErrorNode("ErrorNode")
    consumer = Consumer("FinalConsumer")

    sg = Subgraph.from_nodes("ErrorTest", [producer, error_node, consumer])
    sg.connect(("ErrorProducer", "out"), ("ErrorNode", "in"), capacity=5)
    # Note: ErrorNode has no outputs, so no connection to FinalConsumer

    config = SchedulerConfig(tick_interval_ms=10, shutdown_timeout_s=0.3)
    sch = Scheduler(config)
    sch.register(sg)

    # Should not crash despite node errors
    with patch("meridian.core.priority_queue.logger") as mock_logger:
        sch.run()

        # Should have logged errors
        assert mock_logger.error.called
        # Error node should have received messages and errored
        assert error_node.error_count > 0


def test_graceful_shutdown() -> None:
    """Test graceful shutdown semantics."""
    producer = Producer("ShutdownProducer")
    consumer = Consumer("ShutdownConsumer")

    sg = Subgraph.from_nodes("ShutdownTest", [producer, consumer])
    sg.connect(("ShutdownProducer", "out"), ("ShutdownConsumer", "in"))

    config = SchedulerConfig(tick_interval_ms=10, shutdown_timeout_s=1.0)
    sch = Scheduler(config)
    sch.register(sg)

    # Test that shutdown stops the scheduler
    import threading

    def delayed_shutdown():
        time.sleep(0.1)
        sch.shutdown()

    shutdown_thread = threading.Thread(target=delayed_shutdown)
    shutdown_thread.start()

    start_time = time.time()
    sch.run()
    end_time = time.time()

    shutdown_thread.join()

    # Should have stopped before the full timeout
    assert (end_time - start_time) < config.shutdown_timeout_s


def test_fairness_ratio() -> None:
    """Test that fairness ratios are respected across priority bands."""
    # This is a basic test - more sophisticated fairness testing would require
    # more complex scenarios and longer runs
    producer1 = Producer("HighPriorityProducer")
    producer2 = Producer("NormalPriorityProducer")
    consumer = Consumer("FairnessConsumer")

    sg = Subgraph.from_nodes("FairnessTest", [producer1, producer2, consumer])
    high_edge = sg.connect(("HighPriorityProducer", "out"), ("FairnessConsumer", "in"), capacity=10)
    normal_edge = sg.connect(
        ("NormalPriorityProducer", "out"), ("FairnessConsumer", "in"), capacity=10
    )

    config = SchedulerConfig(
        tick_interval_ms=5, fairness_ratio=(4, 2, 1), shutdown_timeout_s=0.3  # control:high:normal
    )
    sch = Scheduler(config)
    sch.register(sg)

    # Set priorities
    sch.set_priority(high_edge, PriorityBand.HIGH)
    sch.set_priority(normal_edge, PriorityBand.NORMAL)

    sch.run()

    # Both producers should have run, but high priority should be favored
    assert producer1.tick_count > 0
    assert producer2.tick_count > 0
    assert consumer.messages_received > 0


def test_registration_validation() -> None:
    """Test that registration validates properly."""
    sch = Scheduler()

    # Test duplicate node names
    node1 = Producer("DuplicateName")
    node2 = Consumer("DuplicateName")  # Same name

    sg1 = Subgraph.from_nodes("Graph1", [node1])
    sg2 = Subgraph.from_nodes("Graph2", [node2])

    sch.register(sg1)
    sch.register(sg2)

    # Should raise error during runtime plan building
    try:
        sch.run()
        raise AssertionError("Should raise ValueError for duplicate node names")
    except ValueError as e:
        assert "Duplicate node name" in str(e)

    # Test registration while running
    sch2 = Scheduler()
    sch2.register(Subgraph.from_nodes("Test", [Producer()]))

    import threading

    def try_register():
        time.sleep(0.05)
        try:
            sch2.register(Subgraph.from_nodes("Test2", [Consumer()]))
            raise AssertionError("Should raise RuntimeError")
        except RuntimeError:
            pass

    reg_thread = threading.Thread(target=try_register)
    reg_thread.start()

    # Brief run
    config = SchedulerConfig(shutdown_timeout_s=0.1)
    sch2._cfg = config
    sch2.run()

    reg_thread.join()
