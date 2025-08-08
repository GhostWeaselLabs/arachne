from __future__ import annotations

# Thin forwarders to provider-backed context functions to avoid duplicate ContextVars.
from .providers import (  # noqa: F401
    generate_trace_id,
    get_span_id,
    get_trace_id,
    set_trace_id,
    start_span,
)
