"""Analytics API Endpoints - Complete Implementation"""

from fastapi import APIRouter, Depends

from apps.api.dependencies.services import get_analytics_service
from apps.api.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/keywords")
async def get_top_keywords(
    limit: int = 20, service: AnalyticsService = Depends(get_analytics_service)
):
    """Get top searched keywords"""
    keywords = await service.get_top_keywords(limit=limit)
    return {"keywords": keywords, "total": len(keywords)}


@router.get("/trending")
async def get_trending_queries(
    limit: int = 10, service: AnalyticsService = Depends(get_analytics_service)
):
    """Get trending search queries"""
    queries = await service.get_trending_queries(limit=limit)
    return {"queries": queries, "total": len(queries)}


@router.get("/products/popular")
async def get_popular_products(
    limit: int = 20,
    metric: str = "click",
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get popular products"""
    products = await service.get_top_products(limit=limit, metric=metric)
    return {"products": products, "total": len(products)}


@router.get("/summary")
async def get_analytics_summary(service: AnalyticsService = Depends(get_analytics_service)):
    """Get comprehensive analytics summary"""
    summary = await service.get_analytics_summary()
    return summary


@router.get("/patterns")
async def get_search_patterns(
    limit: int = 20, service: AnalyticsService = Depends(get_analytics_service)
):
    """Get common search patterns"""
    patterns = await service.get_search_patterns(limit=limit)
    return {"patterns": patterns, "total": len(patterns)}
