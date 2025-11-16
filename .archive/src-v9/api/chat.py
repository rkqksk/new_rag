"""
컨텍스트 인식 채팅 API 엔드포인트

Frontend Integration:
    - Location: frontend/chat.html
    - Base URL: http://localhost:8001
    - Endpoints:
        - POST /chat/create_session  -> CreateSessionRequest/Response
        - POST /chat/query           -> ChatQueryRequest/Response

Usage Example:
    # Frontend JavaScript
    const sessionResp = await fetch('http://localhost:8001/chat/create_session', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({})
    });
    const {session_id} = await sessionResp.json();

    const queryResp = await fetch('http://localhost:8001/chat/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: session_id,
            query: "50ml bottle recommendation"
        })
    });
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

from src.core.conversation_manager import ConversationManager
from src.core.embedding_service import EmbeddingService
from src.core.intent_classifier import get_intent_classifier

# RAG Pipeline imports
from src.core.rag_pipeline import RAGPipeline
from src.core.reference_resolver import get_reference_resolver
from src.services.contextual_rag import ContextualRAG

# Unified LLM Service (NexaAI + Ollama hybrid)
from src.services.unified_llm_service import UnifiedLLMService, NexaConfig, OllamaConfig

# Logger
logger = logging.getLogger(__name__)


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
    collections: Optional[List[str]] = Field(
        None, description="검색할 컬렉션 ID 목록 (예: ['chungjinkorea', 'onehago'])"
    )
    materials: Optional[List[str]] = Field(
        None, description="재질 필터 (예: ['PET', 'PE', '유리'])"
    )


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
    exact_capacity: Optional[float] = None
    collections_searched: Optional[List[str]] = Field(None, description="검색에 사용된 컬렉션 목록")


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


class VLMQueryRequest(BaseModel):
    """VLM 이미지 검색 요청"""

    image_url: Optional[str] = Field(None, description="이미지 URL")
    image_base64: Optional[str] = Field(None, description="Base64 인코딩된 이미지")
    query: str = Field(..., description="이미지에 대한 질문 또는 검색 쿼리")


class VLMQueryResponse(BaseModel):
    """VLM 이미지 검색 응답"""

    query: str
    response: str
    model_used: str
    processing_time: float


# Router 생성
router = APIRouter(prefix="/chat", tags=["chat"])

# 전역 인스턴스
_conv_manager: Optional[ConversationManager] = None
_contextual_rag: Optional[ContextualRAG] = None
_rag_pipeline: Optional[RAGPipeline] = None
_unified_llm: Optional[UnifiedLLMService] = None

# Feature flag: Vector RAG 사용 여부
USE_VECTOR_RAG = os.getenv("USE_VECTOR_RAG", "true").lower() == "true"


def get_conv_manager() -> ConversationManager:
    """ConversationManager 싱글톤"""
    global _conv_manager
    if _conv_manager is None:
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = os.getenv("REDIS_PORT", "6379")
        redis_url = f"redis://{redis_host}:{redis_port}/0"
        _conv_manager = ConversationManager(redis_url=redis_url)
    return _conv_manager


def get_contextual_rag() -> ContextualRAG:
    """ContextualRAG 싱글톤"""
    global _contextual_rag
    if _contextual_rag is None:
        _contextual_rag = ContextualRAG(
            conv_manager=get_conv_manager(),
            intent_classifier=get_intent_classifier(),
            reference_resolver=get_reference_resolver(),
        )
    return _contextual_rag


def get_rag_pipeline() -> RAGPipeline:
    """RAG Pipeline 싱글톤 (Vector Search)"""
    global _rag_pipeline
    if _rag_pipeline is None:
        # Simple loader/splitter for initialized pipeline
        class SimpleLoader:
            def load_documents(self, paths):
                return []

        class SimpleSplitter:
            def split_documents(self, documents):
                return documents

        embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2")

        # Docker environment: use service names
        qdrant_host = os.getenv("QDRANT_HOST", "qdrant")
        qdrant_port = os.getenv("QDRANT_HTTP_PORT", "6333")
        qdrant_url = f"http://{qdrant_host}:{qdrant_port}"

        qdrant_client = QdrantClient(url=qdrant_url)

        _rag_pipeline = RAGPipeline(
            loader=SimpleLoader(),
            text_splitter=SimpleSplitter(),
            embedding_model=embedding_service,
            vector_db=qdrant_client,
            collection_name="products",
            ollama_url="http://localhost:11434",
            ollama_model="qwen2.5:7b-instruct",
        )

    return _rag_pipeline


def get_unified_llm() -> UnifiedLLMService:
    """UnifiedLLMService 싱글톤 (NexaAI + Ollama hybrid)"""
    global _unified_llm
    if _unified_llm is None:
        # NexaAI configuration
        nexa_host = os.getenv("NEXA_HOST", "localhost")
        nexa_port = os.getenv("NEXA_PORT", "8080")
        nexa_vlm_model = os.getenv("NEXA_VLM_MODEL", "NexaAI/Qwen3-VL-4B-Instruct-GGUF")
        nexa_config = NexaConfig(
            base_url=f"http://{nexa_host}:{nexa_port}/v1",
            default_text_model="Qwen3-1.7B",
            default_vision_model=nexa_vlm_model,
            default_embedding_model="EmbeddingGemma"
        )

        # Ollama configuration
        ollama_host = os.getenv("OLLAMA_HOST", "localhost")
        ollama_port = os.getenv("OLLAMA_PORT", "11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "seungduk-yanolja/EEVE-Korean-Instruct-7B-v2.0-Preview")
        ollama_config = OllamaConfig(
            base_url=f"http://{ollama_host}:{ollama_port}",
            default_model=ollama_model
        )

        # Router configuration (enable_nexa/enable_ollama will be set by UnifiedLLMService)
        router_config = {
            "simple_threshold": 0.3,
            "complex_threshold": 0.7
        }

        _unified_llm = UnifiedLLMService(
            nexa_config=nexa_config,
            ollama_config=ollama_config,
            router_config=router_config
        )

    return _unified_llm


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

    return CreateSessionResponse(session_id=session_id, created_at=session["created_at"])


@router.post("/query", response_model=ChatQueryResponse)
async def chat_query(request: ChatQueryRequest):
    """
    컨텍스트 기반 채팅 쿼리

    Args:
        request: 채팅 쿼리 요청

    Returns:
        쿼리 응답
    """
    try:
        if USE_VECTOR_RAG:
            # Multi-collection Vector RAG 사용
            import sys
            from pathlib import Path

            # Add skill to path
            skill_path = Path(__file__).parent.parent.parent / ".claude/skills/rag-pipeline/scripts"
            sys.path.insert(0, str(skill_path))

            from skill import rag_query as skill_rag_query

            # Skill을 통한 multi-collection RAG query
            skill_result = skill_rag_query(
                {
                    "question": request.query,
                    "top_k": 100,  # Increased for infinite scroll
                    "collections": request.collections,  # Pass collections from request
                    "materials": request.materials,  # Pass material filters
                }
            )

            if skill_result["status"] != "success":
                raise HTTPException(
                    status_code=500, detail=skill_result.get("error", "RAG query failed")
                )

            # 제품 정보 포맷팅
            products = []
            for result in skill_result["sources"]:
                metadata = result.get("metadata", {})

                # Capacity 포맷팅 (소수점 제거)
                capacity_str = ""
                if metadata.get("capacity_value"):
                    capacity_unit = metadata.get("capacity_unit", "ml")
                    capacity_value = metadata["capacity_value"]
                    # 정수로 변환 가능하면 소수점 제거
                    if isinstance(capacity_value, (int, float)) and capacity_value == int(
                        capacity_value
                    ):
                        capacity_str = f"{int(capacity_value)}{capacity_unit}"
                    else:
                        capacity_str = f"{capacity_value}{capacity_unit}"

                # Material 포맷팅 (리스트 → 문자열)
                materials = metadata.get("materials", [])
                material_str = ", ".join(materials) if materials else ""

                # Neck size 포맷팅
                neck_size_str = ""
                if metadata.get("neck_size"):
                    neck_size_str = f"{metadata['neck_size']}mm"

                # Image paths 파싱 (모든 이미지 경로 포함)
                image_urls = []
                if metadata.get("image_paths_json"):
                    try:
                        image_urls = json.loads(metadata["image_paths_json"])
                    except:
                        pass

                # Fallback to main image if no images array
                if not image_urls and metadata.get("main_image_path"):
                    image_urls = [metadata["main_image_path"]]

                # MOQ 포맷팅
                moq_str = ""
                if metadata.get("moq"):
                    moq_str = f"{metadata['moq']:,}개"

                products.append(
                    {
                        "idx": metadata.get("product_id", ""),
                        "product_name": metadata.get("product_name", ""),
                        "product_code": metadata.get("product_code", ""),
                        "material": material_str,
                        "specifications": {
                            "capacity": capacity_str,
                            "neck_size": neck_size_str,
                            "moq": moq_str,
                            "origin": metadata.get("origin", ""),
                            "size_dimensions": metadata.get("size_dimensions", ""),
                        },
                        "company": {
                            "name": metadata.get("company_name", ""),
                            "email": metadata.get("email", ""),
                            "phone": metadata.get("phone", ""),
                            "fax": metadata.get("fax", ""),
                            "contact_person": metadata.get("contact_person", ""),
                        },
                        "image_url": (
                            image_urls[0] if image_urls else ""
                        ),  # 메인 이미지 (backward compatibility)
                        "image_urls": image_urls,  # 모든 이미지 (갤러리용)
                        "score": result.get("score", 0.0),
                        "source_collection": metadata.get("source_collection", "unknown"),
                    }
                )

            # Generate enhanced response using UnifiedLLMService
            llm_service = get_unified_llm()

            # Determine if this is a product search or general conversation
            if products:
                # Product search with results - provide context
                product_context = "\n".join([
                    f"- {p['product_name']} ({p['material']}, {p['specifications'].get('capacity', 'N/A')})"
                    for p in products[:5]  # Top 5 products
                ])

                enhanced_prompt = f"""사용자 질문: {request.query}

검색된 제품:
{product_context}

총 {len(products)}개의 제품을 찾았습니다. 사용자에게 친절하고 간결하게 검색 결과를 설명해주세요."""
            else:
                # No products found - determine if general conversation or failed search
                intent = skill_result.get("intent", {})
                intent_type = intent.get("intent", "unknown") if isinstance(intent, dict) else "unknown"

                if intent_type == "search" or intent_type == "product_search":
                    # Product search intent but no results
                    enhanced_prompt = f"""사용자가 다음과 같이 제품을 검색했지만 결과가 없습니다:
"{request.query}"

사용자에게 친절하게:
1. 검색 결과가 없다고 알려주고
2. 다른 키워드로 검색하도록 제안하거나
3. 비슷한 대안을 제시해주세요.

간결하고 도움이 되는 응답을 작성하세요."""
                else:
                    # General conversation - just respond naturally
                    enhanced_prompt = f"""사용자가 다음과 같이 말했습니다:
"{request.query}"

제품 검색 시스템이지만, 일반적인 대화나 질문에도 친절하게 응답해주세요.
간결하고 도움이 되는 응답을 작성하세요."""

            # Generate response using hybrid LLM (auto-routes to NexaAI or Ollama)
            try:
                llm_response = await llm_service.generate(
                    prompt=enhanced_prompt,
                    max_tokens=200,
                    temperature=0.7
                )
            except Exception as e:
                # Fallback to skill answer if LLM fails
                logger.error(f"LLM generation failed: {e}")
                llm_response = skill_result.get("answer", "죄송합니다. 응답 생성 중 오류가 발생했습니다.")

            return ChatQueryResponse(
                session_id=request.session_id,
                query=request.query,
                intent={
                    "type": "product_search",
                    "confidence": float(skill_result.get("confidence", 0.0)),
                },
                reference_resolved=False,
                products=products,
                response=llm_response,
                total_count=len(products),
                matched_profile=None,
                exact_capacity=None,
                collections_searched=skill_result.get("collections", []),
            )

        else:
            # 기존 파일 기반 검색
            contextual_rag = get_contextual_rag()
            result = await contextual_rag.query(
                session_id=request.session_id, user_query=request.query
            )

            # Add LLM enhancement to file-based search results
            llm_service = get_unified_llm()
            products = result.get("products", [])

            if products:
                # Products found - enhance with LLM
                product_context = "\n".join([
                    f"- {p.get('product_name', 'N/A')} ({p.get('material', 'N/A')})"
                    for p in products[:5]
                ])

                enhanced_prompt = f"""사용자 질문: {request.query}

검색된 제품:
{product_context}

총 {len(products)}개의 제품을 찾았습니다. 사용자에게 친절하고 간결하게 검색 결과를 설명해주세요."""
            else:
                # No products - general conversation
                enhanced_prompt = f"""사용자가 다음과 같이 말했습니다:
"{request.query}"

제품 검색 시스템이지만, 일반적인 대화나 질문에도 친절하게 응답해주세요.
간결하고 도움이 되는 응답을 작성하세요."""

            try:
                llm_response = await llm_service.generate(
                    prompt=enhanced_prompt,
                    max_tokens=200,
                    temperature=0.7
                )
                result["response"] = llm_response
            except Exception as e:
                logger.error(f"LLM generation failed in file-based search: {e}")
                # Keep original response if LLM fails

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
                await websocket.send_json({"error": "쿼리가 없습니다."})
                continue

            # 쿼리 처리
            try:
                result = await contextual_rag.query(session_id=session_id, user_query=query)

                # 응답 전송
                await websocket.send_json({"type": "response", "data": result})

            except Exception as e:
                await websocket.send_json({"type": "error", "error": str(e)})

    except WebSocketDisconnect:
        connection_manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket 오류: {e}")
        connection_manager.disconnect(session_id)


# Health check
@router.get("/collections")
async def list_collections(enabled_only: bool = True, embedded_only: bool = True):
    """
    사용 가능한 컬렉션 목록 조회

    Args:
        enabled_only: 활성화된 컬렉션만 조회
        embedded_only: 임베딩된 컬렉션만 조회

    Returns:
        컬렉션 목록
    """
    try:
        import sys
        from pathlib import Path

        # Add skill to path
        skill_path = Path(__file__).parent.parent.parent / ".claude/skills/rag-pipeline/scripts"
        sys.path.insert(0, str(skill_path))

        from skill import list_collections as skill_list_collections

        result = skill_list_collections(
            {"enabled_only": enabled_only, "embedded_only": embedded_only}
        )

        if result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=result.get("error", "Failed to list collections")
            )

        return {"status": "success", "collections": result["collections"], "total": result["total"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vlm_query", response_model=VLMQueryResponse)
async def vlm_query(request: VLMQueryRequest):
    """
    VLM 이미지 검색 엔드포인트

    Args:
        request: VLM 쿼리 요청 (이미지 URL 또는 base64, 텍스트 쿼리)

    Returns:
        VLM 분석 결과
    """
    try:
        start_time = time.time()

        # Validate input
        if not request.image_url and not request.image_base64:
            raise HTTPException(
                status_code=400,
                detail="Either image_url or image_base64 must be provided"
            )

        # Get unified LLM service
        unified_llm = get_unified_llm()

        # Check if NexaAI is enabled
        if not unified_llm.router_config.get("enable_nexa", False):
            raise HTTPException(
                status_code=503,
                detail="VLM service is not enabled. Set ENABLE_NEXA=true in environment."
            )

        # Prepare image input
        if request.image_url:
            image_input = request.image_url
        else:
            # For base64, prefix with data URI scheme
            image_input = f"data:image/jpeg;base64,{request.image_base64}"

        # Call VLM through NexaAI
        try:
            response_text = await unified_llm.vision_query(
                image=image_input,
                prompt=request.query
            )
        except AttributeError:
            # Fallback if vision_query is not implemented
            raise HTTPException(
                status_code=501,
                detail="VLM vision_query method not implemented in UnifiedLLMService"
            )
        except Exception as e:
            logger.error(f"VLM query failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"VLM processing failed: {str(e)}"
            )

        processing_time = time.time() - start_time

        return VLMQueryResponse(
            query=request.query,
            response=response_text,
            model_used=os.getenv("NEXA_VLM_MODEL", "NexaAI/Qwen3-VL-4B-Instruct-GGUF"),
            processing_time=processing_time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"VLM query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
                "contextual_rag": "ok",
            },
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
