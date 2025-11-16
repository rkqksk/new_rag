"""
대시보드 라우트 - 모니터링 및 관리 API
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["dashboard"],
)

# Global references (set from main.py)
document_ingestion_service = None
web_crawler_service = None
qdrant_client = None
redis_client = None


@router.get("/stats")
async def get_dashboard_stats() -> Dict[str, Any]:
    """시스템 전체 통계 조회"""
    try:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "documents": {"total": 0, "formats": {}},
            "vectors": {"total": 0, "dimension": 384},
            "crawlers": {"total_sources": 0, "active": 0},
            "system": {"qdrant": "checking", "redis": "checking", "cache_size": 0},
        }

        # Qdrant stats
        try:
            collections = qdrant_client.get_collections()
            if hasattr(collections, "collections") and len(collections.collections) > 0:
                collection = qdrant_client.get_collection("documents")
                stats["vectors"]["total"] = (
                    collection.vectors_count if hasattr(collection, "vectors_count") else 0
                )
            stats["system"]["qdrant"] = "healthy"
        except Exception as e:
            logger.error(f"Qdrant check error: {e}")
            stats["system"]["qdrant"] = "error"

        # Redis stats
        try:
            redis_client.ping()
            stats["system"]["redis"] = "healthy"
            # Get cache size
            info = redis_client.info()
            stats["system"]["cache_size"] = info.get("used_memory", 0)
        except Exception as e:
            logger.error(f"Redis check error: {e}")
            stats["system"]["redis"] = "error"

        return stats
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def get_documents(
    limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """문서 목록 조회"""
    try:
        # Qdrant에서 points 가져오기
        collection = qdrant_client.get_collection("documents")
        total = collection.vectors_count if hasattr(collection, "vectors_count") else 0

        # 최근 문서 조회
        results = qdrant_client.scroll(collection_name="documents", limit=limit, offset=offset)

        documents = []
        if hasattr(results, "points"):
            seen_docs = set()
            for point in results.points:
                if hasattr(point, "payload"):
                    doc_id = point.payload.get("doc_id", "")
                    if doc_id not in seen_docs:
                        seen_docs.add(doc_id)
                        documents.append(
                            {
                                "doc_id": doc_id,
                                "filename": point.payload.get("filename", "unknown"),
                                "chunks": 1,
                                "created_at": point.payload.get("upload_time", ""),
                                "status": "processed",
                            }
                        )

        return {"total": total, "limit": limit, "offset": offset, "documents": documents[:limit]}
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search-stats")
async def get_search_stats(
    limit: int = Query(50, ge=1, le=500), hours_back: int = Query(24, ge=1, le=720)
) -> Dict[str, Any]:
    """최근 검색 통계"""
    try:
        return {
            "total_searches": 0,
            "average_latency_ms": 0,
            "top_queries": [],
            "recent_searches": [],
        }
    except Exception as e:
        logger.error(f"Error getting search stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """성능 메트릭"""
    try:
        return {
            "embedding_latency_ms": 0.0,
            "search_latency_ms": 0.0,
            "cache_hit_rate": 0.0,
            "memory_usage_mb": 0.0,
            "cpu_usage_percent": 0.0,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crawlers")
async def get_crawlers() -> Dict[str, Any]:
    """크롤러 상태"""
    try:
        if web_crawler_service:
            sources = web_crawler_service.get_sources_status()
            return {"total": len(sources), "sources": sources}
        return {"total": 0, "sources": []}
    except Exception as e:
        logger.error(f"Error getting crawlers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/{doc_id}/delete")
async def delete_document(doc_id: str) -> Dict[str, Any]:
    """문서 삭제"""
    try:
        # Qdrant에서 해당 문서의 모든 points 삭제
        deleted_count = qdrant_client.delete(
            collection_name="documents",
            points_selector={"filter": {"must": [{"field": "doc_id", "match": {"value": doc_id}}]}},
        )
        return {"status": "success", "deleted_chunks": deleted_count}
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache() -> Dict[str, Any]:
    """캐시 초기화"""
    try:
        redis_client.flushdb()
        return {"status": "success", "message": "Cache cleared"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def dashboard_health() -> Dict[str, Any]:
    """대시보드 헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {"api": "running", "qdrant": "running", "redis": "running"},
    }
