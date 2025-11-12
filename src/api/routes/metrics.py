"""
Metrics API Routes
Real-time metrics and monitoring endpoints for Phase 8 services
Version: v8.5.0
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from src.auth.dependencies import get_current_user, require_role
from src.auth.models import CurrentUser, UserRole
from src.services.analytics_service import get_analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/dashboard")
async def get_dashboard_metrics(
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER))
) -> Dict[str, Any]:
    """
    Get real-time dashboard metrics

    Requires: Admin or Manager role

    Returns:
        Dashboard metrics including active users, recent searches, cache hit rate, errors
    """
    try:
        analytics = get_analytics_service()
        metrics = await analytics.get_dashboard_metrics()

        return {
            "success": True,
            "data": metrics
        }

    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard metrics")


@router.get("/search")
async def get_search_metrics(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER))
) -> Dict[str, Any]:
    """
    Get search analytics

    Requires: Admin or Manager role

    Args:
        start_date: Optional start date filter (ISO format)
        end_date: Optional end date filter (ISO format)

    Returns:
        Search analytics including total searches, avg latency, top queries
    """
    try:
        analytics = get_analytics_service()

        # Parse dates
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        search_stats = await analytics.get_search_analytics(start, end)

        return {
            "success": True,
            "data": search_stats,
            "filters": {
                "start_date": start_date,
                "end_date": end_date
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Failed to get search analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get search analytics")


@router.get("/active-users")
async def get_active_users(
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER))
) -> Dict[str, Any]:
    """
    Get active users count

    Requires: Admin or Manager role

    Returns:
        Active users count
    """
    try:
        analytics = get_analytics_service()
        count = await analytics.get_active_users_count()

        return {
            "success": True,
            "data": {
                "active_users": count,
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Failed to get active users: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active users")


@router.post("/track/request")
async def track_request_metric(
    method: str,
    endpoint: str,
    status_code: int,
    duration: float,
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Track API request (internal use)

    Args:
        method: HTTP method
        endpoint: API endpoint
        status_code: Response status code
        duration: Request duration in seconds

    Returns:
        Success status
    """
    try:
        analytics = get_analytics_service()

        await analytics.track_request(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration=duration,
            user_id=current_user.id if current_user else None
        )

        return {"success": True}

    except Exception as e:
        logger.error(f"Failed to track request: {e}")
        return {"success": False, "error": str(e)}


@router.post("/track/search")
async def track_search_metric(
    query: str,
    query_type: str,
    results_count: int,
    latency: float,
    similarity_scores: Optional[List[float]] = None,
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Track search query (internal use)

    Args:
        query: Search query text
        query_type: Type of search (hybrid, vector, text)
        results_count: Number of results
        latency: Search latency in seconds
        similarity_scores: Optional similarity scores

    Returns:
        Success status
    """
    try:
        analytics = get_analytics_service()

        await analytics.track_search(
            query=query,
            query_type=query_type,
            results_count=results_count,
            latency=latency,
            similarity_scores=similarity_scores,
            user_id=current_user.id if current_user else None
        )

        return {"success": True}

    except Exception as e:
        logger.error(f"Failed to track search: {e}")
        return {"success": False, "error": str(e)}


@router.post("/track/error")
async def track_error_metric(
    error_type: str,
    severity: str,
    message: str,
    stacktrace: Optional[str] = None,
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Track error (internal use)

    Args:
        error_type: Type of error
        severity: Error severity (low, medium, high, critical)
        message: Error message
        stacktrace: Optional stack trace

    Returns:
        Success status
    """
    try:
        analytics = get_analytics_service()

        await analytics.track_error(
            error_type=error_type,
            severity=severity,
            message=message,
            stacktrace=stacktrace,
            user_id=current_user.id if current_user else None
        )

        return {"success": True}

    except Exception as e:
        logger.error(f"Failed to track error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/prometheus")
async def get_prometheus_metrics(
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN))
) -> str:
    """
    Get Prometheus metrics in text format

    Requires: Admin role

    Returns:
        Prometheus metrics in text format
    """
    try:
        from prometheus_client import generate_latest

        metrics = generate_latest()
        return metrics.decode('utf-8')

    except Exception as e:
        logger.error(f"Failed to get Prometheus metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Prometheus metrics")
