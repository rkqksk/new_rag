"""
상담 시스템 서비스
제품 추천, 불량 문의 등 고객 상담 로직
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ConsultationRequest(BaseModel):
    """상담 요청 데이터"""
    query: str
    customer_id: Optional[str] = None
    context: Optional[str] = None
    consultation_type: str  # "product_recommendation" or "defect_inquiry"


class ConsultationResponse(BaseModel):
    """상담 응답 데이터"""
    consultation_id: str
    query: str
    consultation_type: str
    response: str
    related_products: List[Dict[str, Any]] = []
    confidence_score: float
    source_documents: List[Dict[str, Any]] = []
    timestamp: str


class ConsultationService:
    """상담 시스템 서비스"""

    def __init__(self, search_client, embedding_model, llm_client):
        """
        Args:
            search_client: Qdrant 검색 클라이언트
            embedding_model: 임베딩 모델
            llm_client: LLM 클라이언트 (Ollama 또는 다른 LLM)
        """
        self.search_client = search_client
        self.embedding_model = embedding_model
        self.llm_client = llm_client
        self.consultation_counter = 0

    async def recommend_product(self, request: ConsultationRequest) -> ConsultationResponse:
        """
        제품 추천 상담

        Args:
            request: 상담 요청

        Returns:
            ConsultationResponse: 상담 응답
        """
        logger.info(f"제품 추천 상담 시작: {request.query}")

        # 1. 사용자 쿼리 임베딩
        query_embedding = self.embedding_model.encode(request.query).tolist()

        # 2. 벡터DB에서 유사한 제품 검색
        search_results = self.search_client.search(
            collection_name="documents",
            query_vector=query_embedding,
            limit=5
        )

        # 3. 검색 결과를 문서로 변환
        source_docs = []
        related_products = []

        for result in search_results:
            doc_info = {
                "product_name": result.payload.get("filename", "Unknown"),
                "score": result.score,
                "text": result.payload.get("text", "")[:200],
            }
            source_docs.append(doc_info)

            # 신뢰도가 높은 것만 추천 제품으로
            if result.score > 0.7:
                related_products.append({
                    "name": result.payload.get("filename", "Unknown"),
                    "confidence": result.score,
                    "description": result.payload.get("text", "")[:300]
                })

        # 4. LLM에 기반한 추천 이유 생성
        context_text = "\n".join([
            f"- {doc['product_name']}: {doc['text']}"
            for doc in source_docs[:3]
        ])

        prompt = f"""사용자 요청: {request.query}

다음 정보를 바탕으로 제품을 추천해주세요:
{context_text}

추천 이유를 간단하게 설명해주세요."""

        recommendation_reason = await self._generate_response(prompt)

        # 5. 응답 생성
        self.consultation_counter += 1
        response = ConsultationResponse(
            consultation_id=f"CONSULT_{self.consultation_counter:06d}",
            query=request.query,
            consultation_type="product_recommendation",
            response=recommendation_reason,
            related_products=related_products,
            confidence_score=max([p["confidence"] for p in related_products]) if related_products else 0.0,
            source_documents=source_docs,
            timestamp=datetime.now().isoformat()
        )

        logger.info(f"제품 추천 상담 완료: {response.consultation_id}")
        return response

    async def handle_defect_inquiry(self, request: ConsultationRequest) -> ConsultationResponse:
        """
        불량 문의 상담

        Args:
            request: 상담 요청

        Returns:
            ConsultationResponse: 상담 응답
        """
        logger.info(f"불량 문의 시작: {request.query}")

        # 1. 사용자 쿼리 임베딩
        query_embedding = self.embedding_model.encode(request.query).tolist()

        # 2. 벡터DB에서 유사한 불량 관련 문서 검색
        search_results = self.search_client.search(
            collection_name="documents",
            query_vector=query_embedding,
            limit=5
        )

        # 3. 검색 결과 처리
        source_docs = []
        for result in search_results:
            doc_info = {
                "title": result.payload.get("filename", "Unknown"),
                "score": result.score,
                "content": result.payload.get("text", "")[:200],
            }
            source_docs.append(doc_info)

        # 4. LLM에 기반한 불량 진단 생성
        context_text = "\n".join([
            f"- {doc['title']}: {doc['content']}"
            for doc in source_docs[:3]
        ])

        prompt = f"""사용자 불량 문의: {request.query}

다음 정보를 바탕으로 불량 원인을 진단하고 해결 방안을 제시해주세요:
{context_text}

진단 결과와 추천 조치를 설명해주세요."""

        diagnosis = await self._generate_response(prompt)

        # 5. 응답 생성
        self.consultation_counter += 1
        response = ConsultationResponse(
            consultation_id=f"DEFECT_{self.consultation_counter:06d}",
            query=request.query,
            consultation_type="defect_inquiry",
            response=diagnosis,
            confidence_score=max([doc["score"] for doc in source_docs]) if source_docs else 0.0,
            source_documents=source_docs,
            timestamp=datetime.now().isoformat()
        )

        logger.info(f"불량 문의 상담 완료: {response.consultation_id}")
        return response

    async def _generate_response(self, prompt: str) -> str:
        """
        LLM을 통한 응답 생성

        Args:
            prompt: 프롬프트

        Returns:
            str: 생성된 응답
        """
        try:
            # Ollama를 통한 로컬 LLM 호출
            # 현재는 간단한 응답 생성
            response = f"분석 결과: {prompt[:100]}..."
            logger.info(f"LLM 응답 생성 완료")
            return response
        except Exception as e:
            logger.error(f"LLM 응답 생성 실패: {e}")
            return "죄송합니다. 현재 상담을 처리할 수 없습니다. 나중에 다시 시도해주세요."
