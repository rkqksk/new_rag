"""
카테고리별 템플릿 시스템
Category-Specific Template System

목적: Bottle/Jar/Cap/Pump 각 카테고리에 최적화된 템플릿 제공
전략: 같은 필드라도 카테고리에 따라 다른 표현 사용
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from src.core.chunk_templates import FieldType, ChunkTemplate


class ProductCategory(Enum):
    """제품 카테고리"""
    BOTTLE = "bottle"
    JAR = "jar"
    CAP = "cap"
    PUMP = "pump"
    UNKNOWN = "unknown"


@dataclass
class CategoryTemplateSet:
    """카테고리별 템플릿 세트"""
    category: ProductCategory
    templates: Dict[FieldType, List[ChunkTemplate]]


class CategoryTemplateRegistry:
    """카테고리별 템플릿 레지스트리"""

    def __init__(self):
        """초기화 - 카테고리별 템플릿 등록"""
        self.category_templates: Dict[ProductCategory, Dict[FieldType, List[ChunkTemplate]]] = {
            ProductCategory.BOTTLE: {},
            ProductCategory.JAR: {},
            ProductCategory.CAP: {},
            ProductCategory.PUMP: {},
            ProductCategory.UNKNOWN: {},
        }
        self._register_category_templates()

    def _register_category_templates(self):
        """카테고리별 템플릿 등록"""
        self._register_bottle_templates()
        self._register_jar_templates()
        self._register_cap_templates()
        self._register_pump_templates()

    # ========== Bottle Templates ==========
    def _register_bottle_templates(self):
        """Bottle 전용 템플릿"""
        bottle = self.category_templates[ProductCategory.BOTTLE]

        # Product Name (Bottle)
        bottle[FieldType.PRODUCT_NAME] = [
            ChunkTemplate(
                field_type=FieldType.PRODUCT_NAME,
                template="{field} 보틀",
                priority=1.0,
                search_keywords=["병", "보틀", "용기", "bottle"]
            ),
            ChunkTemplate(
                field_type=FieldType.PRODUCT_NAME,
                template="{field} 플라스틱 용기",
                priority=0.95,
                search_keywords=["플라스틱", "용기"]
            ),
        ]

        # Capacity (Bottle)
        bottle[FieldType.CAPACITY] = [
            ChunkTemplate(
                field_type=FieldType.CAPACITY,
                template="{field} 용량 보틀",
                priority=0.95,
                search_keywords=["용량", "ml", "리터", "담다"]
            ),
            ChunkTemplate(
                field_type=FieldType.CAPACITY,
                template="{field} 병",
                priority=0.9,
                search_keywords=["용량", "병"]
            ),
            ChunkTemplate(
                field_type=FieldType.CAPACITY,
                template="{field} 액상 용기",
                priority=0.85,
                search_keywords=["액상", "액체"]
            ),
        ]

        # Neck (Bottle) - 중요! 캡과 호환성
        bottle[FieldType.NECK] = [
            ChunkTemplate(
                field_type=FieldType.NECK,
                template="Neck {field} 보틀 (캡 호환)",
                priority=0.95,
                search_keywords=["neck", "넥", "입구", "캡", "뚜껑", "호환"]
            ),
            ChunkTemplate(
                field_type=FieldType.NECK,
                template="{field} 입구 병 ({field} 캡 사용 가능)",
                priority=0.9,
                search_keywords=["입구", "캡", "맞는"]
            ),
        ]

        # Material (Bottle)
        bottle[FieldType.MATERIAL] = [
            ChunkTemplate(
                field_type=FieldType.MATERIAL,
                template="{field} 재질 보틀",
                priority=0.95,
                search_keywords=["재질", "소재", "PE", "PET", "PETG"]
            ),
            ChunkTemplate(
                field_type=FieldType.MATERIAL,
                template="{field} 플라스틱 병",
                priority=0.9,
                search_keywords=["플라스틱", "병"]
            ),
            ChunkTemplate(
                field_type=FieldType.MATERIAL,
                template="{field} 소재 액상 용기",
                priority=0.85,
                search_keywords=["액상", "소재"]
            ),
        ]

        # Use Case (Bottle)
        bottle[FieldType.USE_CASE] = [
            ChunkTemplate(
                field_type=FieldType.USE_CASE,
                template="{field} 담는 보틀",
                priority=0.95,
                search_keywords=["담다", "넣다", "보관", "용도"]
            ),
            ChunkTemplate(
                field_type=FieldType.USE_CASE,
                template="{field} 포장용 병",
                priority=0.9,
                search_keywords=["포장", "용도"]
            ),
        ]

    # ========== Jar Templates ==========
    def _register_jar_templates(self):
        """Jar 전용 템플릿"""
        jar = self.category_templates[ProductCategory.JAR]

        # Product Name (Jar)
        jar[FieldType.PRODUCT_NAME] = [
            ChunkTemplate(
                field_type=FieldType.PRODUCT_NAME,
                template="{field} 자",
                priority=1.0,
                search_keywords=["자", "jar", "크림용기", "통"]
            ),
            ChunkTemplate(
                field_type=FieldType.PRODUCT_NAME,
                template="{field} 크림 용기",
                priority=0.95,
                search_keywords=["크림", "용기"]
            ),
        ]

        # Capacity (Jar)
        jar[FieldType.CAPACITY] = [
            ChunkTemplate(
                field_type=FieldType.CAPACITY,
                template="{field} 용량 크림 자",
                priority=0.95,
                search_keywords=["용량", "ml", "g", "크림"]
            ),
            ChunkTemplate(
                field_type=FieldType.CAPACITY,
                template="{field} 자",
                priority=0.9,
                search_keywords=["용량", "자"]
            ),
            ChunkTemplate(
                field_type=FieldType.CAPACITY,
                template="{field} 크림 담는 용기",
                priority=0.85,
                search_keywords=["크림", "담다"]
            ),
        ]

        # Diameter (Jar) - 자의 경우 직경이 중요
        jar[FieldType.DIAMETER] = [
            ChunkTemplate(
                field_type=FieldType.DIAMETER,
                template="직경 {field} 크림 자",
                priority=0.95,
                search_keywords=["직경", "지름", "파이", "크기"]
            ),
            ChunkTemplate(
                field_type=FieldType.DIAMETER,
                template="{field} 자 (원형)",
                priority=0.9,
                search_keywords=["원형", "둥근"]
            ),
        ]

        # Material (Jar)
        jar[FieldType.MATERIAL] = [
            ChunkTemplate(
                field_type=FieldType.MATERIAL,
                template="{field} 재질 크림 자",
                priority=0.95,
                search_keywords=["재질", "소재", "PP", "PET", "유리"]
            ),
            ChunkTemplate(
                field_type=FieldType.MATERIAL,
                template="{field} 크림 용기",
                priority=0.9,
                search_keywords=["크림", "소재"]
            ),
        ]

        # Use Case (Jar)
        jar[FieldType.USE_CASE] = [
            ChunkTemplate(
                field_type=FieldType.USE_CASE,
                template="{field} 담는 크림 자",
                priority=0.95,
                search_keywords=["담다", "넣다", "크림", "용도"]
            ),
            ChunkTemplate(
                field_type=FieldType.USE_CASE,
                template="{field} 포장용 자",
                priority=0.9,
                search_keywords=["포장", "용도"]
            ),
        ]

    # ========== Cap Templates ==========
    def _register_cap_templates(self):
        """Cap 전용 템플릿"""
        cap = self.category_templates[ProductCategory.CAP]

        # Product Name (Cap)
        cap[FieldType.PRODUCT_NAME] = [
            ChunkTemplate(
                field_type=FieldType.PRODUCT_NAME,
                template="{field} 캡",
                priority=1.0,
                search_keywords=["캡", "뚜껑", "마개", "cap"]
            ),
            ChunkTemplate(
                field_type=FieldType.PRODUCT_NAME,
                template="{field} 뚜껑",
                priority=0.95,
                search_keywords=["뚜껑", "마개"]
            ),
        ]

        # Size (Cap) - 캡의 사이즈는 전체 치수
        cap[FieldType.SIZE] = [
            ChunkTemplate(
                field_type=FieldType.SIZE,
                template="사이즈 {field} 캡",
                priority=0.9,
                search_keywords=["사이즈", "크기", "규격", "mm"]
            ),
            ChunkTemplate(
                field_type=FieldType.SIZE,
                template="{field} 규격 뚜껑",
                priority=0.85,
                search_keywords=["규격", "뚜껑"]
            ),
        ]

        # Neck (Cap) - 캡의 neck은 호환되는 병의 neck
        cap[FieldType.NECK] = [
            ChunkTemplate(
                field_type=FieldType.NECK,
                template="Neck {field} 호환 캡",
                priority=0.98,
                search_keywords=["neck", "넥", "호환", "맞는", "파이"]
            ),
            ChunkTemplate(
                field_type=FieldType.NECK,
                template="{field} 병에 맞는 캡",
                priority=0.95,
                search_keywords=["호환", "맞다", "병"]
            ),
            ChunkTemplate(
                field_type=FieldType.NECK,
                template="{field} 입구용 뚜껑",
                priority=0.9,
                search_keywords=["입구", "뚜껑"]
            ),
        ]

        # Material (Cap)
        cap[FieldType.MATERIAL] = [
            ChunkTemplate(
                field_type=FieldType.MATERIAL,
                template="{field} 재질 캡",
                priority=0.95,
                search_keywords=["재질", "소재", "PP", "PE"]
            ),
            ChunkTemplate(
                field_type=FieldType.MATERIAL,
                template="{field} 플라스틱 뚜껑",
                priority=0.9,
                search_keywords=["플라스틱", "뚜껑"]
            ),
        ]

        # MOQ (Cap) - 캡은 대량 주문이 일반적
        cap[FieldType.MOQ] = [
            ChunkTemplate(
                field_type=FieldType.MOQ,
                template="최소주문수량 {field}개 (캡)",
                priority=0.95,
                search_keywords=["MOQ", "최소주문", "수량", "개수"]
            ),
            ChunkTemplate(
                field_type=FieldType.MOQ,
                template="{field}개부터 주문 가능한 캡",
                priority=0.9,
                search_keywords=["주문", "최소", "캡"]
            ),
        ]

        # Manufacturer (Cap)
        cap[FieldType.MANUFACTURER] = [
            ChunkTemplate(
                field_type=FieldType.MANUFACTURER,
                template="{field} 제조 캡",
                priority=0.95,
                search_keywords=["제조사", "업체", "회사"]
            ),
        ]

    # ========== Pump Templates ==========
    def _register_pump_templates(self):
        """Pump 전용 템플릿"""
        pump = self.category_templates[ProductCategory.PUMP]

        # Product Name (Pump)
        pump[FieldType.PRODUCT_NAME] = [
            ChunkTemplate(
                field_type=FieldType.PRODUCT_NAME,
                template="{field} 펌프",
                priority=1.0,
                search_keywords=["펌프", "pump", "디스펜서"]
            ),
            ChunkTemplate(
                field_type=FieldType.PRODUCT_NAME,
                template="{field} 디스펜서",
                priority=0.95,
                search_keywords=["디스펜서", "dispenser"]
            ),
        ]

        # Neck (Pump) - 펌프의 neck은 직경과 동일 (호환성 중요)
        pump[FieldType.NECK] = [
            ChunkTemplate(
                field_type=FieldType.NECK,
                template="{field} 펌프 (병 호환)",
                priority=0.98,
                search_keywords=["펌프", "직경", "파이", "호환"]
            ),
            ChunkTemplate(
                field_type=FieldType.NECK,
                template="{field} 병에 맞는 펌프",
                priority=0.95,
                search_keywords=["호환", "맞다", "병"]
            ),
        ]

        # Diameter (Pump) - 펌프는 직경이 핵심 스펙
        pump[FieldType.DIAMETER] = [
            ChunkTemplate(
                field_type=FieldType.DIAMETER,
                template="{field} 펌프",
                priority=0.98,
                search_keywords=["직경", "파이", "Ø", "mm"]
            ),
            ChunkTemplate(
                field_type=FieldType.DIAMETER,
                template="{field} 직경 디스펜서",
                priority=0.95,
                search_keywords=["직경", "디스펜서"]
            ),
        ]

        # Material (Pump)
        pump[FieldType.MATERIAL] = [
            ChunkTemplate(
                field_type=FieldType.MATERIAL,
                template="{field} 재질 펌프",
                priority=0.95,
                search_keywords=["재질", "소재", "PP", "PE"]
            ),
        ]

        # Package (Pump) - 펌프는 박스 단위 판매
        pump[FieldType.PACKAGE] = [
            ChunkTemplate(
                field_type=FieldType.PACKAGE,
                template="{field} 패키지 (펌프)",
                priority=0.85,
                search_keywords=["패키지", "포장", "박스", "단위"]
            ),
        ]

        # Manufacturer (Pump)
        pump[FieldType.MANUFACTURER] = [
            ChunkTemplate(
                field_type=FieldType.MANUFACTURER,
                template="{field} 제조 펌프",
                priority=0.95,
                search_keywords=["제조사", "업체", "회사"]
            ),
        ]

    # ========== Public API ==========

    def get_templates(
        self,
        field_type: FieldType,
        category: ProductCategory
    ) -> List[ChunkTemplate]:
        """
        카테고리에 맞는 템플릿 반환

        Args:
            field_type: 필드 타입
            category: 제품 카테고리

        Returns:
            해당 카테고리의 템플릿 리스트 (없으면 빈 리스트)
        """
        category_templates = self.category_templates.get(category, {})
        return category_templates.get(field_type, [])

    def add_custom_template(
        self,
        category: ProductCategory,
        field_type: FieldType,
        template: str,
        priority: float,
        search_keywords: List[str]
    ):
        """
        카테고리별 커스텀 템플릿 추가 (동적 확장)

        Args:
            category: 제품 카테고리
            field_type: 필드 타입
            template: 템플릿 문자열
            priority: 우선순위
            search_keywords: 검색 키워드
        """
        custom_template = ChunkTemplate(
            field_type=field_type,
            template=template,
            priority=priority,
            search_keywords=search_keywords
        )

        if category not in self.category_templates:
            self.category_templates[category] = {}

        if field_type not in self.category_templates[category]:
            self.category_templates[category][field_type] = []

        self.category_templates[category][field_type].append(custom_template)


if __name__ == "__main__":
    # Test with different categories
    from src.core.chunk_templates import FieldExtractor

    test_products = {
        "bottle": {
            "product_name": "100ml PET 보틀",
            "capacity": "100ml",
            "neck": "Ø24",
            "material": "PET",
            "use_case": ["화장수", "에센스"]
        },
        "jar": {
            "product_name": "50g 크림용기",
            "capacity": "50g",
            "diameter": "Ø60",
            "material": "PP",
            "use_case": ["크림", "밤"]
        },
        "cap": {
            "product_name": "GY-20-뾰족캡B",
            "size": "Ø23.8 × 51.5",
            "neck": "Ø20",
            "material": "PP",
            "moq": "5,000"
        },
        "pump": {
            "product_name": "Ø24 펌프 211AVP",
            "diameter": "Ø24",
            "material": "PP",
            "manufacturer": "지에프테크",
            "package": "800ea"
        }
    }

    registry = CategoryTemplateRegistry()
    extractor = FieldExtractor()

    for cat_name, product in test_products.items():
        category = ProductCategory(cat_name)
        print(f"\n{'='*60}")
        print(f"Category: {cat_name.upper()}")
        print(f"{'='*60}")

        fields = extractor.extract_fields(product)

        for field_type, value in fields.items():
            templates = registry.get_templates(field_type, category)
            if templates:
                template = templates[0]  # Use first template
                chunk_text = template.generate(value)
                print(f"\n[{field_type.value.upper()}]")
                print(f"  Text: {chunk_text}")
                print(f"  Priority: {template.priority}")
                print(f"  Keywords: {', '.join(template.search_keywords[:5])}")
