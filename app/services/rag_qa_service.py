"""
RAG Q&A Service
제품 데이터를 기반으로 한 질문-답변 서비스
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import httpx

logger = logging.getLogger(__name__)


@dataclass
class QARequest:
    """Q&A 요청 데이터"""
    question: str
    collection: str = "products_all"
    top_k: int = 3
    customer_id: Optional[str] = None


@dataclass
class QAResponse:
    """Q&A 응답 데이터"""
    question: str
    answer: str
    related_products: List[Dict[str, Any]]
    confidence: float
    qa_id: str
    timestamp: str


class RAGQAService:
    """RAG 기반 Q&A 서비스"""

    def __init__(
        self,
        qdrant_client: QdrantClient,
        embedding_model: SentenceTransformer,
        ollama_url: str = "http://localhost:11434",
        model_name: str = "qwen2.5:3b"
    ):
        self.qdrant = qdrant_client
        self.embedder = embedding_model
        self.ollama_url = ollama_url
        self.model_name = model_name

        logger.info(f"✅ RAGQAService initialized with model: {model_name}")

    async def search_products(
        self,
        query: str,
        collection: str = "products_all",
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """제품 벡터 검색"""
        try:
            # 쿼리 임베딩
            query_embedding = self.embedder.encode(query, convert_to_numpy=True).tolist()

            # Qdrant 검색
            results = self.qdrant.search(
                collection_name=collection,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=0.3  # 최소 유사도
            )

            # 결과 포맷팅
            products = []
            for result in results:
                product = {
                    "product_id": result.payload.get("product_id"),
                    "product_name": result.payload.get("product_name"),
                    "category": result.payload.get("category"),
                    "similarity_score": float(result.score),
                }
                products.append(product)

            logger.info(f"Found {len(products)} products for query: '{query}'")
            return products

        except Exception as e:
            logger.error(f"Product search error: {e}")
            return []

    async def generate_answer(
        self,
        question: str,
        products: List[Dict[str, Any]]
    ) -> tuple[str, float]:
        """LLM을 사용한 답변 생성"""
        try:
            # 컨텍스트 구성
            context = self._build_context(products)

            # 프롬프트 생성
            prompt = f"""당신은 제조업 제품 전문가입니다. 아래 제품 정보를 바탕으로 사용자의 질문에 친절하고 정확하게 답변해주세요.

[제품 정보]
{context}

[사용자 질문]
{question}

[답변 규칙]
1. 제품 정보를 기반으로 정확하게 답변
2. 제품명, 카테고리, 특징을 명확히 언급
3. 추천하는 경우 이유를 설명
4. 존재하지 않는 정보는 추측하지 말것
5. 한국어로 자연스럽게 답변

답변:"""

            # Ollama API 호출
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "top_k": 40,
                        }
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    answer = result.get("response", "답변을 생성할 수 없습니다.")

                    # 신뢰도 계산 (제품 유사도 평균)
                    if products:
                        confidence = sum(p["similarity_score"] for p in products) / len(products)
                    else:
                        confidence = 0.0

                    logger.info(f"Generated answer with confidence: {confidence:.2f}")
                    return answer.strip(), confidence

                else:
                    logger.error(f"Ollama API error: {response.status_code}")
                    return self._fallback_answer(question, products), 0.5

        except httpx.TimeoutException:
            logger.error("Ollama API timeout")
            return self._fallback_answer(question, products), 0.5
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            return self._fallback_answer(question, products), 0.5

    def _build_context(self, products: List[Dict[str, Any]]) -> str:
        """제품 정보를 컨텍스트로 변환"""
        if not products:
            return "검색된 제품이 없습니다."

        context_parts = []
        for idx, product in enumerate(products, 1):
            part = f"{idx}. {product['product_name']} ({product['category']})"
            part += f" - 유사도: {product['similarity_score']:.2f}"
            context_parts.append(part)

        return "\n".join(context_parts)

    def _fallback_answer(
        self,
        question: str,
        products: List[Dict[str, Any]]
    ) -> str:
        """Fallback 답변 (LLM 실패 시)"""
        if not products:
            return f"죄송합니다. '{question}'에 대한 관련 제품을 찾지 못했습니다. 다른 키워드로 검색해보시겠어요?"

        answer_parts = [
            f"'{question}'에 대한 추천 제품입니다:",
            ""
        ]

        for idx, product in enumerate(products, 1):
            answer_parts.append(
                f"{idx}. **{product['product_name']}** ({product['category']})"
            )

        answer_parts.append("")
        answer_parts.append("더 자세한 정보가 필요하시면 구체적인 질문을 해주세요.")

        return "\n".join(answer_parts)

    async def answer_question(self, request: QARequest) -> QAResponse:
        """질문에 답변"""
        try:
            logger.info(f"Q&A request: {request.question}")

            # 1. 제품 검색
            products = await self.search_products(
                query=request.question,
                collection=request.collection,
                top_k=request.top_k
            )

            # 2. LLM 답변 생성
            answer, confidence = await self.generate_answer(
                question=request.question,
                products=products
            )

            # 3. 응답 구성
            qa_id = f"qa_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            response = QAResponse(
                question=request.question,
                answer=answer,
                related_products=products,
                confidence=confidence,
                qa_id=qa_id,
                timestamp=datetime.now().isoformat()
            )

            logger.info(f"Q&A response generated: {qa_id}")
            return response

        except Exception as e:
            logger.error(f"Q&A error: {e}")
            # 에러 시에도 응답 반환
            return QAResponse(
                question=request.question,
                answer=f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}",
                related_products=[],
                confidence=0.0,
                qa_id=f"qa_error_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                timestamp=datetime.now().isoformat()
            )
