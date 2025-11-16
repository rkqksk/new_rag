"""
Intelligent Query Router
Routes queries to appropriate search strategies based on query type
"""

import logging
import re
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Query type classification"""

    PRODUCT_SEARCH = "product_search"  # "100ml bottle"
    SPECIFICATION = "specification"  # "capacity 100ml neck 24mm"
    BUSINESS_INQUIRY = "business_inquiry"  # "MOQ price"
    IMAGE_SEARCH = "image_search"  # Image-based query
    SHAPE_SEARCH = "shape_search"  # Shape/outline query
    HYBRID = "hybrid"  # Multi-modal query
    CONVERSATIONAL = "conversational"  # "Can you find...", "Show me..."
    UNKNOWN = "unknown"


class SearchStrategy(Enum):
    """Search strategy types"""

    TEXT_ONLY = "text_only"
    IMAGE_ONLY = "image_only"
    SHAPE_ONLY = "shape_only"
    TEXT_IMAGE = "text_image"
    TEXT_SHAPE = "text_shape"
    FULL_HYBRID = "full_hybrid"
    SEMANTIC = "semantic"
    KEYWORD = "keyword"


class QueryRouter:
    """
    Intelligent Query Router

    Analyzes queries and routes them to optimal search strategies
    """

    def __init__(self):
        """Initialize query router"""
        self.query_patterns = self._init_patterns()
        logger.info("✅ Query router initialized")

    def _init_patterns(self) -> Dict[QueryType, List[re.Pattern]]:
        """Initialize regex patterns for query classification"""
        return {
            QueryType.PRODUCT_SEARCH: [
                re.compile(r"\d+\s*(ml|cc|L|g|kg)", re.IGNORECASE),  # Capacity
                re.compile(r"(bottle|jar|cap|pump|container)", re.IGNORECASE),  # Product types
                re.compile(r"(pet|pp|pe|hdpe|glass)", re.IGNORECASE),  # Materials
            ],
            QueryType.SPECIFICATION: [
                re.compile(r"(capacity|neck|diameter|height|width)", re.IGNORECASE),
                re.compile(r"\d+\s*(파이|mm|cm)", re.IGNORECASE),  # Measurements
                re.compile(r"(spec|specification|dimension)", re.IGNORECASE),
            ],
            QueryType.BUSINESS_INQUIRY: [
                re.compile(r"(moq|minimum order|최소\s*주문)", re.IGNORECASE),
                re.compile(r"(price|cost|가격)", re.IGNORECASE),
                re.compile(r"(lead time|delivery|배송)", re.IGNORECASE),
            ],
            QueryType.CONVERSATIONAL: [
                re.compile(r"^(can you|could you|please|show me|find me)", re.IGNORECASE),
                re.compile(r"(what is|what are|how to|how do)", re.IGNORECASE),
                re.compile(r"(tell me|explain|describe)", re.IGNORECASE),
            ],
        }

    def classify_query(
        self, query: str, has_image: bool = False, has_shape: bool = False
    ) -> QueryType:
        """
        Classify query type

        Args:
            query: Query text
            has_image: Whether image is provided
            has_shape: Whether shape/outline is provided

        Returns:
            QueryType enum
        """
        if not query and has_image and has_shape:
            return QueryType.SHAPE_SEARCH

        if not query and has_image:
            return QueryType.IMAGE_SEARCH

        if not query:
            return QueryType.UNKNOWN

        # Check patterns
        pattern_matches = {}
        for query_type, patterns in self.query_patterns.items():
            matches = sum(1 for pattern in patterns if pattern.search(query))
            if matches > 0:
                pattern_matches[query_type] = matches

        # Determine query type based on matches
        if not pattern_matches:
            if has_image or has_shape:
                return QueryType.HYBRID
            return QueryType.CONVERSATIONAL if len(query.split()) > 5 else QueryType.PRODUCT_SEARCH

        # Get type with most matches
        best_type = max(pattern_matches.items(), key=lambda x: x[1])[0]

        # If image/shape provided, it's hybrid
        if (has_image or has_shape) and best_type != QueryType.IMAGE_SEARCH:
            return QueryType.HYBRID

        return best_type

    def route_query(
        self,
        query: str,
        has_image: bool = False,
        has_shape: bool = False,
        user_preference: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Route query to appropriate search strategy

        Args:
            query: Query text
            has_image: Whether image is provided
            has_shape: Whether shape is provided
            user_preference: User's search preference

        Returns:
            Routing decision dictionary
        """
        # Classify query
        query_type = self.classify_query(query, has_image, has_shape)

        # Determine search strategy
        strategy = self._determine_strategy(query_type, has_image, has_shape, user_preference)

        # Build routing decision
        decision = {
            "query_type": query_type.value,
            "search_strategy": strategy.value,
            "use_text": self._should_use_text(strategy),
            "use_image": self._should_use_image(strategy),
            "use_shape": self._should_use_shape(strategy),
            "fusion_weights": self._get_fusion_weights(query_type, strategy),
            "use_reranking": self._should_rerank(query_type, strategy),
            "filters": self._extract_filters(query, query_type),
            "explanation": self._explain_routing(query_type, strategy),
        }

        logger.info(f"Query routed: {query_type.value} → {strategy.value}")

        return decision

    def _determine_strategy(
        self,
        query_type: QueryType,
        has_image: bool,
        has_shape: bool,
        user_preference: Optional[str],
    ) -> SearchStrategy:
        """Determine optimal search strategy"""
        # User preference override
        if user_preference:
            try:
                return SearchStrategy(user_preference)
            except ValueError:
                pass

        # Strategy mapping
        strategy_map = {
            QueryType.PRODUCT_SEARCH: SearchStrategy.TEXT_ONLY,
            QueryType.SPECIFICATION: SearchStrategy.TEXT_ONLY,
            QueryType.BUSINESS_INQUIRY: SearchStrategy.TEXT_ONLY,
            QueryType.IMAGE_SEARCH: SearchStrategy.IMAGE_ONLY,
            QueryType.SHAPE_SEARCH: SearchStrategy.SHAPE_ONLY,
            QueryType.CONVERSATIONAL: SearchStrategy.SEMANTIC,
            QueryType.HYBRID: SearchStrategy.FULL_HYBRID,
            QueryType.UNKNOWN: SearchStrategy.SEMANTIC,
        }

        base_strategy = strategy_map.get(query_type, SearchStrategy.TEXT_ONLY)

        # Upgrade strategy if multi-modal
        if has_image and has_shape:
            return SearchStrategy.FULL_HYBRID
        elif has_image:
            return SearchStrategy.TEXT_IMAGE
        elif has_shape:
            return SearchStrategy.TEXT_SHAPE

        return base_strategy

    def _should_use_text(self, strategy: SearchStrategy) -> bool:
        """Check if text should be used"""
        return strategy in [
            SearchStrategy.TEXT_ONLY,
            SearchStrategy.TEXT_IMAGE,
            SearchStrategy.TEXT_SHAPE,
            SearchStrategy.FULL_HYBRID,
            SearchStrategy.SEMANTIC,
            SearchStrategy.KEYWORD,
        ]

    def _should_use_image(self, strategy: SearchStrategy) -> bool:
        """Check if image should be used"""
        return strategy in [
            SearchStrategy.IMAGE_ONLY,
            SearchStrategy.TEXT_IMAGE,
            SearchStrategy.FULL_HYBRID,
        ]

    def _should_use_shape(self, strategy: SearchStrategy) -> bool:
        """Check if shape should be used"""
        return strategy in [
            SearchStrategy.SHAPE_ONLY,
            SearchStrategy.TEXT_SHAPE,
            SearchStrategy.FULL_HYBRID,
        ]

    def _get_fusion_weights(
        self, query_type: QueryType, strategy: SearchStrategy
    ) -> Dict[str, float]:
        """Get optimal fusion weights based on query type"""
        # Default weights
        weights = {"text": 1.0, "image": 0.0, "shape": 0.0}

        if strategy == SearchStrategy.TEXT_ONLY:
            weights = {"text": 1.0}

        elif strategy == SearchStrategy.IMAGE_ONLY:
            weights = {"image": 1.0}

        elif strategy == SearchStrategy.SHAPE_ONLY:
            weights = {"shape": 1.0}

        elif strategy == SearchStrategy.TEXT_IMAGE:
            if query_type == QueryType.PRODUCT_SEARCH:
                weights = {"text": 0.7, "image": 0.3}
            elif query_type == QueryType.SPECIFICATION:
                weights = {"text": 0.8, "image": 0.2}
            else:
                weights = {"text": 0.6, "image": 0.4}

        elif strategy == SearchStrategy.TEXT_SHAPE:
            weights = {"text": 0.5, "shape": 0.5}

        elif strategy == SearchStrategy.FULL_HYBRID:
            weights = {"text": 0.5, "image": 0.3, "shape": 0.2}

        return weights

    def _should_rerank(self, query_type: QueryType, strategy: SearchStrategy) -> bool:
        """Determine if cross-encoder re-ranking should be used"""
        # Re-rank for text-based queries
        return query_type in [
            QueryType.PRODUCT_SEARCH,
            QueryType.SPECIFICATION,
            QueryType.CONVERSATIONAL,
        ] and self._should_use_text(strategy)

    def _extract_filters(self, query: str, query_type: QueryType) -> Dict[str, Any]:
        """Extract filters from query"""
        filters = {}

        # Extract capacity
        capacity_match = re.search(r"(\d+)\s*(ml|cc|L)", query, re.IGNORECASE)
        if capacity_match:
            filters["capacity"] = capacity_match.group(1) + capacity_match.group(2)

        # Extract neck size
        neck_match = re.search(r"(\d+)\s*(파이|mm)", query, re.IGNORECASE)
        if neck_match:
            filters["neck"] = neck_match.group(1) + neck_match.group(2)

        # Extract material
        materials = ["PET", "PP", "PE", "HDPE", "Glass", "Aluminum"]
        for material in materials:
            if material.lower() in query.lower():
                filters["material"] = material
                break

        # Extract product category
        categories = {
            "bottle": ["bottle", "보틀", "병"],
            "jar": ["jar", "용기", "자"],
            "cap": ["cap", "캡", "마개"],
            "pump": ["pump", "펌프"],
        }

        for category, keywords in categories.items():
            if any(keyword in query.lower() for keyword in keywords):
                filters["category"] = category
                break

        return filters

    def _explain_routing(self, query_type: QueryType, strategy: SearchStrategy) -> str:
        """Generate human-readable explanation"""
        explanations = {
            (
                QueryType.PRODUCT_SEARCH,
                SearchStrategy.TEXT_ONLY,
            ): "Product search query detected. Using text-only semantic search.",
            (
                QueryType.SPECIFICATION,
                SearchStrategy.TEXT_ONLY,
            ): "Specification query detected. Using precise text matching.",
            (
                QueryType.BUSINESS_INQUIRY,
                SearchStrategy.TEXT_ONLY,
            ): "Business inquiry detected. Searching business-related fields.",
            (
                QueryType.IMAGE_SEARCH,
                SearchStrategy.IMAGE_ONLY,
            ): "Image-only query. Using visual similarity search.",
            (
                QueryType.SHAPE_SEARCH,
                SearchStrategy.SHAPE_ONLY,
            ): "Shape query detected. Using contour-based matching.",
            (
                QueryType.HYBRID,
                SearchStrategy.FULL_HYBRID,
            ): "Multi-modal query. Combining text, image, and shape search.",
            (
                QueryType.CONVERSATIONAL,
                SearchStrategy.SEMANTIC,
            ): "Conversational query. Using semantic understanding.",
        }

        return explanations.get(
            (query_type, strategy),
            f"Routing {query_type.value} query to {strategy.value} strategy.",
        )

    def get_routing_statistics(self, queries: List[str]) -> Dict[str, Any]:
        """
        Analyze routing statistics for multiple queries

        Args:
            queries: List of queries to analyze

        Returns:
            Statistics dictionary
        """
        type_counts = {}
        strategy_counts = {}

        for query in queries:
            decision = self.route_query(query)
            query_type = decision["query_type"]
            strategy = decision["search_strategy"]

            type_counts[query_type] = type_counts.get(query_type, 0) + 1
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        return {
            "total_queries": len(queries),
            "query_types": type_counts,
            "strategies_used": strategy_counts,
            "most_common_type": (
                max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None
            ),
            "most_common_strategy": (
                max(strategy_counts.items(), key=lambda x: x[1])[0] if strategy_counts else None
            ),
        }

    def __repr__(self):
        return "QueryRouter(patterns_loaded=True)"
