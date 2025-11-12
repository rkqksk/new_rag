"""
Search Ranking API Routes
Advanced search result ranking with BM25, TF-IDF, and hybrid algorithms
Version: v8.5.0
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from src.auth.dependencies import get_current_user
from src.auth.models import CurrentUser
from src.services.search_ranking_service import get_search_ranking_service, SearchResult
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search-ranking"])


class RankRequest(BaseModel):
    """Search ranking request"""
    query: str
    results: List[Dict[str, Any]]
    vector_scores: Optional[List[float]] = None
    algorithm: str = "bm25"  # bm25, tfidf, hybrid
    weights: Optional[Dict[str, float]] = None


class BuildIndexRequest(BaseModel):
    """Build search index request"""
    documents: List[Dict[str, Any]]


@router.post("/rank")
async def rank_search_results(
    request: RankRequest,
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Rank search results using advanced algorithms

    Args:
        request: Ranking request with query, results, algorithm, and weights

    Returns:
        Ranked search results with scores and explanations
    """
    try:
        ranking_service = get_search_ranking_service()

        # Rank results
        ranked_results = ranking_service.rank_results(
            query=request.query,
            results=request.results,
            vector_scores=request.vector_scores,
            algorithm=request.algorithm,
            weights=request.weights
        )

        return {
            "success": True,
            "query": request.query,
            "algorithm": request.algorithm,
            "count": len(ranked_results),
            "results": [
                {
                    "rank": result.rank,
                    "id": result.id,
                    "content": result.content[:200] + "..." if len(result.content) > 200 else result.content,
                    "metadata": result.metadata,
                    "scores": {
                        "final": round(result.final_score, 4),
                        "vector": round(result.vector_score, 4),
                        "bm25": round(result.bm25_score, 4),
                        "tfidf": round(result.tf_idf_score, 4)
                    }
                }
                for result in ranked_results
            ]
        }

    except Exception as e:
        logger.error(f"Failed to rank search results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to rank results: {str(e)}")


@router.post("/rerank")
async def rerank_with_features(
    query: str = Body(...),
    results: List[Dict[str, Any]] = Body(...),
    vector_scores: Optional[List[float]] = Body(None),
    initial_algorithm: str = Body("bm25"),
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Re-rank results using feature-based learning-to-rank

    Args:
        query: Search query
        results: Initial search results
        vector_scores: Optional vector similarity scores
        initial_algorithm: Initial ranking algorithm (bm25, tfidf, hybrid)

    Returns:
        Re-ranked results with feature scores
    """
    try:
        ranking_service = get_search_ranking_service()

        # Initial ranking
        ranked_results = ranking_service.rank_results(
            query=query,
            results=results,
            vector_scores=vector_scores,
            algorithm=initial_algorithm
        )

        # Re-rank with features
        reranked_results = ranking_service.rerank_with_features(
            query=query,
            results=ranked_results
        )

        return {
            "success": True,
            "query": query,
            "initial_algorithm": initial_algorithm,
            "count": len(reranked_results),
            "results": [
                {
                    "rank": result.rank,
                    "id": result.id,
                    "content": result.content[:200] + "..." if len(result.content) > 200 else result.content,
                    "metadata": result.metadata,
                    "scores": {
                        "final": round(result.final_score, 4),
                        "vector": round(result.vector_score, 4),
                        "bm25": round(result.bm25_score, 4),
                        "tfidf": round(result.tf_idf_score, 4)
                    }
                }
                for result in reranked_results
            ]
        }

    except Exception as e:
        logger.error(f"Failed to re-rank results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to re-rank results: {str(e)}")


@router.post("/index/build")
async def build_search_index(
    request: BuildIndexRequest,
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Build search index from documents

    Requires: Authenticated user

    Args:
        request: Documents to index

    Returns:
        Index statistics
    """
    try:
        ranking_service = get_search_ranking_service()

        # Build index
        ranking_service.build_index(request.documents)

        # Get statistics
        stats = ranking_service.get_statistics()

        return {
            "success": True,
            "message": "Search index built successfully",
            "statistics": stats
        }

    except Exception as e:
        logger.error(f"Failed to build search index: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to build index: {str(e)}")


@router.get("/explain/{result_id}")
async def explain_ranking(
    result_id: str,
    query: str = Query(...),
    results: str = Query(..., description="JSON string of results"),
    algorithm: str = Query("bm25"),
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Explain ranking for a specific result

    Args:
        result_id: Result ID to explain
        query: Search query
        results: JSON string of results
        algorithm: Ranking algorithm

    Returns:
        Ranking explanation
    """
    try:
        import json

        ranking_service = get_search_ranking_service()

        # Parse results
        results_list = json.loads(results)

        # Rank results
        ranked_results = ranking_service.rank_results(
            query=query,
            results=results_list,
            algorithm=algorithm
        )

        # Find specific result
        target_result = None
        for result in ranked_results:
            if result.id == result_id:
                target_result = result
                break

        if not target_result:
            raise HTTPException(status_code=404, detail=f"Result {result_id} not found")

        # Get explanation
        explanation = ranking_service.explain_ranking(target_result)

        return {
            "success": True,
            "explanation": explanation
        }

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    except Exception as e:
        logger.error(f"Failed to explain ranking: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to explain ranking: {str(e)}")


@router.get("/statistics")
async def get_ranking_statistics(
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get search ranking statistics

    Returns:
        Index statistics including doc count, avg length, unique terms
    """
    try:
        ranking_service = get_search_ranking_service()
        stats = ranking_service.get_statistics()

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")
