"""
RAG Q&A Service
제품 데이터를 기반으로 한 질문-답변 서비스
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from apps.api.utils.product_utils import (
    batch_validate_products,
    enrich_product_with_metadata,
    generate_image_urls,
    validate_product_integrity,
)

logger = logging.getLogger(__name__)


@dataclass
class QARequest:
    """Q&A 요청 데이터"""

    question: str
    collection: str = "products_all"
    top_k: int = 3
    return_all: bool = False
    min_integrity_score: float = 0.0
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
        model_name: str = "qwen2.5:3b",
    ):
        self.qdrant = qdrant_client
        self.embedder = embedding_model
        self.ollama_url = ollama_url
        self.model_name = model_name

        # Compile regex patterns once for better performance
        self._capacity_ml_pattern = re.compile(r"(\d+)\s*(ml|미리)")
        self._capacity_g_pattern = re.compile(r"(\d+)\s*g\b")
        self._product_ml_pattern = re.compile(r"(\d+)\s*ml")
        self._product_g_pattern = re.compile(r"(\d+)\s*g\b")

        logger.info(f"✅ RAGQAService initialized with model: {model_name}")

    def _extract_capacity_from_query(self, query: str) -> Optional[str]:
        """쿼리에서 용량 추출: "50ml 용기" → "50ml", "50g 크림" → "50g"

        ml과 g를 구분하여 정확히 매칭합니다.

        Args:
            query: 사용자 쿼리 문자열

        Returns:
            추출된 용량 (예: "50ml", "50g") 또는 None
        """
        # ml 우선 검색 (50ml, 50미리)
        match = self._capacity_ml_pattern.search(query.lower())
        if match:
            return match.group(1) + "ml"

        # g 검색 (50g)
        match = self._capacity_g_pattern.search(query.lower())
        if match:
            return match.group(1) + "g"

        return None

    def _extract_capacity_from_product_name(self, product_name: str) -> Optional[str]:
        """제품명에서 용량 추출: "50ml 헤비브로우용기" → "50ml", "50g 크림용기" → "50g"

        ml과 g를 구분하여 첫 번째 용량 값을 추출합니다.

        Args:
            product_name: 제품명 문자열

        Returns:
            추출된 용량 (예: "50ml", "50g") 또는 None
        """
        # ml 우선 검색
        match = self._product_ml_pattern.search(product_name.lower())
        if match:
            return match.group(1) + "ml"

        # g 검색
        match = self._product_g_pattern.search(product_name.lower())
        if match:
            return match.group(1) + "g"

        return None

    def _extract_spec_from_name(self, product_name: str) -> Dict[str, str]:
        """제품명에서 스펙 추출 (용량, 종류 등)

        예: "50ml 헤비브로우용기" -> {capacity: "50ml", type: "헤비브로우"}
        """
        import re

        spec = {}

        # 용량 추출 (ml)
        capacity_match = re.search(r"(\d+ml)", product_name)
        if capacity_match:
            spec["capacity"] = capacity_match.group(1)

        # 종류 추출 (헤비, 다층, 파우더 등)
        if "헤비" in product_name:
            spec["type"] = "헤비브로우"
        elif "다층" in product_name:
            spec["type"] = "다층브로우"
        elif "파우더" in product_name:
            spec["type"] = "파우더브로우"
        else:
            spec["type"] = "일반브로우"

        return spec

    def _extract_material_from_query(self, query: str) -> Optional[str]:
        """쿼리에서 재질 추출: "PET용기" → "PET", "PE 병" → "PE"

        Args:
            query: 사용자 쿼리 문자열

        Returns:
            추출된 재질 (PET, PE, PP, PETG, Other) 또는 None
        """
        query_upper = query.upper()

        # 정확한 재질 매칭 (우선순위: PETG > PET > PE > PP)
        if "PETG" in query_upper:
            return "PETG"
        elif "PET" in query_upper:
            return "PET"
        elif "PE" in query_upper and "PET" not in query_upper:
            return "PE"
        elif "PP" in query_upper:
            return "PP"

        return None

    async def search_products(
        self,
        query: str,
        collection: str = "products_all",
        top_k: int = 3,
        group_by_spec: bool = True,
        return_all: bool = False,
        min_integrity_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """제품 벡터 검색 (엄격한 용량 + 재질 필터링)

        개선 사항:
        - 용량: ml과 g를 구분하여 정확히 매칭 (50ml ≠ 50g)
        - 재질: PET, PE, PP, PETG 정확히 필터링
        - 엄격한 필터링: 조건이 명시된 경우 정확히 일치하는 제품만 반환
        - return_all=True: 모든 필터링된 결과 반환 (top_k 무시)
        - 이미지 URL 자동 생성 및 무결성 검증
        - min_integrity_score: 최소 무결성 점수 필터링 (0.0~1.0)

        Args:
            query: 검색 쿼리
            collection: Qdrant 컬렉션명
            top_k: 반환할 결과 개수 (return_all=False일 때만 적용)
            group_by_spec: 스펙별 그룹핑 여부
            return_all: True면 모든 필터링된 결과 반환, False면 top_k까지만
            min_integrity_score: 최소 무결성 점수 (0.0: 모두 허용, 1.0: 완전한 제품만)

        Returns:
            제품 리스트 (이미지 URL, 무결성 점수 포함)
        """
        try:
            # 1. 쿼리에서 용량 + 재질 추출
            query_capacity = self._extract_capacity_from_query(query)
            query_material = self._extract_material_from_query(query)

            # 2. 쿼리 임베딩
            query_embedding = self.embedder.encode(query, convert_to_numpy=True).tolist()

            # 3. 충분한 결과를 위해 200개 검색
            search_limit = 200

            # 4. Qdrant 검색 (named vector format for multi-vector collection)
            results = self.qdrant.search(
                collection_name=collection,
                query_vector=("text", query_embedding),  # Use named "text" vector
                limit=search_limit,
                score_threshold=0.3,  # 최소 유사도
            )

            # 5. 엄격한 필터링 (용량 + 재질)
            if query_capacity or query_material:
                filtered_results = []
                for result in results:
                    product_name = result.payload.get("product_name", "")
                    category = result.payload.get("category", "")

                    # 용량 체크
                    if query_capacity:
                        product_capacity = self._extract_capacity_from_product_name(product_name)
                        if product_capacity != query_capacity:
                            continue  # 용량 불일치 → 제외

                    # 재질 체크 (category에서 추출: "Bottle/PET" → "PET")
                    if query_material:
                        product_material = category.split("/")[-1] if "/" in category else None
                        if product_material != query_material:
                            continue  # 재질 불일치 → 제외

                    filtered_results.append(result)

                results = filtered_results
                filter_desc = []
                if query_capacity:
                    filter_desc.append(f"용량={query_capacity}")
                if query_material:
                    filter_desc.append(f"재질={query_material}")
                logger.info(f"엄격한 필터링: {', '.join(filter_desc)} - {len(results)}개 제품 매칭")

            if group_by_spec:
                # 스펙 기반 그룹핑
                spec_groups = {}

                for result in results:
                    product_name = result.payload.get("product_name")
                    spec = self._extract_spec_from_name(product_name)

                    # Qdrant payload에서 specifications 추출 (제품 코드 포함)
                    payload_specs = result.payload.get("specifications", {})
                    product_code = payload_specs.get("제품 코드", "")

                    # 제품명에 제품 코드 추가
                    product_name_with_code = product_name
                    if product_code and product_code != "N/A":
                        product_name_with_code = f"{product_name}({product_code})"

                    spec_key = f"{spec.get('capacity', 'unknown')}_{spec.get('type', 'unknown')}"

                    if spec_key not in spec_groups:
                        spec_groups[spec_key] = []

                    product = {
                        "product_id": result.payload.get("product_id"),
                        "product_name": product_name_with_code,
                        "category": result.payload.get("category"),
                        "similarity_score": float(result.score),
                        "specification": spec,
                        "specifications": payload_specs,
                        "print_area_url": result.payload.get("print_area_url"),
                    }
                    spec_groups[spec_key].append(product)

                # 각 스펙 그룹에서 적절한 개수 선택
                unique_products = []
                for spec_key, products_in_group in spec_groups.items():
                    # 유사도 순으로 정렬
                    sorted_products = sorted(
                        products_in_group, key=lambda x: x["similarity_score"], reverse=True
                    )

                    # return_all=True면 전체, 아니면 top_k까지
                    if return_all:
                        unique_products.extend(sorted_products)
                    else:
                        unique_products.extend(sorted_products[:top_k])

                # 전체 유사도 기준으로 다시 정렬
                unique_products.sort(key=lambda x: x["similarity_score"], reverse=True)

                logger.info(
                    f"Found {len(unique_products)} products grouped by spec for query: '{query}' "
                    f"(searched {len(results)} total, {len(spec_groups)} spec groups, return_all={return_all})"
                )
            else:
                # 기존 방식: product_name 기준 deduplication
                seen_product_names = {}
                unique_products = []

                for result in results:
                    product_name = result.payload.get("product_name")

                    if product_name in seen_product_names:
                        logger.debug(f"Skipping duplicate: {product_name}")
                        continue

                    spec = self._extract_spec_from_name(product_name)

                    # Qdrant payload에서 specifications 추출 (제품 코드 포함)
                    payload_specs = result.payload.get("specifications", {})
                    product_code = payload_specs.get("제품 코드", "")

                    # 제품명에 제품 코드 추가
                    product_name_with_code = product_name
                    if product_code and product_code != "N/A":
                        product_name_with_code = f"{product_name}({product_code})"

                    product = {
                        "product_id": result.payload.get("product_id"),
                        "product_name": product_name_with_code,
                        "category": result.payload.get("category"),
                        "similarity_score": float(result.score),
                        "specification": spec,
                        "specifications": payload_specs,
                        "print_area_url": result.payload.get("print_area_url"),
                    }

                    unique_products.append(product)
                    seen_product_names[product_name] = product

                    # return_all=False일 때만 top_k 제한 적용
                    if not return_all and len(unique_products) >= top_k:
                        break

                logger.info(
                    f"Found {len(unique_products)} unique products for query: '{query}' "
                    f"(return_all={return_all})"
                )

            # 6. 데이터 무결성 검증 및 이미지 URL 생성
            validated_products = batch_validate_products(
                unique_products,
                require_images=False,  # 경고만 발생 (필수 아님)
                require_specs=False,  # 경고만 발생 (필수 아님)
                min_integrity_score=min_integrity_score,
            )

            # 7. 메타데이터 보강
            enriched_products = [
                enrich_product_with_metadata(p, include_image_count=True, include_spec_count=True)
                for p in validated_products
            ]

            logger.info(
                f"✅ Final result: {len(enriched_products)} products with integrity validation "
                f"(min_score={min_integrity_score})"
            )

            return enriched_products

        except Exception as e:
            logger.error(f"Product search error: {e}")
            return []

    async def generate_answer(
        self, question: str, products: List[Dict[str, Any]]
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
                        },
                    },
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

    def _fallback_answer(self, question: str, products: List[Dict[str, Any]]) -> str:
        """Fallback 답변 (LLM 실패 시)"""
        if not products:
            return f"죄송합니다. '{question}'에 대한 관련 제품을 찾지 못했습니다. 다른 키워드로 검색해보시겠어요?"

        answer_parts = [f"'{question}'에 대한 추천 제품입니다:", ""]

        for idx, product in enumerate(products, 1):
            answer_parts.append(f"{idx}. **{product['product_name']}** ({product['category']})")

        answer_parts.append("")
        answer_parts.append("더 자세한 정보가 필요하시면 구체적인 질문을 해주세요.")

        return "\n".join(answer_parts)

    async def answer_question(self, request: QARequest) -> QAResponse:
        """질문에 답변"""
        try:
            logger.info(f"Q&A request: {request.question}")

            # 1. 제품 검색 (새로운 파라미터 추가)
            products = await self.search_products(
                query=request.question,
                collection=request.collection,
                top_k=request.top_k,
                return_all=request.return_all,
                min_integrity_score=request.min_integrity_score,
            )

            # 2. LLM 답변 생성
            answer, confidence = await self.generate_answer(
                question=request.question, products=products
            )

            # 3. 응답 구성
            qa_id = f"qa_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            response = QAResponse(
                question=request.question,
                answer=answer,
                related_products=products,
                confidence=confidence,
                qa_id=qa_id,
                timestamp=datetime.now().isoformat(),
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
                timestamp=datetime.now().isoformat(),
            )
