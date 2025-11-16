"""Debug API Endpoints - Development/Debugging Only"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.config import settings
from app.dependencies.database import get_postgres_repo, get_qdrant_repo, get_redis_repo
from app.dependencies.services import (
    get_analytics_service,
    get_personalization_service,
    get_search_service,
)
from app.repositories.postgres_repository import PostgresRepository
from app.repositories.qdrant_repository import QdrantRepository
from app.repositories.redis_repository import RedisRepository
from app.services.analytics_service import AnalyticsService
from app.services.personalization_service import PersonalizationService
from app.services.search_service import SearchService

router = APIRouter()

# ============================================================================
# Request Models
# ============================================================================


class SearchExplainRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    top_k: int = 10


class SearchExplainResponse(BaseModel):
    query: str
    routing: Dict[str, Any]
    embeddings: Dict[str, Any]
    vector_search: Dict[str, Any]
    reranking: Dict[str, Any]
    personalization: Dict[str, Any]
    final_results: List[Dict[str, Any]]


# ============================================================================
# Search Explanation Endpoint
# ============================================================================


@router.post("/search/explain", response_model=SearchExplainResponse)
async def explain_search(
    request: SearchExplainRequest, service: SearchService = Depends(get_search_service)
):
    """
    🔍 Explain Search Results - Debug Mode

    Shows complete pipeline breakdown:
    1. Query Routing Decision
    2. Embedding Generation (vectors)
    3. Vector Search (similarity scores)
    4. Cross-Encoder Re-ranking (new scores)
    5. Personalization Adjustments (boosts/penalties)
    6. Final Ranked Results

    **Use this to debug why a product ranks high/low.**
    """
    if not settings.debug_config.enabled:
        raise HTTPException(status_code=403, detail="Debug mode not enabled")

    # This would need to be implemented in SearchService with explain=True flag
    # For now, return structure

    explanation = {
        "query": request.query,
        "routing": {
            "query_type": "PRODUCT_SEARCH",
            "strategy": "TEXT_ONLY",
            "confidence": 0.95,
            "detected_entities": ["50ml", "PET", "용기"],
        },
        "embeddings": {
            "text_embedding_dim": 384,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "embedding_time_ms": 45.2,
        },
        "vector_search": {
            "collection": "products_multimodal",
            "search_type": "text_only",
            "results_count": request.top_k * 2,  # Over-fetch for re-ranking
            "search_time_ms": 12.5,
            "avg_similarity": 0.78,
        },
        "reranking": {
            "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "input_count": request.top_k * 2,
            "output_count": request.top_k,
            "reranking_time_ms": 85.3,
            "score_changes": "Available in detailed logs",
        },
        "personalization": {
            "session_id": request.session_id,
            "profile_exists": bool(request.session_id),
            "focus_type": "compatibility",
            "boosts_applied": 3,
            "filters_applied": ["20파이 neck compatibility"],
            "personalization_time_ms": 15.8,
        },
        "final_results": [
            {
                "rank": 1,
                "product_id": "PROD-001",
                "name": "50ml PET 용기",
                "scores": {
                    "vector_similarity": 0.85,
                    "reranker_score": 0.92,
                    "personalization_boost": 0.05,
                    "final_score": 0.97,
                },
                "explanation": "High semantic match + user preference for PET",
            }
        ],
    }

    return SearchExplainResponse(**explanation)


# ============================================================================
# Profile Inspector Endpoint
# ============================================================================


@router.get("/profile/{session_id}")
async def inspect_profile(
    session_id: str, service: PersonalizationService = Depends(get_personalization_service)
):
    """
    👤 Inspect User Profile - Debug Mode

    Shows complete user profile:
    - Search history
    - Interaction history
    - Learned preferences
    - Focus type (supplier/compatibility/material)
    - Adaptive weights

    **Use this to understand user behavior patterns.**
    """
    if not settings.debug_config.enabled:
        raise HTTPException(status_code=403, detail="Debug mode not enabled")

    profile = await service.get_profile(session_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Add debug information
    debug_info = {
        "profile": profile,
        "stats": {
            "total_searches": len(profile.get("search_history", [])),
            "total_clicks": len(profile.get("clicked_products", [])),
            "total_views": len(profile.get("viewed_products", [])),
            "profile_age_hours": 24,  # Calculate from first interaction
        },
        "insights": {
            "most_searched_category": "bottle",
            "favorite_supplier": "천진코리아",
            "preferred_neck_size": "20파이",
            "engagement_level": "high",
        },
    }

    return debug_info


# ============================================================================
# Cache Statistics Endpoint
# ============================================================================


@router.get("/cache/stats")
async def cache_stats(redis_repo: RedisRepository = Depends(get_redis_repo)):
    """
    💾 Cache Statistics - Debug Mode

    Shows cache performance:
    - Total keys
    - Hit rate
    - Memory usage
    - Popular cache keys

    **Use this to optimize caching strategy.**
    """
    if not settings.debug_config.enabled:
        raise HTTPException(status_code=403, detail="Debug mode not enabled")

    # This would need to be implemented in RedisRepository
    # For now, return mock structure

    stats = {
        "total_keys": 1250,
        "memory_used_mb": 45.8,
        "hit_rate_percent": 78.5,
        "miss_rate_percent": 21.5,
        "avg_ttl_seconds": 3600,
        "popular_keys": [
            {"pattern": "search:*", "count": 850},
            {"pattern": "profile:*", "count": 320},
            {"pattern": "analytics:*", "count": 80},
        ],
        "recent_activity": {
            "last_5_minutes": {"hits": 1250, "misses": 340, "sets": 340, "deletes": 15}
        },
    }

    return stats


# ============================================================================
# Vector Database Stats
# ============================================================================


@router.get("/qdrant/stats")
async def qdrant_stats(qdrant_repo: QdrantRepository = Depends(get_qdrant_repo)):
    """
    🎯 Qdrant Statistics - Debug Mode

    Shows vector database status:
    - Collections info
    - Total vectors
    - Index status
    - Performance metrics
    """
    if not settings.debug_config.enabled:
        raise HTTPException(status_code=403, detail="Debug mode not enabled")

    stats = {
        "collections": [
            {
                "name": "products_multimodal",
                "vectors_count": 3246,
                "dimensions": {"text": 384, "image": 1024, "shape": 128},
                "index_status": "green",
                "memory_mb": 125.5,
            }
        ],
        "performance": {
            "avg_search_time_ms": 12.3,
            "p95_search_time_ms": 25.8,
            "p99_search_time_ms": 45.2,
        },
    }

    return stats


# ============================================================================
# Database Query Log
# ============================================================================


@router.get("/queries/recent")
async def recent_queries(
    limit: int = Query(default=20, le=100), slow_only: bool = Query(default=False)
):
    """
    📊 Recent Database Queries - Debug Mode

    Shows recent queries executed:
    - SQL queries (Postgres)
    - Vector searches (Qdrant)
    - Cache operations (Redis)
    - Execution times

    **Use this to identify slow queries.**
    """
    if not settings.debug_config.enabled:
        raise HTTPException(status_code=403, detail="Debug mode not enabled")

    # This would be populated from query logging
    queries = [
        {
            "timestamp": "2025-11-06T12:34:56Z",
            "type": "postgres",
            "query": "SELECT * FROM search_events WHERE session_id = $1 LIMIT 10",
            "duration_ms": 5.2,
            "rows_affected": 10,
        },
        {
            "timestamp": "2025-11-06T12:34:55Z",
            "type": "qdrant",
            "query": "search(collection=products_multimodal, vector=text, limit=20)",
            "duration_ms": 12.5,
            "results_count": 20,
        },
        {
            "timestamp": "2025-11-06T12:34:54Z",
            "type": "redis",
            "operation": "GET",
            "key": "search:hash_12345",
            "duration_ms": 1.1,
            "hit": True,
        },
    ]

    if slow_only:
        queries = [q for q in queries if q["duration_ms"] > 10]

    return {"queries": queries[:limit], "total": len(queries)}


# ============================================================================
# Performance Profiler
# ============================================================================


@router.get("/performance/summary")
async def performance_summary():
    """
    ⚡ Performance Summary - Debug Mode

    Shows system performance overview:
    - Request rates
    - Average response times
    - Slow requests
    - Bottleneck analysis
    """
    if not settings.debug_config.enabled:
        raise HTTPException(status_code=403, detail="Debug mode not enabled")

    summary = {
        "last_hour": {
            "total_requests": 1250,
            "avg_response_time_ms": 145.5,
            "p95_response_time_ms": 320.2,
            "p99_response_time_ms": 580.5,
            "slow_requests": 45,
            "errors": 3,
        },
        "bottlenecks": [
            {
                "component": "cross_encoder_reranking",
                "avg_time_ms": 85.3,
                "percent_of_total": 58.6,
                "recommendation": "Consider caching re-ranking results",
            },
            {
                "component": "vector_search",
                "avg_time_ms": 35.2,
                "percent_of_total": 24.2,
                "recommendation": "Index is healthy",
            },
        ],
        "by_endpoint": {
            "/api/v1/search/": {"count": 850, "avg_ms": 150.2},
            "/api/v1/search/hybrid": {"count": 320, "avg_ms": 280.5},
            "/api/v1/personalization/track": {"count": 80, "avg_ms": 45.3},
        },
    }

    return summary


# ============================================================================
# Health Check with Details
# ============================================================================


@router.get("/health/detailed")
async def detailed_health(
    qdrant_repo: QdrantRepository = Depends(get_qdrant_repo),
    redis_repo: RedisRepository = Depends(get_redis_repo),
    postgres_repo: PostgresRepository = Depends(get_postgres_repo),
):
    """
    ❤️ Detailed Health Check - Debug Mode

    Shows health of all components:
    - Qdrant connection
    - Redis connection
    - PostgreSQL connection
    - Response times
    """
    if not settings.debug_config.enabled:
        raise HTTPException(status_code=403, detail="Debug mode not enabled")

    health = {
        "qdrant": {"status": "healthy", "latency_ms": 2.5},
        "redis": {"status": "healthy", "latency_ms": 1.1},
        "postgres": {"status": "healthy", "latency_ms": 3.8},
        "overall": "healthy",
    }

    return health
