"""
인터랙티브 제품 비교 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from src.services.comparison_engine import get_comparison_engine, ComparisonEngine


# Pydantic 모델
class CompareRequest(BaseModel):
    """제품 비교 요청"""
    product_idxs: List[str] = Field(..., description="비교할 제품 idx 목록 (2-5개)")
    metrics: Optional[List[str]] = Field(None, description="비교할 메트릭 목록 (None이면 전체)")


class FilterRequest(BaseModel):
    """필터 적용 요청"""
    products: List[Dict] = Field(..., description="필터링할 제품 목록")
    filters: Dict[str, Any] = Field(..., description="필터 조건")


class ComparisonResponse(BaseModel):
    """비교 결과 응답"""
    products: List[Dict]
    comparison_matrix: List[Dict]
    metrics: List[str]
    product_count: int
    recommendation: str


class MetricsResponse(BaseModel):
    """비교 메트릭 목록 응답"""
    metrics: Dict[str, Dict]
    total_count: int


# Router 생성
router = APIRouter(prefix="/compare", tags=["compare"])


# 의존성 주입
def get_engine() -> ComparisonEngine:
    return get_comparison_engine()


# API 엔드포인트

@router.post("/products", response_model=ComparisonResponse)
async def compare_products(
    request: CompareRequest,
    engine: ComparisonEngine = Depends(get_engine)
):
    """
    여러 제품 비교

    Args:
        request: 비교 요청 (제품 idx 목록, 메트릭)

    Returns:
        비교 결과 (비교 매트릭스, 추천)
    """
    try:
        # 제품 개수 검증
        if len(request.product_idxs) < 2:
            raise HTTPException(
                status_code=400,
                detail="최소 2개 이상의 제품을 선택해주세요."
            )

        if len(request.product_idxs) > 5:
            raise HTTPException(
                status_code=400,
                detail="최대 5개까지 비교 가능합니다."
            )

        # 비교 실행
        result = engine.compare_products(
            product_idxs=request.product_idxs,
            metrics=request.metrics
        )

        # 에러 처리
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return ComparisonResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/filter")
async def filter_products(
    request: FilterRequest,
    engine: ComparisonEngine = Depends(get_engine)
):
    """
    동적 필터 적용

    Args:
        request: 필터 요청 (제품 목록, 필터 조건)

    Returns:
        필터링된 제품 목록
    """
    try:
        filtered = engine.apply_filters(
            products=request.products,
            filters=request.filters
        )

        return {
            "products": filtered,
            "total_count": len(filtered),
            "applied_filters": request.filters
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    engine: ComparisonEngine = Depends(get_engine)
):
    """
    비교 가능한 메트릭 목록 조회

    Returns:
        메트릭 목록 및 설명
    """
    return MetricsResponse(
        metrics=engine.comparison_metrics,
        total_count=len(engine.comparison_metrics)
    )


@router.get("/health")
async def health_check():
    """
    헬스 체크

    Returns:
        시스템 상태
    """
    return {
        "status": "healthy",
        "service": "comparison_engine",
        "features": {
            "comparison": "enabled",
            "filtering": "enabled",
            "smart_recommendation": "enabled"
        }
    }
