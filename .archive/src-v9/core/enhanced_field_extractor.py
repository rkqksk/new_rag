"""
Enhanced Field Extractor
강화된 필드 추출기

목적: Bottle/Jar 및 Cap/Pump 제품 데이터에서 구조화된 필드 추출
전략:
- Bottle/Jar: enriched_info에서 상세 정보 추출
- Cap/Pump: spec/detail/description에서 파싱
"""

import re
from typing import Any, Dict, Optional

from src.core.chunk_templates import FieldType


class EnhancedFieldExtractor:
    """강화된 필드 추출기"""

    @staticmethod
    def extract_fields(product_data: Dict) -> Dict[FieldType, Any]:
        """
        제품 데이터에서 모든 필드 추출 (Enhanced)

        Args:
            product_data: 제품 데이터

        Returns:
            {FieldType: value} 딕셔너리
        """
        fields = {}

        # Determine product type (Bottle/Jar vs Cap/Pump)
        has_enriched_info = "enriched_info" in product_data and product_data["enriched_info"]

        if has_enriched_info:
            # Bottle/Jar products with enriched_info
            fields.update(EnhancedFieldExtractor._extract_from_enriched(product_data))
        else:
            # Cap/Pump products without enriched_info
            fields.update(EnhancedFieldExtractor._extract_from_cap_pump(product_data))

        # Common fields (all products)
        fields.update(EnhancedFieldExtractor._extract_common_fields(product_data))

        return fields

    @staticmethod
    def _extract_common_fields(product_data: Dict) -> Dict[FieldType, Any]:
        """공통 필드 추출"""
        fields = {}

        # Product Identity
        if "product_name" in product_data:
            fields[FieldType.PRODUCT_NAME] = product_data["product_name"]
        elif "description" in product_data:
            fields[FieldType.PRODUCT_NAME] = product_data["description"]

        if "product_code" in product_data:
            fields[FieldType.PRODUCT_CODE] = product_data["product_code"]

        # Manufacturer
        if "manufacturer" in product_data:
            fields[FieldType.MANUFACTURER] = product_data["manufacturer"]
        elif "vendor" in product_data:
            fields[FieldType.MANUFACTURER] = product_data["vendor"]

        return fields

    @staticmethod
    def _extract_from_enriched(product_data: Dict) -> Dict[FieldType, Any]:
        """Bottle/Jar: enriched_info에서 필드 추출"""
        fields = {}
        enriched = product_data.get("enriched_info", {})

        # Material
        if "material_benefits" in enriched:
            material_info = enriched["material_benefits"]
            if isinstance(material_info, dict) and "material" in material_info:
                material = material_info["material"]
                # Extract short form (e.g., "PE (폴리에틸렌)" → "PE")
                match = re.match(r"([A-Z]+)", material)
                if match:
                    fields[FieldType.MATERIAL] = match.group(1)

        # Capacity
        if "capacity_info" in enriched:
            capacity_info = enriched["capacity_info"]
            if isinstance(capacity_info, dict) and "capacity" in capacity_info:
                fields[FieldType.CAPACITY] = capacity_info["capacity"]

        # Neck/Diameter from specifications_explained
        if "specifications_explained" in enriched:
            spec_info = enriched["specifications_explained"]
            if isinstance(spec_info, dict):
                if "diameter" in spec_info:
                    fields[FieldType.NECK] = spec_info["diameter"]
                if "dimensions" in spec_info:
                    fields[FieldType.SIZE] = spec_info["dimensions"]

        # Use Cases
        if "use_cases" in enriched:
            use_cases = enriched["use_cases"]
            if isinstance(use_cases, list) and use_cases:
                fields[FieldType.USE_CASE] = ", ".join(use_cases[:3])  # Top 3

        # Target Customers (skip - no TARGET field type)
        # if "target_customers" in enriched:
        #     customers = enriched["target_customers"]
        #     if isinstance(customers, list) and customers:
        #         fields[FieldType.TARGET] = ", ".join(customers[:3])

        # Keywords
        if "keywords" in enriched:
            keywords = enriched["keywords"]
            if isinstance(keywords, list) and keywords:
                fields[FieldType.KEYWORD] = ", ".join(keywords)

        return fields

    @staticmethod
    def _extract_from_cap_pump(product_data: Dict) -> Dict[FieldType, Any]:
        """Cap/Pump: spec/detail/description에서 필드 파싱"""
        fields = {}

        # Neck extraction from spec, detail, description
        neck_value = EnhancedFieldExtractor._parse_neck(product_data)
        if neck_value:
            fields[FieldType.NECK] = neck_value

        # MOQ from package
        moq_value = EnhancedFieldExtractor._parse_moq(product_data)
        if moq_value:
            fields[FieldType.MOQ] = moq_value

        # Material from spec/description
        material_value = EnhancedFieldExtractor._parse_material(product_data)
        if material_value:
            fields[FieldType.MATERIAL] = material_value

        # Price
        if "supply_price" in product_data:
            fields[FieldType.PRICE] = product_data["supply_price"]
        elif "selling_price" in product_data:
            fields[FieldType.PRICE] = product_data["selling_price"]

        # Note (additional info)
        if "note" in product_data and product_data["note"]:
            fields[FieldType.DESCRIPTION] = product_data["note"]

        return fields

    @staticmethod
    def _parse_neck(product_data: Dict) -> Optional[str]:
        """Neck 직경 파싱 (파이, Ø)"""
        # Patterns to match
        patterns = [
            r"(\d+)\s*파이",  # "24파이"
            r"Ø\s*(\d+)",  # "Ø24"
            r"내경\s*Ø\s*(\d+)",  # "내경 Ø24"
            r"(\d+)Ø",  # "24Ø"
        ]

        # Search in spec, detail, description, note
        search_fields = [
            product_data.get("spec", ""),
            product_data.get("detail", ""),
            product_data.get("description", ""),
            product_data.get("note", ""),
        ]

        for field in search_fields:
            if not field:
                continue

            for pattern in patterns:
                match = re.search(pattern, str(field))
                if match:
                    neck_num = match.group(1)
                    return f"Ø{neck_num}"

        return None

    @staticmethod
    def _parse_moq(product_data: Dict) -> Optional[int]:
        """MOQ 파싱 (package 필드)"""
        if "package" not in product_data:
            return None

        package = product_data["package"]
        if not package:
            return None

        # Extract number from "800ea", "1,000ea", etc.
        match = re.search(r"([\d,]+)\s*(?:ea|개|pcs)?", str(package), re.IGNORECASE)
        if match:
            moq_str = match.group(1).replace(",", "")
            try:
                return int(moq_str)
            except ValueError:
                pass

        return None

    @staticmethod
    def _parse_material(product_data: Dict) -> Optional[str]:
        """재질 파싱 (PP, PE, PET, PETG 등)"""
        # Common materials
        materials = ["PP", "PE", "PET", "PETG", "PS", "ABS", "PC"]

        # Search in spec, detail, description
        search_fields = [
            product_data.get("spec", ""),
            product_data.get("detail", ""),
            product_data.get("description", ""),
            product_data.get("note", ""),
        ]

        for field in search_fields:
            if not field:
                continue

            field_upper = str(field).upper()
            for material in materials:
                if material in field_upper:
                    return material

        return None

    @staticmethod
    def create_composite_fields(fields: Dict[FieldType, Any]) -> Dict[FieldType, str]:
        """복합 필드 생성 (여러 필드 조합)"""
        composite = {}

        # SPEC_COMPOSITE: capacity + neck + material
        spec_parts = []
        if FieldType.CAPACITY in fields:
            spec_parts.append(f"{fields[FieldType.CAPACITY]}")
        if FieldType.NECK in fields:
            spec_parts.append(f"{fields[FieldType.NECK]}")
        if FieldType.MATERIAL in fields:
            spec_parts.append(f"{fields[FieldType.MATERIAL]} 재질")

        if spec_parts:
            composite[FieldType.SPEC_COMPOSITE] = " ".join(spec_parts)

        # BUSINESS_COMPOSITE: MOQ + price
        business_parts = []
        if FieldType.MOQ in fields:
            moq = fields[FieldType.MOQ]
            if isinstance(moq, int):
                business_parts.append(f"최소주문수량 {moq:,}개")
            else:
                business_parts.append(f"최소주문수량 {moq}")
        if FieldType.PRICE in fields:
            price = fields[FieldType.PRICE]
            if isinstance(price, (int, float)):
                business_parts.append(f"가격 {price:,.0f}원")
            else:
                business_parts.append(f"가격 {price}")

        if business_parts:
            composite[FieldType.BUSINESS_COMPOSITE] = ", ".join(business_parts)

        return composite


if __name__ == "__main__":
    # Test with sample data
    print("=" * 80)
    print("ENHANCED FIELD EXTRACTOR TEST")
    print("=" * 80)

    # Test 1: Cap/Pump product
    cap_product = {
        "vendor": "지에프테크",
        "description": "Ø24 펌프 211AVP",
        "product_code": "PO024-CG01",
        "spec": "24파이 일반펌프",
        "detail": "내경 Ø24",
        "package": "800ea",
        "supply_price": 140.0,
        "note": "GF-211A (24Ø)",
    }

    print("\n[Test 1] Cap/Pump Product")
    print(f"Product: {cap_product['description']}")

    extractor = EnhancedFieldExtractor()
    fields = extractor.extract_fields(cap_product)

    print(f"\nExtracted fields ({len(fields)}):")
    for field_type, value in fields.items():
        print(f"  {field_type.value}: {value}")

    # Test composite
    composite = extractor.create_composite_fields(fields)
    print(f"\nComposite fields ({len(composite)}):")
    for field_type, value in composite.items():
        print(f"  {field_type.value}: {value}")

    # Test 2: Bottle/Jar product
    bottle_product = {
        "product_id": "idx_13",
        "product_code": "BE040-R001",
        "product_name": "40ml 브로우용기",
        "enriched_info": {
            "material_benefits": {
                "material": "PE (폴리에틸렌)",
                "advantages": ["식품등급 안전성", "가벼운 무게"],
            },
            "capacity_info": {"capacity": "40ml", "usage_duration": "1-2주"},
            "specifications_explained": {"dimensions": "28x95(mm)", "diameter": "Ø20"},
            "use_cases": ["에센스", "세럼", "트래블"],
            "keywords": ["소형", "휴대용", "트래블"],
        },
    }

    print("\n" + "─" * 80)
    print("[Test 2] Bottle/Jar Product")
    print(f"Product: {bottle_product['product_name']}")

    fields2 = extractor.extract_fields(bottle_product)

    print(f"\nExtracted fields ({len(fields2)}):")
    for field_type, value in fields2.items():
        print(f"  {field_type.value}: {value}")

    composite2 = extractor.create_composite_fields(fields2)
    print(f"\nComposite fields ({len(composite2)}):")
    for field_type, value in composite2.items():
        print(f"  {field_type.value}: {value}")

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETED")
    print("=" * 80)
