from __future__ import annotations

import time
from typing import Any

import pytest

from meridian.core import Message, MessageType


def test_headers_auto_populated_when_missing() -> None:
    m = Message(type=MessageType.DATA, payload={"k": "v"})
    # trace_id and timestamp should be auto-injected
    trace_id = m.get_trace_id()
    ts = m.get_timestamp()

    assert isinstance(trace_id, str) and len(trace_id) > 0
    assert isinstance(ts, float) and ts > 0.0

    # The raw headers should also contain these keys
    assert "trace_id" in m.headers
    assert "timestamp" in m.headers


def test_headers_preserved_when_provided() -> None:
    headers = {"trace_id": "abc123", "timestamp": 123.456, "custom": "x"}
    m = Message(type=MessageType.DATA, payload=42, headers=headers)

    assert m.get_trace_id() == "abc123"
    assert m.get_timestamp() == pytest.approx(123.456)
    # Preserve custom header
    assert m.headers["custom"] == "x"


def test_with_headers_merges_and_overrides() -> None:
    base = Message(type=MessageType.CONTROL, payload=None, headers={"h1": "v1", "h2": "v2"})
    derived = base.with_headers(h2="override", h3="new")

    # Type and payload are preserved
    assert derived.type == base.type
    assert derived.payload == base.payload

    # Headers merged: h1 stays, h2 overridden, h3 added
    assert derived.headers["h1"] == "v1"
    assert derived.headers["h2"] == "override"
    assert derived.headers["h3"] == "new"

    # Ensure original message headers unchanged (immutability-by-convention check)
    assert base.headers["h2"] == "v2"
    assert "h3" not in base.headers


def test_get_trace_id_coerces_to_string_and_handles_missing() -> None:
    m1 = Message(type=MessageType.DATA, payload=0, headers={"trace_id": 12345})
    assert m1.get_trace_id() == "12345"  # coerced to string

    m2 = Message(type=MessageType.DATA, payload=0, headers={"trace_id": None})
    assert m2.get_trace_id() == ""  # None -> empty string

    m3 = Message(type=MessageType.DATA, payload=0, headers={})
    assert isinstance(m3.get_trace_id(), str)
    assert len(m3.get_trace_id()) > 0  # auto-generated during __post_init__


def test_get_timestamp_handles_bad_values() -> None:
    m_bad_type = Message(type=MessageType.DATA, payload=0, headers={"timestamp": "not-a-float"})
    # Should fall back to 0.0 when conversion fails
    assert m_bad_type.get_timestamp() == 0.0

    m_none = Message(type=MessageType.DATA, payload=0, headers={"timestamp": None})
    # None -> 0.0 via coercion path
    assert m_none.get_timestamp() == 0.0


def test_is_helpers() -> None:
    assert Message(MessageType.DATA, payload="x").is_data()
    assert not Message(MessageType.DATA, payload="x").is_error()
    assert not Message(MessageType.DATA, payload="x").is_control()

    assert Message(MessageType.ERROR, payload="oops").is_error()
    assert Message(MessageType.CONTROL, payload=None).is_control()


def test_timestamp_is_reasonable_monotonic_increase() -> None:
    # Two messages created in sequence should have non-decreasing timestamps
    m1 = Message(type=MessageType.DATA, payload=1)
    t1 = m1.get_timestamp()
    # Ensure a measurable delta
    time.sleep(0.001)
    m2 = Message(type=MessageType.DATA, payload=2)
    t2 = m2.get_timestamp()

    assert t1 > 0.0 and t2 > 0.0
    assert t2 >= t1


def test_with_headers_does_not_strip_existing_trace_id() -> None:
    m = Message(type=MessageType.DATA, payload=1)
    original_trace = m.get_trace_id()
    assert original_trace

    updated = m.with_headers(custom="y")
    # Should preserve prior trace_id unless explicitly overridden
    assert updated.get_trace_id() == original_trace
    assert updated.headers["custom"] == "y"


def test_with_headers_can_override_trace_id() -> None:
    m = Message(type=MessageType.DATA, payload=1)
    overridden = m.with_headers(trace_id="override-trace")
    assert overridden.get_trace_id() == "override-trace"


@pytest.mark.parametrize(
    "initial_headers, expected_present_keys",
    [
        ({}, {"trace_id", "timestamp"}),
        ({"trace_id": "t"}, {"trace_id", "timestamp"}),
        ({"timestamp": 1.23}, {"trace_id", "timestamp"}),
        ({"trace_id": "t", "timestamp": 1.23}, {"trace_id", "timestamp"}),
    ],
)
def test_header_normalization_matrix(
    initial_headers: dict[str, Any], expected_present_keys: set[str]
) -> None:
    m = Message(type=MessageType.DATA, payload="ok", headers=initial_headers)
    for k in expected_present_keys:
        assert k in m.headers
