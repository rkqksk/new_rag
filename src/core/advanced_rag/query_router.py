"""
Advanced Query Router for Phase 5.2
Intelligent query routing to appropriate collections based on query type
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Query type classification"""

    PRODUCT_SEARCH = "product_search"  # "50ml PET 병 찾아줘"
    DOCUMENT_LOOKUP = "document_lookup"  # "사용 설명서", "매뉴얼"
    IMAGE_SEARCH = "image_search"  # "이 제품과 비슷한 이미지"
    TABLE_DATA = "table_data"  # "가격표", "스펙표"
    MULTI_SOURCE = "multi_source"  # "제품과 관련 문서 모두"
    UNKNOWN = "unknown"


@dataclass
class QueryIntent:
    """Query intent analysis result"""

    query_type: QueryType
    target_collections: List[str]
    confidence: float
    extracted_entities: Dict[str, Any]
    search_strategy: str  # "single", "parallel", "cascade"


class AdvancedQueryRouter:
    """
    Advanced Query Router

    Analyzes user queries and routes to appropriate collections

    Features:
    - Query type classification (product, document, image, table)
    - Entity extraction (capacity, material, etc.)
    - Smart collection selection
    - Search strategy recommendation

    Example:
        >>> router = AdvancedQueryRouter()
        >>> intent = router.analyze_query("50ml PET 병 사용설명서")
        >>> print(intent.target_collections)
        ['products_multimodal', 'documents_semantic']
    """

    def __init__(self):
        """Initialize Advanced Query Router"""
        # Product-related keywords
        self.product_keywords = {
            "제품",
            "병",
            "용기",
            "캡",
            "펌프",
            "자",
            "보틀",
            "bottle",
            "cap",
            "jar",
            "pump",
            "마개",
            "뚜껑",
            "container",
            "product",
            "포장",
            "package",
        }

        # Document-related keywords
        self.document_keywords = {
            "설명서",
            "매뉴얼",
            "가이드",
            "문서",
            "manual",
            "guide",
            "document",
            "instruction",
            "사용법",
            "안내서",
            "pdf",
            "카탈로그",
            "catalog",
        }

        # Image-related keywords
        self.image_keywords = {
            "이미지",
            "사진",
            "그림",
            "비슷한",
            "같은",
            "image",
            "photo",
            "picture",
            "similar",
            "look like",
            "모양",
            "shape",
            "외관",
            "appearance",
        }

        # Table-related keywords
        self.table_keywords = {
            "가격표",
            "스펙표",
            "표",
            "table",
            "목록",
            "list",
            "리스트",
            "데이터",
            "data",
            "통계",
            "statistics",
            "excel",
            "csv",
        }

        # Entity extraction patterns
        self.entity_patterns = {
            "capacity": r"(\d+(?:\.\d+)?)\s*(ml|ML|l|L|ℓ|cc)",
            "neck": r"(\d+)\s*파이|Ø\s*(\d+)|내경\s*(\d+)",
            "material": r"(PP|PE|PET|PETG|HDPE|LDPE|PS|PVC|ABS)",
            "moq": r"(\d+(?:,\d{3})*)\s*개|최소\s*(\d+)",
            "quantity": r"(\d+(?:,\d{3})*)\s*(개|ea|pcs|pieces)",
        }

        logger.info("✅ AdvancedQueryRouter initialized")

    def analyze_query(self, query: str) -> QueryIntent:
        """
        Analyze query and determine routing strategy

        Args:
            query: User query string

        Returns:
            QueryIntent with routing information

        Example:
            >>> intent = router.analyze_query("100ml PET 병 찾아줘")
            >>> print(intent.query_type)
            QueryType.PRODUCT_SEARCH
            >>> print(intent.target_collections)
            ['products_multimodal']
        """
        query_lower = query.lower()

        # Count keyword matches
        product_score = self._count_keywords(query_lower, self.product_keywords)
        document_score = self._count_keywords(query_lower, self.document_keywords)
        image_score = self._count_keywords(query_lower, self.image_keywords)
        table_score = self._count_keywords(query_lower, self.table_keywords)

        # Extract entities
        entities = self._extract_entities(query)

        # Classify query type
        scores = {
            "product": product_score,
            "document": document_score,
            "image": image_score,
            "table": table_score,
        }

        max_score = max(scores.values())
        matching_types = [k for k, v in scores.items() if v == max_score and v > 0]

        # Determine query type and target collections
        if len(matching_types) > 1:
            # Multi-source query
            query_type = QueryType.MULTI_SOURCE
            target_collections = self._get_collections_for_types(matching_types)
            search_strategy = "parallel"
            confidence = 0.8
        elif len(matching_types) == 1:
            query_type, target_collections, search_strategy = self._classify_single_type(
                matching_types[0], entities
            )
            confidence = 0.9
        else:
            # Default to product search
            query_type = QueryType.PRODUCT_SEARCH
            target_collections = ["products_multimodal"]
            search_strategy = "single"
            confidence = 0.5

        intent = QueryIntent(
            query_type=query_type,
            target_collections=target_collections,
            confidence=confidence,
            extracted_entities=entities,
            search_strategy=search_strategy,
        )

        logger.debug(
            f"Query analysis: {query_type.value} → {target_collections} (confidence: {confidence:.2f})"
        )

        return intent

    def _count_keywords(self, query: str, keywords: Set[str]) -> int:
        """Count matching keywords in query"""
        count = 0
        for keyword in keywords:
            if keyword in query:
                count += 1
        return count

    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from query using regex patterns"""
        entities = {}

        for entity_name, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                # Handle tuple matches from groups
                if isinstance(matches[0], tuple):
                    # Get first non-empty group
                    value = next((m for m in matches[0] if m), None)
                else:
                    value = matches[0]

                if value:
                    entities[entity_name] = value

        return entities

    def _classify_single_type(
        self, type_key: str, entities: Dict[str, Any]
    ) -> tuple[QueryType, List[str], str]:
        """Classify single type query"""
        if type_key == "product":
            return (QueryType.PRODUCT_SEARCH, ["products_multimodal"], "single")
        elif type_key == "document":
            return (QueryType.DOCUMENT_LOOKUP, ["documents_semantic"], "single")
        elif type_key == "image":
            return (QueryType.IMAGE_SEARCH, ["images_visual", "products_multimodal"], "parallel")
        elif type_key == "table":
            return (QueryType.TABLE_DATA, ["tables_structured"], "single")
        else:
            return (QueryType.UNKNOWN, ["products_multimodal"], "single")

    def _get_collections_for_types(self, types: List[str]) -> List[str]:
        """Get collections for multiple types"""
        collections = set()

        for type_key in types:
            if type_key == "product":
                collections.add("products_multimodal")
            elif type_key == "document":
                collections.add("documents_semantic")
            elif type_key == "image":
                collections.add("images_visual")
                collections.add("products_multimodal")
            elif type_key == "table":
                collections.add("tables_structured")

        return list(collections)

    def get_search_weights(self, intent: QueryIntent) -> Dict[str, float]:
        """
        Get search weights for each collection based on query intent

        Args:
            intent: Query intent

        Returns:
            Dict of {collection_name: weight}

        Example:
            >>> weights = router.get_search_weights(intent)
            >>> # {'products_multimodal': 0.7, 'documents_semantic': 0.3}
        """
        weights = {}

        if intent.query_type == QueryType.PRODUCT_SEARCH:
            weights["products_multimodal"] = 1.0

        elif intent.query_type == QueryType.DOCUMENT_LOOKUP:
            weights["documents_semantic"] = 1.0

        elif intent.query_type == QueryType.IMAGE_SEARCH:
            weights["images_visual"] = 0.6
            weights["products_multimodal"] = 0.4

        elif intent.query_type == QueryType.TABLE_DATA:
            weights["tables_structured"] = 1.0

        elif intent.query_type == QueryType.MULTI_SOURCE:
            # Equal weights for all target collections
            num_collections = len(intent.target_collections)
            for collection in intent.target_collections:
                weights[collection] = 1.0 / num_collections

        else:
            # Default: product search
            weights["products_multimodal"] = 1.0

        return weights

    def should_use_filters(self, intent: QueryIntent) -> bool:
        """Determine if filters should be applied based on entities"""
        return len(intent.extracted_entities) > 0

    def build_filters(self, intent: QueryIntent) -> Dict[str, Any]:
        """
        Build Qdrant filters from extracted entities

        Args:
            intent: Query intent with entities

        Returns:
            Qdrant filter dict

        Example:
            >>> filters = router.build_filters(intent)
            >>> # {"must": [{"key": "capacity_ml", "range": {"gte": 50, "lte": 100}}]}
        """
        filters = {"must": []}
        entities = intent.extracted_entities

        # Capacity filter
        if "capacity" in entities:
            capacity_str = entities["capacity"]
            # Extract number
            capacity_num = float(re.findall(r"\d+(?:\.\d+)?", capacity_str)[0])

            # Range: ±20%
            min_capacity = capacity_num * 0.8
            max_capacity = capacity_num * 1.2

            filters["must"].append(
                {"key": "capacity_ml", "range": {"gte": min_capacity, "lte": max_capacity}}
            )

        # Material filter
        if "material" in entities:
            material = entities["material"].upper()
            filters["must"].append({"key": "material", "match": {"value": material}})

        # Neck filter
        if "neck" in entities:
            neck_str = entities["neck"]
            neck_num = int(re.findall(r"\d+", neck_str)[0])

            filters["must"].append({"key": "neck_size", "match": {"value": f"{neck_num}파이"}})

        # MOQ filter
        if "moq" in entities:
            moq_str = entities["moq"].replace(",", "")
            moq_num = int(re.findall(r"\d+", moq_str)[0])

            filters["must"].append({"key": "moq", "range": {"lte": moq_num}})

        return filters if filters["must"] else {}

    def __repr__(self):
        return (
            f"AdvancedQueryRouter("
            f"keywords={{product:{len(self.product_keywords)}, "
            f"document:{len(self.document_keywords)}, "
            f"image:{len(self.image_keywords)}, "
            f"table:{len(self.table_keywords)}}})"
        )
