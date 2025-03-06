import structlog
from typing import Optional

TRACE_ID_CONTEXT_KEY = "pantheon_trace_id"
TRACE_ID_HEADER_KEY = "pantheon-trace-id"


def get_trace_id() -> Optional[str]:
    """
    Get the current trace ID from the context.

    Returns:
        Optional[str]: The trace ID if available, None otherwise
    """
    context_vars = structlog.contextvars.get_contextvars()
    return context_vars.get(TRACE_ID_CONTEXT_KEY)
