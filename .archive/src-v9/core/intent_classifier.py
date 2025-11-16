"""
사용자 의도 분류 시스템
규칙 기반 분류 + ML 모델 확장 가능
"""

import re
from enum import Enum
from typing import Dict, List, Optional, Tuple


class Intent(str, Enum):
    """의도 타입"""

    SEARCH = "search"  # 제품 검색
    COMPARE = "compare"  # 제품 비교
    DETAIL = "detail"  # 상세 정보 요청
    FILTER = "filter"  # 필터 적용/수정
    COMPATIBILITY = "compatibility"  # 호환성 확인
    PRICE = "price"  # 가격 정보
    REFERENCE = "reference"  # 이전 대화 참조
    RECOMMENDATION = "recommendation"  # 추천 요청
    GREETING = "greeting"  # 인사
    UNKNOWN = "unknown"  # 알 수 없음


class IntentClassifier:
    """사용자 의도 분류기 (규칙 기반)"""

    def __init__(self):
        # 의도별 키워드 패턴
        self.intent_patterns = {
            Intent.SEARCH: [
                r"찾아.*?줘",
                r"검색",
                r"보여.*?줘",
                r"추천",
                r"있어",
                r"있나",
                r"있을까",
                r"알려줘",
                r"\d+ml",
                r"\d+g",
                r"용기",
                r"병",
                r"펌프",
                r"캡",
            ],
            Intent.COMPARE: [r"비교", r"차이", r"어떤.*?게.*?나", r"vs", r"어느.*?게", r"둘.*?중"],
            Intent.DETAIL: [r"상세", r"자세히", r"더.*?알고", r"스펙", r"정보", r"어떤.*?제품"],
            Intent.FILTER: [
                r"제외",
                r"말고",
                r"빼고",
                r"~만",
                r"~이하",
                r"~이상",
                r"저렴한",
                r"비싼",
                r"싼",
                r"값싼",
                r"투명",
                r"불투명",
                r"프리미엄",
            ],
            Intent.COMPATIBILITY: [
                r"맞는",
                r"호환",
                r"쓸.*?수.*?있",
                r"가능한",
                r"될.*?까",
                r"사용.*?가능",
                r"적합",
            ],
            Intent.PRICE: [r"가격", r"얼마", r"비용", r"원", r"₩", r"돈", r"값"],
            Intent.REFERENCE: [
                r"그.*?거",
                r"이.*?거",
                r"저.*?거",
                r"첫.*?번째",
                r"두.*?번째",
                r"마지막",
                r"위.*?에",
                r"이전",
                r"아까",
                r"방금",
            ],
            Intent.RECOMMENDATION: [
                r"추천",
                r"좋은",
                r"괜찮은",
                r"어울리는",
                r"적합한",
                r"어떤.*?게.*?좋",
                r"뭐.*?가.*?좋",
            ],
            Intent.GREETING: [r"^안녕", r"^hi", r"^hello", r"처음", r"도와줘", r"도와주세요"],
        }

        # 복합 패턴 (우선순위 높음)
        self.compound_patterns = [
            # "첫 번째 제품 가격" → REFERENCE + PRICE
            (r"(첫|두|세|마지막).*?(가격|얼마)", [Intent.REFERENCE, Intent.PRICE]),
            # "그거 호환되는 펌프" → REFERENCE + COMPATIBILITY
            (r"(그|이|저).*?(호환|맞는)", [Intent.REFERENCE, Intent.COMPATIBILITY]),
            # "저렴한 거 추천" → FILTER + RECOMMENDATION
            (r"(저렴|싼|비싼).*?(추천|보여)", [Intent.FILTER, Intent.RECOMMENDATION]),
        ]

    def classify(self, query: str, context: Dict = None) -> Tuple[Intent, float]:
        """
        사용자 쿼리의 의도 분류

        Args:
            query: 사용자 쿼리
            context: 대화 컨텍스트 (선택사항)

        Returns:
            (Intent, confidence_score)
        """
        query_lower = query.lower().strip()

        # 🔥 PRIORITY: 제품 유형 키워드 감지 → 무조건 SEARCH로 분류
        # 이를 통해 짧은 제품군 쿼리("토너", "세럼")가 REFERENCE로 오분류되는 문제 해결
        product_types = [
            "토너",
            "로션",
            "에센스",
            "세럼",
            "크림",
            "앰플",
            "클렌징",
            "샴푸",
            "바디워시",
            "미스트",
            "젤",
            "펌프",
            "캡",
            "용기",
            "병",
            "오일",
            "핸드크림",
            "아이크림",
            "페이스오일",
        ]
        for ptype in product_types:
            if ptype in query:
                # 제품군 키워드가 있으면 SEARCH intent로 강제 분류 (높은 신뢰도)
                return Intent.SEARCH, 0.95

        # 1. 복합 패턴 우선 체크
        for pattern, intents in self.compound_patterns:
            if re.search(pattern, query):
                # 복합 의도는 첫 번째를 primary로 반환
                return intents[0], 0.9

        # 2. 단일 패턴 매칭
        intent_scores = {}

        for intent, patterns in self.intent_patterns.items():
            score = 0.0
            matches = 0

            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    matches += 1
                    score += 1.0

            if matches > 0:
                # 매칭된 패턴 개수로 정규화
                intent_scores[intent] = score / len(patterns)

        # 3. 컨텍스트 기반 추론
        if context:
            context_intent = self._infer_from_context(query, context)
            if context_intent:
                # 컨텍스트 추론은 가중치 +0.3
                intent_scores[context_intent] = intent_scores.get(context_intent, 0) + 0.3

        # 4. 최고 점수 의도 선택
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            return best_intent[0], min(best_intent[1], 1.0)

        # 5. 기본값: 길이 기반 추론
        if len(query) < 10 and context and context.get("current_focus"):
            # 짧은 질문 + 포커스 있음 → REFERENCE 가능성 높음
            return Intent.REFERENCE, 0.6

        # 6. UNKNOWN
        return Intent.UNKNOWN, 0.3

    def _infer_from_context(self, query: str, context: Dict) -> Optional[Intent]:
        """
        컨텍스트 기반 의도 추론

        Args:
            query: 사용자 쿼리
            context: 대화 컨텍스트

        Returns:
            추론된 의도 또는 None
        """
        # 현재 포커스 제품이 있고 짧은 질문
        if context.get("current_focus") and len(query) < 20:
            # 대명사 패턴이 있으면 REFERENCE
            if re.search(r"(그|이|저|첫|두|세)", query):
                return Intent.REFERENCE

        # 최근 검색 이력 확인
        search_history = context.get("search_history", [])
        if search_history:
            last_query = search_history[-1]

            # 마지막 쿼리가 검색이었고 현재 필터 키워드
            if last_query.get("intent") == Intent.SEARCH.value:
                if any(kw in query for kw in ["말고", "제외", "만"]):
                    return Intent.FILTER

        # 활성 필터가 있고 추가 필터 키워드
        if context.get("filters") and len(query) < 15:
            if any(kw in query for kw in ["더", "추가", "그리고"]):
                return Intent.FILTER

        return None

    def get_intent_description(self, intent: Intent) -> str:
        """
        의도에 대한 설명 반환

        Args:
            intent: 의도 타입

        Returns:
            의도 설명
        """
        descriptions = {
            Intent.SEARCH: "제품 검색",
            Intent.COMPARE: "제품 비교",
            Intent.DETAIL: "상세 정보 조회",
            Intent.FILTER: "필터 적용",
            Intent.COMPATIBILITY: "호환성 확인",
            Intent.PRICE: "가격 정보 조회",
            Intent.REFERENCE: "이전 대화 참조",
            Intent.RECOMMENDATION: "추천 요청",
            Intent.GREETING: "인사",
            Intent.UNKNOWN: "알 수 없음",
        }
        return descriptions.get(intent, "알 수 없음")

    def extract_entities(self, query: str) -> Dict[str, any]:
        """
        쿼리에서 엔티티 추출

        Args:
            query: 사용자 쿼리

        Returns:
            추출된 엔티티 딕셔너리
        """
        entities = {}

        # 용량 추출 (ml, g)
        capacity_match = re.search(r"(\d+(?:\.\d+)?)\s*(ml|g)", query, re.IGNORECASE)
        if capacity_match:
            entities["capacity"] = {
                "value": float(capacity_match.group(1)),
                "unit": capacity_match.group(2).lower(),
            }

        # 재질 추출
        materials = ["PE", "PET", "PETG", "PP"]
        for material in materials:
            if re.search(rf"\b{material}\b", query, re.IGNORECASE):
                entities["material"] = material

        # 네크 사이즈 추출
        neck_match = re.search(r"(\d+)\s*파이", query)
        if neck_match:
            entities["neck_size"] = f"{neck_match.group(1)}파이"

        # 가격 범위 추출
        price_match = re.search(r"(\d+)\s*원?\s*이하", query)
        if price_match:
            entities["price_max"] = int(price_match.group(1))

        price_match = re.search(r"(\d+)\s*원?\s*이상", query)
        if price_match:
            entities["price_min"] = int(price_match.group(1))

        # 제품 유형 추출
        product_types = [
            "토너",
            "로션",
            "에센스",
            "세럼",
            "크림",
            "앰플",
            "클렌징",
            "샴푸",
            "바디워시",
            "미스트",
        ]
        for ptype in product_types:
            if ptype in query:
                entities["product_type"] = ptype

        # 속성 추출
        attributes = {
            "투명": "transparent",
            "불투명": "opaque",
            "프리미엄": "premium",
            "저렴": "budget",
            "오일": "oil_compatible",
        }
        for keyword, attr in attributes.items():
            if keyword in query:
                if "attributes" not in entities:
                    entities["attributes"] = []
                entities["attributes"].append(attr)

        return entities

    def classify_detailed(self, query: str, context: Dict = None) -> Dict:
        """
        상세한 의도 분류 (의도 + 엔티티)

        Args:
            query: 사용자 쿼리
            context: 대화 컨텍스트

        Returns:
            상세 분류 결과 딕셔너리
        """
        intent, confidence = self.classify(query, context)
        entities = self.extract_entities(query)

        return {
            "intent": intent.value,
            "confidence": confidence,
            "intent_description": self.get_intent_description(intent),
            "entities": entities,
            "query": query,
        }


# 전역 인스턴스 (싱글톤)
_intent_classifier_instance = None


def get_intent_classifier() -> IntentClassifier:
    """IntentClassifier 싱글톤 인스턴스 반환"""
    global _intent_classifier_instance
    if _intent_classifier_instance is None:
        _intent_classifier_instance = IntentClassifier()
    return _intent_classifier_instance
