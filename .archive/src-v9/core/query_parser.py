"""
자연어 쿼리 파서 (Natural Language Query Parser)
Query Parser & Entity Extractor

목적: 자연어 질문에서 검색 가능한 엔티티 추출
예시: "20파이 캡 5,000개 주문 가능한 제품 추천해줘"
     → {neck: "Ø20", category: "cap", moq: 5000}
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class EntityType(Enum):
    """추출 가능한 엔티티 타입"""

    # Specifications
    CAPACITY = "capacity"  # 용량 (ml, g)
    NECK = "neck"  # Neck 직경 (파이, Ø)
    DIAMETER = "diameter"  # 직경
    SIZE = "size"  # 사이즈

    # Materials
    MATERIAL = "material"  # 재질 (PE, PET, PP 등)

    # Business
    MOQ = "moq"  # 최소 주문량
    PRICE = "price"  # 가격

    # Category
    CATEGORY = "category"  # 제품 카테고리

    # Use Case
    USE_CASE = "use_case"  # 용도
    PRODUCT_TYPE = "product_type"  # 제품 유형

    # Origin
    ORIGIN = "origin"  # 원산지
    MANUFACTURER = "manufacturer"  # 제조사

    # Attributes
    ATTRIBUTE = "attribute"  # 속성 (가벼운, 작은, 큰 등)


@dataclass
class ExtractedEntity:
    """추출된 엔티티"""

    entity_type: EntityType
    value: Any
    original_text: str  # 원본 텍스트
    confidence: float = 1.0  # 신뢰도
    position: int = 0  # 텍스트 내 위치


@dataclass
class ParsedQuery:
    """파싱된 쿼리"""

    original_query: str
    entities: List[ExtractedEntity]
    intent: str = "search"  # search, recommend, compare, info

    def get_entities_by_type(self, entity_type: EntityType) -> List[ExtractedEntity]:
        """특정 타입의 엔티티만 필터링"""
        return [e for e in self.entities if e.entity_type == entity_type]

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "original_query": self.original_query,
            "intent": self.intent,
            "entities": {e.entity_type.value: e.value for e in self.entities},
        }


class QueryParser:
    """자연어 쿼리 파서"""

    # ========== Pattern Definitions ==========

    # Neck/Diameter patterns (파이, Ø)
    NECK_PATTERNS = [
        r"(\d+)\s*파이",  # "20파이", "24 파이"
        r"Ø\s*(\d+)",  # "Ø20", "Ø 24"
        r"(\d+)\s*mm\s*입구",  # "20mm 입구"
        r"neck\s*(\d+)",  # "neck 20"
        r"넥\s*(\d+)",  # "넥 20"
    ]

    # Capacity patterns (ml, g)
    CAPACITY_PATTERNS = [
        r"(\d+)\s*ml",  # "100ml", "100 ml"
        r"(\d+)\s*g",  # "50g", "50 g"
        r"(\d+)\s*리터",  # "1리터"
        r"(\d+)\s*cc",  # "100cc"
    ]

    # MOQ patterns (최소 주문량)
    MOQ_PATTERNS = [
        r"(\d{1,3}(?:,\d{3})*)\s*개",  # "5,000개", "1000개"
        r"최소\s*(\d{1,3}(?:,\d{3})*)",  # "최소 5000"
        r"MOQ\s*(\d{1,3}(?:,\d{3})*)",  # "MOQ 5000"
        r"(\d{1,3}(?:,\d{3})*)\s*이상",  # "5000개 이상"
    ]

    # Price patterns (가격)
    PRICE_PATTERNS = [
        r"(\d{1,3}(?:,\d{3})*)\s*원",  # "1,000원"
        r"가격\s*(\d{1,3}(?:,\d{3})*)",  # "가격 1000"
    ]

    # Size patterns (사이즈, 크기)
    SIZE_PATTERNS = [
        r"Ø\s*(\d+\.?\d*)\s*[×xX]\s*(\d+\.?\d*)",  # "Ø23.8 × 51.5"
        r"(\d+)\s*[×xX]\s*(\d+)\s*mm",  # "50 x 100 mm"
    ]

    # Material keywords
    MATERIAL_KEYWORDS = {
        "PE": ["PE", "폴리에틸렌"],
        "PET": ["PET", "페트"],
        "PP": ["PP", "폴리프로필렌"],
        "PETG": ["PETG"],
        "유리": ["유리", "glass"],
        "알루미늄": ["알루미늄", "aluminum"],
    }

    # Category keywords
    CATEGORY_KEYWORDS = {
        "bottle": ["병", "보틀", "bottle", "용기"],
        "jar": ["자", "jar", "크림용기", "크림자"],
        "cap": ["캡", "뚜껑", "cap", "마개"],
        "pump": ["펌프", "pump", "디스펜서", "dispenser"],
    }

    # Use case keywords
    USE_CASE_KEYWORDS = {
        "화장수": ["화장수", "토너", "toner"],
        "에센스": ["에센스", "essence", "세럼", "serum"],
        "로션": ["로션", "lotion", "밀크"],
        "크림": ["크림", "cream"],
        "샴푸": ["샴푸", "shampoo"],
        "바디": ["바디", "body"],
    }

    # Origin keywords
    ORIGIN_KEYWORDS = {
        "한국": ["한국", "국내", "국산", "한국산"],
        "중국": ["중국", "중국산"],
        "일본": ["일본", "일본산"],
    }

    # Attribute keywords
    ATTRIBUTE_KEYWORDS = {
        "작은": ["작은", "소형", "미니", "트래블"],
        "큰": ["큰", "대형", "라지"],
        "가벼운": ["가벼운", "경량", "light"],
        "휴대용": ["휴대", "휴대용", "portable"],
        "투명": ["투명", "clear"],
        "불투명": ["불투명", "opaque"],
    }

    # Intent keywords
    INTENT_KEYWORDS = {
        "search": ["찾아줘", "검색", "보여줘", "알려줘"],
        "recommend": ["추천", "recommend", "좋은", "적합한"],
        "compare": ["비교", "차이", "compare"],
        "info": ["정보", "스펙", "상세", "설명"],
    }

    def __init__(self):
        """초기화"""
        pass

    def parse(self, query: str) -> ParsedQuery:
        """
        자연어 쿼리 파싱

        Args:
            query: 자연어 질문 (예: "20파이 캡 5,000개 주문 가능한 제품 추천해줘")

        Returns:
            ParsedQuery: 파싱 결과
        """
        entities = []

        # 1. Neck/Diameter 추출
        neck_entities = self._extract_neck(query)
        entities.extend(neck_entities)

        # 2. Capacity 추출
        capacity_entities = self._extract_capacity(query)
        entities.extend(capacity_entities)

        # 3. MOQ 추출
        moq_entities = self._extract_moq(query)
        entities.extend(moq_entities)

        # 4. Price 추출
        price_entities = self._extract_price(query)
        entities.extend(price_entities)

        # 5. Size 추출
        size_entities = self._extract_size(query)
        entities.extend(size_entities)

        # 6. Material 추출
        material_entities = self._extract_material(query)
        entities.extend(material_entities)

        # 7. Category 추출
        category_entities = self._extract_category(query)
        entities.extend(category_entities)

        # 8. Use Case 추출
        use_case_entities = self._extract_use_case(query)
        entities.extend(use_case_entities)

        # 9. Origin 추출
        origin_entities = self._extract_origin(query)
        entities.extend(origin_entities)

        # 10. Attributes 추출
        attribute_entities = self._extract_attributes(query)
        entities.extend(attribute_entities)

        # 11. Intent 추출
        intent = self._extract_intent(query)

        return ParsedQuery(original_query=query, entities=entities, intent=intent)

    # ========== Entity Extractors ==========

    def _extract_neck(self, query: str) -> List[ExtractedEntity]:
        """Neck 직경 추출"""
        entities = []
        for pattern in self.NECK_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                neck_value = int(match.group(1))
                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.NECK,
                        value=f"Ø{neck_value}",
                        original_text=match.group(0),
                        confidence=0.95,
                        position=match.start(),
                    )
                )
                break  # First match wins
        return entities

    def _extract_capacity(self, query: str) -> List[ExtractedEntity]:
        """용량 추출"""
        entities = []
        for pattern in self.CAPACITY_PATTERNS:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                capacity_value = int(match.group(1))
                unit = "ml" if "ml" in match.group(0).lower() else "g"
                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.CAPACITY,
                        value=f"{capacity_value}{unit}",
                        original_text=match.group(0),
                        confidence=0.95,
                        position=match.start(),
                    )
                )
        return entities

    def _extract_moq(self, query: str) -> List[ExtractedEntity]:
        """MOQ 추출"""
        entities = []
        for pattern in self.MOQ_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                moq_str = match.group(1).replace(",", "")
                moq_value = int(moq_str)
                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.MOQ,
                        value=moq_value,
                        original_text=match.group(0),
                        confidence=0.9,
                        position=match.start(),
                    )
                )
                break
        return entities

    def _extract_price(self, query: str) -> List[ExtractedEntity]:
        """가격 추출"""
        entities = []
        for pattern in self.PRICE_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(",", "")
                price_value = int(price_str)
                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.PRICE,
                        value=price_value,
                        original_text=match.group(0),
                        confidence=0.85,
                        position=match.start(),
                    )
                )
                break
        return entities

    def _extract_size(self, query: str) -> List[ExtractedEntity]:
        """사이즈 추출"""
        entities = []
        for pattern in self.SIZE_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.SIZE,
                        value=match.group(0),
                        original_text=match.group(0),
                        confidence=0.9,
                        position=match.start(),
                    )
                )
                break
        return entities

    def _extract_material(self, query: str) -> List[ExtractedEntity]:
        """재질 추출"""
        entities = []
        for material, keywords in self.MATERIAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    entities.append(
                        ExtractedEntity(
                            entity_type=EntityType.MATERIAL,
                            value=material,
                            original_text=keyword,
                            confidence=0.9,
                        )
                    )
                    return entities  # First match wins
        return entities

    def _extract_category(self, query: str) -> List[ExtractedEntity]:
        """카테고리 추출"""
        entities = []
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    entities.append(
                        ExtractedEntity(
                            entity_type=EntityType.CATEGORY,
                            value=category,
                            original_text=keyword,
                            confidence=0.95,
                        )
                    )
                    return entities  # First match wins
        return entities

    def _extract_use_case(self, query: str) -> List[ExtractedEntity]:
        """용도 추출"""
        entities = []
        for use_case, keywords in self.USE_CASE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    entities.append(
                        ExtractedEntity(
                            entity_type=EntityType.USE_CASE,
                            value=use_case,
                            original_text=keyword,
                            confidence=0.8,
                        )
                    )
        return entities

    def _extract_origin(self, query: str) -> List[ExtractedEntity]:
        """원산지 추출"""
        entities = []
        for origin, keywords in self.ORIGIN_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    entities.append(
                        ExtractedEntity(
                            entity_type=EntityType.ORIGIN,
                            value=origin,
                            original_text=keyword,
                            confidence=0.9,
                        )
                    )
                    return entities
        return entities

    def _extract_attributes(self, query: str) -> List[ExtractedEntity]:
        """속성 추출"""
        entities = []
        for attr, keywords in self.ATTRIBUTE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    entities.append(
                        ExtractedEntity(
                            entity_type=EntityType.ATTRIBUTE,
                            value=attr,
                            original_text=keyword,
                            confidence=0.7,
                        )
                    )
        return entities

    def _extract_intent(self, query: str) -> str:
        """의도 추출"""
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return intent
        return "search"  # Default


if __name__ == "__main__":
    # Test cases
    test_queries = [
        "20파이 캡 5,000개 주문 가능한 제품 추천해줘",
        "100ml PE 보틀 찾아줘",
        "한국산 PP 재질 크림 자",
        "24파이 펌프 최소 1000개",
        "에센스 담을 수 있는 소형 용기",
        "Ø23.8 × 51.5 사이즈 캡",
        "가벼운 트래블용 40ml 병",
    ]

    parser = QueryParser()

    print("=" * 80)
    print("QUERY PARSER TEST")
    print("=" * 80)

    for query in test_queries:
        print(f"\n{'─'*80}")
        print(f"Query: {query}")
        print(f"{'─'*80}")

        result = parser.parse(query)

        print(f"Intent: {result.intent}")
        print(f"\nExtracted Entities ({len(result.entities)}):")
        for entity in result.entities:
            print(f"  • {entity.entity_type.value.upper()}: {entity.value}")
            print(f"    - Original: '{entity.original_text}'")
            print(f"    - Confidence: {entity.confidence}")

        print(f"\nStructured Output:")
        print(f"  {result.to_dict()}")
