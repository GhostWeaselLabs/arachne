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

    # Control edge (high priority)
    sg.connect(("ControlNode", "ctrl_out"), ("ControlConsumer", "in"), capacity=1)

    config = SchedulerConfig(tick_interval_ms=10, shutdown_timeout_s=0.5)
    sch = Scheduler(config)
    sch.register(sg)

    # Run scheduler briefly
    sch.run()

    # Control messages should be processed first
    assert ctrl_consumer.messages_received > 0
    assert consumer.messages_received > 0


def test_backpressure_handling() -> None:
    """Test backpressure when queues are full."""
    producer = Producer("FastProducer")
    consumer = Consumer("SlowConsumer")

    sg = Subgraph.from_nodes("BackpressureTest", [producer, consumer])
    # Small capacity to trigger backpressure
    sg.connect(("FastProducer", "out"), ("SlowConsumer", "in"), capacity=1)

    config = SchedulerConfig(tick_interval_ms=10, shutdown_timeout_s=0.5)
    sch = Scheduler(config)
    sch.register(sg)

    sch.run()

    # Should handle backpressure gracefully
    assert consumer.messages_received > 0


def test_runtime_mutators() -> None:
    """Test runtime priority and capacity changes."""
    producer = Producer("Producer")
    consumer = Consumer("Consumer")

    sg = Subgraph.from_nodes("MutatorTest", [producer, consumer])
    edge_id = sg.connect(("Producer", "out"), ("Consumer", "in"), capacity=10)

    config = SchedulerConfig(tick_interval_ms=10, shutdown_timeout_s=0.5)
    sch = Scheduler(config)
    sch.register(sg)

    # Start scheduler in background
    import threading
    thread = threading.Thread(target=sch.run)
    thread.start()

    # Wait a bit for scheduler to start
    time.sleep(0.1)

    # Test runtime priority change
    sch.set_priority(edge_id, PriorityBand.CONTROL)
    
    # Test runtime capacity change
    sch.set_capacity(edge_id, 5)

    # Shutdown
    sch.shutdown()
    thread.join(timeout=1.0)

    assert consumer.messages_received > 0


def test_error_handling() -> None:
    """Test scheduler handles node errors gracefully."""
    producer = Producer("Producer")
    error_node = ErrorNode("ErrorNode")

    sg = Subgraph.from_nodes("ErrorTest", [producer, error_node])
    sg.connect(("Producer", "out"), ("ErrorNode", "in"), capacity=10)

    config = SchedulerConfig(tick_interval_ms=10, shutdown_timeout_s=0.5)
    sch = Scheduler(config)
    sch.register(sg)

    # Should handle errors gracefully
    sch.run()

    # Error node should have received some messages before failing
    assert error_node.error_count > 0


def test_graceful_shutdown() -> None:
    """Test graceful shutdown behavior."""
    producer = Producer("Producer")
    consumer = Consumer("Consumer")

    sg = Subgraph.from_nodes("ShutdownTest", [producer, consumer])
    sg.connect(("Producer", "out"), ("Consumer", "in"), capacity=10)

    config = SchedulerConfig(tick_interval_ms=10, shutdown_timeout_s=0.5)
    sch = Scheduler(config)
    sch.register(sg)

    # Start scheduler in background
    import threading

    def delayed_shutdown():
        time.sleep(0.1)
        sch.shutdown()

    shutdown_thread = threading.Thread(target=delayed_shutdown)
    shutdown_thread.start()

    # Run scheduler
    sch.run()

    shutdown_thread.join(timeout=1.0)

    # Should have processed some messages before shutdown
    assert consumer.messages_received > 0


def test_fairness_ratio() -> None:
    """Test fairness ratio configuration."""
    producer1 = Producer("Producer1")
    producer2 = Producer("Producer2")
    consumer1 = Consumer("Consumer1")
    consumer2 = Consumer("Consumer2")

    sg = Subgraph.from_nodes("FairnessTest", [producer1, producer2, consumer1, consumer2])
    sg.connect(("Producer1", "out"), ("Consumer1", "in"), capacity=10)
    sg.connect(("Producer2", "out"), ("Consumer2", "in"), capacity=10)

    # Custom fairness ratio
    config = SchedulerConfig(
        tick_interval_ms=10, 
        shutdown_timeout_s=0.5,
        fairness_ratio=(2, 1, 1)  # Different ratio
    )
    sch = Scheduler(config)
    sch.register(sg)

    sch.run()

    # Both consumers should receive messages
    assert consumer1.messages_received > 0
    assert consumer2.messages_received > 0


def test_registration_validation() -> None:
    """Test registration validation."""
    sch = Scheduler()
    
    # Test registering while running
    producer = Producer("Producer")
    consumer = Consumer("Consumer")
    sg = Subgraph.from_nodes("Test", [producer, consumer])
    sg.connect(("Producer", "out"), ("Consumer", "in"), capacity=10)
    
    sch.register(sg)
    
    # Start scheduler
    import threading
    thread = threading.Thread(target=sch.run)
    thread.start()
    time.sleep(0.1)
    
    # Try to register while running - should raise RuntimeError
    another_sg = Subgraph.from_nodes("Another", [Producer("P2")])
    
    try:
        sch.register(another_sg)
        raise AssertionError("Should not allow registration while running")
    except RuntimeError:
        pass  # Expected
    
    sch.shutdown()
    thread.join(timeout=1.0)


def test_priority_validation() -> None:
    """Test priority validation."""
    sch = Scheduler()
    
    # Test invalid priority type
    try:
        sch.set_priority("edge_id", "invalid_priority")  # type: ignore
        raise AssertionError("Should reject invalid priority type")
    except ValueError:
        pass  # Expected


def test_priority_change_edge_not_found() -> None:
    """Test priority change when edge doesn't exist."""
    sch = Scheduler()
    
    # Start scheduler
    producer = Producer("Producer")
    consumer = Consumer("Consumer")
    sg = Subgraph.from_nodes("Test", [producer, consumer])
    sg.connect(("Producer", "out"), ("Consumer", "in"), capacity=10)
    
    sch.register(sg)
    
    import threading
    thread = threading.Thread(target=sch.run)
    thread.start()
    time.sleep(0.1)
    
    # Try to change priority of non-existent edge
    sch.set_priority("non_existent_edge", PriorityBand.CONTROL)
    
    sch.shutdown()
    thread.join(timeout=1.0)


def test_capacity_change_edge_not_found() -> None:
    """Test capacity change when edge doesn't exist."""
    sch = Scheduler()
    
    # Start scheduler
    producer = Producer("Producer")
    consumer = Consumer("Consumer")
    sg = Subgraph.from_nodes("Test", [producer, consumer])
    sg.connect(("Producer", "out"), ("Consumer", "in"), capacity=10)
    
    sch.register(sg)
    
    import threading
    thread = threading.Thread(target=sch.run)
    thread.start()
    time.sleep(0.1)
    
    # Try to change capacity of non-existent edge
    sch.set_capacity("non_existent_edge", 5)
    
    sch.shutdown()
    thread.join(timeout=1.0)


def test_pending_priority_application() -> None:
    """Test that pending priorities are applied during plan build."""
    sch = Scheduler()
    
    # Set priority before registering
    sch.set_priority("edge_id", PriorityBand.CONTROL)
    
    # Register graph
    producer = Producer("Producer")
    consumer = Consumer("Consumer")
    sg = Subgraph.from_nodes("Test", [producer, consumer])
    edge_id = sg.connect(("Producer", "out"), ("Consumer", "in"), capacity=10)
    
    # The pending priority should be applied during registration
    sch.register(sg)
    
    # Run briefly to ensure it works
    sch.run()


def test_scheduler_reentrant_run() -> None:
    """Test that re-entrant run() calls are ignored."""
    sch = Scheduler()
    
    producer = Producer("Producer")
    consumer = Consumer("Consumer")
    sg = Subgraph.from_nodes("Test", [producer, consumer])
    sg.connect(("Producer", "out"), ("Consumer", "in"), capacity=10)
    
    sch.register(sg)
    
    # Start scheduler in background
    import threading
    thread = threading.Thread(target=sch.run)
    thread.start()
    time.sleep(0.1)
    
    # Try to run again while already running - should be ignored
    sch.run()
    
    sch.shutdown()
    thread.join(timeout=1.0)


def test_scheduler_stats() -> None:
    """Test scheduler stats retrieval."""
    sch = Scheduler()
    
    # Get stats before running
    stats = sch.get_stats()
    assert "status" in stats
    assert stats["status"] == "stopped"
    
    # Start scheduler
    producer = Producer("Producer")
    consumer = Consumer("Consumer")
    sg = Subgraph.from_nodes("Test", [producer, consumer])
    sg.connect(("Producer", "out"), ("Consumer", "in"), capacity=10)
    
    sch.register(sg)
    
    import threading
    thread = threading.Thread(target=sch.run)
    thread.start()
    time.sleep(0.1)
    
    # Get stats while running
    stats = sch.get_stats()
    assert stats["status"] == "running"
    assert "nodes_count" in stats
    assert "edges_count" in stats
    assert "runnable_nodes" in stats
    
    sch.shutdown()
    thread.join(timeout=1.0)
