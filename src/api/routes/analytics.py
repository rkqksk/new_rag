"""
분석 및 추적 API 엔드포인트
클릭 추적, 샘플 신청 등
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

from src.analytics.behavior_tracker import get_behavior_tracker


router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============================================================
# Request Models
# ============================================================

class ClickEventRequest(BaseModel):
    """클릭 이벤트 요청"""
    user_id: str
    session_id: str
    product_idx: str
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    material: Optional[str] = None
    capacity_ml: Optional[float] = None
    neck_size: Optional[str] = None
    click_position: Optional[int] = None  # 검색 결과에서 위치
    search_query: Optional[str] = None
    referrer: str = "search_result"  # search_result, related_products, homepage, etc.


class PageViewEventRequest(BaseModel):
    """페이지 뷰 이벤트 요청 (상세 페이지)"""
    user_id: str
    session_id: str
    product_idx: str
    time_on_page_seconds: int
    viewed_images: bool = False
    checked_specs: bool = False
    checked_compatibility: bool = False


class SampleRequestSubmit(BaseModel):
    """샘플 신청 제출"""
    user_id: str
    session_id: str
    product_idx: str
    intended_use: str = Field(..., description="용도: 로션, 크림, 세럼, etc.")
    company_name: str
    contact_name: str
    contact_phone: str
    contact_email: Optional[str] = None
    contact_address: Optional[str] = None
    notes: Optional[str] = None


# ============================================================
# Endpoints
# ============================================================

@router.post("/track/click")
async def track_click(request: ClickEventRequest, req: Request):
    """
    제품 클릭 이벤트 추적

    **사용 시나리오**:
    - 검색 결과에서 제품 클릭
    - 관련 제품에서 클릭
    - 홈페이지에서 인기 제품 클릭

    **추적 데이터**:
    - 어떤 제품이 클릭되었는지
    - 검색 결과에서 몇 번째 위치였는지
    - 어떤 검색 쿼리에서 왔는지
    """
    try:
        tracker = get_behavior_tracker()

        # IP 주소 추출
        ip_address = req.client.host if req.client else None

        await tracker.track_click(
            user_id=request.user_id,
            session_id=request.session_id,
            product_idx=request.product_idx,
            product_code=request.product_code,
            product_name=request.product_name,
            category=request.category,
            material=request.material,
            capacity_ml=request.capacity_ml,
            neck_size=request.neck_size,
            click_position=request.click_position,
            search_query=request.search_query,
            referrer=request.referrer,
            ip_address=ip_address
        )

        return {"status": "success", "message": "Click event tracked"}

    except Exception as e:
        # 추적 실패는 사용자 경험에 영향 주지 않음
        print(f"[Analytics API] Click tracking failed: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/track/pageview")
async def track_pageview(request: PageViewEventRequest, req: Request):
    """
    페이지 뷰 이벤트 추적 (상세 페이지)

    **사용 시나리오**:
    - 제품 상세 페이지 이탈 시
    - 페이지 닫기 전 행동 기록

    **추적 데이터**:
    - 페이지 체류 시간
    - 이미지 확대 여부
    - 스펙 탭 클릭 여부
    - 호환성 확인 여부
    """
    try:
        tracker = get_behavior_tracker()

        # IP 주소 추출
        ip_address = req.client.host if req.client else None

        # 기존 클릭 로그 업데이트 (최신 클릭 로그에 행동 패턴 추가)
        # TODO: 실제로는 기존 클릭 로그를 찾아서 UPDATE
        # 지금은 새로운 클릭 로그로 기록
        await tracker.track_click(
            user_id=request.user_id,
            session_id=request.session_id,
            product_idx=request.product_idx,
            product_code=None,
            product_name=None,
            category=None,
            material=None,
            capacity_ml=None,
            neck_size=None,
            click_position=None,
            search_query=None,
            referrer="pageview",
            time_on_page_seconds=request.time_on_page_seconds,
            viewed_images=request.viewed_images,
            checked_specs=request.checked_specs,
            checked_compatibility=request.checked_compatibility,
            ip_address=ip_address
        )

        return {"status": "success", "message": "Page view event tracked"}

    except Exception as e:
        print(f"[Analytics API] Page view tracking failed: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/sample-request")
async def submit_sample_request(request: SampleRequestSubmit, req: Request):
    """
    샘플 신청 제출

    **사용 시나리오**:
    - 제품 상세 페이지에서 "샘플 신청" 버튼 클릭
    - 필수 정보 입력 후 제출

    **수집 데이터**:
    - 제품 정보
    - 용도 (로션, 크림, 세럼, etc.)
    - 회사 정보 및 연락처

    **가중치**: 10.0 (가장 강력한 구매 의도 신호)
    """
    try:
        tracker = get_behavior_tracker()

        # IP 주소 추출
        ip_address = req.client.host if req.client else None

        # 제품 정보 로드 (실제로는 DB에서 가져와야 함)
        # 여기서는 간단히 처리
        product_data = {
            "product_idx": request.product_idx,
            "product_code": None,
            "product_name": None,
            "category": None,
            "material": None,
            "capacity_ml": None,
            "neck_size": None
        }

        # 연락처 정보 구성
        contact_info = {
            "name": request.contact_name,
            "phone": request.contact_phone,
            "email": request.contact_email,
            "address": request.contact_address
        }

        await tracker.track_sample_request(
            user_id=request.user_id,
            session_id=request.session_id,
            product_idx=request.product_idx,
            product_code=product_data["product_code"],
            product_name=product_data["product_name"],
            category=product_data["category"],
            material=product_data["material"],
            capacity_ml=product_data["capacity_ml"],
            neck_size=product_data["neck_size"],
            intended_use=request.intended_use,
            company_name=request.company_name,
            contact_info=contact_info,
            notes=request.notes,
            ip_address=ip_address
        )

        return {
            "status": "success",
            "message": "샘플 신청이 접수되었습니다.",
            "request_id": f"{request.user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"샘플 신청 실패: {str(e)}")


@router.get("/status")
async def get_tracker_status():
    """
    추적기 상태 확인

    **응답**:
    - 큐에 대기 중인 이벤트 수
    - 마지막 플러시 시간
    """
    tracker = get_behavior_tracker()

    return {
        "status": "active",
        "queue_size": len(tracker.queue),
        "batch_size": tracker.batch_size,
        "flush_interval_seconds": tracker.flush_interval_seconds
    }


@router.post("/flush")
async def flush_tracker():
    """
    즉시 플러시 (관리자용)

    큐에 있는 모든 이벤트를 즉시 DB에 저장
    """
    tracker = get_behavior_tracker()
    await tracker.flush()

    return {
        "status": "success",
        "message": "Tracker flushed successfully"
    }
