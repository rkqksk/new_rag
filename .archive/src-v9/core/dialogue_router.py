"""
대화 라우팅 시스템 (Dialogue Router)
영업사원 수준의 맥락 기반 대화를 위한 의도 해석 및 라우팅
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.core.conversation_state import ConversationState, DialogueContext, StateTransition
from src.core.enhanced_reference_resolver import EnhancedReferenceResolver
from src.core.filter_manager import FilterManager
from src.core.synonym_manager import get_synonym_manager


class IntentType(str, Enum):
    """사용자 의도 유형"""

    SEARCH = "search"  # 새로운 제품 검색
    FILTER = "filter"  # 필터 추가 (누적)
    REFERENCE = "reference"  # 숫자/대명사 참조
    DOCUMENT = "document"  # 문서 요청
    COMPATIBILITY = "compatibility"  # 호환성 확인
    COMPARE = "compare"  # 제품 비교
    DETAIL = "detail"  # 상세 정보
    GREETING = "greeting"  # 인사
    CLARIFICATION = "clarification"  # 명확화 필요
    RESET = "reset"  # 대화 초기화


@dataclass
class RoutingDecision:
    """라우팅 결정 결과"""

    intent: IntentType
    action: str  # "search", "filter", "show_detail", "show_document", etc.
    parameters: Dict[str, Any]
    next_state: ConversationState
    use_cache: bool = False
    confidence: float = 1.0


class DialogueRouter:
    """
    대화 라우팅 시스템

    핵심 기능:
    1. 의도 분류: 사용자 쿼리 → IntentType
    2. 참조 해결: "3번", "그거" → 실제 제품 idx
    3. 액션 결정: 의도 + 상태 → 구체적 액션
    4. 상태 전환: 다음 대화 상태 결정
    """

    def __init__(self):
        self.reference_resolver = EnhancedReferenceResolver()
        self.synonym_manager = get_synonym_manager()

        # 의도 분류 키워드
        self.intent_keywords = {
            IntentType.SEARCH: [
                "찾아줘",
                "검색",
                "보여줘",
                "있어?",
                "추천",
                "용기",
                "병",
                "캡",
                "펌프",
                "제품",
            ],
            IntentType.FILTER: [
                "PET",
                "HDPE",
                "PP",
                "투명",
                "불투명",
                "만",
                "제외",
                "빼고",
                "~ml",
                "미리",
            ],
            IntentType.REFERENCE: [
                "번",
                "번째",
                "그거",
                "이거",
                "저거",
                "첫",
                "마지막",
                "위",
                "아래",
            ],
            IntentType.DOCUMENT: [
                "원산지",
                "증명서",
                "스펙",
                "시트",
                "사양서",
                "카탈로그",
                "자료",
                "문서",
                "도면",
            ],
            IntentType.COMPATIBILITY: [
                "호환",
                "맞는",
                "어울리는",
                "사용할 수 있는",
                "네크",
                "사이즈",
            ],
            IntentType.COMPARE: ["비교", "차이", "다른", "비슷한"],
            IntentType.DETAIL: ["자세히", "상세", "정보", "설명"],
            IntentType.GREETING: ["안녕", "하이", "헬로", "처음", "도와줘"],
            IntentType.RESET: ["초기화", "리셋", "처음부터", "다시"],
        }

    def route(
        self, query: str, context: DialogueContext, filter_manager: FilterManager
    ) -> RoutingDecision:
        """
        쿼리를 분석하여 라우팅 결정

        Args:
            query: 사용자 쿼리
            context: 현재 대화 컨텍스트
            filter_manager: 필터 관리자

        Returns:
            RoutingDecision: 라우팅 결정 (의도, 액션, 파라미터, 다음 상태)
        """

        # 1. 의도 분류 먼저 (호환성, 문서 요청 등 컨텍스트 기반 의도 파악)
        intent = self._classify_intent(query, context)

        # 2. 호환성/문서 요청은 우선 처리
        if intent == IntentType.COMPATIBILITY:
            return self._handle_compatibility(query, context)
        elif intent == IntentType.DOCUMENT:
            # 문서 요청일 경우 참조 해결 시도
            resolved, product_idx, ref_type, doc_type = self.reference_resolver.resolve(
                query, context
            )
            if resolved and doc_type:
                return self._handle_reference(query, context, product_idx, ref_type, doc_type)

        # 3. 참조 해결 시도 (숫자, 대명사 등)
        resolved, product_idx, ref_type, doc_type = self.reference_resolver.resolve(query, context)

        if resolved:
            return self._handle_reference(query, context, product_idx, ref_type, doc_type)

        # 3. 의도별 라우팅
        if intent == IntentType.SEARCH:
            return self._handle_search(query, context, filter_manager)

        elif intent == IntentType.FILTER:
            return self._handle_filter(query, context, filter_manager)

        elif intent == IntentType.COMPATIBILITY:
            return self._handle_compatibility(query, context)

        elif intent == IntentType.COMPARE:
            return self._handle_compare(query, context)

        elif intent == IntentType.DETAIL:
            return self._handle_detail(query, context)

        elif intent == IntentType.GREETING:
            return self._handle_greeting(query, context)

        elif intent == IntentType.RESET:
            return self._handle_reset(query, context)

        else:
            # 명확화 필요
            return self._handle_clarification(query, context)

    def _classify_intent(self, query: str, context: DialogueContext) -> IntentType:
        """의도 분류"""

        # 우선순위 체크 (컨텍스트 기반)

        # 1. 호환성 체크 (포커스 제품이 있고 호환성 키워드 포함)
        if context.focused_product and any(
            kw in query for kw in self.intent_keywords[IntentType.COMPATIBILITY]
        ):
            return IntentType.COMPATIBILITY

        # 2. 문서 요청 체크 (문서 키워드 포함)
        if any(kw in query for kw in self.intent_keywords[IntentType.DOCUMENT]):
            return IntentType.DOCUMENT

        # 현재 상태에서 예상되는 의도들
        expected_intents = StateTransition.get_expected_intents(context.current_state)

        # 키워드 기반 스코어링
        scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for kw in keywords if kw in query)
            scores[intent] = score

        # 상태 기반 가중치
        for intent_str in expected_intents:
            try:
                intent = IntentType(intent_str)
                scores[intent] = scores.get(intent, 0) * 2  # 2배 가중치
            except ValueError:
                continue

        # 최고 스코어 의도 반환
        if max(scores.values(), default=0) > 0:
            return max(scores, key=scores.get)

        # 기본값: 검색
        return IntentType.SEARCH

    def _handle_reference(
        self,
        query: str,
        context: DialogueContext,
        product_idx: str,
        ref_type: str,
        doc_type: Optional[str],
    ) -> RoutingDecision:
        """참조 처리"""

        # 문서 요청인 경우
        if ref_type == "document" and doc_type:
            return RoutingDecision(
                intent=IntentType.DOCUMENT,
                action="show_document",
                parameters={"product_idx": product_idx, "document_type": doc_type, "query": query},
                next_state=ConversationState.DOCUMENT_REQUEST,
                confidence=0.95,
            )

        # 제품 참조 (상세보기)
        return RoutingDecision(
            intent=IntentType.REFERENCE,
            action="show_detail",
            parameters={"product_idx": product_idx, "reference_type": ref_type, "query": query},
            next_state=ConversationState.FOCUSED,
            confidence=0.95,
        )

    def _handle_search(
        self, query: str, context: DialogueContext, filter_manager: FilterManager
    ) -> RoutingDecision:
        """새로운 검색 처리 (동의어 처리 통합)"""

        # 1. 쿼리 정규화 ("24파이" → "24", "로션펌프" → "로션 펌프")
        normalized_query = self.synonym_manager.normalize_query(query)

        # 2. 모든 필터 자동 추출 (동의어 처리 포함)
        filters = self.synonym_manager.get_search_filters(normalized_query)

        # 3. 쿼리 확장 (동의어 추가)
        expanded_query = self.synonym_manager.expand_query(normalized_query)

        return RoutingDecision(
            intent=IntentType.SEARCH,
            action="search",
            parameters={
                "query": expanded_query,
                "filters": filters,
                "use_hybrid": True,
                "normalized_query": normalized_query,
            },
            next_state=ConversationState.SEARCHING,
            confidence=0.8,
        )

    def _handle_filter(
        self, query: str, context: DialogueContext, filter_manager: FilterManager
    ) -> RoutingDecision:
        """누적 필터 처리 (동의어 처리 통합)"""

        # 이전 결과가 있어야 필터 가능
        if not context.last_search_results:
            return self._handle_clarification(query, context)

        # 1. 쿼리 정규화
        normalized_query = self.synonym_manager.normalize_query(query)

        # 2. 모든 필터 자동 추출 (동의어 처리 포함)
        new_filters = self.synonym_manager.get_search_filters(normalized_query)

        # 3. 필터 추가 (누적)
        for key, value in new_filters.items():
            filter_manager.add_filter(key, value)

        return RoutingDecision(
            intent=IntentType.FILTER,
            action="apply_filter",
            parameters={
                "filters": new_filters,
                "cached_results": context.last_search_results,
                "normalized_query": normalized_query,
            },
            next_state=ConversationState.FILTERING,
            use_cache=True,
            confidence=0.9,
        )

    def _handle_compatibility(self, query: str, context: DialogueContext) -> RoutingDecision:
        """호환성 확인 처리"""

        # 포커스 제품이 있어야 호환성 확인 가능
        if not context.focused_product:
            return self._handle_clarification(query, context)

        # 호환 제품 타입 추출 (예: "캡", "펌프")
        compatible_type = self._extract_compatible_type(query)

        return RoutingDecision(
            intent=IntentType.COMPATIBILITY,
            action="find_compatible",
            parameters={
                "base_product_idx": context.focused_product,
                "compatible_type": compatible_type,
                "query": query,
            },
            next_state=ConversationState.COMPATIBILITY_CHECK,
            confidence=0.85,
        )

    def _handle_compare(self, query: str, context: DialogueContext) -> RoutingDecision:
        """제품 비교 처리"""

        # 최소 2개 제품 필요
        if len(context.comparison_products) < 2:
            if not context.last_search_results or len(context.last_search_results) < 2:
                return self._handle_clarification(query, context)

            # 상위 2개 자동 선택
            products = context.last_search_results[:2]
        else:
            products = context.comparison_products

        return RoutingDecision(
            intent=IntentType.COMPARE,
            action="compare_products",
            parameters={"product_indices": products, "query": query},
            next_state=ConversationState.COMPARING,
            confidence=0.8,
        )

    def _handle_detail(self, query: str, context: DialogueContext) -> RoutingDecision:
        """상세 정보 처리"""

        # 포커스 제품이 있으면 그것 사용
        if context.focused_product:
            product_idx = context.focused_product
        elif context.last_search_results:
            product_idx = context.last_search_results[0]
        else:
            return self._handle_clarification(query, context)

        return RoutingDecision(
            intent=IntentType.DETAIL,
            action="show_detail",
            parameters={"product_idx": product_idx, "query": query},
            next_state=ConversationState.FOCUSED,
            confidence=0.8,
        )

    def _handle_greeting(self, query: str, context: DialogueContext) -> RoutingDecision:
        """인사 처리"""

        return RoutingDecision(
            intent=IntentType.GREETING,
            action="greeting",
            parameters={"query": query},
            next_state=ConversationState.GREETING,
            confidence=0.95,
        )

    def _handle_reset(self, query: str, context: DialogueContext) -> RoutingDecision:
        """대화 초기화 처리"""

        return RoutingDecision(
            intent=IntentType.RESET,
            action="reset",
            parameters={"query": query},
            next_state=ConversationState.IDLE,
            confidence=0.95,
        )

    def _handle_clarification(self, query: str, context: DialogueContext) -> RoutingDecision:
        """명확화 필요 처리"""

        # 명확화 질문 생성
        clarification = self.reference_resolver.get_clarification_question(query, context)

        return RoutingDecision(
            intent=IntentType.CLARIFICATION,
            action="request_clarification",
            parameters={
                "query": query,
                "clarification_message": clarification or "무엇을 도와드릴까요?",
            },
            next_state=ConversationState.CLARIFICATION,
            confidence=0.5,
        )

    # ===== 추출 유틸리티 =====

    def _extract_capacity(self, query: str) -> Optional[float]:
        """용량 추출 (ml)"""
        import re

        # "50ml", "50미리", "50 ml"
        patterns = [r"(\d+)\s*ml", r"(\d+)\s*미리", r"(\d+)\s*mL"]

        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return float(match.group(1))

        return None

    def _extract_material(self, query: str) -> Optional[str]:
        """재질 추출"""
        materials = ["PET", "HDPE", "PP", "PETG", "PLA", "PS", "PC"]

        query_upper = query.upper()
        for material in materials:
            if material in query_upper:
                return material

        return None

    def _extract_transparency(self, query: str) -> Optional[str]:
        """투명도 추출"""
        if "투명" in query or "clear" in query.lower():
            return "transparent"
        elif "불투명" in query or "opaque" in query.lower():
            return "opaque"

        return None

    def _extract_neck_size(self, query: str) -> Optional[str]:
        """네크 사이즈 추출"""
        import re

        # "28/410", "24/410"
        pattern = r"(\d{2}/\d{3})"
        match = re.search(pattern, query)
        if match:
            return match.group(1)

        return None

    def _extract_compatible_type(self, query: str) -> Optional[str]:
        """호환 제품 타입 추출"""
        types = {
            "캡": "cap",
            "뚜껑": "cap",
            "펌프": "pump",
            "스프레이": "spray",
            "디스펜서": "dispenser",
        }

        for korean, english in types.items():
            if korean in query:
                return english

        return None
