"""
스마트 추천 API 엔드포인트
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.core.conversation_manager import ConversationManager
from src.services.collaborative_recommender import (
    CollaborativeRecommender,
    UserInteractionTracker,
    get_collaborative_recommender,
)
from src.services.contextual_rag import ContextualRAG
from src.services.intent_recommender import IntentBasedRecommender, get_intent_recommender


# Pydantic 모델
class RecommendRequest(BaseModel):
    """추천 요청"""

    query: str = Field(..., description="사용자 쿼리 (제품 유형 포함)")
    user_id: Optional[str] = Field(None, description="사용자 ID (개인화용)")
    limit: int = Field(10, description="반환할 제품 수")
    use_personalization: bool = Field(True, description="개인화 추천 사용 여부")


class TrackInteractionRequest(BaseModel):
    """인터랙션 추적 요청"""

    user_id: str = Field(..., description="사용자 ID")
    product_idx: str = Field(..., description="제품 idx")
    action: str = Field(..., description="행동 (view, click, select, purchase)")
    metadata: Optional[Dict[str, Any]] = None


class UserProfileResponse(BaseModel):
    """사용자 프로필 응답"""

    user_id: str
    material_preference: Dict[str, float]
    capacity_preference: Dict[str, float]
    neck_size_preference: Dict[str, float]
    category_preference: Dict[str, float]
    price_sensitivity: float
    total_interactions: int
    last_updated: str


class ProductProfilesResponse(BaseModel):
    """제품군 프로필 목록"""

    profiles: Dict[str, Dict]
    total_count: int


# Router 생성
router = APIRouter(prefix="/recommend", tags=["recommend"])


# 의존성 주입
def get_intent_rec() -> IntentBasedRecommender:
    return get_intent_recommender()


def get_collab_rec() -> CollaborativeRecommender:
    return get_collaborative_recommender()


# API 엔드포인트


@router.post("/smart")
async def smart_recommend(
    request: RecommendRequest,
    intent_rec: IntentBasedRecommender = Depends(get_intent_rec),
    collab_rec: CollaborativeRecommender = Depends(get_collab_rec),
):
    """
    스마트 추천 (의도 기반 + 개인화)

    Args:
        request: 추천 요청

    Returns:
        추천 제품 목록
    """
    try:
        # 1. 기본 검색 실행 (간단한 키워드 검색)
        from src.core.conversation_manager import ConversationManager
        from src.core.intent_classifier import get_intent_classifier
        from src.core.reference_resolver import get_reference_resolver
        from src.services.contextual_rag import ContextualRAG

        # ContextualRAG 인스턴스 생성 (임시 세션)
        conv_manager = ConversationManager()
        temp_session_id = conv_manager.create_session(user_id=request.user_id)

        rag = ContextualRAG(
            conv_manager=conv_manager,
            intent_classifier=get_intent_classifier(),
            reference_resolver=get_reference_resolver(),
        )

        # 검색 실행
        search_result = await rag.query(temp_session_id, request.query)
        products = search_result.get("products", [])

        if not products:
            return {
                "query": request.query,
                "products": [],
                "total_count": 0,
                "recommendation_type": "none",
                "message": "검색 결과가 없습니다.",
            }

        # 2. 의도 기반 추천 적용
        intent_products = intent_rec.recommend(
            query=request.query,
            products=products,
            limit=request.limit * 2,  # 개인화 전에 더 많이 가져옴
        )

        # 3. 개인화 추천 적용 (옵션)
        if request.use_personalization and request.user_id:
            final_products = collab_rec.recommend_for_user(
                user_id=request.user_id, products=intent_products, limit=request.limit
            )
            recommendation_type = "intent_based + personalized"
        else:
            final_products = intent_products[: request.limit]
            recommendation_type = "intent_based"

        # 4. 제품 유형 감지
        product_type = intent_rec.detect_product_type(request.query)

        return {
            "query": request.query,
            "products": final_products,
            "total_count": len(final_products),
            "recommendation_type": recommendation_type,
            "matched_profile": product_type,
            "profile_description": (
                intent_rec.get_profile_description(product_type) if product_type else None
            ),
            "personalization_applied": request.use_personalization and request.user_id is not None,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track")
async def track_interaction(
    request: TrackInteractionRequest, collab_rec: CollaborativeRecommender = Depends(get_collab_rec)
):
    """
    사용자 인터랙션 추적

    Args:
        request: 인터랙션 추적 요청

    Returns:
        성공 여부
    """
    try:
        success = collab_rec.tracker.track(
            user_id=request.user_id,
            product_idx=request.product_idx,
            action=request.action,
            metadata=request.metadata,
        )

        return {
            "success": success,
            "message": "인터랙션이 기록되었습니다.",
            "user_id": request.user_id,
            "product_idx": request.product_idx,
            "action": request.action,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str, collab_rec: CollaborativeRecommender = Depends(get_collab_rec)
):
    """
    사용자 선호도 프로필 조회

    Args:
        user_id: 사용자 ID

    Returns:
        사용자 프로필
    """
    try:
        profile = collab_rec.build_user_profile(user_id)

        return UserProfileResponse(**profile)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles", response_model=ProductProfilesResponse)
async def get_product_profiles(intent_rec: IntentBasedRecommender = Depends(get_intent_rec)):
    """
    제품군 프로필 목록 조회

    Returns:
        제품군 프로필 목록
    """
    profiles = intent_rec.get_all_profiles()

    return ProductProfilesResponse(profiles=profiles, total_count=len(profiles))


@router.get("/health")
async def health_check():
    """
    헬스 체크

    Returns:
        시스템 상태
    """
    return {
        "status": "healthy",
        "services": {"intent_recommender": "ok", "collaborative_recommender": "ok"},
        "product_profiles_count": len(get_intent_recommender().get_all_profiles()),
    }
