"""
Analytics API Endpoints (v6.0.0)
=================================

Real-time analytics query endpoints powered by ClickHouse OLAP.

Endpoints:
- GET /analytics/stats - Overall statistics
- GET /analytics/queries/top - Most popular queries
- GET /analytics/queries/trend - Hourly search trend
- GET /analytics/performance/strategy - Performance by strategy
- POST /analytics/track/search - Track search event
- POST /analytics/track/event - Track user event

Version: v6.0.0
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.clickhouse_client import get_clickhouse_client
from app.services.analytics_pipeline import track_search, track_user_event, track_performance

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class SearchTrackRequest(BaseModel):
    """Request to track a search event"""

    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    query: str = Field(..., description="Search query")
    results_count: int = Field(..., description="Number of results returned")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    search_strategy: str = Field(default="dense", description="Search strategy used")
    filters: str = Field(default="", description="Filters applied (JSON string)")
    top_k: int = Field(default=10, description="Top-K results requested")
    cache_hit: bool = Field(default=False, description="Whether cache was hit")


class UserEventTrackRequest(BaseModel):
    """Request to track a user event"""

    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    event_type: str = Field(..., description="Event type (click, session_start, etc.)")
    event_data: str = Field(default="", description="Event data (JSON string)")
    product_id: str = Field(default="", description="Product ID (if applicable)")
    query: str = Field(default="", description="Associated query (if applicable)")


class SearchStats(BaseModel):
    """Search statistics response"""

    total_searches: int
    avg_response_time: float
    cache_hit_rate: float
    avg_results_count: float
    unique_sessions: int
    unique_queries: int


class QueryStats(BaseModel):
    """Query statistics"""

    query: str
    search_count: int
    avg_response_time: float
    avg_results: float


class HourlyTrend(BaseModel):
    """Hourly trend data"""

    hour: str
    searches: int
    avg_response_time: float


class StrategyPerformance(BaseModel):
    """Performance by strategy"""

    strategy: str
    count: int
    avg_response_time: float
    p95_response_time: float


# ============================================================================
# Query Endpoints
# ============================================================================


@router.get(
    "/stats",
    response_model=SearchStats,
    summary="Get overall search statistics",
    description="Get search statistics for last N hours",
)
async def get_search_stats(
    hours: int = Query(default=24, ge=1, le=168, description="Time window in hours (1-168)")
) -> SearchStats:
    """
    Get overall search statistics

    Returns:
    - total_searches: Total number of searches
    - avg_response_time: Average response time (ms)
    - cache_hit_rate: Cache hit rate (0-1)
    - avg_results_count: Average number of results
    - unique_sessions: Number of unique sessions
    - unique_queries: Number of unique queries
    """
    try:
        client = get_clickhouse_client()
        stats = client.get_search_stats(hours=hours)
        return SearchStats(**stats)
    except Exception as e:
        logger.error(f"Failed to get search stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get(
    "/queries/top",
    response_model=List[QueryStats],
    summary="Get most popular queries",
    description="Get top queries by search count",
)
async def get_top_queries(
    hours: int = Query(default=24, ge=1, le=168, description="Time window in hours"),
    limit: int = Query(default=10, ge=1, le=100, description="Number of queries to return"),
) -> List[QueryStats]:
    """
    Get most popular queries

    Returns list of queries sorted by search count with:
    - query: Search query text
    - search_count: Number of times searched
    - avg_response_time: Average response time (ms)
    - avg_results: Average number of results
    """
    try:
        client = get_clickhouse_client()
        queries = client.get_top_queries(hours=hours, limit=limit)
        return [QueryStats(**q) for q in queries]
    except Exception as e:
        logger.error(f"Failed to get top queries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get queries: {str(e)}")


@router.get(
    "/queries/trend",
    response_model=List[HourlyTrend],
    summary="Get hourly search trend",
    description="Get search volume trend by hour",
)
async def get_hourly_trend(
    hours: int = Query(default=24, ge=1, le=168, description="Time window in hours")
) -> List[HourlyTrend]:
    """
    Get hourly search volume trend

    Returns list of hourly data points with:
    - hour: Hour timestamp (YYYY-MM-DD HH:00)
    - searches: Number of searches in that hour
    - avg_response_time: Average response time (ms)
    """
    try:
        client = get_clickhouse_client()
        trend = client.get_hourly_search_trend(hours=hours)
        return [HourlyTrend(**t) for t in trend]
    except Exception as e:
        logger.error(f"Failed to get hourly trend: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trend: {str(e)}")


@router.get(
    "/performance/strategy",
    response_model=List[StrategyPerformance],
    summary="Get performance by search strategy",
    description="Get performance metrics grouped by search strategy",
)
async def get_performance_by_strategy(
    hours: int = Query(default=24, ge=1, le=168, description="Time window in hours")
) -> List[StrategyPerformance]:
    """
    Get performance metrics by search strategy

    Returns list of strategies with:
    - strategy: Search strategy name (dense, hybrid, hybrid+rerank)
    - count: Number of searches using this strategy
    - avg_response_time: Average response time (ms)
    - p95_response_time: 95th percentile response time (ms)
    """
    try:
        client = get_clickhouse_client()
        performance = client.get_performance_by_strategy(hours=hours)
        return [StrategyPerformance(**p) for p in performance]
    except Exception as e:
        logger.error(f"Failed to get performance by strategy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance: {str(e)}")


# ============================================================================
# Tracking Endpoints
# ============================================================================


@router.post(
    "/track/search",
    summary="Track a search event",
    description="Publish search event to analytics pipeline",
    status_code=202,
)
async def track_search_event(request: SearchTrackRequest) -> Dict[str, str]:
    """
    Track a search event

    This is an async operation that publishes to Kafka.
    The event will be processed asynchronously and stored in ClickHouse.

    Returns:
    - status: "queued" (event accepted for processing)
    """
    try:
        track_search(
            session_id=request.session_id,
            user_id=request.user_id,
            query=request.query,
            results_count=request.results_count,
            response_time_ms=request.response_time_ms,
            search_strategy=request.search_strategy,
            filters=request.filters,
            top_k=request.top_k,
            cache_hit=request.cache_hit,
        )
        return {"status": "queued"}
    except Exception as e:
        logger.error(f"Failed to track search: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track: {str(e)}")


@router.post(
    "/track/event",
    summary="Track a user event",
    description="Publish user event to analytics pipeline",
    status_code=202,
)
async def track_user_event_endpoint(request: UserEventTrackRequest) -> Dict[str, str]:
    """
    Track a user event

    This is an async operation that publishes to Kafka.
    The event will be processed asynchronously and stored in ClickHouse.

    Supported event types:
    - product_click: User clicked on a product
    - session_start: User started a session
    - session_end: User ended a session
    - search_refinement: User refined their search

    Returns:
    - status: "queued" (event accepted for processing)
    """
    try:
        track_user_event(
            session_id=request.session_id,
            user_id=request.user_id,
            event_type=request.event_type,
            event_data=request.event_data,
            product_id=request.product_id,
            query=request.query,
        )
        return {"status": "queued"}
    except Exception as e:
        logger.error(f"Failed to track event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track: {str(e)}")


@router.get(
    "/health",
    summary="Check analytics health",
    description="Check if analytics infrastructure is available",
)
async def check_analytics_health() -> Dict[str, Any]:
    """
    Check analytics infrastructure health

    Returns:
    - clickhouse: ClickHouse availability
    - kafka: Kafka availability
    - status: overall or degraded
    """
    client = get_clickhouse_client()
    clickhouse_available = client.client is not None

    from app.services.analytics_pipeline import get_analytics_producer
    producer = get_analytics_producer()
    kafka_available = producer.producer is not None

    status = "healthy" if (clickhouse_available and kafka_available) else "degraded"

    return {
        "status": status,
        "clickhouse": "available" if clickhouse_available else "unavailable",
        "kafka": "available" if kafka_available else "unavailable",
        "message": (
            "Analytics fully operational"
            if status == "healthy"
            else "Analytics running in degraded mode (using mock data)"
        ),
    }


# ============================================================================
# Export Router
# ============================================================================

__all__ = ["router"]
