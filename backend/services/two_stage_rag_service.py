"""
Two-Stage RAG Q&A Service
Stage 1: Planning with Claude Sonnet 4.5
Stage 2: Execution with Local LLM (Qwen) + Product Dictionary
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import anthropic
import httpx
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


@dataclass
class QueryPlan:
    """Query analysis and execution plan"""

    intent: str
    capacity_filter: Optional[str]
    material_preference: Optional[str]
    use_case: Optional[str]
    top_k: int
    search_strategy: str
    answer_template: str


class ProductDictionary:
    """Product enrichment dictionary loader"""

    def __init__(self, dictionary_path: str):
        self.dictionary_path = Path(dictionary_path)
        self.dictionary = self._load_dictionary()
        logger.info(f"✅ Loaded product dictionary: {len(self.dictionary)} products")

    def _load_dictionary(self) -> Dict[str, Any]:
        """Load product dictionary from JSON"""
        try:
            if not self.dictionary_path.exists():
                logger.warning(f"Dictionary file not found: {self.dictionary_path}")
                return {}

            with open(self.dictionary_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading dictionary: {e}")
            return {}

    def get_enriched_info(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get enriched information for a product"""
        return self.dictionary.get(product_id, {}).get("enriched_info")

    def enrich_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich product with dictionary information"""
        product_id = product.get("product_id")
        enriched_info = self.get_enriched_info(product_id)

        if enriched_info:
            product["enriched"] = enriched_info
            logger.debug(f"Enriched product: {product_id}")
        else:
            logger.debug(f"No enrichment for: {product_id}")

        return product


class TwoStageRAGService:
    """Two-stage RAG service with Sonnet planning and Qwen execution"""

    def __init__(
        self,
        qdrant_client: QdrantClient,
        embedding_model: SentenceTransformer,
        dictionary_path: str,
        anthropic_api_key: Optional[str] = None,
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "qwen2.5:3b",
    ):
        self.qdrant = qdrant_client
        self.embedder = embedding_model
        self.dictionary = ProductDictionary(dictionary_path)
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model

        # Initialize Anthropic client (optional for planning stage)
        if anthropic_api_key:
            self.anthropic = anthropic.Anthropic(api_key=anthropic_api_key)
            logger.info("✅ Anthropic client initialized for planning")
        else:
            self.anthropic = None
            logger.warning("⚠️ Anthropic client not initialized - using simple planning")

    async def plan_query(self, question: str) -> QueryPlan:
        """
        Stage 1: Planning with Claude Sonnet 4.5
        Analyze query intent and create execution plan
        """
        if not self.anthropic:
            # Fallback to simple planning
            return self._simple_plan(question)

        try:
            planning_prompt = f"""당신은 제품 검색 전문가입니다. 사용자 질문을 분석하고 최적의 검색 전략을 수립하세요.

[사용자 질문]
{question}

[분석 요청]
1. 의도 파악 (제품 추천, 정보 문의, 비교 등)
2. 용량 필터 (예: 50ml, 100ml) - 있다면 추출
3. 재질 선호도 (PE, PET, Glass 등) - 있다면 추출
4. 사용 용도 (에센스, 크림, 토너 등) - 있다면 추출
5. 검색할 제품 수 (top_k)
6. 검색 전략 (용량 우선, 재질 우선, 종합 검색)

[응답 형식 - JSON만 출력]
{{
  "intent": "제품 추천",
  "capacity_filter": "50ml",
  "material_preference": null,
  "use_case": "에센스",
  "top_k": 3,
  "search_strategy": "capacity_priority",
  "reasoning": "사용자가 50ml 용량의 에센스용 용기를 찾고 있음"
}}
"""

            response = self.anthropic.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1024,
                temperature=0.3,
                messages=[{"role": "user", "content": planning_prompt}],
            )

            result_text = response.content[0].text.strip()

            # Extract JSON from response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            plan_data = json.loads(result_text)

            # Create answer template
            answer_template = self._create_answer_template(plan_data)

            plan = QueryPlan(
                intent=plan_data.get("intent", "제품 추천"),
                capacity_filter=plan_data.get("capacity_filter"),
                material_preference=plan_data.get("material_preference"),
                use_case=plan_data.get("use_case"),
                top_k=plan_data.get("top_k", 3),
                search_strategy=plan_data.get("search_strategy", "comprehensive"),
                answer_template=answer_template,
            )

            logger.info(f"✅ Query plan created: {plan.intent} | top_k={plan.top_k}")
            return plan

        except Exception as e:
            logger.error(f"Planning error: {e}, using fallback")
            return self._simple_plan(question)

    def _simple_plan(self, question: str) -> QueryPlan:
        """Fallback simple planning without Sonnet"""
        import re

        # Extract capacity
        capacity_match = re.search(r"(\d+)\s*ml", question.lower())
        capacity = capacity_match.group(1) + "ml" if capacity_match else None

        # Detect use case
        use_case = None
        if any(kw in question for kw in ["에센스", "세럼"]):
            use_case = "에센스"
        elif "크림" in question:
            use_case = "크림"
        elif "토너" in question:
            use_case = "토너"

        return QueryPlan(
            intent="제품 추천",
            capacity_filter=capacity,
            material_preference=None,
            use_case=use_case,
            top_k=3,
            search_strategy="comprehensive",
            answer_template=self._create_answer_template(
                {"intent": "제품 추천", "capacity_filter": capacity, "use_case": use_case}
            ),
        )

    def _create_answer_template(self, plan_data: Dict) -> str:
        """Create customized answer template based on plan"""
        template = f"""당신은 화장품 용기 전문가입니다. 제품 상세 정보를 바탕으로 친절하고 전문적인 답변을 제공하세요.

[분석된 요청]
- 의도: {plan_data.get('intent')}
- 용량: {plan_data.get('capacity_filter', '미지정')}
- 용도: {plan_data.get('use_case', '미지정')}

[제품 상세 정보]
{{PRODUCTS_CONTEXT}}

[답변 규칙]
1. 제품명과 제품 코드를 명확히 언급
2. 추천 이유를 상세히 설명:
   - 용량 및 사용 기간
   - 재질의 장점
   - 적합한 사용 용도
   - 타겟 고객층
3. 관련 대체 제품 제안 (더 크거나 작은 용량)
4. 구체적이고 실용적인 정보 제공
5. 한국어로 자연스럽게 작성

답변:"""

        return template

    def _build_enriched_context(self, products: List[Dict[str, Any]]) -> str:
        """Build enriched context from products and dictionary"""
        if not products:
            return "검색된 제품이 없습니다."

        context_parts = []

        for idx, product in enumerate(products, 1):
            enriched = product.get("enriched", {})

            if enriched:
                # Enriched product with full details
                part = f"""
{idx}. **{product['product_name']}** (제품코드: {enriched.get('product_code', 'N/A')})
   - 상세 설명: {enriched.get('detailed_description', '')}
   - 용량 정보: {enriched.get('capacity_info', {}).get('capacity', '')} ({enriched.get('capacity_info', {}).get('usage_duration', '')})
   - 재질: {enriched.get('material_benefits', {}).get('material', '')}
   - 재질 장점: {', '.join(enriched.get('material_benefits', {}).get('advantages', []))}
   - 주요 용도: {', '.join(enriched.get('use_cases', []))}
   - 적합 고객: {', '.join(enriched.get('target_customers', []))}
   - 추천 시나리오: {enriched.get('recommendations', {}).get('when_to_use', '')}
   - 대체 제품: {', '.join(enriched.get('related_products', []))}
   - 유사도: {product['similarity_score']:.2f}
"""
            else:
                # Fallback to basic info
                part = f"""
{idx}. **{product['product_name']}** ({product['category']})
   - 유사도: {product['similarity_score']:.2f}
"""

            context_parts.append(part)

        return "\n".join(context_parts)

    async def search_products(
        self, query: str, plan: QueryPlan, collection: str = "products_all"
    ) -> List[Dict[str, Any]]:
        """Search products based on plan"""
        try:
            # Embed query
            query_embedding = self.embedder.encode(query, convert_to_numpy=True).tolist()

            # Search with higher limit
            search_limit = 200 if plan.capacity_filter else plan.top_k * 3

            results = self.qdrant.search(
                collection_name=collection,
                query_vector=query_embedding,
                limit=search_limit,
                score_threshold=0.3,
            )

            # Apply capacity filter if specified
            if plan.capacity_filter:
                import re

                filtered_results = []
                for result in results:
                    product_name = result.payload.get("product_name", "")
                    capacity_match = re.search(r"(\d+ml)", product_name.lower())
                    if capacity_match and capacity_match.group(1) == plan.capacity_filter:
                        filtered_results.append(result)
                results = filtered_results[: plan.top_k * 2]
                logger.info(
                    f"Capacity filter applied: {plan.capacity_filter} - {len(results)} products"
                )

            # Convert to product dicts
            products = []
            for result in results[: plan.top_k * 2]:
                product = {
                    "product_id": result.payload.get("product_id"),
                    "product_name": result.payload.get("product_name"),
                    "category": result.payload.get("category"),
                    "similarity_score": float(result.score),
                }

                # Enrich with dictionary
                product = self.dictionary.enrich_product(product)
                products.append(product)

            # Sort by enrichment (enriched products first)
            products.sort(
                key=lambda x: (1 if "enriched" in x else 0, x["similarity_score"]), reverse=True
            )

            return products[: plan.top_k]

        except Exception as e:
            logger.error(f"Product search error: {e}")
            return []

    async def generate_answer(
        self, question: str, products: List[Dict[str, Any]], plan: QueryPlan
    ) -> tuple[str, float]:
        """
        Stage 2: Generate answer with Ollama (Qwen)
        Using enriched product context
        """
        try:
            # Build enriched context
            context = self._build_enriched_context(products)

            # Fill template
            prompt = plan.answer_template.replace("{PRODUCTS_CONTEXT}", context)

            # Call Ollama
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.ollama_model,
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

                    # Calculate confidence
                    if products:
                        confidence = sum(p["similarity_score"] for p in products) / len(products)
                    else:
                        confidence = 0.0

                    logger.info(f"✅ Generated answer with confidence: {confidence:.2f}")
                    return answer.strip(), confidence

                else:
                    logger.error(f"Ollama API error: {response.status_code}")
                    return self._fallback_answer(question, products), 0.5

        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            return self._fallback_answer(question, products), 0.5

    def _fallback_answer(self, question: str, products: List[Dict[str, Any]]) -> str:
        """Fallback answer using dictionary only"""
        if not products:
            return f"죄송합니다. '{question}'에 대한 관련 제품을 찾지 못했습니다."

        answer_parts = [f"'{question}'에 대한 추천 제품입니다:", ""]

        for idx, product in enumerate(products, 1):
            enriched = product.get("enriched", {})

            if enriched:
                part = f"""{idx}. **{product['product_name']}** ({enriched.get('product_code', 'N/A')})
   - {enriched.get('detailed_description', '')}
   - 용도: {', '.join(enriched.get('use_cases', [])[:2])}
   - 추천: {enriched.get('recommendations', {}).get('when_to_use', '')}
"""
            else:
                part = f"{idx}. **{product['product_name']}** ({product['category']})"

            answer_parts.append(part)

        return "\n".join(answer_parts)

    async def answer_question(
        self, question: str, collection: str = "products_all"
    ) -> Dict[str, Any]:
        """Two-stage Q&A process"""
        try:
            logger.info(f"Two-stage Q&A: {question}")

            # Stage 1: Planning
            plan = await self.plan_query(question)

            # Stage 2: Execution
            products = await self.search_products(question, plan, collection)
            answer, confidence = await self.generate_answer(question, products, plan)

            qa_id = f"qa_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            return {
                "question": question,
                "answer": answer,
                "related_products": products,
                "confidence": confidence,
                "plan": {
                    "intent": plan.intent,
                    "capacity_filter": plan.capacity_filter,
                    "top_k": plan.top_k,
                    "search_strategy": plan.search_strategy,
                },
                "qa_id": qa_id,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Two-stage Q&A error: {e}")
            return {
                "question": question,
                "answer": f"처리 중 오류가 발생했습니다: {str(e)}",
                "related_products": [],
                "confidence": 0.0,
                "plan": None,
                "qa_id": f"qa_error_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
            }
