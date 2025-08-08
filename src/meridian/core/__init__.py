"""
Meridian core public API.

This package exposes the primary runtime building blocks:
- Message and MessageType: immutable envelopes for data/control/error.
- Port and PortDirection: node connection points.
- Edge: bounded channel between node ports.
- Node: processing unit with lifecycle hooks and emit().
- Subgraph: composable collection of nodes and edges.
- Scheduler and SchedulerConfig: cooperative graph scheduler.
- Policies and strategies: backpressure/routing/retry controls.

Typical usage:
    from meridian.core import Node, Edge, Subgraph, Scheduler, Message, MessageType
    # Build nodes/subgraph, connect ports with edges, then run via Scheduler.
"""

from __future__ import annotations

from .edge import Edge
from .message import Message, MessageType
# Backward compatible re-exports for Node
from .node import Node
from .policies import BackpressureStrategy, RetryPolicy, RoutingPolicy
from .ports import Port, PortDirection, PortSpec
# Backward compatible re-exports for scheduler
from .scheduler import Scheduler, SchedulerConfig
from .subgraph import Subgraph

__all__ = [
    "Message",
    "MessageType",
    "Port",
    "PortDirection",
    "PortSpec",
    "BackpressureStrategy",
    "RetryPolicy",
    "RoutingPolicy",
    "Edge",
    "Node",
    "Subgraph",
    "Scheduler",
    "SchedulerConfig",
]
