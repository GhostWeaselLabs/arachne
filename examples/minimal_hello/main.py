#!/usr/bin/env python3
"""
Minimal Hello World example for Meridian Runtime.

This example demonstrates the basic concepts:
- Creating nodes with typed ports
- Connecting nodes with bounded edges
- Running a simple dataflow

Run with: python examples/minimal_hello/main.py
"""

from __future__ import annotations

from meridian.core import Subgraph, Scheduler, Message, MessageType, Node, PortSpec
from meridian.core.ports import Port, PortDirection


class Producer(Node):
    """Produces integer messages on tick intervals."""
    
    def __init__(self, name: str = "producer", max_count: int = 5):
        super().__init__(
            name=name,
            inputs=[],
            outputs=[Port("output", PortDirection.OUTPUT, spec=PortSpec("output", int))],
        )
        self.max_count = max_count
        self.count = 0
        
    def _handle_tick(self) -> None:
        if self.count < self.max_count:
            self.emit("output", Message(type=MessageType.DATA, payload=self.count))
            self.count += 1


class Consumer(Node):
    """Consumes and prints integer messages."""
    
    def __init__(self, name: str = "consumer"):
        super().__init__(
            name=name,
            inputs=[Port("in", PortDirection.INPUT, spec=PortSpec("in", int))],
            outputs=[],
        )
        self.values = []
        
    def _handle_message(self, port: str, msg: Message) -> None:
        if port == "in":
            self.values.append(msg.payload)
            print(f"Consumer received: {msg.payload}")


def main():
    """Run the minimal hello world example."""
    print("=== Meridian Runtime - Minimal Hello World ===\n")
    
    # Create nodes
    producer = Producer(max_count=5)
    consumer = Consumer()
    
    # Create subgraph and connect nodes
    sg = Subgraph.from_nodes("hello_world", [producer, consumer])
    sg.connect(("producer", "output"), ("consumer", "in"), capacity=8)
    
    # Create scheduler and run
    sch = Scheduler()
    sch.register(sg)
    
    print("Starting dataflow...")
    sch.run()
    
    print(f"\nConsumer processed {len(consumer.values)} messages")
    print("✓ Example completed successfully!")


if __name__ == "__main__":
    main() 