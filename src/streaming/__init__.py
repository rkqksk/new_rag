"""
Real-Time Streaming Services for Phase 8
Server-Sent Events (SSE) and Analytics Dashboard
"""

from .sse_manager import SSEManager, SSEEvent, SSEConnection
from .sse_endpoints import (
    router as sse_router,
    emit_search_result,
    emit_pipeline_update,
    emit_analytics_update,
    emit_notification
)
from .analytics_dashboard import (
    RealTimeAnalytics,
    Metric,
    MetricSeries,
    Timer
)

__all__ = [
    # SSE Manager
    'SSEManager',
    'SSEEvent',
    'SSEConnection',

    # SSE Endpoints
    'sse_router',
    'emit_search_result',
    'emit_pipeline_update',
    'emit_analytics_update',
    'emit_notification',

    # Analytics Dashboard
    'RealTimeAnalytics',
    'Metric',
    'MetricSeries',
    'Timer',
]
