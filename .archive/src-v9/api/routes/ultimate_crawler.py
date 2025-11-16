"""
Ultimate Crawler API Routes - v7.4.0
Complete API for Ultimate Crawling System
"""

from typing import List, Dict, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl

from src.services.ultimate_crawler_service import (
    UltimateCrawlerService,
    ContentType,
    CrawlStatus,
    get_ultimate_crawler_service
)


# ========================================================================
# Request/Response Models
# ========================================================================

class UltimateCrawlRequest(BaseModel):
    """Request for ultimate crawl"""
    url: str = Field(..., description="URL to crawl")
    enable_incremental: bool = Field(True, description="Enable incremental crawling")
    enable_ai_extraction: bool = Field(True, description="Enable AI extraction")
    enable_quality_validation: bool = Field(True, description="Enable quality validation")
    quality_threshold: float = Field(70.0, ge=0, le=100, description="Quality threshold")


class BulkCrawlRequest(BaseModel):
    """Request for bulk crawling"""
    urls: List[str] = Field(..., min_items=1, max_items=1000, description="URLs to crawl")
    enable_incremental: bool = Field(True)
    quality_threshold: float = Field(70.0, ge=0, le=100)


class ScheduleResponse(BaseModel):
    """Response for schedule"""
    url: str
    priority: int
    estimated_change_freq: float
    next_scheduled: str
    importance_score: float


# ========================================================================
# Router
# ========================================================================

class UltimateCrawlerRouter:
    """Ultimate Crawler API Router"""

    def __init__(self, crawler_service: Optional[UltimateCrawlerService] = None):
        self.router = APIRouter(prefix="/ultimate-crawler", tags=["Ultimate Crawler"])
        self.crawler_service = crawler_service or get_ultimate_crawler_service()
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        @self.router.post("/crawl")
        async def ultimate_crawl(request: UltimateCrawlRequest):
            """
            Ultimate crawl with all features

            Features:
            - Incremental crawling (change detection)
            - AI content extraction
            - Quality validation
            - Smart scheduling
            - Anti-bot evasion
            """
            try:
                # Update service settings
                self.crawler_service.enable_incremental = request.enable_incremental
                self.crawler_service.enable_ai_extraction = request.enable_ai_extraction
                self.crawler_service.enable_quality_validation = request.enable_quality_validation
                self.crawler_service.quality_threshold = request.quality_threshold

                # Execute ultimate crawl
                result = await self.crawler_service.ultimate_crawl(request.url)

                return result

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Crawl failed: {str(e)}")

        @self.router.post("/bulk-crawl")
        async def bulk_crawl(request: BulkCrawlRequest, background_tasks: BackgroundTasks):
            """
            Bulk crawl multiple URLs

            Executes in background for large batches
            """
            try:
                async def process_bulk():
                    results = []
                    for url in request.urls:
                        result = await self.crawler_service.ultimate_crawl(url)
                        results.append(result)
                    return results

                # Run in background
                background_tasks.add_task(process_bulk)

                return {
                    "status": "started",
                    "total_urls": len(request.urls),
                    "message": "Bulk crawl started in background"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Bulk crawl failed: {str(e)}")

        @self.router.get("/crawl-state/{url:path}")
        async def get_crawl_state(url: str):
            """
            Get incremental crawl state for URL

            Returns:
            - Content hash
            - Last modified
            - Crawl count
            - Change frequency
            """
            try:
                state = self.crawler_service.crawl_states.get(url)
                if not state:
                    raise HTTPException(status_code=404, detail="No crawl state found")

                return {
                    "url": state.url,
                    "content_hash": state.content_hash,
                    "last_modified": state.last_modified.isoformat() if state.last_modified else None,
                    "etag": state.etag,
                    "crawl_count": state.crawl_count,
                    "last_change_detected": state.last_change_detected.isoformat() if state.last_change_detected else None,
                    "change_frequency": state.change_frequency
                }

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get crawl state: {str(e)}")

        @self.router.get("/schedule")
        async def get_smart_schedules(
            limit: int = Query(50, ge=1, le=500),
            priority_min: Optional[int] = Query(None, ge=1, le=10)
        ):
            """
            Get smart crawl schedules

            Returns optimized crawl schedules based on:
            - Content type
            - Historical change frequency
            - Priority
            """
            try:
                schedules = list(self.crawler_service.schedules.values())

                # Filter by priority
                if priority_min:
                    schedules = [s for s in schedules if s.priority >= priority_min]

                # Sort by next_scheduled
                schedules.sort(key=lambda x: x.next_scheduled)

                # Apply limit
                schedules = schedules[:limit]

                return {
                    "schedules": [
                        {
                            "url": s.url,
                            "priority": s.priority,
                            "estimated_change_freq": s.estimated_change_freq,
                            "last_crawl": s.last_crawl.isoformat(),
                            "next_scheduled": s.next_scheduled.isoformat(),
                            "importance_score": s.importance_score
                        }
                        for s in schedules
                    ],
                    "total": len(schedules)
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get schedules: {str(e)}")

        @self.router.get("/quality-report")
        async def get_quality_report(
            min_score: Optional[float] = Query(None, ge=0, le=100),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """
            Get quality report for crawled content

            Returns quality metrics for recent crawls
            """
            try:
                # This would typically query a database
                # For now, return summary stats
                stats = self.crawler_service.get_ultimate_stats()

                return {
                    "avg_quality_score": stats.get("avg_quality_score", 0.0),
                    "quality_failures": stats.get("quality_failures", 0),
                    "total_crawls": stats.get("total_crawls", 0),
                    "quality_failure_rate": (
                        stats["quality_failures"] / max(stats["total_crawls"], 1) * 100
                    )
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get quality report: {str(e)}")

        @self.router.get("/content-types")
        async def get_content_type_distribution():
            """
            Get distribution of detected content types

            Returns breakdown by:
            - Product
            - Article
            - News
            - Documentation
            - Forum
            - E-commerce
            - Unknown
            """
            try:
                # This would aggregate from database
                # Placeholder data
                return {
                    "distribution": {
                        "product": 35,
                        "article": 25,
                        "news": 15,
                        "documentation": 10,
                        "forum": 8,
                        "ecommerce": 5,
                        "unknown": 2
                    },
                    "total": 100
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get content types: {str(e)}")

        @self.router.get("/extracted-entities")
        async def get_extracted_entities(
            entity_type: Optional[str] = Query(None, description="Filter by entity type"),
            limit: int = Query(100, ge=1, le=1000)
        ):
            """
            Get extracted named entities

            Entity types:
            - EMAIL
            - PHONE
            - PRICE
            """
            try:
                # This would query from database
                # Placeholder response
                return {
                    "entities": [
                        {"type": "EMAIL", "value": "contact@example.com", "count": 5},
                        {"type": "PHONE", "value": "02-1234-5678", "count": 3},
                        {"type": "PRICE", "value": "₩50,000", "count": 10}
                    ],
                    "total": 18
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get entities: {str(e)}")

        @self.router.get("/change-detection")
        async def get_change_detection_stats():
            """
            Get change detection statistics

            Returns:
            - Incremental hits (unchanged content)
            - Content changes detected
            - Hit rate percentage
            """
            try:
                stats = self.crawler_service.get_ultimate_stats()

                return {
                    "incremental_hits": stats.get("incremental_hits", 0),
                    "content_changes": stats.get("content_changes", 0),
                    "incremental_hit_rate": stats.get("incremental_hit_rate", 0.0),
                    "total_crawls": stats.get("total_crawls", 0)
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get change stats: {str(e)}")

        @self.router.get("/anti-bot-stats")
        async def get_anti_bot_stats():
            """
            Get anti-bot statistics

            Returns:
            - Bot detection blocks
            - User agent rotations
            - Success rate
            """
            try:
                stats = self.crawler_service.get_ultimate_stats()

                return {
                    "anti_bot_blocks": stats.get("anti_bot_blocks", 0),
                    "total_crawls": stats.get("total_crawls", 0),
                    "block_rate": (
                        stats.get("anti_bot_blocks", 0) / max(stats.get("total_crawls", 1), 1) * 100
                    )
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get anti-bot stats: {str(e)}")

        @self.router.delete("/crawl-state/{url:path}")
        async def delete_crawl_state(url: str):
            """
            Delete crawl state for URL

            Forces fresh crawl on next request
            """
            try:
                if url in self.crawler_service.crawl_states:
                    del self.crawler_service.crawl_states[url]
                    return {"status": "deleted", "url": url}
                else:
                    raise HTTPException(status_code=404, detail="Crawl state not found")

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to delete state: {str(e)}")

        @self.router.delete("/schedule/{url:path}")
        async def delete_schedule(url: str):
            """
            Delete smart schedule for URL
            """
            try:
                if url in self.crawler_service.schedules:
                    del self.crawler_service.schedules[url]
                    return {"status": "deleted", "url": url}
                else:
                    raise HTTPException(status_code=404, detail="Schedule not found")

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to delete schedule: {str(e)}")

        @self.router.get("/stats")
        async def get_ultimate_stats():
            """
            Get comprehensive crawler statistics

            Returns:
            - Total crawls
            - Incremental hits
            - Content changes
            - Quality failures
            - Anti-bot blocks
            - Average quality score
            - Cache hit rate
            """
            try:
                stats = self.crawler_service.get_ultimate_stats()
                return stats

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

        @self.router.post("/clear-all")
        async def clear_all_state():
            """
            Clear all crawl state and schedules

            WARNING: This will force fresh crawls for all URLs
            """
            try:
                self.crawler_service.crawl_states.clear()
                self.crawler_service.schedules.clear()

                return {
                    "status": "cleared",
                    "message": "All crawl state and schedules cleared"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to clear state: {str(e)}")

        @self.router.get("/health")
        async def health_check():
            """
            Health check endpoint

            Returns service status and configuration
            """
            return {
                "status": "healthy",
                "service": "Ultimate Crawler",
                "version": "7.4.0",
                "features": {
                    "incremental_crawling": self.crawler_service.enable_incremental,
                    "ai_extraction": self.crawler_service.enable_ai_extraction,
                    "quality_validation": self.crawler_service.enable_quality_validation,
                    "smart_scheduling": self.crawler_service.enable_smart_scheduling
                },
                "stats": self.crawler_service.get_ultimate_stats()
            }


def get_ultimate_crawler_router(crawler_service: Optional[UltimateCrawlerService] = None) -> APIRouter:
    """
    Factory function to create Ultimate Crawler router

    Args:
        crawler_service: Optional crawler service instance

    Returns:
        Configured APIRouter
    """
    router_instance = UltimateCrawlerRouter(crawler_service=crawler_service)
    return router_instance.router
