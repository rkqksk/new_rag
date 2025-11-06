"""
청크 생성 모듈
Chunk Generator

목적: 제품 데이터를 계층적 청크로 분할하여 임베딩 준비
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from src.core.product_classifier import (
    ProductCategory,
    ProductSubCategory,
    ProductClassifier,
)


class ChunkType(Enum):
    """청크 타입"""
    PRIMARY = "primary"
    DESCRIPTION = "description"
    USE_CASE = "use_case"
    MATERIAL = "material"
    CAPACITY = "capacity"
    DIMENSION = "dimension"
    KEYWORD = "keyword"
    RECOMMENDATION = "recommendation"
    SPECIFICATION = "specification"
    PRICING = "pricing"
    COMPATIBILITY = "compatibility"


@dataclass
class Chunk:
    """청크 데이터 클래스"""
    chunk_id: str
    chunk_type: ChunkType
    text: str
    metadata: Dict
    priority: float = 1.0  # Search priority (0.0 ~ 1.0)

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "chunk_id": self.chunk_id,
            "chunk_type": self.chunk_type.value,
            "text": self.text,
            "metadata": self.metadata,
            "priority": self.priority,
        }


class ChunkGenerator:
    """청크 생성기"""

    def __init__(self):
        """초기화"""
        self.classifier = ProductClassifier()

    def generate_chunks(self, product: Dict) -> List[Chunk]:
        """
        제품 데이터로부터 청크 생성

        Args:
            product: 제품 데이터

        Returns:
            List[Chunk]: 생성된 청크 리스트
        """
        # 1. 제품 분류
        classification = self.classifier.classify(product)

        # 2. 카테고리별 청크 생성 전략
        if classification.category in [ProductCategory.BOTTLE, ProductCategory.JAR]:
            return self._generate_bottle_jar_chunks(product, classification)
        elif classification.category in [ProductCategory.CAP, ProductCategory.PUMP]:
            return self._generate_cap_pump_chunks(product, classification)
        else:
            # Unknown category - create minimal chunk
            return self._generate_fallback_chunks(product)

    def _generate_bottle_jar_chunks(
        self,
        product: Dict,
        classification
    ) -> List[Chunk]:
        """
        Bottle/Jar 제품 청크 생성 (8가지 타입)
        """
        chunks = []
        product_id = product.get("product_id", "unknown")
        product_name = product.get("product_name", "")
        enriched = product.get("enriched_info", {})

        # Base metadata (모든 청크에 공통)
        base_metadata = self._extract_base_metadata(product, classification)

        # 1. Primary Chunk
        primary_text = self._build_primary_text_bottle(product, enriched)
        if primary_text:
            chunks.append(Chunk(
                chunk_id=f"{product_id}_primary",
                chunk_type=ChunkType.PRIMARY,
                text=primary_text,
                metadata={**base_metadata, "chunk_type": "primary"},
                priority=1.0
            ))

        # 2. Description Chunk
        description = enriched.get("detailed_description", "")
        if description:
            chunks.append(Chunk(
                chunk_id=f"{product_id}_description",
                chunk_type=ChunkType.DESCRIPTION,
                text=description,
                metadata={**base_metadata, "chunk_type": "description"},
                priority=0.9
            ))

        # 3. Use Case Chunk
        use_case_text = self._build_use_case_text(enriched)
        if use_case_text:
            chunks.append(Chunk(
                chunk_id=f"{product_id}_use_case",
                chunk_type=ChunkType.USE_CASE,
                text=use_case_text,
                metadata={**base_metadata, "chunk_type": "use_case"},
                priority=0.9
            ))

        # 4. Material Chunk
        material_text = self._build_material_text(enriched)
        if material_text:
            chunks.append(Chunk(
                chunk_id=f"{product_id}_material",
                chunk_type=ChunkType.MATERIAL,
                text=material_text,
                metadata={**base_metadata, "chunk_type": "material"},
                priority=0.8
            ))

        # 5. Capacity Chunk
        capacity_text = self._build_capacity_text(enriched)
        if capacity_text:
            chunks.append(Chunk(
                chunk_id=f"{product_id}_capacity",
                chunk_type=ChunkType.CAPACITY,
                text=capacity_text,
                metadata={**base_metadata, "chunk_type": "capacity"},
                priority=0.8
            ))

        # 6. Dimension Chunk
        dimension_text = self._build_dimension_text(enriched)
        if dimension_text:
            chunks.append(Chunk(
                chunk_id=f"{product_id}_dimension",
                chunk_type=ChunkType.DIMENSION,
                text=dimension_text,
                metadata={**base_metadata, "chunk_type": "dimension"},
                priority=0.7
            ))

        # 7. Keyword Chunk
        keyword_text = self._build_keyword_text(enriched)
        if keyword_text:
            chunks.append(Chunk(
                chunk_id=f"{product_id}_keyword",
                chunk_type=ChunkType.KEYWORD,
                text=keyword_text,
                metadata={**base_metadata, "chunk_type": "keyword"},
                priority=0.85
            ))

        # 8. Recommendation Chunk
        recommendation_text = self._build_recommendation_text(enriched)
        if recommendation_text:
            chunks.append(Chunk(
                chunk_id=f"{product_id}_recommendation",
                chunk_type=ChunkType.RECOMMENDATION,
                text=recommendation_text,
                metadata={**base_metadata, "chunk_type": "recommendation"},
                priority=0.75
            ))

        return chunks

    def _generate_cap_pump_chunks(
        self,
        product: Dict,
        classification
    ) -> List[Chunk]:
        """
        Cap/Pump 제품 청크 생성 (4가지 타입)
        """
        chunks = []
        product_code = product.get("product_code", "unknown")

        # Base metadata
        base_metadata = self._extract_base_metadata(product, classification)

        # 1. Primary Chunk
        primary_text = self._build_primary_text_cap_pump(product)
        if primary_text:
            chunks.append(Chunk(
                chunk_id=f"{product_code}_primary",
                chunk_type=ChunkType.PRIMARY,
                text=primary_text,
                metadata={**base_metadata, "chunk_type": "primary"},
                priority=1.0
            ))

        # 2. Specification Chunk
        spec_text = self._build_specification_text(product)
        if spec_text:
            chunks.append(Chunk(
                chunk_id=f"{product_code}_specification",
                chunk_type=ChunkType.SPECIFICATION,
                text=spec_text,
                metadata={**base_metadata, "chunk_type": "specification"},
                priority=0.9
            ))

        # 3. Pricing Chunk
        pricing_text = self._build_pricing_text(product)
        if pricing_text:
            chunks.append(Chunk(
                chunk_id=f"{product_code}_pricing",
                chunk_type=ChunkType.PRICING,
                text=pricing_text,
                metadata={**base_metadata, "chunk_type": "pricing"},
                priority=0.7
            ))

        # 4. Compatibility Chunk (추론 기반)
        compatibility_text = self._build_compatibility_text(product)
        if compatibility_text:
            chunks.append(Chunk(
                chunk_id=f"{product_code}_compatibility",
                chunk_type=ChunkType.COMPATIBILITY,
                text=compatibility_text,
                metadata={**base_metadata, "chunk_type": "compatibility"},
                priority=0.8
            ))

        return chunks

    def _generate_fallback_chunks(self, product: Dict) -> List[Chunk]:
        """Fallback: 최소한의 청크 생성"""
        product_id = product.get("product_id", product.get("product_code", "unknown"))
        product_name = product.get("product_name", product.get("description", ""))

        return [Chunk(
            chunk_id=f"{product_id}_primary",
            chunk_type=ChunkType.PRIMARY,
            text=product_name,
            metadata={"product_id": product_id, "category": "unknown"},
            priority=0.5
        )]

    # ========== Chunk Text Builders (Bottle/Jar) ==========

    def _build_primary_text_bottle(self, product: Dict, enriched: Dict) -> str:
        """Primary 청크 텍스트 생성 (Bottle/Jar)"""
        name = product.get("product_name", "")
        capacity_info = enriched.get("capacity_info", {})
        capacity = capacity_info.get("capacity", "")
        material = enriched.get("material_benefits", {}).get("material", "")
        spec = enriched.get("specifications_explained", {})
        diameter = spec.get("diameter", "")

        parts = [name]
        if capacity:
            parts.append(f"({capacity})")
        if material:
            parts.append(f"{material} 재질")
        if diameter:
            parts.append(f"{diameter}")

        return " ".join(parts)

    def _build_use_case_text(self, enriched: Dict) -> str:
        """Use Case 청크 텍스트 생성"""
        use_cases = enriched.get("use_cases", [])
        capacity_info = enriched.get("capacity_info", {})
        suitable_products = capacity_info.get("suitable_products", [])

        parts = []
        if use_cases:
            parts.append(", ".join(use_cases) + "에 적합")
        if suitable_products:
            parts.append(", ".join(suitable_products) + " 제품에 사용 가능")

        return ". ".join(parts) if parts else ""

    def _build_material_text(self, enriched: Dict) -> str:
        """Material 청크 텍스트 생성"""
        material_info = enriched.get("material_benefits", {})
        material = material_info.get("material", "")
        advantages = material_info.get("advantages", [])

        if not material:
            return ""

        parts = [f"{material} 재질"]
        if advantages:
            parts.append(": " + ", ".join(advantages))

        return "".join(parts)

    def _build_capacity_text(self, enriched: Dict) -> str:
        """Capacity 청크 텍스트 생성"""
        capacity_info = enriched.get("capacity_info", {})
        capacity = capacity_info.get("capacity", "")
        usage_duration = capacity_info.get("usage_duration", "")
        positioning = capacity_info.get("positioning", "")
        suitable = capacity_info.get("suitable_products", [])

        if not capacity:
            return ""

        parts = [f"{capacity} 용량"]
        if positioning:
            parts.append(f"({positioning} 사이즈)")
        if usage_duration:
            parts.append(f": {usage_duration} 사용량")
        if suitable:
            parts.append(", " + "/".join(suitable) + " 제품에 적합")

        return "".join(parts)

    def _build_dimension_text(self, enriched: Dict) -> str:
        """Dimension 청크 텍스트 생성"""
        spec = enriched.get("specifications_explained", {})
        dimensions = spec.get("dimensions", "")
        diameter = spec.get("diameter", "")
        meaning = spec.get("meaning", "")

        if not dimensions:
            return ""

        parts = [f"크기 {dimensions}"]
        if diameter:
            parts.append(f", 직경 {diameter}")
        if meaning:
            parts.append(f": {meaning}")

        return "".join(parts)

    def _build_keyword_text(self, enriched: Dict) -> str:
        """Keyword 청크 텍스트 생성"""
        keywords = enriched.get("keywords", [])
        return ", ".join(keywords) if keywords else ""

    def _build_recommendation_text(self, enriched: Dict) -> str:
        """Recommendation 청크 텍스트 생성"""
        recommendations = enriched.get("recommendations", {})
        when_to_use = recommendations.get("when_to_use", "")
        when_not = recommendations.get("when_not_to_use", "")
        alternatives_small = recommendations.get("alternatives_if_too_small", "")
        alternatives_large = recommendations.get("alternatives_if_too_large", "")

        parts = []
        if when_to_use:
            parts.append(f"추천: {when_to_use}")
        if when_not:
            parts.append(f"비추천: {when_not}")
        if alternatives_small:
            parts.append(f"더 큰 용기: {alternatives_small}")
        if alternatives_large:
            parts.append(f"더 작은 용기: {alternatives_large}")

        return ". ".join(parts) if parts else ""

    # ========== Chunk Text Builders (Cap/Pump) ==========

    def _build_primary_text_cap_pump(self, product: Dict) -> str:
        """Primary 청크 텍스트 생성 (Cap/Pump)"""
        description = product.get("description", "")
        spec = product.get("spec", "")
        detail = product.get("detail", "")

        parts = [description] if description else []
        if spec:
            parts.append(f"({spec}")
        if detail:
            parts.append(f", {detail})")
        elif spec:
            parts.append(")")

        return " ".join(parts)

    def _build_specification_text(self, product: Dict) -> str:
        """Specification 청크 텍스트 생성"""
        spec = product.get("spec", "")
        detail = product.get("detail", "")
        note = product.get("note", "")

        parts = []
        if spec:
            parts.append(spec)
        if detail:
            parts.append(detail)
        if note:
            parts.append(f"({note})")

        return ", ".join(parts) if parts else ""

    def _build_pricing_text(self, product: Dict) -> str:
        """Pricing 청크 텍스트 생성"""
        vendor = product.get("vendor", "")
        package = product.get("package", "")
        supply_price = product.get("supply_price")
        selling_price = product.get("selling_price")

        parts = []
        if vendor:
            parts.append(f"{vendor} 제조")
        if package:
            parts.append(f"{package} 패키지")
        if supply_price is not None:
            parts.append(f"공급가 {supply_price}원")
        if selling_price is not None:
            parts.append(f"판매가 {selling_price}원")

        return ", ".join(parts) if parts else ""

    def _build_compatibility_text(self, product: Dict) -> str:
        """Compatibility 청크 텍스트 생성 (추론 기반)"""
        detail = product.get("detail", "")

        # Extract diameter (e.g., "내경 Ø24" -> 24)
        diameter_match = re.search(r"Ø(\d+)", detail)
        if not diameter_match:
            return ""

        diameter = int(diameter_match.group(1))

        # Infer compatible bottle sizes
        if diameter <= 24:
            compatible_sizes = "30-80ml 소형 용기"
        elif diameter <= 28:
            compatible_sizes = "80-150ml 중소형 용기"
        elif diameter <= 32:
            compatible_sizes = "150-300ml 중대형 용기"
        else:
            compatible_sizes = "300ml 이상 대형 용기"

        spec = product.get("spec", "")
        return f"직경 Ø{diameter} {spec}: {diameter}mm 입구를 가진 용기와 호환 (일반적으로 {compatible_sizes})"

    # ========== Metadata Extraction ==========

    def _extract_base_metadata(self, product: Dict, classification) -> Dict:
        """모든 청크에 공통으로 들어갈 기본 메타데이터 추출"""
        metadata = {
            "product_id": product.get("product_id", product.get("product_code", "unknown")),
            "product_code": product.get("product_code", ""),
            "product_name": product.get("product_name", product.get("description", "")),
            "category": classification.category.value,
            "sub_category": classification.sub_category.value,
            "classification_confidence": classification.confidence,
        }

        # Category-specific metadata
        if classification.category in [ProductCategory.BOTTLE, ProductCategory.JAR]:
            metadata.update(self._extract_bottle_jar_metadata(product))
        elif classification.category in [ProductCategory.CAP, ProductCategory.PUMP]:
            metadata.update(self._extract_cap_pump_metadata(product))

        return metadata

    def _extract_bottle_jar_metadata(self, product: Dict) -> Dict:
        """Bottle/Jar 메타데이터 추출"""
        enriched = product.get("enriched_info", {})
        capacity_info = enriched.get("capacity_info", {})
        material_info = enriched.get("material_benefits", {})
        spec_info = enriched.get("specifications_explained", {})

        # Extract capacity (ml)
        capacity_str = capacity_info.get("capacity", "")
        capacity_ml = self._parse_capacity(capacity_str)

        # Extract diameter (mm)
        diameter_str = spec_info.get("diameter", "")
        diameter_mm = self._parse_diameter(diameter_str)

        # Capacity range
        capacity_range = self._get_capacity_range(capacity_ml)

        # Keywords
        keywords = enriched.get("keywords", [])
        use_cases = capacity_info.get("suitable_products", [])

        return {
            "capacity_ml": capacity_ml,
            "capacity_range": capacity_range,
            "diameter_mm": diameter_mm,
            "material": material_info.get("material", ""),
            "keywords": keywords,
            "use_cases": use_cases,
            "target_customers": enriched.get("target_customers", []),
        }

    def _extract_cap_pump_metadata(self, product: Dict) -> Dict:
        """Cap/Pump 메타데이터 추출"""
        detail = product.get("detail", "")

        # Extract pump diameter
        diameter_match = re.search(r"Ø(\d+)", detail)
        pump_diameter = int(diameter_match.group(1)) if diameter_match else None

        # Extract spec type
        spec = product.get("spec", "")
        pump_type = "regular_pump" if "일반" in spec else "dispenser"

        return {
            "pump_diameter_mm": pump_diameter,
            "pump_type": pump_type,
            "vendor": product.get("vendor", ""),
            "supply_price": product.get("supply_price"),
            "selling_price": product.get("selling_price"),
        }

    def _parse_capacity(self, capacity_str: str) -> Optional[int]:
        """용량 문자열에서 ml 수치 추출"""
        if not capacity_str:
            return None

        # Extract numbers (e.g., "40ml" -> 40, "100ml" -> 100)
        match = re.search(r"(\d+)\s*ml", capacity_str, re.IGNORECASE)
        if match:
            return int(match.group(1))

        # Try just numbers
        match = re.search(r"(\d+)", capacity_str)
        if match:
            return int(match.group(1))

        return None

    def _parse_diameter(self, diameter_str: str) -> Optional[int]:
        """직경 문자열에서 mm 수치 추출"""
        if not diameter_str:
            return None

        # Extract numbers (e.g., "Ø20" -> 20)
        match = re.search(r"Ø(\d+)", diameter_str)
        if match:
            return int(match.group(1))

        match = re.search(r"(\d+)\s*mm", diameter_str, re.IGNORECASE)
        if match:
            return int(match.group(1))

        return None

    def _get_capacity_range(self, capacity_ml: Optional[int]) -> str:
        """용량 범위 분류"""
        if capacity_ml is None:
            return "unknown"

        if capacity_ml < 30:
            return "tiny"
        elif capacity_ml < 100:
            return "small"
        elif capacity_ml < 300:
            return "medium"
        else:
            return "large"


# Batch generation function
def generate_all_chunks(products: List[Dict]) -> List[Chunk]:
    """
    제품 리스트로부터 모든 청크 생성

    Args:
        products: 제품 데이터 리스트

    Returns:
        List[Chunk]: 모든 청크 리스트
    """
    generator = ChunkGenerator()
    all_chunks = []

    for product in products:
        chunks = generator.generate_chunks(product)
        all_chunks.extend(chunks)

    return all_chunks


if __name__ == "__main__":
    # Test
    import json

    test_product_bottle = {
        "product_id": "idx_13",
        "product_code": "BE040-R001",
        "product_name": "40ml 브로우용기",
        "enriched_info": {
            "detailed_description": "40ml PE 브로우 용기는 소형 액상 화장품에 최적화된 경량 용기입니다.",
            "use_cases": ["고농축 에센스", "트래블 사이즈"],
            "material_benefits": {
                "material": "PE",
                "advantages": ["식품등급 안전성", "가벼운 무게"]
            },
            "capacity_info": {
                "capacity": "40ml",
                "usage_duration": "1-2주",
                "suitable_products": ["세럼", "에센스"]
            },
            "specifications_explained": {
                "dimensions": "28x95(mm)",
                "diameter": "Ø20"
            },
            "keywords": ["소형", "휴대용", "트래블"],
            "recommendations": {
                "when_to_use": "고가의 농축 제품"
            }
        }
    }

    test_product_pump = {
        "vendor": "지에프테크",
        "description": "Ø24 펌프 211AVP",
        "product_code": "PO024-CG01",
        "spec": "24파이 일반펌프",
        "detail": "내경 Ø24",
        "package": "800ea",
        "supply_price": 140.0,
        "selling_price": 240.0
    }

    generator = ChunkGenerator()

    print("=== Bottle Chunks ===")
    bottle_chunks = generator.generate_chunks(test_product_bottle)
    for chunk in bottle_chunks:
        print(f"\n{chunk.chunk_type.value.upper()}: {chunk.text[:100]}...")

    print("\n\n=== Pump Chunks ===")
    pump_chunks = generator.generate_chunks(test_product_pump)
    for chunk in pump_chunks:
        print(f"\n{chunk.chunk_type.value.upper()}: {chunk.text[:100]}...")
