"""
Real-Time Streaming Services for Phase 8
Server-Sent Events (SSE) and Analytics Dashboard
"""

from .analytics_dashboard import Metric, MetricSeries, RealTimeAnalytics, Timer
from .sse_endpoints import (
    emit_analytics_update,
    emit_notification,
    emit_pipeline_update,
    emit_search_result,
)
from .sse_endpoints import router as sse_router
from .sse_manager import SSEConnection, SSEEvent, SSEManager

__all__ = [
    # SSE Manager
    "SSEManager",
    "SSEEvent",
    "SSEConnection",
    # SSE Endpoints
    "sse_router",
    "emit_search_result",
    "emit_pipeline_update",
    "emit_analytics_update",
    "emit_notification",
    # Analytics Dashboard
    "RealTimeAnalytics",
    "Metric",
    "MetricSeries",
    "Timer",
]
