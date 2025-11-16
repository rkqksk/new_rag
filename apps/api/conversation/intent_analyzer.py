"""
LLM-based Intent Analyzer using Ollama
Analyzes user queries to understand intent and extract criteria
"""

import json
from typing import Any, Dict, Optional

import httpx

from .states import ConversationContext, IntentType, SearchCriteria


class IntentAnalyzer:
    """Analyzes user intent using Ollama LLM"""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "llama3.1:8b"

    async def analyze_intent(
        self, query: str, context: Optional[ConversationContext] = None
    ) -> Dict[str, Any]:
        """Analyze user query and determine intent

        Args:
            query: User's current query
            context: Current conversation context

        Returns:
            {
                "intent": IntentType,
                "criteria": SearchCriteria,
                "confidence": float,
                "explanation": str
            }
        """
        # Build prompt with context
        prompt = self._build_analysis_prompt(query, context)

        # Call Ollama
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",  # Request JSON output
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    llm_response = data.get("response", "{}")

                    # Parse LLM response
                    try:
                        result = json.loads(llm_response)
                        return self._normalize_result(result)
                    except json.JSONDecodeError:
                        # Fallback: try to extract JSON from text
                        return self._extract_json_from_text(llm_response)
                else:
                    return self._fallback_intent_analysis(query, context)

        except Exception as e:
            print(f"Intent analysis error: {e}")
            return self._fallback_intent_analysis(query, context)

    def _build_analysis_prompt(self, query: str, context: Optional[ConversationContext]) -> str:
        """Build detailed prompt for intent analysis"""

        base_prompt = f"""당신은 화장품 용기 검색 시스템의 대화 이해 전문가입니다.
사용자의 질문을 분석하여 의도와 검색 조건을 추출하세요.

**가능한 의도 (intent):**
- new_search: 새로운 검색 시작 (예: "50ml 용기 보여줘")
- filter_previous: 이전 결과 필터링 (예: "이중에 PETG만", "여기서 PET 재질")
- refine_search: 검색 조건 수정 (예: "아니 100ml로 바꿔줘")
- view_details: 상세 정보 조회 (예: "OT080-S001 자세히 보여줘")
- compare_products: 제품 비교 (예: "이 두 개 비교해줘")
- request_quote: 견적 요청 (예: "견적 내줘", "가격 알려줘")
- ask_question: 일반 질문 (예: "PET와 PETG 차이가 뭐야?")
- reset_context: 맥락 초기화 (예: "처음부터 다시", "새로 검색")
- recommend_accessory: 호환 액세서리 추천 (예: "이 용기에 맞는 펌프 추천해줘", "어떤 캡이 맞아?")

**추출할 검색 조건 (criteria):**
- capacity: 용량 숫자 (예: 50, 100)
- capacity_unit: 단위 (ml, g)
- material: 재질 (PET, PETG, PE, PP, Other)
- product_code: 제품 코드 (예: OT080-S001)
- product_type: 제품 타입 (BOTTLE, JAR, CAP, PUMP) - "병", "용기", "jar"는 BOTTLE, "캡", "뚜껑"은 CAP, "펌프"는 PUMP
- neck_size: 네크사이즈 (예: "20파이", "24파이", "28파이") - "20파이", "24 파이", "Ø20" 등 추출
- dosage: 펌프 토출량 (예: 0.2, 0.12) - "0.2cc", "0.12cc", "토출량 0.2" 등 추출
- has_coating: 코팅 가능 여부 (true/false)
- keywords: 추가 키워드 리스트

**현재 사용자 질문:**
"{query}"
"""

        # Add context if available
        if context:
            context_info = f"""
**현재 대화 상태:**
- 상태: {context.state}
- 이전 질문: {context.previous_query or "없음"}
- 이전 결과 수: {len(context.previous_results)}개
- 현재 질문: {context.current_query or "없음"}
- 현재 결과 수: {len(context.current_results)}개
"""
            base_prompt += context_info

        base_prompt += """

**JSON 응답 형식 (정확히 이 형식으로 반환):**
{
  "intent": "new_search|filter_previous|refine_search|view_details|compare_products|request_quote|ask_question|reset_context|recommend_accessory",
  "criteria": {
    "capacity": 50,
    "capacity_unit": "ml",
    "material": "PETG",
    "product_code": null,
    "product_type": "BOTTLE",
    "neck_size": "24파이",
    "has_coating": null,
    "keywords": []
  },
  "confidence": 0.95,
  "explanation": "사용자가 50ml PETG 용기를 검색하려는 의도"
}

JSON만 반환하세요. 추가 설명은 필요 없습니다.
"""

        return base_prompt

    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate LLM result"""

        # Ensure intent is valid
        intent_str = result.get("intent", "new_search")
        try:
            intent = IntentType(intent_str)
        except ValueError:
            intent = IntentType.NEW_SEARCH

        # Extract criteria
        criteria_dict = result.get("criteria", {})
        criteria = SearchCriteria(**criteria_dict) if criteria_dict else SearchCriteria()

        return {
            "intent": intent,
            "criteria": criteria,
            "confidence": float(result.get("confidence", 0.5)),
            "explanation": result.get("explanation", ""),
        }

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Try to extract JSON from text response"""
        # Look for JSON in markdown code blocks or plain text
        import re

        # Try to find JSON in code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if not json_match:
            # Try to find raw JSON
            json_match = re.search(r"\{.*\}", text, re.DOTALL)

        if json_match:
            try:
                json_str = json_match.group(1) if json_match.lastindex else json_match.group(0)
                result = json.loads(json_str)
                return self._normalize_result(result)
            except:
                pass

        # Complete fallback
        return {
            "intent": IntentType.NEW_SEARCH,
            "criteria": SearchCriteria(),
            "confidence": 0.3,
            "explanation": "Failed to parse LLM response",
        }

    def _fallback_intent_analysis(
        self, query: str, context: Optional[ConversationContext]
    ) -> Dict[str, Any]:
        """Fallback rule-based intent analysis when LLM fails"""

        query_lower = query.lower()

        # Detect contextual keywords (맥락 필터링)
        context_keywords = [
            "이중에",
            "이 중에",
            "이중",
            "여기서",
            "여기에서",
            "그중에",
            "그 중에",
            "그중",
            "저기서",
            "저기에서",
            "거기서",
            "거기에서",
            "이것",
            "저것",
            "그것",
            "만",
            "만보여",
            "만 보여",  # "PET만", "PETG만"
        ]
        is_contextual = any(kw in query_lower for kw in context_keywords)

        # Detect reset keywords
        reset_keywords = ["처음부터", "다시", "새로", "초기화", "리셋"]
        is_reset = any(kw in query_lower for kw in reset_keywords)

        # Detect detail view
        detail_keywords = ["자세히", "상세", "디테일", "정보"]
        is_detail = any(kw in query_lower for kw in detail_keywords)

        # Detect quote request
        quote_keywords = ["견적", "가격", "얼마"]
        is_quote = any(kw in query_lower for kw in quote_keywords)

        # Detect accessory recommendation
        accessory_keywords = [
            "펌프",
            "pump",
            "캡",
            "cap",
            "뚜껑",
            "추천",
            "recommend",
            "맞는",
            "호환",
            "어울리",
            "잘 맞",
            "같이",
            "함께",
            "세트",
        ]
        is_accessory = any(kw in query_lower for kw in accessory_keywords)

        # Determine intent with better logic
        if is_reset:
            intent = IntentType.RESET_CONTEXT
        elif is_quote:
            intent = IntentType.REQUEST_QUOTE
        elif is_detail:
            intent = IntentType.VIEW_DETAILS
        elif is_accessory and (context and len(context.current_results) > 0):
            # Only recommend accessories if we have context (bottles to match)
            intent = IntentType.RECOMMEND_ACCESSORY
        elif is_contextual:
            # Check if we have previous results to filter
            if context and len(context.current_results) > 0:
                intent = IntentType.FILTER_PREVIOUS
            elif context and len(context.previous_results) > 0:
                intent = IntentType.FILTER_PREVIOUS
            else:
                # Contextual keyword but no previous results - still treat as filter attempt
                intent = IntentType.FILTER_PREVIOUS
        else:
            intent = IntentType.NEW_SEARCH

        # Extract basic criteria (capacity, material)
        criteria = self._extract_basic_criteria(query)

        return {
            "intent": intent,
            "criteria": criteria,
            "confidence": 0.7 if is_contextual else 0.6,
            "explanation": f"Fallback analysis: {intent.value} (contextual={is_contextual})",
        }

    def _extract_basic_criteria(self, query: str) -> SearchCriteria:
        """Extract basic search criteria using regex"""
        import re

        criteria = SearchCriteria()

        # Extract capacity
        capacity_match = re.search(r"(\d+)\s*(ml|미리|밀리|g|그램)", query, re.IGNORECASE)
        if capacity_match:
            criteria.capacity = float(capacity_match.group(1))
            unit = capacity_match.group(2).lower()
            if unit in ["미리", "밀리", "ml"]:
                criteria.capacity_unit = "ml"
            elif unit in ["그램", "g"]:
                criteria.capacity_unit = "g"

        # Extract material
        material_keywords = {
            "PETG": ["petg", "피이티지"],
            "PET": ["pet", "페트", "피이티"],
            "PP": ["pp", "피피"],
            "PE": ["pe", "피이"],
        }

        for material, keywords in material_keywords.items():
            if any(kw in query.lower() for kw in keywords):
                criteria.material = material
                break

        # Extract product type (BOTTLE, JAR, CAP, PUMP)
        # NOTE: Order matters! Check specific types before general ones
        product_type_keywords = {
            "PUMP": ["펌프", "pump", "분사", "스프레이", "미스트"],
            "CAP": ["캡", "cap", "뚜껑", "마개", "원터치"],
            "JAR": ["jar", "자", "항아리"],
            "BOTTLE": ["병", "용기", "bottle", "보틀", "컨테이너"],
        }

        query_lower = query.lower()
        for product_type, keywords in product_type_keywords.items():
            if any(kw in query_lower for kw in keywords):
                criteria.product_type = product_type
                break

        # Extract neck size (네크사이즈)
        # Patterns: "20파이", "24 파이", "Ø20", "Ø24", "내경 20", "내경Ø20"
        neck_patterns = [
            r"(\d+)\s*파이",  # 20파이, 24 파이
            r"Ø\s*(\d+)",  # Ø20, Ø24
            r"내경\s*Ø?\s*(\d+)",  # 내경 20, 내경Ø20
        ]

        for pattern in neck_patterns:
            neck_match = re.search(pattern, query, re.IGNORECASE)
            if neck_match:
                neck_value = neck_match.group(1)
                criteria.neck_size = f"{neck_value}파이"
                break

        # Extract dosage (토출량)
        # Patterns: "0.2cc", "0.12cc", "토출량 0.2", "0.2 cc"
        dosage_patterns = [
            r"(\d+\.?\d*)\s*cc",  # 0.2cc, 0.12 cc
            r"토출량\s*(\d+\.?\d*)",  # 토출량 0.2
            r"(\d+\.?\d*)\s*씨씨",  # 0.2씨씨
        ]

        for pattern in dosage_patterns:
            dosage_match = re.search(pattern, query, re.IGNORECASE)
            if dosage_match:
                criteria.dosage = float(dosage_match.group(1))
                break

        # Extract product code
        code_match = re.search(r"[A-Z]{2}\d{3,4}[-_][A-Z]\d{3}", query.upper())
        if code_match:
            criteria.product_code = code_match.group(0)

        return criteria
