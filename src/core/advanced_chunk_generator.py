"""
통합 청크 생성 파이프라인
Advanced Chunk Generator Pipeline

목적: Classifier + Field Extractor + Category Templates 통합
전략: Atomic Field-Level Chunking with Category-Specific Templates
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field as dc_field

from src.core.product_classifier import ProductClassifier, ProductCategory as ProdCat, ClassificationResult
from src.core.chunk_templates import FieldType, FieldExtractor, ChunkTemplate
from src.core.category_templates import CategoryTemplateRegistry, ProductCategory


@dataclass
class AtomicChunk:
    """원자 단위 청크 (Atomic Chunk)"""
    chunk_id: str
    field_type: FieldType
    text: str
    priority: float
    metadata: Dict
    search_keywords: List[str] = dc_field(default_factory=list)

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "chunk_id": self.chunk_id,
            "field_type": self.field_type.value,
            "text": self.text,
            "priority": self.priority,
            "metadata": self.metadata,
            "search_keywords": self.search_keywords,
        }


class AdvancedChunkGenerator:
    """통합 청크 생성기 (Atomic Field-Level)"""

    def __init__(self):
        """초기화"""
        self.classifier = ProductClassifier()
        self.field_extractor = FieldExtractor()
        self.template_registry = CategoryTemplateRegistry()

    def generate_chunks(self, product: Dict) -> List[AtomicChunk]:
        """
        제품 데이터로부터 Atomic Chunks 생성

        Steps:
        1. 제품 분류 (Bottle/Jar/Cap/Pump)
        2. 필드 추출 (모든 필드 + 조합 필드)
        3. 카테고리별 템플릿 적용
        4. Atomic Chunks 생성

        Args:
            product: 제품 데이터

        Returns:
            List[AtomicChunk]: 원자 단위 청크 리스트
        """
        # Step 1: 제품 분류
        classification = self.classifier.classify(product)
        category = self._map_category(classification.category)

        # Step 2: 필드 추출
        fields = self.field_extractor.extract_fields(product)
        composite_fields = self.field_extractor.create_composite_fields(fields)
        fields.update(composite_fields)

        # Step 3: Base metadata 생성
        base_metadata = self._create_base_metadata(product, classification)

        # Step 4: 각 필드를 Atomic Chunk로 변환
        chunks = []
        product_id = product.get("product_id", product.get("product_code", "unknown"))

        for field_type, value in fields.items():
            # Skip empty values
            if not value or (isinstance(value, str) and value.strip() == ""):
                continue

            # Get category-specific templates for this field
            templates = self.template_registry.get_templates(field_type, category)

            if not templates:
                # No category-specific template - use generic template
                chunks.append(self._create_generic_chunk(
                    product_id, field_type, value, base_metadata
                ))
                continue

            # Generate chunks from all templates (multiple variations)
            for idx, template in enumerate(templates):
                chunk_text = template.generate(value)

                chunk_id = f"{product_id}_{field_type.value}"
                if idx > 0:
                    chunk_id += f"_v{idx+1}"  # Version suffix for variants

                chunk = AtomicChunk(
                    chunk_id=chunk_id,
                    field_type=field_type,
                    text=chunk_text,
                    priority=template.priority,
                    metadata={
                        **base_metadata,
                        "field_type": field_type.value,
                        "template_variant": idx + 1,
                    },
                    search_keywords=template.search_keywords
                )
                chunks.append(chunk)

        return chunks

    def _map_category(self, prod_cat: ProdCat) -> ProductCategory:
        """ProductClassifier의 카테고리 → CategoryTemplateRegistry 카테고리 매핑"""
        mapping = {
            ProdCat.BOTTLE: ProductCategory.BOTTLE,
            ProdCat.JAR: ProductCategory.JAR,
            ProdCat.CAP: ProductCategory.CAP,
            ProdCat.PUMP: ProductCategory.PUMP,
            ProdCat.UNKNOWN: ProductCategory.UNKNOWN,
        }
        return mapping.get(prod_cat, ProductCategory.UNKNOWN)

    def _create_base_metadata(
        self,
        product: Dict,
        classification: ClassificationResult
    ) -> Dict:
        """공통 메타데이터 생성"""
        return {
            "product_id": product.get("product_id", product.get("product_code", "unknown")),
            "product_code": product.get("product_code", ""),
            "product_name": product.get("product_name", product.get("description", "")),
            "category": classification.category.value,
            "sub_category": classification.sub_category.value,
            "classification_confidence": classification.confidence,
        }

    def _create_generic_chunk(
        self,
        product_id: str,
        field_type: FieldType,
        value: any,
        base_metadata: Dict
    ) -> AtomicChunk:
        """Generic chunk 생성 (템플릿 없는 경우)"""
        if isinstance(value, (list, tuple)):
            value = ", ".join(str(v) for v in value)

        return AtomicChunk(
            chunk_id=f"{product_id}_{field_type.value}",
            field_type=field_type,
            text=str(value),
            priority=0.7,
            metadata={
                **base_metadata,
                "field_type": field_type.value,
                "template_variant": 0,  # Generic
            },
            search_keywords=[]
        )


# Batch processing
def generate_all_chunks_atomic(products: List[Dict]) -> List[AtomicChunk]:
    """
    제품 리스트로부터 모든 Atomic Chunks 생성

    Args:
        products: 제품 데이터 리스트

    Returns:
        List[AtomicChunk]: 모든 Atomic Chunks
    """
    generator = AdvancedChunkGenerator()
    all_chunks = []

    for product in products:
        chunks = generator.generate_chunks(product)
        all_chunks.extend(chunks)

    return all_chunks


# Statistics helper
def get_chunk_statistics(chunks: List[AtomicChunk]) -> Dict:
    """청크 통계 정보"""
    total = len(chunks)
    by_category = {}
    by_field_type = {}
    by_priority = {}

    for chunk in chunks:
        # By category
        category = chunk.metadata.get("category", "unknown")
        by_category[category] = by_category.get(category, 0) + 1

        # By field type
        field = chunk.field_type.value
        by_field_type[field] = by_field_type.get(field, 0) + 1

        # By priority
        priority_range = f"{int(chunk.priority * 10) / 10:.1f}"
        by_priority[priority_range] = by_priority.get(priority_range, 0) + 1

    return {
        "total_chunks": total,
        "by_category": by_category,
        "by_field_type": by_field_type,
        "by_priority": by_priority,
    }


if __name__ == "__main__":
    import json

    # Test with various products
    test_products = [
        # Cap
        {
            "product_name": "GY-20-뾰족캡B",
            "product_code": "GY-20",
            "size": "Ø23.8 × 51.5",
            "neck": "Ø20",
            "moq": "5,000",
            "material": "PP",
            "origin": "한국",
            "manufacturer": "금양실업",
            "phone": "032-671-7630",
            "email": "toritoya@naver.com"
        },
        # Bottle
        {
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
                    "suitable_products": ["세럼", "에센스"]
                },
                "specifications_explained": {
                    "dimensions": "28x95(mm)",
                    "diameter": "Ø20"
                },
                "keywords": ["소형", "휴대용", "트래블"]
            }
        },
        # Pump
        {
            "vendor": "지에프테크",
            "description": "Ø24 펌프 211AVP",
            "product_code": "PO024-CG01",
            "spec": "24파이 일반펌프",
            "detail": "내경 Ø24",
            "package": "800ea",
            "supply_price": 140.0,
            "selling_price": 240.0
        }
    ]

    generator = AdvancedChunkGenerator()

    print("="*80)
    print("ADVANCED CHUNK GENERATOR - Atomic Field-Level Chunking")
    print("="*80)

    all_chunks = []

    for idx, product in enumerate(test_products):
        product_name = product.get("product_name", product.get("description", f"Product {idx+1}"))
        print(f"\n{'─'*80}")
        print(f"Product {idx+1}: {product_name}")
        print(f"{'─'*80}")

        chunks = generator.generate_chunks(product)
        all_chunks.extend(chunks)

        print(f"\nGenerated {len(chunks)} atomic chunks:")
        for chunk in chunks:
            print(f"\n  [{chunk.field_type.value.upper()}] (Priority: {chunk.priority})")
            print(f"    ID: {chunk.chunk_id}")
            print(f"    Text: {chunk.text}")
            print(f"    Keywords: {', '.join(chunk.search_keywords[:5])}")

    # Statistics
    print(f"\n{'='*80}")
    print("STATISTICS")
    print(f"{'='*80}")
    stats = get_chunk_statistics(all_chunks)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
