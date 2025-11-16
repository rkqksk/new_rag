"""
Recommendations API Routes
Product recommendations using collaborative and content-based filtering
Version: v8.5.0
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import numpy as np

from src.auth.dependencies import get_current_user
from src.auth.models import CurrentUser
from src.services.recommendation_service import get_recommendation_service, RecommendationStrategy
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class InteractionRequest(BaseModel):
    """User interaction tracking request"""
    item_id: str
    interaction_type: str = "view"  # view, click, like, purchase, etc.
    score: Optional[float] = None


class ItemFeaturesRequest(BaseModel):
    """Item features for content-based filtering"""
    item_id: str
    features: List[float]
    metadata: Optional[Dict[str, Any]] = None


@router.get("/user/{user_id}")
async def get_user_recommendations(
    user_id: str,
    strategy: str = Query("hybrid", description="Recommendation strategy: collaborative, content_based, hybrid, popular, trending"),
    top_k: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    collaborative_weight: float = Query(0.5, ge=0, le=1, description="Weight for collaborative filtering (hybrid only)"),
    content_weight: float = Query(0.5, ge=0, le=1, description="Weight for content-based filtering (hybrid only)"),
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get personalized recommendations for a user

    Args:
        user_id: User ID
        strategy: Recommendation strategy (collaborative, content_based, hybrid, popular, trending)
        top_k: Number of recommendations (1-50)
        collaborative_weight: Weight for collaborative filtering (0-1, hybrid only)
        content_weight: Weight for content-based filtering (0-1, hybrid only)

    Returns:
        List of recommended items with scores and reasons
    """
    try:
        rec_service = get_recommendation_service()

        if strategy == RecommendationStrategy.COLLABORATIVE:
            recommendations = rec_service.get_collaborative_recommendations(user_id, top_k)
        elif strategy == RecommendationStrategy.CONTENT_BASED:
            recommendations = rec_service.get_content_based_recommendations(user_id, top_k)
        elif strategy == RecommendationStrategy.HYBRID:
            recommendations = rec_service.get_hybrid_recommendations(
                user_id, top_k, collaborative_weight, content_weight
            )
        elif strategy == RecommendationStrategy.POPULAR:
            recommendations = rec_service.get_popular_recommendations(top_k)
        elif strategy == RecommendationStrategy.TRENDING:
            recommendations = rec_service.get_popular_recommendations(top_k, time_window_days=7)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy}")

        return {
            "success": True,
            "user_id": user_id,
            "strategy": strategy,
            "count": len(recommendations),
            "recommendations": [
                {
                    "item_id": rec.item_id,
                    "score": round(rec.score, 4),
                    "reason": rec.reason,
                    "metadata": rec.metadata
                }
                for rec in recommendations
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get recommendations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/popular")
async def get_popular_items(
    top_k: int = Query(10, ge=1, le=50),
    time_window_days: Optional[int] = Query(None, ge=1, le=365, description="Time window for trending items")
) -> Dict[str, Any]:
    """
    Get popular or trending items

    Args:
        top_k: Number of items (1-50)
        time_window_days: Optional time window for trending items (1-365 days)

    Returns:
        List of popular/trending items
    """
    try:
        rec_service = get_recommendation_service()

        recommendations = rec_service.get_popular_recommendations(top_k, time_window_days)

        return {
            "success": True,
            "type": "trending" if time_window_days else "popular",
            "time_window_days": time_window_days,
            "count": len(recommendations),
            "items": [
                {
                    "item_id": rec.item_id,
                    "score": round(rec.score, 2),
                    "reason": rec.reason,
                    "metadata": rec.metadata
                }
                for rec in recommendations
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get popular items: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get popular items: {str(e)}")


@router.get("/similar/{item_id}")
async def get_similar_items(
    item_id: str,
    top_k: int = Query(10, ge=1, le=50)
) -> Dict[str, Any]:
    """
    Get similar items based on content features

    Args:
        item_id: Item ID
        top_k: Number of similar items (1-50)

    Returns:
        List of similar items with similarity scores
    """
    try:
        rec_service = get_recommendation_service()

        recommendations = rec_service.get_similar_items(item_id, top_k)

        return {
            "success": True,
            "item_id": item_id,
            "count": len(recommendations),
            "similar_items": [
                {
                    "item_id": rec.item_id,
                    "similarity": round(rec.score, 4),
                    "reason": rec.reason,
                    "metadata": rec.metadata
                }
                for rec in recommendations
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get similar items for {item_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get similar items: {str(e)}")


@router.post("/track")
async def track_interaction(
    request: InteractionRequest,
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Track user-item interaction

    Args:
        request: Interaction data (item_id, interaction_type, score)

    Returns:
        Success status
    """
    try:
        rec_service = get_recommendation_service()

        user_id = current_user.id if current_user else "anonymous"

        rec_service.track_interaction(
            user_id=user_id,
            item_id=request.item_id,
            interaction_type=request.interaction_type,
            score=request.score
        )

        return {
            "success": True,
            "message": f"Tracked {request.interaction_type} interaction for user {user_id}"
        }

    except Exception as e:
        logger.error(f"Failed to track interaction: {e}")
        return {"success": False, "error": str(e)}


@router.post("/items/features")
async def add_item_features(
    request: ItemFeaturesRequest,
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Add item features for content-based filtering

    Requires: Authenticated user

    Args:
        request: Item features data (item_id, features, metadata)

    Returns:
        Success status
    """
    try:
        rec_service = get_recommendation_service()

        features = np.array(request.features)

        rec_service.add_item_features(
            item_id=request.item_id,
            features=features,
            metadata=request.metadata
        )

        return {
            "success": True,
            "message": f"Added features for item {request.item_id}",
            "feature_dim": len(request.features)
        }

    except Exception as e:
        logger.error(f"Failed to add item features: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add item features: {str(e)}")


@router.get("/statistics")
async def get_recommendation_statistics(
    current_user: CurrentUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get recommendation engine statistics

    Requires: Authenticated user

    Returns:
        Statistics including total users, items, interactions
    """
    try:
        rec_service = get_recommendation_service()
        stats = rec_service.get_statistics()

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")
