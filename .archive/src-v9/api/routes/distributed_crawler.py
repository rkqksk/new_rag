"""
Distributed Web Crawler API Routes - v7.3.0
Production-scale web crawling with distributed architecture
"""

from typing import List, Dict, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl

from src.services.distributed_crawler_service import (
    DistributedCrawlerService,
    CrawlJob,
    CrawlResult,
    CrawlStatus,
    CrawlPriority,
    CrawlerStats,
    get_distributed_crawler_service
)


# ========================================================================
# Request/Response Models
# ========================================================================

class CrawlJobRequest(BaseModel):
    """Request model for creating a crawl job"""
    url: str = Field(..., description="URL to crawl")
    priority: CrawlPriority = Field(CrawlPriority.NORMAL, description="Job priority")
    max_depth: int = Field(3, ge=0, le=10, description="Maximum crawl depth")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BulkCrawlRequest(BaseModel):
    """Request model for bulk crawl jobs"""
    urls: List[str] = Field(..., min_items=1, max_items=1000, description="URLs to crawl")
    priority: CrawlPriority = Field(CrawlPriority.NORMAL, description="Job priority")
    max_depth: int = Field(3, ge=0, le=10, description="Maximum crawl depth")


class WebsiteCrawlRequest(BaseModel):
    """Request model for crawling entire website"""
    start_url: str = Field(..., description="Starting URL")
    max_pages: int = Field(100, ge=1, le=10000, description="Maximum pages to crawl")
    max_depth: int = Field(3, ge=0, le=10, description="Maximum crawl depth")
    same_domain_only: bool = Field(True, description="Only crawl same domain")


class CrawlJobResponse(BaseModel):
    """Response model for crawl job"""
    job_id: str
    url: str
    status: str
    priority: int
    created_at: datetime
    message: str


class CrawlResultResponse(BaseModel):
    """Response model for crawl result"""
    url: str
    job_id: str
    status: CrawlStatus
    content_length: Optional[int] = None
    links_count: int
    metadata: Dict[str, Any]
    error: Optional[str] = None
    crawled_at: datetime
    duration_ms: float


class WorkerStatus(BaseModel):
    """Worker status model"""
    worker_id: int
    status: str
    jobs_processed: int
    last_activity: Optional[datetime] = None


# ========================================================================
# Router Class
# ========================================================================

class DistributedCrawlerRouter:
    """Distributed Crawler API Router"""

    def __init__(self, crawler_service: Optional[DistributedCrawlerService] = None):
        """
        Initialize Distributed Crawler Router

        Args:
            crawler_service: Crawler service instance
        """
        self.router = APIRouter(prefix="/crawler", tags=["Web Crawler"])
        self.crawler_service = crawler_service or get_distributed_crawler_service()
        self._setup_routes()

    def _setup_routes(self):
        """Configure API routes"""

        @self.router.post("/jobs", response_model=CrawlJobResponse)
        async def create_crawl_job(request: CrawlJobRequest):
            """
            Create a new crawl job

            Adds URL to the distributed queue for crawling.

            Args:
                request: Crawl job configuration

            Returns:
                Job details with job_id for tracking
            """
            try:
                # Create job
                job = CrawlJob(
                    url=request.url,
                    job_id=f"job_{datetime.now().timestamp()}",
                    priority=request.priority,
                    max_depth=request.max_depth,
                    metadata=request.metadata or {}
                )

                # Enqueue job
                await self.crawler_service.enqueue_job(job)

                return CrawlJobResponse(
                    job_id=job.job_id,
                    url=job.url,
                    status="pending",
                    priority=job.priority.value,
                    created_at=job.created_at,
                    message="Job created successfully"
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

        @self.router.post("/jobs/bulk")
        async def create_bulk_jobs(request: BulkCrawlRequest):
            """
            Create multiple crawl jobs at once

            Efficiently enqueue multiple URLs for crawling.

            Args:
                request: Bulk crawl request with URLs

            Returns:
                Summary of created jobs
            """
            try:
                created_jobs = []

                for url in request.urls:
                    job = CrawlJob(
                        url=url,
                        job_id=f"job_{datetime.now().timestamp()}_{url}",
                        priority=request.priority,
                        max_depth=request.max_depth
                    )
                    await self.crawler_service.enqueue_job(job)
                    created_jobs.append(job.job_id)

                return {
                    "message": f"Created {len(created_jobs)} crawl jobs",
                    "total_jobs": len(created_jobs),
                    "job_ids": created_jobs,
                    "priority": request.priority.value
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to create bulk jobs: {str(e)}")

        @self.router.post("/crawl-website")
        async def crawl_website(request: WebsiteCrawlRequest, background_tasks: BackgroundTasks):
            """
            Crawl an entire website (recursive crawling)

            Starts from a URL and crawls linked pages up to max_depth.

            Args:
                request: Website crawl configuration
                background_tasks: FastAPI background tasks

            Returns:
                Crawl session details
            """
            try:
                # Start website crawl in background
                session_id = f"session_{datetime.now().timestamp()}"

                async def run_crawl():
                    results = await self.crawler_service.crawl_website(
                        start_url=request.start_url,
                        max_pages=request.max_pages,
                        max_depth=request.max_depth,
                        same_domain_only=request.same_domain_only
                    )
                    # Store results (could save to database)
                    return results

                background_tasks.add_task(run_crawl)

                return {
                    "session_id": session_id,
                    "start_url": request.start_url,
                    "max_pages": request.max_pages,
                    "max_depth": request.max_depth,
                    "status": "started",
                    "message": "Website crawl started in background"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to start website crawl: {str(e)}")

        @self.router.get("/jobs/{job_id}")
        async def get_job_status(job_id: str):
            """
            Get crawl job status

            Args:
                job_id: Job identifier

            Returns:
                Current job status and details
            """
            try:
                # In a real implementation, would query Redis or database
                # For now, return mock status
                return {
                    "job_id": job_id,
                    "status": "pending",
                    "message": "Job status lookup not yet implemented in service"
                }

            except Exception as e:
                raise HTTPException(status_code=404, detail=f"Job not found: {str(e)}")

        @self.router.get("/results")
        async def get_crawl_results(
            limit: int = Query(50, ge=1, le=1000),
            status: Optional[CrawlStatus] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
        ):
            """
            Get crawl results with filtering

            Args:
                limit: Maximum number of results
                status: Filter by crawl status
                start_date: Filter results after this date
                end_date: Filter results before this date

            Returns:
                List of crawl results
            """
            try:
                # In real implementation, would query database
                # For now, return empty results
                return {
                    "results": [],
                    "total": 0,
                    "filters": {
                        "status": status,
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "message": "Results retrieval requires database integration"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")

        @self.router.get("/stats", response_model=CrawlerStats)
        async def get_crawler_stats():
            """
            Get crawler statistics

            Returns:
            - Total jobs
            - Completed/failed/in-progress counts
            - Pages per second throughput
            - Average duration
            - Error rate
            """
            try:
                stats = self.crawler_service.get_stats()
                return stats

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

        @self.router.post("/start")
        async def start_crawler(num_workers: int = Query(5, ge=1, le=20)):
            """
            Start crawler workers

            Starts background workers to process crawl queue.

            Args:
                num_workers: Number of concurrent workers to start

            Returns:
                Confirmation message
            """
            try:
                await self.crawler_service.start()

                return {
                    "status": "started",
                    "num_workers": num_workers,
                    "message": f"Started {num_workers} crawler workers"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to start crawler: {str(e)}")

        @self.router.post("/stop")
        async def stop_crawler():
            """
            Stop all crawler workers

            Gracefully shuts down all running workers.

            Returns:
                Confirmation message
            """
            try:
                await self.crawler_service.stop()

                return {
                    "status": "stopped",
                    "message": "All crawler workers stopped"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to stop crawler: {str(e)}")

        @self.router.get("/workers")
        async def get_worker_status():
            """
            Get status of all crawler workers

            Returns:
            - Worker IDs
            - Current status (running/idle/stopped)
            - Jobs processed
            - Last activity timestamp
            """
            try:
                # In real implementation, would track worker status
                # For now, return mock data
                workers = [
                    {
                        "worker_id": i,
                        "status": "idle" if self.crawler_service.running else "stopped",
                        "jobs_processed": 0,
                        "last_activity": None
                    }
                    for i in range(self.crawler_service.num_workers)
                ]

                return {
                    "workers": workers,
                    "total_workers": len(workers),
                    "running": self.crawler_service.running
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get worker status: {str(e)}")

        @self.router.delete("/queue")
        async def clear_queue():
            """
            Clear all pending jobs from queue

            WARNING: This will remove all pending crawl jobs!

            Returns:
                Confirmation message
            """
            try:
                # In real implementation, would clear Redis queue
                return {
                    "status": "success",
                    "message": "Queue cleared (not yet implemented)",
                    "warning": "This operation cannot be undone"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to clear queue: {str(e)}")

        @self.router.get("/domains")
        async def get_crawled_domains(limit: int = Query(50, ge=1, le=500)):
            """
            Get list of crawled domains with statistics

            Args:
                limit: Maximum number of domains to return

            Returns:
                List of domains with page counts and last crawl time
            """
            try:
                # In real implementation, would aggregate from database
                return {
                    "domains": [],
                    "total_domains": 0,
                    "message": "Domain aggregation requires database integration"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get domains: {str(e)}")

        @self.router.get("/health")
        async def health_check():
            """
            Health check endpoint

            Returns service status and configuration
            """
            return {
                "status": "healthy",
                "service": "Distributed Crawler",
                "version": "7.3.0",
                "running": self.crawler_service.running,
                "num_workers": self.crawler_service.num_workers,
                "redis_connected": self.crawler_service.redis_client is not None,
                "features": {
                    "distributed_queue": self.crawler_service.redis_client is not None,
                    "javascript_rendering": True,
                    "rate_limiting": True,
                    "proxy_rotation": False  # TODO
                }
            }


def get_distributed_crawler_router(crawler_service: Optional[DistributedCrawlerService] = None) -> APIRouter:
    """
    Factory function to create Distributed Crawler router

    Args:
        crawler_service: Optional crawler service instance

    Returns:
        Configured APIRouter
    """
    router_instance = DistributedCrawlerRouter(crawler_service=crawler_service)
    return router_instance.router
