"""Unit tests for arachne.utils.ids module."""

import re
import uuid

import pytest

from arachne.utils.ids import new_trace_id, new_id, generate_trace_id, generate_correlation_id, generate_span_id


class TestNewTraceId:
    """Test suite for new_trace_id function."""
    
    def test_returns_string(self):
        """Test that new_trace_id returns a string."""
        trace_id = new_trace_id()
        assert isinstance(trace_id, str)
    
    def test_returns_hex_without_dashes(self):
        """Test that trace ID is hex format without dashes."""
        trace_id = new_trace_id()
        # Should be 32 hex characters (UUID4 without dashes)
        assert len(trace_id) == 32
        assert re.match(r'^[0-9a-f]{32}$', trace_id)
    
    def test_generates_unique_ids(self):
        """Test that multiple calls generate unique IDs."""
        ids = {new_trace_id() for _ in range(100)}
        assert len(ids) == 100  # All should be unique
    
    def test_no_dashes_in_output(self):
        """Test that output contains no dashes."""
        trace_id = new_trace_id()
        assert '-' not in trace_id


class TestNewId:
    """Test suite for new_id function."""
    
    def test_without_prefix(self):
        """Test new_id without prefix."""
        id_val = new_id()
        assert isinstance(id_val, str)
        assert len(id_val) == 32
        assert re.match(r'^[0-9a-f]{32}$', id_val)
    
    def test_with_prefix(self):
        """Test new_id with prefix."""
        prefix = "test"
        id_val = new_id(prefix)
        assert id_val.startswith(f"{prefix}_")
        
        # Should be prefix + underscore + 32 hex chars
        assert len(id_val) == len(prefix) + 1 + 32
        
        # Extract the ID part and verify it's valid hex
        id_part = id_val[len(prefix) + 1:]
        assert re.match(r'^[0-9a-f]{32}$', id_part)
    
    def test_with_empty_prefix(self):
        """Test new_id with empty prefix."""
        id_val = new_id("")
        # Empty prefix should be treated as None
        assert len(id_val) == 32
        assert re.match(r'^[0-9a-f]{32}$', id_val)
    
    def test_with_none_prefix(self):
        """Test new_id with None prefix."""
        id_val = new_id(None)
        assert len(id_val) == 32
        assert re.match(r'^[0-9a-f]{32}$', id_val)
    
    def test_prefix_uniqueness(self):
        """Test that IDs with same prefix are still unique."""
        prefix = "node"
        ids = {new_id(prefix) for _ in range(50)}
        assert len(ids) == 50  # All should be unique
        
        # All should have the same prefix
        for id_val in ids:
            assert id_val.startswith(f"{prefix}_")
    
    def test_different_prefixes(self):
        """Test IDs with different prefixes."""
        id1 = new_id("node")
        id2 = new_id("edge")
        
        assert id1.startswith("node_")
        assert id2.startswith("edge_")
        assert id1 != id2


class TestLegacyAliases:
    """Test suite for legacy alias functions."""
    
    def test_generate_trace_id(self):
        """Test legacy generate_trace_id function."""
        trace_id = generate_trace_id()
        assert isinstance(trace_id, str)
        # Legacy version returns UUID with dashes
        assert len(trace_id) == 36
        assert re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', trace_id)
    
    def test_generate_correlation_id(self):
        """Test legacy generate_correlation_id function."""
        corr_id = generate_correlation_id()
        assert isinstance(corr_id, str)
        assert len(corr_id) == 36
        assert re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', corr_id)
    
    def test_generate_span_id(self):
        """Test legacy generate_span_id function."""
        span_id = generate_span_id()
        assert isinstance(span_id, str)
        assert len(span_id) == 36
        assert re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', span_id)
    
    def test_legacy_uniqueness(self):
        """Test that legacy functions generate unique IDs."""
        trace_ids = {generate_trace_id() for _ in range(20)}
        corr_ids = {generate_correlation_id() for _ in range(20)}
        span_ids = {generate_span_id() for _ in range(20)}
        
        assert len(trace_ids) == 20
        assert len(corr_ids) == 20
        assert len(span_ids) == 20


class TestPerformance:
    """Basic performance sanity tests."""
    
    def test_id_generation_performance(self):
        """Test that ID generation is reasonably fast."""
        import time
        
        start = time.perf_counter()
        for _ in range(1000):
            new_trace_id()
        elapsed = time.perf_counter() - start
        
        # Should generate 1000 IDs in well under a second
        assert elapsed < 1.0
    
    def test_prefixed_id_performance(self):
        """Test that prefixed ID generation is reasonably fast."""
        import time
        
        start = time.perf_counter()
        for _ in range(1000):
            new_id("test")
        elapsed = time.perf_counter() - start
        
        # Should generate 1000 prefixed IDs in well under a second
        assert elapsed < 1.0 