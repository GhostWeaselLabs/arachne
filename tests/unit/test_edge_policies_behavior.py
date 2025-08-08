"""Focused unit tests for Edge policy behavior.

Covers:
- Capacity accounting and enqueue/dequeue semantics.
- Policy outcomes for Block, Drop, Latest, and Coalesce.
- Depth gauge behavior via Edge.depth() queries (functional check).
- PortSpec enforcement at enqueue boundaries.
"""

from __future__ import annotations

import math
from typing import Any

import pytest

from meridian.core.edge import Edge
from meridian.core.message import Message, MessageType
from meridian.core.policies import Block, Coalesce, Drop, Latest, PutResult
from meridian.core.ports import Port, PortDirection, PortSpec


def make_edge(
    capacity: int = 2,
    spec: PortSpec | None = None,
    source_node: str = "A",
    target_node: str = "B",
    source_port_name: str = "o",
    target_port_name: str = "i",
) -> Edge[Any]:
    """Helper to create a minimal Edge with specified capacity/spec."""
    src_port = Port(source_port_name, PortDirection.OUTPUT, spec=None)
    dst_port = Port(target_port_name, PortDirection.INPUT, spec=spec)
    return Edge(
        source_node=source_node,
        source_port=src_port,
        target_node=target_node,
        target_port=dst_port,
        capacity=capacity,
        spec=spec,
    )


class TestEdgeDepthAndBasicEnqueueDequeue:
    def test_depth_updates_on_put_and_get(self) -> None:
        edge = make_edge(capacity=3)
        assert edge.depth() == 0
        assert edge.try_put(1) == PutResult.OK
        assert edge.depth() == 1
        assert edge.try_put(2) == PutResult.OK
        assert edge.depth() == 2

        # Dequeue in FIFO order
        assert edge.try_get() == 1
        assert edge.depth() == 1
        assert edge.try_get() == 2
        assert edge.depth() == 0
        # Empty returns None and keeps depth at 0
        assert edge.try_get() is None
        assert edge.depth() == 0


class TestBlockPolicy:
    def test_block_applies_when_full(self) -> None:
        edge = make_edge(capacity=2)
        # Fill to capacity
        assert edge.try_put(1, Block()) == PutResult.OK
        assert edge.try_put(2, Block()) == PutResult.OK
        assert edge.depth() == 2

        # Next put with Block policy => BLOCKED, no change in depth
        res = edge.try_put(3, Block())
        assert res == PutResult.BLOCKED
        assert edge.depth() == 2

        # After a consumer gets one, put should succeed
        assert edge.try_get() == 1
        assert edge.depth() == 1
        assert edge.try_put(3, Block()) == PutResult.OK
        assert edge.depth() == 2

    def test_block_with_message_envelope(self) -> None:
        edge = make_edge(capacity=1)
        msg = Message(MessageType.DATA, payload={"k": "v"})
        assert edge.try_put(msg, Block()) == PutResult.OK
        # Next should block
        assert edge.try_put(msg, Block()) == PutResult.BLOCKED
        assert edge.depth() == 1


class TestDropPolicy:
    def test_drop_discards_on_full(self) -> None:
        edge = make_edge(capacity=1)
        assert edge.try_put("x", Drop()) == PutResult.OK
        # Full -> DROPPED
        assert edge.try_put("y", Drop()) == PutResult.DROPPED
        # Depth preserved at capacity
        assert edge.depth() == 1
        # Ensure dequeued item is original
        assert edge.try_get() == "x"
        assert edge.depth() == 0


class TestLatestPolicy:
    def test_latest_replaces_when_full(self) -> None:
        edge = make_edge(capacity=1)
        assert edge.try_put("old", Latest()) == PutResult.OK
        # Full -> REPLACED (keep latest only)
        assert edge.try_put("new", Latest()) == PutResult.REPLACED
        assert edge.depth() == 1
        # The only item present should be "new"
        assert edge.try_get() == "new"
        assert edge.depth() == 0

    def test_latest_default_policy_when_none(self) -> None:
        # Edge.try_put defaults to Latest() when policy is None
        edge = make_edge(capacity=1)
        assert edge.try_put("first") == PutResult.OK
        assert edge.try_put("second") == PutResult.REPLACED
        assert edge.depth() == 1
        assert edge.try_get() == "second"


class TestCoalescePolicy:
    def test_coalesce_merges_latest_two_when_full(self) -> None:
        edge = make_edge(capacity=1)

        def merge(a: Any, b: Any) -> Any:
            # Simple numeric sum or string concat for demonstration
            if isinstance(a, int | float) and isinstance(b, int | float):
                return a + b
            return f"{a}|{b}"

        # Start with a value
        assert edge.try_put(10, Coalesce(merge)) == PutResult.OK
        # Next insert coalesces with the latest (only) item
        assert edge.try_put(5, Coalesce(merge)) == PutResult.COALESCED
        assert edge.depth() == 1

        # Verify merged result
        merged = edge.try_get()
        assert merged == 15

    def test_coalesce_on_empty_behaves_like_enqueue(self) -> None:
        edge = make_edge(capacity=2)

        def merge(a: Any, b: Any) -> Any:  # pragma: no cover - not invoked on first put
            return a  # arbitrary

        # Queue empty and capacity not reached -> OK and append
        assert edge.try_put("a", Coalesce(merge)) == PutResult.OK
        assert edge.depth() == 1
        assert edge.try_get() == "a"
        assert edge.depth() == 0

    def test_coalesce_function_exception_falls_back_to_append_new_item(self) -> None:
        edge = make_edge(capacity=1)

        def boom(a: Any, b: Any) -> Any:
            raise RuntimeError("coalesce failed")

        assert edge.try_put("x", Coalesce(boom)) == PutResult.OK
        # At capacity -> COALESCED branch taken, but function raises; runtime should append new item
        assert edge.try_put("y", Coalesce(boom)) == PutResult.COALESCED
        assert edge.depth() == 1
        assert edge.try_get() == "y"


class TestPortSpecValidation:
    def test_spec_accepts_matching_types(self) -> None:
        spec = PortSpec(name="i", schema=int)
        edge = make_edge(capacity=2, spec=spec)

        # Raw value that matches schema
        assert edge.try_put(123) == PutResult.OK

        # Message payload that matches schema
        msg = Message(MessageType.DATA, payload=456)
        assert edge.try_put(msg) == PutResult.OK

        # Drain and verify order
        assert edge.try_get() == 123
        got = edge.try_get()
        assert isinstance(got, Message)
        assert isinstance(got.payload, int)  # type: ignore[union-attr]

    def test_spec_rejects_non_matching_types(self) -> None:
        spec = PortSpec(name="i", schema=int)
        edge = make_edge(capacity=1, spec=spec)

        with pytest.raises(TypeError):
            _ = edge.try_put("not-int")

        with pytest.raises(TypeError):
            _ = edge.try_put(Message(MessageType.DATA, payload="nope"))

        # Depth unchanged by failed validation
        assert edge.depth() == 0


class TestEdgeIsEmptyIsFull:
    def test_is_empty_and_is_full(self) -> None:
        edge = make_edge(capacity=2)
        assert edge.is_empty()
        assert not edge.is_full()

        assert edge.try_put(1) == PutResult.OK
        assert not edge.is_empty()
        assert not edge.is_full()

        assert edge.try_put(2) == PutResult.OK
        assert not edge.is_empty()
        assert edge.is_full()

    def test_is_full_with_latest_replacement(self) -> None:
        edge = make_edge(capacity=1)
        assert edge.try_put("a", Latest()) == PutResult.OK
        assert edge.is_full()
        # Replacement keeps depth at 1, still full
        assert edge.try_put("b", Latest()) == PutResult.REPLACED
        assert edge.is_full()
        assert edge.try_get() == "b"
        assert edge.is_empty()


class TestEdgeWithMessages:
    def test_message_headers_are_preserved_and_normalized(self) -> None:
        edge = make_edge(capacity=1)
        msg = Message(MessageType.DATA, payload={"v": 1}, headers={})
        assert msg.get_trace_id() != ""  # generated on construction
        assert edge.try_put(msg) in (PutResult.OK, PutResult.REPLACED)
        got = edge.try_get()
        assert isinstance(got, Message)
        assert got.get_trace_id() != ""
        ts = got.get_timestamp()
        assert isinstance(ts, float) and ts > 0 and math.isfinite(ts)
