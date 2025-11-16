"""Personalization API Endpoints - Complete Implementation"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from apps.api.dependencies.services import get_personalization_service
from apps.api.services.personalization_service import PersonalizationService
from apps.api.services.product_loader import load_products

router = APIRouter()

# Cache products in memory to avoid loading from files on every request
_product_cache: Optional[Dict[str, Any]] = None


def get_all_products() -> List[Dict[str, Any]]:
    """Get all products from cache or load from files"""
    global _product_cache

    if _product_cache is None:
        _product_cache = load_products()

    return list(_product_cache.values())


class TrackRequest(BaseModel):
    session_id: str
    product_id: str
    product: Dict[str, Any]
    event_type: str  # click, view, bookmark
    search_context: Optional[str] = None


@router.post("/track")
async def track_interaction(
    request: TrackRequest, service: PersonalizationService = Depends(get_personalization_service)
):
    """Track user interaction (click, view, bookmark)"""
    success = await service.track_interaction(
        session_id=request.session_id,
        product_id=request.product_id,
        event_type=request.event_type,
        product_data=request.product,
        search_context=request.search_context,
    )

    if success:
        return {"status": "tracked", "session_id": request.session_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to track interaction")


@router.get("/profile/{session_id}")
async def get_profile(
    session_id: str, service: PersonalizationService = Depends(get_personalization_service)
):
    """Get user profile and preferences"""
    profile = await service.get_profile(session_id)
    return profile


@router.get("/recommendations/{session_id}")
async def get_recommendations(
    session_id: str,
    top_k: int = 10,
    category: Optional[str] = None,
    service: PersonalizationService = Depends(get_personalization_service),
):
    """Get personalized recommendations"""
    # Load all products from cache
    all_products = get_all_products()

    recommendations = await service.get_recommendations(
        session_id=session_id, all_products=all_products, top_k=top_k, category_filter=category
    )

    return {"recommendations": recommendations, "total": len(recommendations)}
