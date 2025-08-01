"""Unit tests for arachne.utils.time module."""

import re
import time
from datetime import datetime, timezone

import pytest

from arachne.utils.time import (
    now_ts_ms,
    now_rfc3339,
    monotonic_ns,
    time_block,
    generate_timestamp,
    generate_monotonic_timestamp
)


class TestNowTsMs:
    """Test suite for now_ts_ms function."""
    
    def test_returns_int(self):
        """Test that now_ts_ms returns an integer."""
        timestamp = now_ts_ms()
        assert isinstance(timestamp, int)
    
    def test_reasonable_timestamp(self):
        """Test that timestamp is in reasonable range."""
        timestamp = now_ts_ms()
        
        # Should be sometime after 2020 and before 2100
        # 2020-01-01 00:00:00 UTC = 1577836800000 ms
        # 2100-01-01 00:00:00 UTC = 4102444800000 ms
        assert 1577836800000 < timestamp < 4102444800000
    
    def test_monotonic_increase(self):
        """Test that consecutive calls return increasing values."""
        ts1 = now_ts_ms()
        time.sleep(0.001)  # Sleep 1ms
        ts2 = now_ts_ms()
        
        assert ts2 >= ts1  # Should be equal or greater
    
    def test_millisecond_precision(self):
        """Test that function returns milliseconds."""
        ts_ms = now_ts_ms()
        ts_s = time.time()
        
        # Convert seconds to milliseconds and compare
        ts_s_as_ms = int(ts_s * 1000)
        
        # Should be within a few milliseconds
        assert abs(ts_ms - ts_s_as_ms) < 100


class TestNowRfc3339:
    """Test suite for now_rfc3339 function."""
    
    def test_returns_string(self):
        """Test that now_rfc3339 returns a string."""
        timestamp = now_rfc3339()
        assert isinstance(timestamp, str)
    
    def test_rfc3339_format(self):
        """Test that output matches RFC3339 format."""
        timestamp = now_rfc3339()
        
        # RFC3339 format: 2024-01-15T10:30:45.123456Z
        rfc3339_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$'
        assert re.match(rfc3339_pattern, timestamp)
    
    def test_utc_timezone(self):
        """Test that timestamp is in UTC (ends with Z)."""
        timestamp = now_rfc3339()
        assert timestamp.endswith('Z')
    
    def test_parseable_datetime(self):
        """Test that output can be parsed back to datetime."""
        timestamp = now_rfc3339()
        
        # Remove Z and parse
        dt_str = timestamp[:-1] + '+00:00'
        parsed = datetime.fromisoformat(dt_str)
        
        assert parsed.tzinfo == timezone.utc
    
    def test_recent_timestamp(self):
        """Test that timestamp is recent."""
        timestamp = now_rfc3339()
        
        # Parse and check it's within last minute
        dt_str = timestamp[:-1] + '+00:00'
        parsed = datetime.fromisoformat(dt_str)
        now = datetime.now(timezone.utc)
        
        diff = (now - parsed).total_seconds()
        assert 0 <= diff < 60  # Within last minute


class TestMonotonicNs:
    """Test suite for monotonic_ns function."""
    
    def test_returns_int(self):
        """Test that monotonic_ns returns an integer."""
        ns = monotonic_ns()
        assert isinstance(ns, int)
    
    def test_positive_value(self):
        """Test that monotonic time is positive."""
        ns = monotonic_ns()
        assert ns > 0
    
    def test_monotonic_increase(self):
        """Test that consecutive calls return increasing values."""
        ns1 = monotonic_ns()
        ns2 = monotonic_ns()
        
        assert ns2 >= ns1
    
    def test_nanosecond_precision(self):
        """Test that function returns nanoseconds."""
        ns = monotonic_ns()
        
        # Nanoseconds should be a very large number
        assert ns > 1_000_000_000  # At least 1 second worth of nanoseconds
    
    def test_matches_time_monotonic_ns(self):
        """Test that output matches time.monotonic_ns()."""
        our_ns = monotonic_ns()
        std_ns = time.monotonic_ns()
        
        # Should be very close (within microseconds)
        assert abs(our_ns - std_ns) < 1000000  # Within 1ms in nanoseconds


class TestTimeBlock:
    """Test suite for time_block context manager."""
    
    def test_context_manager_protocol(self):
        """Test that time_block works as context manager."""
        with time_block() as start_time:
            assert isinstance(start_time, float)
            assert start_time > 0
    
    def test_yields_start_time(self):
        """Test that context manager yields start time."""
        before = time.monotonic()
        
        with time_block() as start_time:
            after = time.monotonic()
            
            # Start time should be between before and after
            assert before <= start_time <= after
    
    def test_timing_measurement(self):
        """Test that elapsed time can be measured."""
        sleep_duration = 0.01  # 10ms
        
        with time_block() as start_time:
            time.sleep(sleep_duration)
        
        elapsed = time.monotonic() - start_time
        
        # Should be approximately the sleep duration
        assert sleep_duration <= elapsed < sleep_duration + 0.01
    
    def test_with_name_parameter(self):
        """Test that name parameter is accepted."""
        # Should not raise any exceptions
        with time_block("test_operation") as start_time:
            assert isinstance(start_time, float)
    
    def test_exception_handling(self):
        """Test that exceptions don't break timing."""
        with pytest.raises(ValueError):
            with time_block() as start_time:
                assert isinstance(start_time, float)
                raise ValueError("Test exception")
    
    def test_minimal_overhead(self):
        """Test that context manager has minimal overhead."""
        # Time the context manager itself
        start = time.perf_counter()
        with time_block() as block_start:
            pass
        end = time.perf_counter()
        
        overhead = end - start
        
        # Should complete in well under 1ms
        assert overhead < 0.001


class TestLegacyFunctions:
    """Test suite for legacy compatibility functions."""
    
    def test_generate_timestamp(self):
        """Test legacy generate_timestamp function."""
        timestamp = generate_timestamp()
        assert isinstance(timestamp, float)
        
        # Should be reasonable Unix timestamp
        assert 1577836800 < timestamp < 4102444800  # 2020-2100
    
    def test_generate_monotonic_timestamp(self):
        """Test legacy generate_monotonic_timestamp function."""
        timestamp = generate_monotonic_timestamp()
        assert isinstance(timestamp, float)
        assert timestamp > 0
    
    def test_legacy_compatibility(self):
        """Test that legacy functions work as expected."""
        ts1 = generate_timestamp()
        ts2 = generate_timestamp()
        
        mono1 = generate_monotonic_timestamp()
        mono2 = generate_monotonic_timestamp()
        
        # Timestamps should be close
        assert abs(ts2 - ts1) < 1.0
        
        # Monotonic should increase
        assert mono2 >= mono1


class TestPerformance:
    """Basic performance sanity tests."""
    
    def test_timestamp_performance(self):
        """Test that timestamp functions are fast."""
        start = time.perf_counter()
        for _ in range(1000):
            now_ts_ms()
        elapsed = time.perf_counter() - start
        
        # Should complete 1000 calls in well under 1 second
        assert elapsed < 0.1
    
    def test_rfc3339_performance(self):
        """Test that RFC3339 formatting is reasonably fast."""
        start = time.perf_counter()
        for _ in range(100):
            now_rfc3339()
        elapsed = time.perf_counter() - start
        
        # Should complete 100 calls in reasonable time
        assert elapsed < 1.0
    
    def test_monotonic_performance(self):
        """Test that monotonic calls are fast."""
        start = time.perf_counter()
        for _ in range(1000):
            monotonic_ns()
        elapsed = time.perf_counter() - start
        
        # Should complete 1000 calls very quickly
        assert elapsed < 0.1 