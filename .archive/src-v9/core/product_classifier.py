"""
제품 카테고리 자동 분류 모듈
Product Category Classifier

목적: 제품명과 메타데이터를 기반으로 Bottle/Jar/Cap/Pump 자동 분류
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple


class ProductCategory(Enum):
    """제품 메인 카테고리"""

    BOTTLE = "bottle"
    JAR = "jar"
    CAP = "cap"
    PUMP = "pump"
    UNKNOWN = "unknown"


class ProductSubCategory(Enum):
    """제품 서브 카테고리"""

    # Bottles
    BLOW_BOTTLE = "blow_bottle"  # 브로우용기
    PET_BOTTLE = "pet_bottle"  # PET 용기
    ROUND_BOTTLE = "round_bottle"  # 원형 용기
    OVAL_BOTTLE = "oval_bottle"  # 타원형 용기
    SQUARE_BOTTLE = "square_bottle"  # 사각 용기

    # Jars
    CREAM_JAR = "cream_jar"  # 크림용기
    ROUND_JAR = "round_jar"  # R용기 (Round jar)
    AIRLESS_JAR = "airless_jar"  # 에어리스 용기

    # Caps
    SCREW_CAP = "screw_cap"  # 나사 캡
    FLIP_CAP = "flip_cap"  # 플립 캡
    DISC_CAP = "disc_cap"  # 디스크 캡

    # Pumps
    REGULAR_PUMP = "regular_pump"  # 일반 펌프
    DISPENSER = "dispenser"  # 디스펜서
    MIST_PUMP = "mist_pump"  # 미스트 펌프

    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """분류 결과"""

    category: ProductCategory
    sub_category: ProductSubCategory
    confidence: float  # 0.0 ~ 1.0
    reasoning: str  # 분류 근거


class ProductClassifier:
    """제품 카테고리 분류기"""

    # 카테고리별 키워드 패턴
    BOTTLE_KEYWORDS = [
        r"브로우\s*용기",
        r"블로우\s*용기",
        r"병",
        r"보틀",
        r"PET.*용기",
        r"PE.*용기",
        r"PETG.*용기",
        r"\d+ml.*용기",
        r"원형.*용기",
        r"타원형.*용기",
        r"사각.*용기",
    ]

    JAR_KEYWORDS = [
        r"크림\s*용기",
        r"크림\s*자",
        r"R\s*용기",
        r"jar",
        r"에어리스",
        r"자용기",
        r"광\s*용기",
    ]

    CAP_KEYWORDS = [
        r"캡",
        r"뚜껑",
        r"cap",
        r"마개",
        r"나사\s*캡",
        r"플립\s*캡",
        r"디스크\s*캡",
        r"스크류",
    ]

    PUMP_KEYWORDS = [
        r"펌프",
        r"pump",
        r"디스펜서",
        r"dispenser",
        r"미스트",
        r"mist",
        r"\d+파이.*펌프",
    ]

    # 서브 카테고리 패턴
    SUB_CATEGORY_PATTERNS = {
        # Bottles
        ProductSubCategory.BLOW_BOTTLE: [r"브로우", r"블로우"],
        ProductSubCategory.PET_BOTTLE: [r"PET\s*\d+ml", r"PET.*용기"],
        ProductSubCategory.ROUND_BOTTLE: [r"원형.*용기"],
        ProductSubCategory.OVAL_BOTTLE: [r"타원형.*용기"],
        ProductSubCategory.SQUARE_BOTTLE: [r"사각.*용기", r"각.*용기"],
        # Jars
        ProductSubCategory.CREAM_JAR: [r"크림\s*용기", r"크림\s*자"],
        ProductSubCategory.ROUND_JAR: [r"R\s*용기", r"라운드"],
        ProductSubCategory.AIRLESS_JAR: [r"에어리스"],
        # Caps
        ProductSubCategory.SCREW_CAP: [r"나사\s*캡", r"스크류"],
        ProductSubCategory.FLIP_CAP: [r"플립\s*캡"],
        ProductSubCategory.DISC_CAP: [r"디스크\s*캡"],
        # Pumps
        ProductSubCategory.REGULAR_PUMP: [r"\d+파이\s*일반\s*펌프", r"일반\s*펌프"],
        ProductSubCategory.DISPENSER: [r"디스펜서"],
        ProductSubCategory.MIST_PUMP: [r"미스트"],
    }

    def __init__(self):
        """초기화"""
        pass

    def classify(self, product_data: Dict) -> ClassificationResult:
        """
        제품 데이터를 분석하여 카테고리 분류

        Args:
            product_data: 제품 데이터 딕셔너리

        Returns:
            ClassificationResult: 분류 결과
        """
        # 1. 제품명 추출
        product_name = product_data.get("product_name", "")
        if not product_name:
            product_name = product_data.get("description", "")

        # None 체크
        if product_name is None:
            product_name = ""

        # 2. 추가 힌트 (구조 기반)
        has_enriched_info = "enriched_info" in product_data
        has_vendor = "vendor" in product_data
        has_pump_spec = "파이" in product_name or "Ø" in str(product_data)

        # 3. 메인 카테고리 분류
        category, cat_confidence, cat_reasoning = self._classify_main_category(
            product_name, has_enriched_info, has_vendor, has_pump_spec
        )

        # 4. 서브 카테고리 분류
        sub_category, sub_confidence = self._classify_sub_category(product_name, category)

        # 5. 최종 confidence (메인 카테고리 confidence 우선)
        final_confidence = cat_confidence * 0.7 + sub_confidence * 0.3

        return ClassificationResult(
            category=category,
            sub_category=sub_category,
            confidence=final_confidence,
            reasoning=cat_reasoning,
        )

    def _classify_main_category(
        self, product_name: str, has_enriched_info: bool, has_vendor: bool, has_pump_spec: bool
    ) -> Tuple[ProductCategory, float, str]:
        """
        메인 카테고리 분류

        Returns:
            (category, confidence, reasoning)
        """
        # 구조 기반 힌트
        if has_vendor and has_pump_spec:
            return ProductCategory.PUMP, 0.9, "vendor + pump spec present"

        if has_vendor:
            return ProductCategory.CAP, 0.7, "vendor field present (likely cap/pump)"

        if has_enriched_info:
            # enriched_info는 주로 Bottle/Jar에만 있음
            # Bottle vs Jar 구분
            if self._matches_patterns(product_name, self.JAR_KEYWORDS):
                return ProductCategory.JAR, 0.85, "jar keywords + enriched_info"
            else:
                return ProductCategory.BOTTLE, 0.85, "bottle keywords + enriched_info"

        # 키워드 기반 분류
        if self._matches_patterns(product_name, self.PUMP_KEYWORDS):
            return ProductCategory.PUMP, 0.8, "pump keywords matched"

        if self._matches_patterns(product_name, self.CAP_KEYWORDS):
            return ProductCategory.CAP, 0.8, "cap keywords matched"

        if self._matches_patterns(product_name, self.JAR_KEYWORDS):
            return ProductCategory.JAR, 0.75, "jar keywords matched"

        if self._matches_patterns(product_name, self.BOTTLE_KEYWORDS):
            return ProductCategory.BOTTLE, 0.75, "bottle keywords matched"

        return ProductCategory.UNKNOWN, 0.3, "no clear category match"

    def _classify_sub_category(
        self, product_name: str, main_category: ProductCategory
    ) -> Tuple[ProductSubCategory, float]:
        """
        서브 카테고리 분류

        Returns:
            (sub_category, confidence)
        """
        # 메인 카테고리에 맞는 서브 카테고리만 검사
        for sub_cat, patterns in self.SUB_CATEGORY_PATTERNS.items():
            # 메인 카테고리와 서브 카테고리가 일치하는지 확인
            if not self._is_compatible_sub_category(main_category, sub_cat):
                continue

            if self._matches_patterns(product_name, patterns):
                return sub_cat, 0.8

        # 기본 서브 카테고리 (메인 카테고리 기반)
        default_sub = self._get_default_sub_category(main_category)
        return default_sub, 0.5

    def _is_compatible_sub_category(
        self, main_cat: ProductCategory, sub_cat: ProductSubCategory
    ) -> bool:
        """메인 카테고리와 서브 카테고리 호환성 확인"""
        compatibility = {
            ProductCategory.BOTTLE: [
                ProductSubCategory.BLOW_BOTTLE,
                ProductSubCategory.PET_BOTTLE,
                ProductSubCategory.ROUND_BOTTLE,
                ProductSubCategory.OVAL_BOTTLE,
                ProductSubCategory.SQUARE_BOTTLE,
            ],
            ProductCategory.JAR: [
                ProductSubCategory.CREAM_JAR,
                ProductSubCategory.ROUND_JAR,
                ProductSubCategory.AIRLESS_JAR,
            ],
            ProductCategory.CAP: [
                ProductSubCategory.SCREW_CAP,
                ProductSubCategory.FLIP_CAP,
                ProductSubCategory.DISC_CAP,
            ],
            ProductCategory.PUMP: [
                ProductSubCategory.REGULAR_PUMP,
                ProductSubCategory.DISPENSER,
                ProductSubCategory.MIST_PUMP,
            ],
        }

        return sub_cat in compatibility.get(main_cat, [])

    def _get_default_sub_category(self, main_cat: ProductCategory) -> ProductSubCategory:
        """메인 카테고리에 대한 기본 서브 카테고리"""
        defaults = {
            ProductCategory.BOTTLE: ProductSubCategory.BLOW_BOTTLE,
            ProductCategory.JAR: ProductSubCategory.ROUND_JAR,
            ProductCategory.CAP: ProductSubCategory.SCREW_CAP,
            ProductCategory.PUMP: ProductSubCategory.REGULAR_PUMP,
        }
        return defaults.get(main_cat, ProductSubCategory.UNKNOWN)

    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """텍스트가 패턴 리스트 중 하나와 매칭되는지 확인"""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False


# Batch classification function
def classify_products(products: List[Dict]) -> List[Dict]:
    """
    제품 리스트를 일괄 분류

    Args:
        products: 제품 데이터 리스트

    Returns:
        분류 결과가 추가된 제품 리스트
    """
    classifier = ProductClassifier()
    results = []

    for product in products:
        classification = classifier.classify(product)
        product_with_class = product.copy()
        product_with_class["classification"] = {
            "category": classification.category.value,
            "sub_category": classification.sub_category.value,
            "confidence": classification.confidence,
            "reasoning": classification.reasoning,
        }
        results.append(product_with_class)

    return results


if __name__ == "__main__":
    # Test examples
    test_products = [
        {"product_name": "40ml 브로우용기", "enriched_info": {}},
        {"product_name": "30g 크림용기 / 헤비브로우"},
        {"product_name": "PET 150ml 원형R용기 (SHORT)"},
        {"vendor": "지에프테크", "description": "Ø24 펌프 211AVP", "spec": "24파이 일반펌프"},
    ]

    classifier = ProductClassifier()
    for prod in test_products:
        result = classifier.classify(prod)
        print(f"\nProduct: {prod.get('product_name', prod.get('description', 'N/A'))}")
        print(f"Category: {result.category.value}")
        print(f"Sub-category: {result.sub_category.value}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Reasoning: {result.reasoning}")
