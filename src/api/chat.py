"""
컨텍스트 인식 채팅 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json

from src.core.conversation_manager import ConversationManager
from src.core.intent_classifier import get_intent_classifier
from src.core.reference_resolver import get_reference_resolver
from src.services.contextual_rag import ContextualRAG


# Pydantic 모델
class CreateSessionRequest(BaseModel):
    """세션 생성 요청"""
    user_id: Optional[str] = None


class CreateSessionResponse(BaseModel):
    """세션 생성 응답"""
    session_id: str
    created_at: str


class ChatQueryRequest(BaseModel):
    """채팅 쿼리 요청"""
    session_id: str = Field(..., description="세션 ID")
    query: str = Field(..., description="사용자 쿼리")


class ProductInfo(BaseModel):
    """제품 정보"""
    idx: str
    product_name: str
    product_code: Optional[str] = None
    material: Optional[str] = None
    capacity: Optional[str] = None
    neck_size: Optional[str] = None


class ChatQueryResponse(BaseModel):
    """채팅 쿼리 응답"""
    session_id: str
    query: str
    intent: Dict[str, Any]
    reference_resolved: bool
    expanded_query: Optional[str] = None
    products: List[Dict[str, Any]]
    response: str
    total_count: int
    matched_profile: Optional[str] = None


class SessionInfoResponse(BaseModel):
    """세션 정보 응답"""
    session_id: str
    user_id: str
    created_at: str
    last_activity: str
    context: Dict[str, Any]


class SessionStatsResponse(BaseModel):
    """세션 통계 응답"""
    session_id: str
    user_id: Optional[str]
    duration_seconds: float
    total_queries: int
    unique_products_viewed: int
    active_filters: int
    created_at: str
    last_activity: str


# Router 생성
router = APIRouter(prefix="/chat", tags=["chat"])

# 전역 인스턴스
_conv_manager: Optional[ConversationManager] = None
_contextual_rag: Optional[ContextualRAG] = None


def get_conv_manager() -> ConversationManager:
    """ConversationManager 싱글톤"""
    global _conv_manager
    if _conv_manager is None:
        _conv_manager = ConversationManager(
            redis_url="redis://localhost:6379/0"
        )
    return _conv_manager


def get_contextual_rag() -> ContextualRAG:
    """ContextualRAG 싱글톤"""
    global _contextual_rag
    if _contextual_rag is None:
        _contextual_rag = ContextualRAG(
            conv_manager=get_conv_manager(),
            intent_classifier=get_intent_classifier(),
            reference_resolver=get_reference_resolver()
        )
    return _contextual_rag


# API 엔드포인트

@router.post("/create_session", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """
    새 대화 세션 생성

    Args:
        request: 세션 생성 요청

    Returns:
        생성된 세션 정보
    """
    conv_manager = get_conv_manager()
    session_id = conv_manager.create_session(user_id=request.user_id)

    session = conv_manager.get_session(session_id)

    return CreateSessionResponse(
        session_id=session_id,
        created_at=session["created_at"]
    )


@router.post("/query", response_model=ChatQueryResponse)
async def chat_query(request: ChatQueryRequest):
    """
    컨텍스트 기반 채팅 쿼리

    Args:
        request: 채팅 쿼리 요청

    Returns:
        쿼리 응답
    """
    contextual_rag = get_contextual_rag()

    try:
        result = await contextual_rag.query(
            session_id=request.session_id,
            user_query=request.query
        )

        return ChatQueryResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}", response_model=SessionInfoResponse)
async def get_session_info(session_id: str):
    """
    세션 정보 조회

    Args:
        session_id: 세션 ID

    Returns:
        세션 정보
    """
    conv_manager = get_conv_manager()
    session = conv_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    return SessionInfoResponse(**session)


@router.get("/session/{session_id}/stats", response_model=SessionStatsResponse)
async def get_session_stats(session_id: str):
    """
    세션 통계 조회

    Args:
        session_id: 세션 ID

    Returns:
        세션 통계
    """
    conv_manager = get_conv_manager()
    stats = conv_manager.get_session_stats(session_id)

    if not stats:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    return SessionStatsResponse(**stats)


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    세션 삭제

    Args:
        session_id: 세션 ID

    Returns:
        삭제 결과
    """
    conv_manager = get_conv_manager()
    success = conv_manager.delete_session(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    return {"success": True, "message": "세션이 삭제되었습니다."}


@router.post("/session/{session_id}/extend")
async def extend_session(session_id: str):
    """
    세션 TTL 연장

    Args:
        session_id: 세션 ID

    Returns:
        연장 결과
    """
    conv_manager = get_conv_manager()
    success = conv_manager.extend_session_ttl(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    return {"success": True, "message": "세션이 연장되었습니다."}


# WebSocket 엔드포인트

class ConnectionManager:
    """WebSocket 연결 관리"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """WebSocket 연결"""
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        """WebSocket 연결 해제"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: str, message: dict):
        """메시지 전송"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)


connection_manager = ConnectionManager()


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket 기반 실시간 채팅

    Args:
        websocket: WebSocket 연결
        session_id: 세션 ID
    """
    await connection_manager.connect(session_id, websocket)

    contextual_rag = get_contextual_rag()

    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            message = json.loads(data)

            query = message.get("query")

            if not query:
                await websocket.send_json({
                    "error": "쿼리가 없습니다."
                })
                continue

            # 쿼리 처리
            try:
                result = await contextual_rag.query(
                    session_id=session_id,
                    user_query=query
                )

                # 응답 전송
                await websocket.send_json({
                    "type": "response",
                    "data": result
                })

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "error": str(e)
                })

    except WebSocketDisconnect:
        connection_manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket 오류: {e}")
        connection_manager.disconnect(session_id)


# Health check
@router.get("/health")
async def health_check():
    """
    헬스 체크

    Returns:
        시스템 상태
    """
    try:
        # Redis 연결 확인
        conv_manager = get_conv_manager()
        conv_manager.redis_client.ping()

        return {
            "status": "healthy",
            "redis": "connected",
            "services": {
                "conversation_manager": "ok",
                "intent_classifier": "ok",
                "reference_resolver": "ok",
                "contextual_rag": "ok"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
