"""
Hybrid Search API Endpoints (v6.0.0)
====================================

Endpoints for hybrid search combining dense vectors, sparse BM25, and re-ranking.

Features:
- Dense + Sparse fusion via Reciprocal Rank Fusion (RRF)
- Cross-encoder re-ranking for precision boost
- Configurable weights and parameters
- Performance metrics

Endpoints:
- POST /api/v1/hybrid/search - Hybrid search with configurable parameters
- GET  /api/v1/hybrid/health - Health check
"""

import logging
import time
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.hybrid_search import HybridSearchEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hybrid", tags=["hybrid-search"])

# Global hybrid search engine (singleton)
_hybrid_engine: Optional[HybridSearchEngine] = None


def get_hybrid_engine() -> HybridSearchEngine:
    """Get or create hybrid search engine"""
    global _hybrid_engine
    if _hybrid_engine is None:
        _hybrid_engine = HybridSearchEngine(
            cross_encoder_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            enable_cross_encoder=True,
            rrf_k=60,
        )
    return _hybrid_engine


# ============================================================================
# Request/Response Models
# ============================================================================


class HybridSearchRequest(BaseModel):
    """Hybrid search request"""

    query: str = Field(..., description="Search query", min_length=1)
    collections: Optional[List[str]] = Field(None, description="Collections to search")
    materials: Optional[List[str]] = Field(None, description="Material filters")
    top_k: int = Field(100, description="Number of results", ge=1, le=1000)
    dense_weight: float = Field(0.5, description="Weight for dense search", ge=0.0, le=1.0)
    sparse_weight: float = Field(0.5, description="Weight for sparse search", ge=0.0, le=1.0)
    enable_reranking: bool = Field(True, description="Enable cross-encoder re-ranking")


class HybridSearchResponse(BaseModel):
    """Hybrid search response"""

    query: str
    total_results: int
    results: List[Dict]
    search_strategy: str
    performance: Dict
    parameters: Dict


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/search", response_model=HybridSearchResponse)
async def hybrid_search(request: HybridSearchRequest):
    """
    Perform hybrid search combining dense vectors, sparse BM25, and re-ranking

    Pipeline:
    1. Dense vector search (Qdrant)
    2. Sparse keyword search (BM25)
    3. Reciprocal Rank Fusion (RRF)
    4. Cross-encoder re-ranking (optional)

    Args:
        request: Search parameters

    Returns:
        Hybrid search results with performance metrics
    """
    start_time = time.time()

    try:
        # Get hybrid search engine
        engine = get_hybrid_engine()

        # Step 1: Dense vector search (via RAG skill)
        logger.info(f"Hybrid search: {request.query}")

        import sys
        from pathlib import Path

        skill_path = (
            Path(__file__).parent.parent.parent.parent / ".claude/skills/rag-pipeline/scripts"
        )
        if str(skill_path) not in sys.path:
            sys.path.insert(0, str(skill_path))

        from skill import rag_query as skill_rag_query

        # Execute RAG query (dense search)
        dense_start = time.time()
        skill_result = skill_rag_query(
            {
                "question": request.query,
                "top_k": request.top_k,
                "collections": request.collections,
                "materials": request.materials,
            }
        )
        dense_time = time.time() - dense_start

        if skill_result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=skill_result.get("error", "RAG query failed")
            )

        # Convert to dense results format
        dense_results = []
        documents = []
        for result in skill_result.get("sources", []):
            doc = {
                "metadata": result.get("metadata", {}),
                "text": result.get("text", ""),
                "score": result.get("score", 0.0),
            }
            documents.append(doc)
            dense_results.append((doc, result.get("score", 0.0)))

        # Step 2: Build BM25 index (sparse search)
        bm25_start = time.time()
        bm25_index = engine.build_bm25_index(documents)
        bm25_time = time.time() - bm25_start

        # Step 3: Hybrid search (fusion + re-ranking)
        hybrid_start = time.time()
        hybrid_results = engine.hybrid_search(
            query=request.query,
            dense_results=dense_results,
            bm25_index=bm25_index,
            documents=documents,
            top_k=request.top_k,
            dense_weight=request.dense_weight,
            sparse_weight=request.sparse_weight,
            enable_reranking=request.enable_reranking,
        )
        hybrid_time = time.time() - hybrid_start

        # Format results
        formatted_results = []
        for doc, score in hybrid_results:
            metadata = doc.get("metadata", {})
            formatted_results.append(
                {
                    "product_id": metadata.get("product_id", ""),
                    "product_name": metadata.get("product_name", ""),
                    "product_code": metadata.get("product_code", ""),
                    "material": metadata.get("material", ""),
                    "capacity": metadata.get("capacity", ""),
                    "score": float(score),
                    "source_collection": metadata.get("source_collection", "unknown"),
                }
            )

        total_time = time.time() - start_time

        # Performance metrics
        performance = {
            "total_time_ms": round(total_time * 1000, 2),
            "dense_search_ms": round(dense_time * 1000, 2),
            "bm25_build_ms": round(bm25_time * 1000, 2),
            "hybrid_fusion_ms": round(hybrid_time * 1000, 2),
            "documents_processed": len(documents),
            "final_results": len(formatted_results),
        }

        # Determine search strategy
        strategy = []
        if request.dense_weight > 0:
            strategy.append("dense-vectors")
        if request.sparse_weight > 0:
            strategy.append("bm25-sparse")
        if request.enable_reranking:
            strategy.append("cross-encoder-rerank")
        search_strategy = " + ".join(strategy)

        return HybridSearchResponse(
            query=request.query,
            total_results=len(formatted_results),
            results=formatted_results,
            search_strategy=search_strategy,
            performance=performance,
            parameters={
                "dense_weight": request.dense_weight,
                "sparse_weight": request.sparse_weight,
                "enable_reranking": request.enable_reranking,
                "top_k": request.top_k,
            },
        )

    except Exception as e:
        logger.error(f"Hybrid search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def hybrid_health():
    """Check hybrid search service health"""
    engine = get_hybrid_engine()

    return {
        "status": "healthy",
        "cross_encoder": {
            "enabled": engine.enable_cross_encoder,
            "model": engine.cross_encoder_model,
            "loaded": engine.cross_encoder is not None,
        },
        "rrf_k": engine.rrf_k,
        "endpoint": "/api/v1/hybrid/search",
    }


@router.get("/config")
async def hybrid_config():
    """Get current hybrid search configuration"""
    engine = get_hybrid_engine()

    return {
        "cross_encoder_model": engine.cross_encoder_model,
        "enable_cross_encoder": engine.enable_cross_encoder,
        "rrf_k": engine.rrf_k,
        "default_dense_weight": 0.5,
        "default_sparse_weight": 0.5,
        "supported_strategies": [
            "dense-only (dense_weight=1, sparse_weight=0)",
            "sparse-only (dense_weight=0, sparse_weight=1)",
            "hybrid (dense_weight=0.5, sparse_weight=0.5)",
            "hybrid-reranked (hybrid + cross-encoder)",
        ],
    }
