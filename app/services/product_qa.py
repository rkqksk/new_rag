"""
Product Q&A Service
Generates answers to product-specific questions using LLM
Phase 1: 제품 속성 질문 응답 시스템
"""

import httpx
from typing import Dict, Any, Optional
import json


async def generate_product_answer(
    question: str,
    product: Dict[str, Any],
    ollama_url: str = "http://localhost:11434"
) -> str:
    """Generate answer to product question using Ollama LLM

    Args:
        question: User's question (e.g., "토출량은?", "납기는?")
        product: Product data dictionary
        ollama_url: Ollama API URL

    Returns:
        Natural language answer
    """

    # Build context from product data
    product_context = _build_product_context(product)

    # Build prompt
    prompt = f"""당신은 화장품 용기 제품 전문가입니다.
아래 제품 정보를 바탕으로 고객의 질문에 답변하세요.

**제품 정보:**
{product_context}

**고객 질문:**
{question}

**답변 지침:**
- 제품 정보에 있는 내용만 답변하세요
- 정보가 없으면 "죄송하지만 해당 정보가 제공되지 않았습니다"라고 말하세요
- 간결하고 명확하게 답변하세요 (1-2문장)
- 친절하고 전문적인 톤을 유지하세요

답변:"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": "llama3.1:8b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for factual answers
                        "top_p": 0.9,
                        "num_predict": 150  # Short answers
                    }
                }
            )

            if response.status_code == 200:
                data = response.json()
                answer = data.get('response', '').strip()
                return answer if answer else "죄송합니다. 답변을 생성할 수 없습니다."
            else:
                return "죄송합니다. 일시적인 오류가 발생했습니다."

    except Exception as e:
        print(f"[Product QA] Error generating answer: {e}")
        return "죄송합니다. 답변을 생성하는 중 오류가 발생했습니다."


def _build_product_context(product: Dict[str, Any]) -> str:
    """Build formatted product context for LLM

    Args:
        product: Product dictionary

    Returns:
        Formatted context string
    """
    context_parts = []

    # Basic info
    context_parts.append(f"제품명: {product.get('product_name', '정보 없음')}")

    if product.get('product_code'):
        context_parts.append(f"제품 코드: {product['product_code']}")

    # Specifications
    specs = product.get('specifications', {})
    if specs:
        context_parts.append("\n사양:")

        # Material
        if specs.get('material') or product.get('material'):
            material = specs.get('material') or product.get('material')
            context_parts.append(f"  - 재질: {material}")

        # Capacity
        if specs.get('capacity') or product.get('capacity'):
            capacity = specs.get('capacity') or product.get('capacity')
            context_parts.append(f"  - 용량: {capacity}")

        # Neck size
        if specs.get('neck_size') or product.get('neck_size'):
            neck_size = specs.get('neck_size') or product.get('neck_size')
            context_parts.append(f"  - 네크 사이즈: {neck_size}")

        # Dosage (for pumps)
        if specs.get('dosage') or specs.get('dosage_value'):
            dosage = specs.get('dosage') or specs.get('dosage_value')
            context_parts.append(f"  - 토출량: {dosage}cc")

        # Dimensions
        if specs.get('dimensions'):
            dimensions = specs.get('dimensions')
            if isinstance(dimensions, dict):
                dim_str = ", ".join([f"{k}: {v}" for k, v in dimensions.items() if v])
                context_parts.append(f"  - 치수: {dim_str}")
            else:
                context_parts.append(f"  - 치수: {dimensions}")
        elif product.get('spec'):
            context_parts.append(f"  - 사양: {product['spec']}")

    # Pricing (MOQ, delivery)
    pricing = product.get('pricing', {})
    if pricing:
        context_parts.append("\n가격 및 주문 정보:")

        if pricing.get('moq'):
            context_parts.append(f"  - 최소 주문 수량 (MOQ): {pricing['moq']}")

        # Delivery time (if available in product data)
        if pricing.get('delivery_time'):
            context_parts.append(f"  - 납기: {pricing['delivery_time']}")
        else:
            context_parts.append(f"  - 납기: 일반적으로 3-5 영업일 (재고 상황에 따라 변동)")

        # Customization options
        if pricing.get('customization_options'):
            options = pricing['customization_options']
            if isinstance(options, list):
                context_parts.append(f"  - 맞춤 옵션: {', '.join(options)}")
            else:
                context_parts.append(f"  - 맞춤 옵션: {options}")
        else:
            context_parts.append(f"  - 맞춤 옵션: 인쇄, 코팅, 색상 변경 가능 (별도 문의)")

        # Discount policy
        if pricing.get('discount_policy'):
            context_parts.append(f"  - 할인 정책: {pricing['discount_policy']}")
        else:
            context_parts.append(f"  - 할인 정책: 대량 주문 시 협의 가능")

    return "\n".join(context_parts)


def extract_product_from_context(
    context: Any,
    query: str
) -> Optional[Dict[str, Any]]:
    """Extract referenced product from conversation context

    Args:
        context: ConversationContext object
        query: User query

    Returns:
        Product dictionary or None
    """
    # Priority 1: Explicit product code in query
    import re
    product_code_pattern = r'[A-Z]{2}\d{3}-[A-Z]\d{3}'
    match = re.search(product_code_pattern, query)
    if match and context.current_results:
        product_code = match.group(0)
        for product in context.current_results:
            if product.get('product_code') == product_code:
                return product

    # Priority 2: Last referenced product in context
    if context.last_referenced_product:
        return context.last_referenced_product

    # Priority 3: First product in current results
    if context.current_results and len(context.current_results) > 0:
        return context.current_results[0]

    return None


# Knowledge base for common questions (fallback when product data is insufficient)
KNOWLEDGE_BASE = {
    "delivery": {
        "keywords": ["납기", "배송", "언제", "받을", "소요", "기간"],
        "default_answer": "일반적으로 제품 납기는 3-5 영업일입니다. 재고 상황과 주문 수량에 따라 달라질 수 있으니 정확한 납기는 별도 문의 부탁드립니다."
    },
    "customization": {
        "keywords": ["색상", "인쇄", "코팅", "맞춤", "커스텀", "변경", "디스카운트", "할인"],
        "default_answer": "인쇄, 코팅, 색상 변경 등 맞춤 제작이 가능합니다. 대량 주문 시 할인 협의도 가능하니 구체적인 요구사항을 말씀해 주시면 상담해 드리겠습니다."
    },
    "material": {
        "keywords": ["재질", "소재", "material"],
        "default_answer": "제품의 정확한 재질 정보는 제품 상세 정보를 확인해 주세요."
    },

    # Phase 3: 한국 규제/인증 지식 베이스 (우선순위 높음)
    "mfds_cosmetic": {
        "keywords": ["식약처", "mfds", "화장품법", "화장품 용기", "식품의약품안전처"],
        "regulations": {
            "primary_law": "화장품법 (법률 제19264호)",
            "container_standards": "화장품 포장 및 용기 기준 (식약처 고시)",
            "key_requirements": [
                "화장품 용기는 내용물 보호 및 품질 유지 가능해야 함",
                "용기 재질은 인체에 무해해야 함",
                "1차 포장(내용물 직접 접촉)은 안전성 확보 필수",
                "PET, PETG, PP, PE 등 식품용 플라스틱 적합"
            ],
            "labeling": "화장품 표시·광고 실증에 관한 규정 준수 필요"
        },
        "default_answer": """화장품 용기는 식약처(식품의약품안전처) 화장품법에 따라 다음 기준을 충족해야 합니다:

1. **재질 안전성**: 내용물과 직접 접촉하는 1차 포장은 인체에 무해한 재질 사용
2. **적합 재질**: PET, PETG, PP, PE, HDPE 등 식품용 플라스틱
3. **품질 유지**: 내용물 보호 및 품질 유지 가능한 용기
4. **표시사항**: 화장품법에 따른 표시·광고 규정 준수

당사 제품은 화장품 용기 기준에 적합한 재질로 제작됩니다."""
    },

    "env_recycling": {
        "keywords": ["환경부", "재활용", "분리배출", "epr", "재질구조"],
        "regulations": {
            "primary_law": "자원의 절약과 재활용촉진에 관한 법률",
            "epr_system": "생산자책임재활용제도 (EPR)",
            "packaging_standards": "포장재 재질·구조 개선 등에 관한 기준",
            "key_requirements": [
                "재활용 가능 재질 사용 권장",
                "PET, PE, PP 등 단일 재질 용기 재활용 용이",
                "라벨은 쉽게 분리 가능해야 함",
                "재활용 등급 표시 (최우수/우수/보통/어려움)"
            ],
            "recycling_grades": {
                "excellent": "PET 단일 재질, 무색 투명",
                "good": "PET, PE, PP 단일 재질",
                "normal": "복합 재질이나 분리 가능",
                "difficult": "복합 재질, 분리 어려움"
            }
        },
        "default_answer": """화장품 용기는 환경부 재활용 기준을 준수해야 합니다:

1. **재활용 용이 재질**: PET, PE, PP 등 단일 재질 권장
2. **EPR 대상**: 생산자책임재활용제도 적용
3. **분리배출 표시**: 재질 표시 및 분리배출 방법 안내
4. **재활용 등급**:
   - 최우수: PET 무색 투명
   - 우수: PET/PE/PP 단일 재질
   - 보통: 복합 재질 분리 가능
   - 어려움: 복합 재질 분리 불가

당사는 재활용 우수 등급 제품을 우선 공급합니다."""
    },

    "kc_certification": {
        "keywords": ["kc인증", "kc마크", "안전인증", "국가통합인증"],
        "regulations": {
            "certification_type": "KC(Korea Certification) 마크",
            "applicable_products": "전기전자제품, 생활용품",
            "cosmetic_containers": "화장품 용기는 KC 인증 대상 아님",
            "note": "화장품 용기 자체는 KC 인증 불필요, 내용물(화장품)만 식약처 신고"
        },
        "default_answer": """화장품 용기는 KC 인증 대상이 아닙니다.

- KC 인증은 전기전자제품, 생활용품이 대상
- 화장품 용기는 식약처 화장품법 적용
- 화장품(내용물)만 식약처 제조/수입 신고 필요

용기 안전성은 식약처 화장품 용기 기준을 준수합니다."""
    },

    "test_certificate": {
        "keywords": ["시험성적서", "테스트", "검사", "성적서", "인증서"],
        "available_tests": [
            "재질 시험 (KTR, 한국화학융합시험연구원)",
            "중금속 용출 시험 (납, 카드뮴 등)",
            "내용물 적합성 시험",
            "내열성/내한성 시험"
        ],
        "default_answer": """제품 시험성적서는 다음 항목으로 발급 가능합니다:

1. **재질 분석**: KTR, 한국화학융합시험연구원 등
2. **안전성 시험**: 중금속 용출 시험 (납, 카드뮴, 비소 등)
3. **품질 시험**: 내열성, 내한성, 낙하 시험
4. **식품용기 기준**: 식품용 재질 적합성 시험

시험성적서 발급은 별도 문의 부탁드립니다."""
    },

    # 보조: 국제 규제 (필요시 참고)
    "fda_regulation": {
        "keywords": ["fda", "미국", "21 cfr"],
        "regulations": {
            "regulation": "FDA 21 CFR Part 177 (식품 접촉 물질)",
            "note": "화장품 용기는 CFR Part 700 시리즈 적용",
            "korean_priority": "한국 비즈니스는 식약처 기준 우선"
        },
        "default_answer": """FDA 규제는 미국 수출 시 참고사항입니다.

- FDA 21 CFR Part 700: 화장품 포장 기준
- 한국 비즈니스는 **식약처 화장품법** 우선 적용
- 수출 시에만 FDA 기준 확인 필요

국내 판매는 식약처 기준만 충족하면 됩니다."""
    },

    "eu_regulation": {
        "keywords": ["eu", "유럽", "ce", "reach"],
        "regulations": {
            "regulation": "EU Regulation (EC) 1935/2004",
            "reach": "REACH 규정 (화학물질 등록평가)",
            "note": "유럽 수출 시 적용, 한국은 환경부/식약처 기준 우선"
        },
        "default_answer": """EU 규제는 유럽 수출 시 참고사항입니다.

- EU 1935/2004: 식품 접촉 재료 기준
- REACH: 화학물질 등록평가 제한
- 한국 비즈니스는 **환경부/식약처 기준** 우선

국내 판매는 한국 규제만 충족하면 됩니다."""
    }
}


def get_fallback_answer(question: str) -> Optional[str]:
    """Get fallback answer from knowledge base

    Args:
        question: User question

    Returns:
        Fallback answer or None
    """
    question_lower = question.lower()

    for topic, info in KNOWLEDGE_BASE.items():
        if any(keyword in question_lower for keyword in info['keywords']):
            return info['default_answer']

    return None
