"""
청크 템플릿 시스템 (Atomic Field-Level Chunking)
Chunk Template System

목적: 각 필드를 독립적인 청크로 분리하여 세밀한 자연어 검색 지원
전략: 필드별 템플릿 + 조합 템플릿으로 검색 커버리지 극대화
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class FieldType(Enum):
    """필드 타입"""
    # Product Identity
    PRODUCT_NAME = "product_name"
    PRODUCT_CODE = "product_code"

    # Specifications
    CAPACITY = "capacity"
    SIZE = "size"
    NECK = "neck"
    DIAMETER = "diameter"
    DIMENSIONS = "dimensions"
    WEIGHT = "weight"

    # Materials & Manufacturing
    MATERIAL = "material"
    ORIGIN = "origin"
    MANUFACTURER = "manufacturer"

    # Business
    MOQ = "moq"
    PRICE = "price"
    SUPPLY_PRICE = "supply_price"
    SELLING_PRICE = "selling_price"
    PACKAGE = "package"

    # Contact
    PHONE = "phone"
    FAX = "fax"
    EMAIL = "email"
    MANAGER = "manager"

    # Use Cases
    USE_CASE = "use_case"
    TARGET_PRODUCT = "target_product"

    # Descriptions
    DESCRIPTION = "description"
    KEYWORD = "keyword"

    # Composite (조합)
    SPEC_COMPOSITE = "spec_composite"
    BUSINESS_COMPOSITE = "business_composite"


@dataclass
class ChunkTemplate:
    """청크 템플릿"""
    field_type: FieldType
    template: str  # {field} placeholder를 사용
    priority: float  # Search priority
    search_keywords: List[str]  # 검색 시 매칭될 키워드

    def generate(self, value: Any, product_category: str = "") -> str:
        """템플릿으로 청크 텍스트 생성"""
        if isinstance(value, (list, tuple)):
            value = ", ".join(str(v) for v in value)

        text = self.template.format(
            field=value,
            category=product_category
        )
        return text.strip()


class ChunkTemplateRegistry:
    """청크 템플릿 레지스트리 - 확장 가능한 템플릿 관리"""

    def __init__(self):
        """초기화 - 기본 템플릿 등록"""
        self.templates: Dict[FieldType, List[ChunkTemplate]] = {}
        self._register_default_templates()

    def _register_default_templates(self):
        """기본 템플릿 등록"""

        # ========== Product Identity Templates ==========
        self.register(FieldType.PRODUCT_NAME, [
            ChunkTemplate(
                field_type=FieldType.PRODUCT_NAME,
                template="{field}",
                priority=1.0,
                search_keywords=["제품명", "상품명", "이름"]
            ),
            ChunkTemplate(
                field_type=FieldType.PRODUCT_NAME,
                template="{field} {category}",
                priority=0.95,
                search_keywords=["제품", "상품", "용기", "캡", "펌프"]
            ),
        ])

        self.register(FieldType.PRODUCT_CODE, [
            ChunkTemplate(
                field_type=FieldType.PRODUCT_CODE,
                template="제품코드 {field}",
                priority=0.9,
                search_keywords=["제품코드", "코드", "품번", "모델"]
            ),
        ])

        # ========== Specification Templates ==========
        self.register(FieldType.CAPACITY, [
            ChunkTemplate(
                field_type=FieldType.CAPACITY,
                template="{field} 용량 {category}",
                priority=0.95,
                search_keywords=["용량", "ml", "리터", "크기", "사이즈"]
            ),
            ChunkTemplate(
                field_type=FieldType.CAPACITY,
                template="{field} {category} 제품",
                priority=0.9,
                search_keywords=["용량", "크기"]
            ),
        ])

        self.register(FieldType.SIZE, [
            ChunkTemplate(
                field_type=FieldType.SIZE,
                template="사이즈 {field}",
                priority=0.9,
                search_keywords=["사이즈", "크기", "치수", "규격", "mm"]
            ),
            ChunkTemplate(
                field_type=FieldType.SIZE,
                template="{field} 규격",
                priority=0.85,
                search_keywords=["규격", "사이즈"]
            ),
        ])

        self.register(FieldType.NECK, [
            ChunkTemplate(
                field_type=FieldType.NECK,
                template="Neck {field} 호환",
                priority=0.95,
                search_keywords=["neck", "넥", "입구", "직경", "파이", "Ø"]
            ),
            ChunkTemplate(
                field_type=FieldType.NECK,
                template="{field} neck 입구 {category}",
                priority=0.9,
                search_keywords=["입구", "넥"]
            ),
            ChunkTemplate(
                field_type=FieldType.NECK,
                template="{field} 호환 {category}",
                priority=0.85,
                search_keywords=["호환", "맞는"]
            ),
        ])

        self.register(FieldType.DIAMETER, [
            ChunkTemplate(
                field_type=FieldType.DIAMETER,
                template="직경 {field}",
                priority=0.9,
                search_keywords=["직경", "지름", "파이", "Ø", "mm"]
            ),
            ChunkTemplate(
                field_type=FieldType.DIAMETER,
                template="{field} 직경 {category}",
                priority=0.85,
                search_keywords=["직경"]
            ),
        ])

        self.register(FieldType.DIMENSIONS, [
            ChunkTemplate(
                field_type=FieldType.DIMENSIONS,
                template="치수 {field}",
                priority=0.85,
                search_keywords=["치수", "크기", "사이즈", "규격"]
            ),
        ])

        # ========== Material & Manufacturing Templates ==========
        self.register(FieldType.MATERIAL, [
            ChunkTemplate(
                field_type=FieldType.MATERIAL,
                template="{field} 재질 {category}",
                priority=0.95,
                search_keywords=["재질", "소재", "material", "PE", "PET", "PP", "플라스틱"]
            ),
            ChunkTemplate(
                field_type=FieldType.MATERIAL,
                template="{field} {category}",
                priority=0.9,
                search_keywords=["재질", "소재"]
            ),
            ChunkTemplate(
                field_type=FieldType.MATERIAL,
                template="{field} 플라스틱 {category}",
                priority=0.85,
                search_keywords=["플라스틱"]
            ),
        ])

        self.register(FieldType.ORIGIN, [
            ChunkTemplate(
                field_type=FieldType.ORIGIN,
                template="{field}산 {category}",
                priority=0.9,
                search_keywords=["원산지", "제조국", "국산", "한국산", "중국산"]
            ),
            ChunkTemplate(
                field_type=FieldType.ORIGIN,
                template="{field} 제조 {category}",
                priority=0.85,
                search_keywords=["제조", "생산"]
            ),
            ChunkTemplate(
                field_type=FieldType.ORIGIN,
                template="국내산 {category}" if "{field}" == "한국" else "{field}산 {category}",
                priority=0.8,
                search_keywords=["국내", "국산"]
            ),
        ])

        self.register(FieldType.MANUFACTURER, [
            ChunkTemplate(
                field_type=FieldType.MANUFACTURER,
                template="{field} 제조 {category}",
                priority=0.95,
                search_keywords=["제조사", "제조업체", "업체", "회사", "manufacturer"]
            ),
            ChunkTemplate(
                field_type=FieldType.MANUFACTURER,
                template="{field} {category}",
                priority=0.9,
                search_keywords=["제조사"]
            ),
        ])

        # ========== Business Templates ==========
        self.register(FieldType.MOQ, [
            ChunkTemplate(
                field_type=FieldType.MOQ,
                template="최소주문수량 {field}개",
                priority=0.95,
                search_keywords=["MOQ", "최소주문", "최소수량", "minimum", "최소", "개수"]
            ),
            ChunkTemplate(
                field_type=FieldType.MOQ,
                template="{field}개부터 주문 가능",
                priority=0.9,
                search_keywords=["주문", "최소"]
            ),
            ChunkTemplate(
                field_type=FieldType.MOQ,
                template="최소 {field}개 단위 주문",
                priority=0.85,
                search_keywords=["최소", "단위"]
            ),
        ])

        self.register(FieldType.PRICE, [
            ChunkTemplate(
                field_type=FieldType.PRICE,
                template="가격 {field}원",
                priority=0.9,
                search_keywords=["가격", "price", "원", "금액", "비용"]
            ),
        ])

        self.register(FieldType.SUPPLY_PRICE, [
            ChunkTemplate(
                field_type=FieldType.SUPPLY_PRICE,
                template="공급가 {field}원",
                priority=0.85,
                search_keywords=["공급가", "도매가", "공급단가"]
            ),
        ])

        self.register(FieldType.SELLING_PRICE, [
            ChunkTemplate(
                field_type=FieldType.SELLING_PRICE,
                template="판매가 {field}원",
                priority=0.85,
                search_keywords=["판매가", "소비자가", "정가"]
            ),
        ])

        self.register(FieldType.PACKAGE, [
            ChunkTemplate(
                field_type=FieldType.PACKAGE,
                template="{field} 패키지",
                priority=0.8,
                search_keywords=["패키지", "포장", "단위", "박스"]
            ),
        ])

        # ========== Contact Templates ==========
        self.register(FieldType.PHONE, [
            ChunkTemplate(
                field_type=FieldType.PHONE,
                template="전화 {field}",
                priority=0.7,
                search_keywords=["전화", "연락처", "tel", "phone"]
            ),
        ])

        self.register(FieldType.FAX, [
            ChunkTemplate(
                field_type=FieldType.FAX,
                template="팩스 {field}",
                priority=0.6,
                search_keywords=["팩스", "fax"]
            ),
        ])

        self.register(FieldType.EMAIL, [
            ChunkTemplate(
                field_type=FieldType.EMAIL,
                template="이메일 {field}",
                priority=0.7,
                search_keywords=["이메일", "email", "메일"]
            ),
        ])

        self.register(FieldType.MANAGER, [
            ChunkTemplate(
                field_type=FieldType.MANAGER,
                template="담당자 {field}",
                priority=0.75,
                search_keywords=["담당", "담당자", "연락처", "매니저"]
            ),
        ])

        # ========== Use Case Templates ==========
        self.register(FieldType.USE_CASE, [
            ChunkTemplate(
                field_type=FieldType.USE_CASE,
                template="{field}에 적합한 {category}",
                priority=0.9,
                search_keywords=["용도", "사용", "적합", "추천"]
            ),
            ChunkTemplate(
                field_type=FieldType.USE_CASE,
                template="{field} 제품용",
                priority=0.85,
                search_keywords=["용도"]
            ),
        ])

        self.register(FieldType.TARGET_PRODUCT, [
            ChunkTemplate(
                field_type=FieldType.TARGET_PRODUCT,
                template="{field} 담을 수 있는 {category}",
                priority=0.9,
                search_keywords=["담다", "넣다", "포장", "제품"]
            ),
        ])

        # ========== Description Templates ==========
        self.register(FieldType.DESCRIPTION, [
            ChunkTemplate(
                field_type=FieldType.DESCRIPTION,
                template="{field}",
                priority=0.8,
                search_keywords=["설명", "특징", "description"]
            ),
        ])

        self.register(FieldType.KEYWORD, [
            ChunkTemplate(
                field_type=FieldType.KEYWORD,
                template="{field}",
                priority=0.85,
                search_keywords=["키워드", "검색어"]
            ),
        ])

        # ========== Composite Templates (조합) ==========
        self.register(FieldType.SPEC_COMPOSITE, [
            ChunkTemplate(
                field_type=FieldType.SPEC_COMPOSITE,
                template="{field}",  # Custom composition
                priority=0.95,
                search_keywords=["스펙", "사양", "규격"]
            ),
        ])

        self.register(FieldType.BUSINESS_COMPOSITE, [
            ChunkTemplate(
                field_type=FieldType.BUSINESS_COMPOSITE,
                template="{field}",  # Custom composition
                priority=0.9,
                search_keywords=["구매", "주문", "가격"]
            ),
        ])

    def register(self, field_type: FieldType, templates: List[ChunkTemplate]):
        """템플릿 등록 (확장 가능)"""
        self.templates[field_type] = templates

    def get_templates(self, field_type: FieldType) -> List[ChunkTemplate]:
        """필드 타입에 해당하는 템플릿 리스트 반환"""
        return self.templates.get(field_type, [])

    def add_custom_template(
        self,
        field_type: FieldType,
        template: str,
        priority: float,
        search_keywords: List[str]
    ):
        """커스텀 템플릿 추가 (동적 확장)"""
        custom_template = ChunkTemplate(
            field_type=field_type,
            template=template,
            priority=priority,
            search_keywords=search_keywords
        )

        if field_type not in self.templates:
            self.templates[field_type] = []

        self.templates[field_type].append(custom_template)


# ========== Field Extractors (필드 추출기) ==========

class FieldExtractor:
    """제품 데이터에서 필드 추출"""

    @staticmethod
    def extract_fields(product_data: Dict) -> Dict[FieldType, Any]:
        """
        제품 데이터에서 모든 필드 추출

        Returns:
            {FieldType: value} 딕셔너리
        """
        fields = {}

        # Product Identity
        if "product_name" in product_data:
            fields[FieldType.PRODUCT_NAME] = product_data["product_name"]
        elif "description" in product_data:
            fields[FieldType.PRODUCT_NAME] = product_data["description"]

        if "product_code" in product_data:
            fields[FieldType.PRODUCT_CODE] = product_data["product_code"]

        # Specifications
        if "capacity" in product_data:
            fields[FieldType.CAPACITY] = product_data["capacity"]

        if "size" in product_data:
            fields[FieldType.SIZE] = product_data["size"]

        if "neck" in product_data:
            fields[FieldType.NECK] = product_data["neck"]

        if "diameter" in product_data:
            fields[FieldType.DIAMETER] = product_data["diameter"]

        if "dimensions" in product_data:
            fields[FieldType.DIMENSIONS] = product_data["dimensions"]

        # Materials
        if "material" in product_data:
            fields[FieldType.MATERIAL] = product_data["material"]

        if "origin" in product_data:
            fields[FieldType.ORIGIN] = product_data["origin"]

        if "manufacturer" in product_data:
            fields[FieldType.MANUFACTURER] = product_data["manufacturer"]
        elif "vendor" in product_data:
            fields[FieldType.MANUFACTURER] = product_data["vendor"]

        # Business
        if "moq" in product_data:
            fields[FieldType.MOQ] = product_data["moq"]

        if "price" in product_data:
            fields[FieldType.PRICE] = product_data["price"]

        if "supply_price" in product_data:
            fields[FieldType.SUPPLY_PRICE] = product_data["supply_price"]

        if "selling_price" in product_data:
            fields[FieldType.SELLING_PRICE] = product_data["selling_price"]

        if "package" in product_data:
            fields[FieldType.PACKAGE] = product_data["package"]

        # Contact
        if "phone" in product_data:
            fields[FieldType.PHONE] = product_data["phone"]

        if "fax" in product_data:
            fields[FieldType.FAX] = product_data["fax"]

        if "email" in product_data:
            fields[FieldType.EMAIL] = product_data["email"]

        if "manager" in product_data:
            fields[FieldType.MANAGER] = product_data["manager"]

        # Use Cases
        if "use_case" in product_data:
            fields[FieldType.USE_CASE] = product_data["use_case"]

        if "target_product" in product_data:
            fields[FieldType.TARGET_PRODUCT] = product_data["target_product"]

        # Descriptions
        if "description" in product_data and "product_name" in product_data:
            # description이 별도로 있는 경우
            fields[FieldType.DESCRIPTION] = product_data["description"]

        if "keywords" in product_data:
            fields[FieldType.KEYWORD] = product_data["keywords"]

        # Nested enriched_info 처리
        if "enriched_info" in product_data:
            enriched = product_data["enriched_info"]

            if "detailed_description" in enriched:
                fields[FieldType.DESCRIPTION] = enriched["detailed_description"]

            if "keywords" in enriched:
                fields[FieldType.KEYWORD] = enriched["keywords"]

            if "use_cases" in enriched:
                fields[FieldType.USE_CASE] = enriched["use_cases"]

            # Capacity from capacity_info
            if "capacity_info" in enriched:
                cap_info = enriched["capacity_info"]
                if "capacity" in cap_info:
                    fields[FieldType.CAPACITY] = cap_info["capacity"]
                if "suitable_products" in cap_info:
                    fields[FieldType.TARGET_PRODUCT] = cap_info["suitable_products"]

            # Material from material_benefits
            if "material_benefits" in enriched:
                mat_info = enriched["material_benefits"]
                if "material" in mat_info:
                    fields[FieldType.MATERIAL] = mat_info["material"]

            # Dimensions from specifications_explained
            if "specifications_explained" in enriched:
                spec_info = enriched["specifications_explained"]
                if "dimensions" in spec_info:
                    fields[FieldType.DIMENSIONS] = spec_info["dimensions"]
                if "diameter" in spec_info:
                    fields[FieldType.DIAMETER] = spec_info["diameter"]

        return fields

    @staticmethod
    def create_composite_fields(fields: Dict[FieldType, Any]) -> Dict[FieldType, str]:
        """
        조합 필드 생성 (검색 최적화)

        예: Spec Composite = "Neck Ø20, 사이즈 Ø23.8 × 51.5mm"
        """
        composites = {}

        # Spec Composite (스펙 조합)
        spec_parts = []
        if FieldType.NECK in fields:
            spec_parts.append(f"Neck {fields[FieldType.NECK]}")
        if FieldType.SIZE in fields:
            spec_parts.append(f"사이즈 {fields[FieldType.SIZE]}")
        if FieldType.DIAMETER in fields:
            spec_parts.append(f"직경 {fields[FieldType.DIAMETER]}")
        if FieldType.CAPACITY in fields:
            spec_parts.append(f"{fields[FieldType.CAPACITY]} 용량")

        if spec_parts:
            composites[FieldType.SPEC_COMPOSITE] = ", ".join(spec_parts)

        # Business Composite (비즈니스 조합)
        business_parts = []
        if FieldType.MOQ in fields:
            business_parts.append(f"MOQ {fields[FieldType.MOQ]}개")
        if FieldType.PRICE in fields:
            business_parts.append(f"가격 {fields[FieldType.PRICE]}원")
        if FieldType.SUPPLY_PRICE in fields:
            business_parts.append(f"공급가 {fields[FieldType.SUPPLY_PRICE]}원")
        if FieldType.MATERIAL in fields:
            business_parts.append(f"{fields[FieldType.MATERIAL]} 재질")

        if business_parts:
            composites[FieldType.BUSINESS_COMPOSITE] = ", ".join(business_parts)

        return composites


if __name__ == "__main__":
    # Test with real data
    test_product = {
        "product_name": "GY-20-뾰족캡B",
        "product_code": "GY-20",
        "capacity": "",  # Empty
        "size": "Ø23.8 × 51.5",
        "neck": "Ø20",
        "moq": "5,000",
        "material": "PP",
        "origin": "한국",
        "manufacturer": "금양실업",
        "phone": "032-671-7630",
        "fax": "032-671-7631",
        "manager": "김양원 실장 010-9341-1805",
        "email": "toritoya@naver.com"
    }

    # Extract fields
    extractor = FieldExtractor()
    fields = extractor.extract_fields(test_product)
    composites = extractor.create_composite_fields(fields)
    fields.update(composites)

    # Generate chunks
    registry = ChunkTemplateRegistry()

    print("=== Extracted Fields ===")
    for field_type, value in fields.items():
        print(f"{field_type.value}: {value}")

    print("\n=== Generated Chunks ===")
    for field_type, value in fields.items():
        templates = registry.get_templates(field_type)
        if templates:
            # Use first template
            template = templates[0]
            chunk_text = template.generate(value, product_category="캡")
            print(f"\n[{field_type.value.upper()}]")
            print(f"  Text: {chunk_text}")
            print(f"  Priority: {template.priority}")
            print(f"  Keywords: {', '.join(template.search_keywords[:5])}")
