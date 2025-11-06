"""
Cache Monitoring API
캐시 성능 모니터링 엔드포인트

FastAPI 엔드포인트:
- GET /cache/stats - 캐시 통계
- POST /cache/clear - 캐시 초기화
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

# This would be imported from the main app
# from src.core.caching.cache_manager import CacheManager

router = APIRouter(prefix="/cache", tags=["cache"])

# Global cache instance (would be initialized in main app)
_cache_manager = None


def init_cache_monitor(cache_manager):
    """Initialize cache monitor with CacheManager instance"""
    global _cache_manager
    _cache_manager = cache_manager


@router.get("/stats", response_model=Dict[str, Any])
async def get_cache_stats():
    """
    캐시 통계 조회

    Returns:
        {
            "connected": bool,
            "total_keys": int,
            "memory_used": str,
            "hit_rate": float,
            "keyspace_hits": int,
            "keyspace_misses": int
        }
    """
    if _cache_manager is None:
        raise HTTPException(status_code=503, detail="Cache not initialized")

    return _cache_manager.get_stats()


@router.post("/clear")
async def clear_cache():
    """
    캐시 전체 삭제

    Returns:
        {"message": "Cache cleared successfully"}
    """
    if _cache_manager is None:
        raise HTTPException(status_code=503, detail="Cache not initialized")

    _cache_manager.clear_all()

    return {"message": "Cache cleared successfully"}


@router.get("/health")
async def cache_health():
    """
    캐시 헬스 체크

    Returns:
        {
            "status": "healthy" | "degraded" | "unavailable",
            "connected": bool,
            "message": str
        }
    """
    if _cache_manager is None:
        return {
            "status": "unavailable",
            "connected": False,
            "message": "Cache manager not initialized"
        }

    stats = _cache_manager.get_stats()

    if stats['connected']:
        return {
            "status": "healthy",
            "connected": True,
            "message": "Redis connected and operational"
        }
    else:
        return {
            "status": "degraded",
            "connected": False,
            "message": "Using in-memory fallback (Redis unavailable)"
        }


# Example integration in main app:
"""
from fastapi import FastAPI
from src.api.cache_monitor import router as cache_router, init_cache_monitor
from src.core.caching.cache_manager import CacheManager

app = FastAPI()

# Initialize cache
cache = CacheManager()
init_cache_monitor(cache)

# Include router
app.include_router(cache_router)
"""
