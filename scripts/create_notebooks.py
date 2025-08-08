#!/usr/bin/env python3
"""
Script to create Jupyter notebooks for Meridian Runtime tutorials and examples.
"""

import json
from pathlib import Path


def create_cell(cell_type: str, source: str, metadata: dict = None) -> dict:
    """Create a notebook cell."""
    return {
        "cell_type": cell_type,
        "metadata": metadata or {},
        "source": source.splitlines(keepends=True),
        "execution_count": None,
        "outputs": []
    }

def create_notebook(cells: list, metadata: dict = None) -> dict:
    """Create a complete notebook."""
    return {
        "cells": cells,
        "metadata": metadata or {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.11.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

def create_getting_started_notebook() -> dict:
    """Create the getting started tutorial notebook."""
    
    cells = [
        create_cell("markdown", """# Getting Started with Meridian Runtime

Welcome to your first interactive Meridian Runtime tutorial! This notebook will guide you through the basic concepts of building dataflow graphs with Meridian Runtime.

## What You'll Learn

- How to create simple nodes and connect them
- Understanding the basic graph execution model
- Interactive exploration of message flow
- Real-time visualization of graph behavior

## Prerequisites

Make sure you have the notebook dependencies installed:
```bash
uv sync --extra notebooks
```
"""),
        
        create_cell("code", """# Import required libraries
import sys
import time
import threading
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, clear_output
import networkx as nx
import pandas as pd

# Add the project root to the path
sys.path.insert(0, '../..')

# Import Meridian Runtime
from meridian.core import (
    Node, Message, MessageType, Subgraph, Scheduler, SchedulerConfig,
    PortSpec, Port, PortDirection
)
from meridian.observability.config import ObservabilityConfig, configure_observability
from meridian.observability.logging import get_logger, with_context

print("✅ Meridian Runtime imported successfully!")
"""),
        
        create_cell("markdown", """## Step 1: Understanding the Basic Components

Meridian Runtime is built around four core concepts:

1. **Nodes**: Single-responsibility processing units
2. **Edges**: Bounded queues connecting nodes
3. **Subgraphs**: Composable groups of nodes
4. **Scheduler**: Coordinates execution and enforces backpressure

Let's start by creating a simple producer-consumer pattern.
"""),
        
        create_cell("code", """# Create a simple producer node
class InteractiveProducer(Node):
    \"\"\"A producer that generates numbers with interactive controls.\"\"\"
    
    def __init__(self, name: str = "producer", max_count: int = 10):
        super().__init__(
            name=name,
            inputs=[],
            outputs=[Port("output", PortDirection.OUTPUT, spec=PortSpec("output", int))]
        )
        self._max_count = max_count
        self._current = 0
        self._messages_sent = 0
        
    def _handle_tick(self):
        \"\"\"Emit a number on each tick until we reach max_count.\"\"\"
        if self._current < self._max_count:
            self.emit("output", Message(MessageType.DATA, self._current))
            self._current += 1
            self._messages_sent += 1
            
    def get_stats(self) -> Dict[str, Any]:
        \"\"\"Get current statistics for visualization.\"\"\"
        return {
            "messages_sent": self._messages_sent,
            "current_value": self._current,
            "is_complete": self._current >= self._max_count
        }

# Create a simple consumer node
class InteractiveConsumer(Node):
    \"\"\"A consumer that collects and displays received messages.\"\"\"
    
    def __init__(self, name: str = "consumer"):
        super().__init__(
            name=name,
            inputs=[Port("input", PortDirection.INPUT, spec=PortSpec("input", int))],
            outputs=[]
        )
        self._received_messages = []
        self._message_count = 0
        
    def _handle_message(self, port: str, msg: Message):
        \"\"\"Process incoming messages.\"\"\"
        if port == "input":
            self._received_messages.append(msg.payload)
            self._message_count += 1
            print(f"📨 Consumer received: {msg.payload}")
            
    def get_stats(self) -> Dict[str, Any]:
        \"\"\"Get current statistics for visualization.\"\"\"
        return {
            "messages_received": self._message_count,
            "last_values": self._received_messages[-5:] if self._received_messages else [],
            "all_values": self._received_messages.copy()
        }

print("✅ Producer and Consumer nodes created!")
"""),
        
        create_cell("markdown", """## Step 2: Building Your First Graph

Now let's create a simple graph that connects our producer to our consumer. We'll use interactive controls to explore different configurations.
"""),
        
        create_cell("code", """# Interactive controls for graph configuration
max_count_slider = widgets.IntSlider(
    value=5, min=1, max=20, step=1,
    description='Max Count:',
    style={'description_width': 'initial'}
)

capacity_slider = widgets.IntSlider(
    value=8, min=1, max=32, step=1,
    description='Edge Capacity:',
    style={'description_width': 'initial'}
)

tick_interval_slider = widgets.IntSlider(
    value=100, min=50, max=500, step=50,
    description='Tick Interval (ms):',
    style={'description_width': 'initial'}
)

# Display controls
print("🎛️  Graph Configuration Controls:")
display(max_count_slider, capacity_slider, tick_interval_slider)
"""),
        
        create_cell("code", """def build_interactive_graph(max_count: int, capacity: int) -> tuple[Subgraph, InteractiveProducer, InteractiveConsumer]:
    \"\"\"Build a graph with the given configuration.\"\"\"
    
    # Create nodes
    producer = InteractiveProducer(name="producer", max_count=max_count)
    consumer = InteractiveConsumer(name="consumer")
    
    # Create subgraph
    graph = Subgraph.from_nodes("interactive_demo", [producer, consumer])
    
    # Connect nodes with specified capacity
    graph.connect(("producer", "output"), ("consumer", "input"), capacity=capacity)
    
    return graph, producer, consumer

# Build the graph with current slider values
graph, producer, consumer = build_interactive_graph(
    max_count_slider.value,
    capacity_slider.value
)

print(f"✅ Graph built with {max_count_slider.value} messages and capacity {capacity_slider.value}")
"""),
        
        create_cell("markdown", """## Step 3: Visualizing the Graph Structure

Let's create a visual representation of our graph to understand the topology.
"""),
        
        create_cell("code", """def visualize_graph(graph: Subgraph):
    \"\"\"Create a visual representation of the graph topology.\"\"\"
    
    # Create NetworkX graph for visualization
    G = nx.DiGraph()
    
    # Add nodes - iterate over node objects, not node names
    for node in graph.nodes.values():
        G.add_node(node.name, type=node.__class__.__name__)
    
    # Add edges with capacity information
    for edge in graph.edges:
        policy_name = edge.default_policy.__class__.__name__ if edge.default_policy else "Latest"
        G.add_edge(
            edge.source_node, 
            edge.target_node, 
            capacity=edge.capacity,
            policy=policy_name
        )
    
    # Create the visualization
    plt.figure(figsize=(10, 6))
    pos = nx.spring_layout(G, seed=42)
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=2000)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
    
    # Draw edges with labels
    edge_labels = {(u, v): f"cap={d['capacity']}" for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowsize=20)
    
    plt.title("Meridian Runtime Graph Topology", fontsize=14, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    plt.show()
    
    # Print graph information
    print(f"📊 Graph Information:")
    print(f"   Nodes: {len(graph.nodes)}")
    print(f"   Edges: {len(graph.edges)}")
    for edge in graph.edges:
        print(f"   {edge.source_node} → {edge.target_node} (capacity: {edge.capacity})")

# Visualize our graph
visualize_graph(graph)
"""),
        
        create_cell("markdown", """## Step 4: Running the Graph with Real-time Monitoring

Now let's run our graph and watch the messages flow in real-time!
"""),
        
        create_cell("code", """# Configure observability for better visibility
configure_observability(ObservabilityConfig(
    log_level="INFO",
    log_json=False,  # Human-readable logs for notebooks
    metrics_enabled=True,
    tracing_enabled=False
))

def run_graph_with_monitoring(graph: Subgraph, producer: InteractiveProducer, 
                              consumer: InteractiveConsumer, max_ticks: int = 50):
    \"\"\"Run the graph with real-time monitoring and visualization.\"\"\"
    
    import threading
    import time
    
    # Create scheduler with short timeout for interactive use
    scheduler = Scheduler(SchedulerConfig(
        tick_interval_ms=100,  # Slower ticks for better monitoring
        shutdown_timeout_s=30.0,  # 30 second timeout
        idle_sleep_ms=10  # Shorter idle sleep for responsiveness
    ))
    scheduler.register(graph)
    
    # Monitoring data
    producer_stats = []
    consumer_stats = []
    execution_complete = threading.Event()
    
    def monitor_execution():
        \"\"\"Monitor execution and collect stats.\"\"\"
        start_time = time.time()
        last_stats_time = start_time
        
        while not execution_complete.is_set() and (time.time() - start_time) < 30:
            current_time = time.time()
            
            # Collect stats every 0.5 seconds
            if current_time - last_stats_time >= 0.5:
                producer_stat = producer.get_stats()
                consumer_stat = consumer.get_stats()
                
                producer_stats.append(producer_stat)
                consumer_stats.append(consumer_stat)
                
                # Print progress
                print(f"⏱️  {current_time - start_time:.1f}s: "
                      f"Producer sent {producer_stat['messages_sent']}, "
                      f"Consumer received {consumer_stat['messages_received']}")
                
                # Check if producer is complete
                if producer_stat["is_complete"]:
                    print("✅ Producer completed!")
                    execution_complete.set()
                    break
                
                last_stats_time = current_time
            
            time.sleep(0.1)  # Check every 100ms
    
    print("🚀 Starting graph execution...")
    print("=" * 50)
    
    # Start monitoring in a separate thread
    monitor_thread = threading.Thread(target=monitor_execution)
    monitor_thread.start()
    
    try:
        # Run the scheduler (this will block until completion or timeout)
        scheduler.run()
    except Exception as e:
        print(f"⚠️  Scheduler error: {e}")
    finally:
        # Signal monitoring to stop
        execution_complete.set()
        monitor_thread.join(timeout=1.0)
    
    print("=" * 50)
    print("🏁 Graph execution completed!")
    
    # Final statistics
    final_producer_stats = producer.get_stats()
    final_consumer_stats = consumer.get_stats()
    
    print(f"📈 Final Statistics:")
    print(f"   Producer sent: {final_producer_stats['messages_sent']} messages")
    print(f"   Consumer received: {final_consumer_stats['messages_received']} messages")
    print(f"   Messages received: {final_consumer_stats['all_values']}")
    
    return producer_stats, consumer_stats

# Run the graph
producer_stats, consumer_stats = run_graph_with_monitoring(graph, producer, consumer)
"""),
        
        create_cell("markdown", """## Step 5: Interactive Experimentation

Now let's create an interactive experiment where you can change parameters and see the results!
"""),
        
        create_cell("code", """# Create an interactive experiment button
experiment_button = widgets.Button(
    description="Run New Experiment",
    button_style='success',
    tooltip='Click to run a new experiment with current settings'
)

output_area = widgets.Output()

def on_experiment_click(b):
    \"\"\"Handle experiment button click.\"\"\"
    with output_area:
        clear_output()
        
        # Build new graph with current settings
        new_graph, new_producer, new_consumer = build_interactive_graph(
            max_count_slider.value,
            capacity_slider.value
        )
        
        # Run the experiment
        run_graph_with_monitoring(new_graph, new_producer, new_consumer)
        
        # Show the graph visualization
        visualize_graph(new_graph)

experiment_button.on_click(on_experiment_click)

print("🔬 Interactive Experiment Controls:")
print("Adjust the sliders above, then click the button to run a new experiment!")
display(experiment_button, output_area)
"""),
        
        create_cell("markdown", """## Step 6: Understanding Backpressure

Let's explore what happens when we create a bottleneck in our graph. This demonstrates Meridian's backpressure mechanism.
"""),
        
        create_cell("code", """# Create a slow consumer to demonstrate backpressure
class SlowConsumer(InteractiveConsumer):
    \"\"\"A consumer that processes messages slowly to create backpressure.\"\"\"
    
    def __init__(self, name: str = "slow_consumer", delay_ms: int = 200):
        super().__init__(name=name)
        self._delay_ms = delay_ms
        
    def _handle_message(self, port: str, msg: Message):
        \"\"\"Process messages with artificial delay.\"\"\"
        if port == "input":
            # Simulate slow processing
            time.sleep(self._delay_ms / 1000.0)
            self._received_messages.append(msg.payload)
            self._message_count += 1
            print(f"🐌 Slow consumer processed: {msg.payload} (took {self._delay_ms}ms)")

# Interactive controls for backpressure experiment
delay_slider = widgets.IntSlider(
    value=100, min=0, max=500, step=50,
    description='Consumer Delay (ms):',
    style={'description_width': 'initial'}
)

backpressure_button = widgets.Button(
    description="Run Backpressure Experiment",
    button_style='warning',
    tooltip='Click to run backpressure experiment'
)

backpressure_output = widgets.Output()

def on_backpressure_click(b):
    \"\"\"Handle backpressure experiment button click.\"\"\"
    with backpressure_output:
        clear_output()
        
        print(f"🔍 Backpressure Experiment with {delay_slider.value}ms delay")
        print("=" * 60)
        
        # Create graph with slow consumer
        producer = InteractiveProducer(name="fast_producer", max_count=10)
        consumer = SlowConsumer(name="slow_consumer", delay_ms=delay_slider.value)
        
        graph = Subgraph.from_nodes("backpressure_demo", [producer, consumer])
        graph.connect(("fast_producer", "output"), ("slow_consumer", "input"), capacity=3)
        
        # Run with monitoring
        start_time = time.time()
        run_graph_with_monitoring(graph, producer, consumer, max_ticks=100)
        end_time = time.time()
        
        print(f"⏱️  Total execution time: {end_time - start_time:.2f} seconds")
        print(f"📊 Producer sent: {producer.get_stats()['messages_sent']} messages")
        print(f"📊 Consumer received: {consumer.get_stats()['messages_received']} messages")
        
        # Explain what happened
        if delay_slider.value > 0:
            print("\\n💡 Backpressure Explanation:")
            print("   - The slow consumer created a bottleneck")
            print("   - The edge capacity (3) limited buffering")
            print("   - The producer was forced to wait (backpressure)")
            print("   - This prevents unbounded memory usage")

backpressure_button.on_click(on_backpressure_click)

print("🔍 Backpressure Experiment Controls:")
display(delay_slider, backpressure_button, backpressure_output)
"""),
        
        create_cell("markdown", """## Summary

Congratulations! You've successfully completed your first Meridian Runtime tutorial. Here's what you've learned:

### Key Concepts
✅ **Nodes**: Single-responsibility processing units (Producer, Consumer)
✅ **Edges**: Bounded queues connecting nodes with configurable capacity
✅ **Subgraphs**: Composable groups of nodes
✅ **Scheduler**: Coordinates execution and manages the graph lifecycle
✅ **Backpressure**: Automatic flow control when consumers can't keep up

### Interactive Features
✅ **Real-time monitoring**: Watch messages flow through your graph
✅ **Visual graph topology**: See how nodes are connected
✅ **Parameter experimentation**: Adjust settings and see immediate results
✅ **Backpressure demonstration**: Understand flow control in action

### Next Steps

Ready to explore more advanced concepts? Check out:

1. **02-backpressure-policies.ipynb**: Different overflow policies (Drop, Latest, Coalesce)
2. **03-control-plane-priorities.ipynb**: Priority messaging and control flow
3. **04-observability-basics.ipynb**: Logs, metrics, and tracing

### Production Considerations

Remember that Jupyter notebooks are great for learning and experimentation, but for production:

- Use the command-line examples in the `examples/` directory
- Implement proper error handling and graceful shutdown
- Consider performance implications of your graph design
- Use appropriate observability and monitoring

Happy building with Meridian Runtime! 🚀
""")
    ]
    
    return create_notebook(cells)

def main():
    """Create all notebooks."""
    
    # Create notebooks directory structure
    notebooks_dir = Path("notebooks")
    tutorials_dir = notebooks_dir / "tutorials"
    examples_dir = notebooks_dir / "examples"
    research_dir = notebooks_dir / "research"
    
    for dir_path in [notebooks_dir, tutorials_dir, examples_dir, research_dir]:
        dir_path.mkdir(exist_ok=True)
    
    # Create getting started notebook
    getting_started = create_getting_started_notebook()
    
    with open(tutorials_dir / "01-getting-started.ipynb", "w") as f:
        json.dump(getting_started, f, indent=2)
    
    print("✅ Created notebooks/tutorials/01-getting-started.ipynb")
    
    # TODO: Create additional notebooks
    # - 02-backpressure-policies.ipynb
    # - 03-control-plane-priorities.ipynb
    # - 04-observability-basics.ipynb
    # - sentiment-pipeline-interactive.ipynb
    # - streaming-coalesce-demo.ipynb
    # - performance-benchmarks.ipynb
    # - policy-comparison.ipynb
    
    print("🎉 Notebook creation completed!")
    print("\\nNext steps:")
    print("1. Run: uv sync --extra notebooks")
    print("2. Start Jupyter: uv run jupyter lab")
    print("3. Navigate to notebooks/tutorials/01-getting-started.ipynb")

if __name__ == "__main__":
    main()
