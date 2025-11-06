"""
하이브리드 검색 엔진 (Hybrid Search Engine)
Search Engine with Filter Builder

목적: 파싱된 쿼리 → Qdrant 필터 + 벡터 검색 → 결과 반환
전략: Metadata Filtering + Semantic Search + Re-ranking
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from src.core.query_parser import QueryParser, ParsedQuery, EntityType, ExtractedEntity


@dataclass
class SearchResult:
    """검색 결과"""
    product_id: str
    product_name: str
    score: float
    matched_chunks: List[Dict]
    metadata: Dict


class FilterBuilder:
    """Qdrant 필터 빌더"""

    def __init__(self):
        """초기화"""
        pass

    def build_filters(self, parsed_query: ParsedQuery) -> Dict:
        """
        파싱된 쿼리로부터 Qdrant 필터 생성

        Args:
            parsed_query: 파싱된 쿼리

        Returns:
            Qdrant 필터 딕셔너리
        """
        must_conditions = []
        should_conditions = []

        for entity in parsed_query.entities:
            if entity.entity_type == EntityType.CATEGORY:
                # Category: exact match (must)
                must_conditions.append({
                    "key": "category",
                    "match": {"value": entity.value}
                })

            elif entity.entity_type == EntityType.NECK:
                # Neck: exact match (must)
                neck_value = self._normalize_neck(entity.value)
                must_conditions.append({
                    "key": "neck",
                    "match": {"value": neck_value}
                })

            elif entity.entity_type == EntityType.MATERIAL:
                # Material: exact match (should - not critical)
                should_conditions.append({
                    "key": "material",
                    "match": {"value": entity.value}
                })

            elif entity.entity_type == EntityType.ORIGIN:
                # Origin: exact match (should)
                should_conditions.append({
                    "key": "origin",
                    "match": {"value": entity.value}
                })

            elif entity.entity_type == EntityType.CAPACITY:
                # Capacity: range match (±20%)
                capacity_ml = self._parse_capacity(entity.value)
                if capacity_ml:
                    range_min = int(capacity_ml * 0.8)
                    range_max = int(capacity_ml * 1.2)
                    should_conditions.append({
                        "key": "capacity_ml",
                        "range": {"gte": range_min, "lte": range_max}
                    })

            elif entity.entity_type == EntityType.MOQ:
                # MOQ: less than or equal (must)
                must_conditions.append({
                    "key": "moq",
                    "range": {"lte": entity.value}
                })

            elif entity.entity_type == EntityType.PRICE:
                # Price: range match (±20%)
                range_min = int(entity.value * 0.8)
                range_max = int(entity.value * 1.2)
                should_conditions.append({
                    "key": "price",
                    "range": {"gte": range_min, "lte": range_max}
                })

            elif entity.entity_type == EntityType.USE_CASE:
                # Use case: match any
                should_conditions.append({
                    "key": "use_cases",
                    "match": {"any": [entity.value]}
                })

            elif entity.entity_type == EntityType.DIAMETER:
                # Diameter: range match (±2mm)
                diameter_mm = self._parse_diameter(entity.value)
                if diameter_mm:
                    should_conditions.append({
                        "key": "diameter_mm",
                        "range": {"gte": diameter_mm - 2, "lte": diameter_mm + 2}
                    })

        # Build final filter
        filter_dict = {}
        if must_conditions:
            filter_dict["must"] = must_conditions
        if should_conditions:
            filter_dict["should"] = should_conditions

        return filter_dict if filter_dict else None

    def _normalize_neck(self, neck_str: str) -> str:
        """Neck 값 정규화 (Ø20, 20파이 → Ø20)"""
        match = re.search(r"(\d+)", neck_str)
        if match:
            return f"Ø{match.group(1)}"
        return neck_str

    def _parse_capacity(self, capacity_str: str) -> Optional[int]:
        """용량 문자열 → ml 숫자"""
        match = re.search(r"(\d+)\s*(ml|g)", capacity_str, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def _parse_diameter(self, diameter_str: str) -> Optional[int]:
        """직경 문자열 → mm 숫자"""
        match = re.search(r"(\d+)", diameter_str)
        if match:
            return int(match.group(1))
        return None


class SearchEngine:
    """하이브리드 검색 엔진"""

    def __init__(
        self,
        qdrant_client=None,
        embedding_model=None,
        collection_name: str = "products_atomic"
    ):
        """
        초기화

        Args:
            qdrant_client: QdrantClient 인스턴스
            embedding_model: SentenceTransformer 모델
            collection_name: Qdrant collection 이름
        """
        self.qdrant_client = qdrant_client
        self.embedding_model = embedding_model
        self.collection_name = collection_name

        self.query_parser = QueryParser()
        self.filter_builder = FilterBuilder()

    def search(
        self,
        query: str,
        top_k: int = 10,
        enable_reranking: bool = True
    ) -> List[SearchResult]:
        """
        자연어 쿼리로 제품 검색

        Args:
            query: 자연어 질문 (예: "20파이 캡 5,000개 추천해줘")
            top_k: 반환할 결과 수
            enable_reranking: Re-ranking 활성화 여부

        Returns:
            List[SearchResult]: 검색 결과 리스트
        """
        # Step 1: 쿼리 파싱
        parsed_query = self.query_parser.parse(query)

        # Step 2: 필터 생성
        filters = self.filter_builder.build_filters(parsed_query)

        # Step 3: 검색 쿼리 최적화
        search_query = self._build_search_query(parsed_query)

        # Step 4: Qdrant 검색 (현재는 Mock)
        results = self._search_qdrant(
            search_query=search_query,
            filters=filters,
            top_k=top_k * 2  # Over-fetch for re-ranking
        )

        # Step 5: Re-ranking (옵션)
        if enable_reranking:
            results = self._rerank_results(results, parsed_query)

        # Step 6: 제품별 그룹화 및 중복 제거
        final_results = self._deduplicate_by_product(results, top_k)

        return final_results

    def _build_search_query(self, parsed_query: ParsedQuery) -> str:
        """
        파싱된 쿼리로부터 검색 쿼리 최적화

        예: "20파이 캡 5,000개 추천" → "Ø20 캡 최소주문수량 5000개"
        """
        parts = []

        for entity in parsed_query.entities:
            if entity.entity_type == EntityType.NECK:
                parts.append(f"{entity.value} 호환")
            elif entity.entity_type == EntityType.CATEGORY:
                parts.append(entity.value)
            elif entity.entity_type == EntityType.MOQ:
                parts.append(f"최소주문수량 {entity.value}개")
            elif entity.entity_type == EntityType.MATERIAL:
                parts.append(f"{entity.value} 재질")
            elif entity.entity_type == EntityType.CAPACITY:
                parts.append(f"{entity.value} 용량")
            elif entity.entity_type == EntityType.USE_CASE:
                parts.append(f"{entity.value} 담는")
            elif entity.entity_type == EntityType.ORIGIN:
                parts.append(f"{entity.value}산")
            else:
                parts.append(str(entity.value))

        return " ".join(parts) if parts else parsed_query.original_query

    def _search_qdrant(
        self,
        search_query: str,
        filters: Optional[Dict],
        top_k: int
    ) -> List[Dict]:
        """
        Qdrant 벡터 검색 수행

        현재는 Mock 구현. 실제로는 Qdrant client 사용.
        """
        # Mock implementation
        # 실제 구현:
        # query_vector = self.embedding_model.encode(search_query)
        # results = self.qdrant_client.search(
        #     collection_name=self.collection_name,
        #     query_vector=query_vector,
        #     query_filter=filters,
        #     limit=top_k
        # )

        # Mock results
        mock_results = [
            {
                "id": "GY-20_neck",
                "score": 0.95,
                "payload": {
                    "product_id": "GY-20",
                    "product_name": "GY-20-뾰족캡B",
                    "category": "cap",
                    "neck": "Ø20",
                    "moq": 5000,
                    "material": "PP",
                    "chunk_text": "Neck Ø20 호환 캡",
                    "field_type": "neck"
                }
            },
            {
                "id": "GY-20_moq",
                "score": 0.88,
                "payload": {
                    "product_id": "GY-20",
                    "product_name": "GY-20-뾰족캡B",
                    "category": "cap",
                    "neck": "Ø20",
                    "moq": 5000,
                    "material": "PP",
                    "chunk_text": "최소주문수량 5,000개 (캡)",
                    "field_type": "moq"
                }
            },
            {
                "id": "GY-20_product_name",
                "score": 0.82,
                "payload": {
                    "product_id": "GY-20",
                    "product_name": "GY-20-뾰족캡B",
                    "category": "cap",
                    "neck": "Ø20",
                    "moq": 5000,
                    "material": "PP",
                    "chunk_text": "GY-20-뾰족캡B 캡",
                    "field_type": "product_name"
                }
            },
        ]

        print(f"\n[Qdrant Search]")
        print(f"  Query: {search_query}")
        print(f"  Filters: {filters}")
        print(f"  Results: {len(mock_results)} chunks")

        return mock_results

    def _rerank_results(
        self,
        results: List[Dict],
        parsed_query: ParsedQuery
    ) -> List[Dict]:
        """
        결과 재정렬 (Re-ranking)

        전략:
        1. Semantic score (50%)
        2. Field type priority (30%) - NECK, MOQ > PRODUCT_NAME > others
        3. Entity match count (20%)
        """
        for result in results:
            payload = result["payload"]
            field_type = payload.get("field_type", "")

            # Field type priority
            field_priority_map = {
                "neck": 1.0,
                "moq": 1.0,
                "material": 0.9,
                "capacity": 0.9,
                "product_name": 0.8,
                "use_case": 0.8,
                "description": 0.7,
            }
            field_priority = field_priority_map.get(field_type, 0.6)

            # Entity match count (몇 개의 엔티티가 매칭되는지)
            entity_matches = 0
            for entity in parsed_query.entities:
                entity_value = str(entity.value).lower()
                chunk_text = payload.get("chunk_text", "").lower()
                if entity_value in chunk_text or entity.original_text.lower() in chunk_text:
                    entity_matches += 1

            entity_match_score = min(entity_matches / len(parsed_query.entities), 1.0) if parsed_query.entities else 0

            # Final score
            semantic_score = result["score"]
            final_score = (
                semantic_score * 0.5 +
                field_priority * 0.3 +
                entity_match_score * 0.2
            )

            result["reranked_score"] = final_score

        # Sort by reranked score
        results.sort(key=lambda x: x.get("reranked_score", x["score"]), reverse=True)

        return results

    def _deduplicate_by_product(
        self,
        results: List[Dict],
        top_k: int
    ) -> List[SearchResult]:
        """
        제품별로 그룹화하고 중복 제거

        각 제품당 가장 높은 점수의 청크만 유지
        """
        product_map = {}

        for result in results:
            payload = result["payload"]
            product_id = payload.get("product_id", "unknown")

            current_score = result.get("reranked_score", result["score"])

            if product_id not in product_map:
                product_map[product_id] = {
                    "product_id": product_id,
                    "product_name": payload.get("product_name", ""),
                    "best_score": current_score,
                    "matched_chunks": [payload],
                    "metadata": {k: v for k, v in payload.items() if k not in ["chunk_text", "field_type"]}
                }
            else:
                # Update best score if higher
                if current_score > product_map[product_id]["best_score"]:
                    product_map[product_id]["best_score"] = current_score

                # Append chunk
                product_map[product_id]["matched_chunks"].append(payload)

        # Convert to SearchResult
        search_results = [
            SearchResult(
                product_id=data["product_id"],
                product_name=data["product_name"],
                score=data["best_score"],
                matched_chunks=data["matched_chunks"],
                metadata=data["metadata"]
            )
            for data in product_map.values()
        ]

        # Sort by score and limit
        search_results.sort(key=lambda x: x.score, reverse=True)
        return search_results[:top_k]


if __name__ == "__main__":
    # Test search engine
    print("="*80)
    print("SEARCH ENGINE TEST")
    print("="*80)

    # Initialize search engine (without actual Qdrant/Embedding)
    engine = SearchEngine()

    test_queries = [
        "20파이 캡 5,000개 주문 가능한 제품 추천해줘",
        "100ml PE 보틀",
        "한국산 PP 크림 자",
    ]

    for query in test_queries:
        print(f"\n{'─'*80}")
        print(f"Query: {query}")
        print(f"{'─'*80}")

        results = engine.search(query, top_k=3)

        print(f"\nResults ({len(results)}):")
        for idx, result in enumerate(results, 1):
            print(f"\n{idx}. {result.product_name} (Score: {result.score:.3f})")
            print(f"   Product ID: {result.product_id}")
            print(f"   Matched Chunks: {len(result.matched_chunks)}")
            for chunk in result.matched_chunks[:3]:  # Show top 3 chunks
                print(f"     • [{chunk.get('field_type', 'unknown').upper()}] {chunk.get('chunk_text', '')}")
