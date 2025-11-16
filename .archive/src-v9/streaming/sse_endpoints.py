"""
FastAPI SSE Endpoints for Phase 8.1
REST API endpoints for Server-Sent Events
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from .sse_manager import SSEEvent, SSEManager

logger = logging.getLogger(__name__)

# Global SSE manager instance
sse_manager = SSEManager()

# Router for SSE endpoints
router = APIRouter(prefix="/api/v1/stream", tags=["streaming"])


@router.get("/subscribe")
async def subscribe_sse(
    channels: Optional[str] = Query(None, description="Comma-separated channel names"),
    client_id: Optional[str] = Query(None, description="Optional client ID"),
):
    """
    Subscribe to Server-Sent Events

    Channels:
    - search: Real-time search results
    - pipeline: Pipeline progress updates
    - analytics: Analytics dashboard updates
    - notifications: System notifications

    Example:
        ```javascript
        const eventSource = new EventSource('/api/v1/stream/subscribe?channels=search,analytics');

        eventSource.addEventListener('search_result', (event) => {
            const data = JSON.parse(event.data);
            console.log('Search result:', data);
        });

        eventSource.addEventListener('analytics_update', (event) => {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        });
        ```

    Returns:
        SSE stream
    """
    # Parse channels
    if channels:
        channel_list = [c.strip() for c in channels.split(",")]
    else:
        # Default: all channels
        channel_list = ["search", "pipeline", "analytics", "notifications"]

    async def event_generator():
        """Generate SSE events"""
        try:
            async for event in sse_manager.subscribe(client_id=client_id, channels=channel_list):
                yield event.format()
        except Exception as e:
            logger.error(f"SSE stream error: {e}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/stats")
async def get_sse_stats():
    """
    Get SSE manager statistics

    Returns:
        Statistics including active connections, channels, and events sent

    Example:
        ```bash
        curl http://localhost:8001/api/v1/stream/stats
        ```
    """
    return sse_manager.get_stats()


@router.get("/clients")
async def get_active_clients(channel: Optional[str] = Query(None, description="Filter by channel")):
    """
    Get active client IDs

    Args:
        channel: Optional channel filter

    Returns:
        List of active client IDs

    Example:
        ```bash
        # All clients
        curl http://localhost:8001/api/v1/stream/clients

        # Clients on 'search' channel
        curl http://localhost:8001/api/v1/stream/clients?channel=search
        ```
    """
    clients = sse_manager.get_active_clients(channel=channel)
    return {"channel": channel, "active_clients": len(clients), "client_ids": clients}


# Helper functions for emitting events


async def emit_search_result(query: str, result: dict):
    """
    Emit search result event

    Args:
        query: Search query
        result: Search result
    """
    await sse_manager.emit(
        channel="search",
        event="search_result",
        data={"query": query, "result": result, "timestamp": "now"},
    )


async def emit_pipeline_update(pipeline_id: str, stage: str, progress: float, message: str):
    """
    Emit pipeline progress update

    Args:
        pipeline_id: Pipeline run ID
        stage: Current stage
        progress: Progress percentage (0-100)
        message: Status message
    """
    await sse_manager.emit(
        channel="pipeline",
        event="pipeline_update",
        data={"pipeline_id": pipeline_id, "stage": stage, "progress": progress, "message": message},
    )


async def emit_analytics_update(metrics: dict):
    """
    Emit analytics dashboard update

    Args:
        metrics: Analytics metrics
    """
    await sse_manager.emit(channel="analytics", event="analytics_update", data=metrics)


async def emit_notification(level: str, message: str, details: Optional[dict] = None):
    """
    Emit system notification

    Args:
        level: Notification level (info, warning, error)
        message: Notification message
        details: Optional additional details
    """
    await sse_manager.emit(
        channel="notifications",
        event="notification",
        data={"level": level, "message": message, "details": details or {}},
    )
