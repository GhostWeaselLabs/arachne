from __future__ import annotations

# Thin forwarders to provider-backed context functions to avoid duplicate ContextVars.
from .providers import (  # noqa: F401
    start_span,
    set_trace_id,
    get_trace_id,
    get_span_id,
    generate_trace_id,
)
