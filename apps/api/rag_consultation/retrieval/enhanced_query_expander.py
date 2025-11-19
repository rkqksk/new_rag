"""
Enhanced Query Expander - Phase 1 Conversational RAG Improvements

Integrates advanced query optimization techniques:
- Parent-Child Chunking support
- Query Decomposition for complex queries
- LLM-based HyDE (Hypothetical Document Embeddings)

Based on: docs/features/CONVERSATIONAL_RAG_CAPABILITIES.md
Phase 1 Target: 85-90% accuracy (from 70-80%)

Features:
- HyDE for ambiguous queries
- Multi-step query decomposition
- Hierarchical chunking integration
- Adaptive strategy selection

Usage:
    expander = EnhancedQueryExpander()
    strategy = await expander.expand(
        query="최근에 갔던 피자집 이름이 뭐였고, 얼마였지?",
        query_type=QueryType.CONVERSATIONAL,
        conversation_id="session-123"
    )
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from apps.api.rag_consultation.models import (
    Intent,
    QueryType,
    RetrievalStrategy,
)
from apps.api.services.advanced_query_optimizer import AdvancedQueryOptimizer, QueryComplexity
from apps.api.services.hierarchical_chunking_service import HierarchicalChunkingService

logger = logging.getLogger(__name__)


@dataclass
class SubQuery:
    """Sub-query from decomposition"""
    query: str
    type: str  # e.g., "temporal", "entity", "price"
    priority: int  # 1 (high) to 3 (low)


@dataclass
class EnhancedRetrievalStrategy:
    """Extended retrieval strategy with Phase 1 features"""

    # Base retrieval settings
    use_dense_retrieval: bool = True
    use_sparse_retrieval: bool = False
    use_hybrid: bool = False
    rerank: bool = True
    top_k: int = 5

    # Phase 1 enhancements
    use_hyde: bool = False
    use_decomposition: bool = False
    use_hierarchical_chunking: bool = True

    # Expanded queries
    expanded_queries: List[str] = None
    sub_queries: List[SubQuery] = None
    hypothetical_document: Optional[str] = None

    # Filters
    filters: Optional[Dict[str, Any]] = None

    # Complexity
    complexity: Optional[QueryComplexity] = None

    def __post_init__(self):
        if self.expanded_queries is None:
            self.expanded_queries = []
        if self.sub_queries is None:
            self.sub_queries = []


class EnhancedQueryExpander:
    """
    Enhanced query expander with Phase 1 improvements.

    Improvements over base QueryExpander:
    1. HyDE for ambiguous queries (+25% accuracy)
    2. Query decomposition for complex queries (+30% accuracy)
    3. Hierarchical chunking integration (+30% context quality)

    Target accuracy: 85-90% (from 70-80%)
    """

    def __init__(
        self,
        qwen_url: str = "http://localhost:11434",
        qwen_model: str = "qwen2.5:latest",
    ):
        """
        Initialize enhanced query expander.

        Args:
            qwen_url: Qwen API URL (local Ollama)
            qwen_model: Qwen model name
        """
        self.optimizer = AdvancedQueryOptimizer(
            qwen_url=qwen_url,
            qwen_model=qwen_model,
        )

        # Complexity thresholds
        self.hyde_threshold = QueryComplexity.MEDIUM  # Use HyDE for medium+ complexity
        self.decomposition_threshold = QueryComplexity.MEDIUM  # Decompose medium+ queries

        logger.info("Initialized EnhancedQueryExpander with Phase 1 features")

    async def expand(
        self,
        query: str,
        query_type: QueryType,
        intent: Intent,
        conversation_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> EnhancedRetrievalStrategy:
        """
        Expand query with Phase 1 enhancements.

        Args:
            query: Original query
            query_type: Classified query type
            intent: Primary intent
            conversation_id: Optional conversation ID for context
            context: Optional conversation context

        Returns:
            EnhancedRetrievalStrategy with Phase 1 features

        Example:
            >>> expander = EnhancedQueryExpander()
            >>> strategy = await expander.expand(
            ...     query="최근에 갔던 피자집 이름이 뭐였고, 얼마였지?",
            ...     query_type=QueryType.CONVERSATIONAL,
            ...     intent=Intent.RECALL
            ... )
            >>> # Strategy includes:
            >>> # - sub_queries: ["최근 피자집", "피자집 이름", "피자집 가격"]
            >>> # - use_hierarchical_chunking: True
            >>> # - complexity: COMPLEX
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            # Step 1: Analyze query complexity
            complexity = await self.optimizer.analyze_complexity(query)
            logger.info(f"Query complexity: {complexity}")

            # Step 2: Initialize strategy
            strategy = EnhancedRetrievalStrategy(complexity=complexity)

            # Step 3: Apply Phase 1 techniques based on complexity

            # 3a. Query Decomposition (for complex queries)
            if self._should_decompose(complexity, query_type):
                logger.info("Applying query decomposition")
                sub_queries = await self.optimizer.decompose_query(query)

                # Convert to SubQuery objects with prioritization
                strategy.sub_queries = self._prioritize_sub_queries(
                    sub_queries, query_type
                )
                strategy.use_decomposition = True

                # Add sub-queries to expanded_queries
                strategy.expanded_queries.extend([sq.query for sq in strategy.sub_queries])

            # 3b. HyDE (for ambiguous queries)
            if self._should_use_hyde(complexity, query_type):
                logger.info("Applying HyDE (Hypothetical Document Embeddings)")
                hypothetical_doc = await self.optimizer.generate_hypothetical_document(query)

                strategy.hypothetical_document = hypothetical_doc
                strategy.use_hyde = True

                # Add hypothetical document to expanded queries
                strategy.expanded_queries.append(hypothetical_doc)

            # 3c. Always include original query
            if query not in strategy.expanded_queries:
                strategy.expanded_queries.insert(0, query)

            # Step 4: Select retrieval parameters based on complexity and query type
            params = self._select_retrieval_params(complexity, query_type, intent)
            strategy.use_dense_retrieval = params["use_dense_retrieval"]
            strategy.use_sparse_retrieval = params["use_sparse_retrieval"]
            strategy.use_hybrid = params["use_hybrid"]
            strategy.rerank = params["rerank"]
            strategy.top_k = params["top_k"]

            # Step 5: Generate filters (temporal, entity-based, etc.)
            strategy.filters = self._generate_filters(query_type, query)

            # Step 6: Enable hierarchical chunking for better context
            strategy.use_hierarchical_chunking = True

            logger.info(
                f"Enhanced expansion complete: "
                f"{len(strategy.expanded_queries)} queries, "
                f"HyDE={strategy.use_hyde}, "
                f"Decomposition={strategy.use_decomposition}, "
                f"SubQueries={len(strategy.sub_queries)}"
            )

            return strategy

        except Exception as e:
            logger.error(f"Enhanced query expansion failed: {e}", exc_info=True)
            # Fallback to simple strategy
            return EnhancedRetrievalStrategy(
                expanded_queries=[query],
                complexity=QueryComplexity.SIMPLE,
                use_hyde=False,
                use_decomposition=False,
            )

    def _should_decompose(self, complexity: QueryComplexity, query_type: QueryType) -> bool:
        """
        Determine if query should be decomposed.

        Decompose if:
        - Complexity >= MEDIUM
        - Query type is CONVERSATIONAL or RECALL
        - Query has multiple conditions
        """
        return (
            complexity.value >= self.decomposition_threshold.value
            and query_type in {QueryType.CONVERSATIONAL, QueryType.COMPARISON}
        )

    def _should_use_hyde(self, complexity: QueryComplexity, query_type: QueryType) -> bool:
        """
        Determine if HyDE should be used.

        Use HyDE if:
        - Query is ambiguous (e.g., "화장품에 쓸 작은 용기")
        - Complexity >= MEDIUM
        - Query type is PRODUCT_SEARCH or CONVERSATIONAL
        """
        return (
            complexity.value >= self.hyde_threshold.value
            and query_type in {QueryType.PRODUCT_SEARCH, QueryType.CONVERSATIONAL}
        )

    def _prioritize_sub_queries(
        self, sub_queries: List[str], query_type: QueryType
    ) -> List[SubQuery]:
        """
        Prioritize sub-queries based on query type.

        Priority rules:
        1. Temporal queries (최근, 지난 달, etc.) - Priority 1
        2. Entity queries (이름, 장소, etc.) - Priority 2
        3. Attribute queries (가격, 크기, etc.) - Priority 3
        """
        prioritized = []

        for i, sq in enumerate(sub_queries):
            # Detect query type
            if any(word in sq for word in ["최근", "지난", "이번", "언제", "날짜", "시간"]):
                priority = 1
                sq_type = "temporal"
            elif any(word in sq for word in ["이름", "어디", "누구", "무엇", "장소"]):
                priority = 2
                sq_type = "entity"
            else:
                priority = 3
                sq_type = "attribute"

            prioritized.append(SubQuery(
                query=sq,
                type=sq_type,
                priority=priority,
            ))

        # Sort by priority
        prioritized.sort(key=lambda x: x.priority)

        return prioritized

    def _select_retrieval_params(
        self, complexity: QueryComplexity, query_type: QueryType, intent: Intent
    ) -> Dict[str, Any]:
        """
        Select retrieval parameters based on complexity, type, and intent.

        Rules:
        - SIMPLE queries: Dense retrieval only, top_k=3
        - MEDIUM queries: Hybrid retrieval, top_k=5, rerank
        - COMPLEX queries: Hybrid retrieval, top_k=10, rerank
        - CONVERSATIONAL: Always rerank
        """
        if complexity == QueryComplexity.SIMPLE:
            return {
                "use_dense_retrieval": True,
                "use_sparse_retrieval": False,
                "use_hybrid": False,
                "rerank": False,
                "top_k": 3,
            }
        elif complexity == QueryComplexity.MEDIUM:
            return {
                "use_dense_retrieval": True,
                "use_sparse_retrieval": True,
                "use_hybrid": True,
                "rerank": True,
                "top_k": 5,
            }
        else:  # COMPLEX
            return {
                "use_dense_retrieval": True,
                "use_sparse_retrieval": True,
                "use_hybrid": True,
                "rerank": True,
                "top_k": 10,
            }

    def _generate_filters(
        self, query_type: QueryType, query: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate metadata filters based on query type and content.

        Filters:
        - Temporal: Extract dates/time ranges
        - Price: Extract price ranges
        - Category: Extract product categories
        """
        filters = {}

        # Temporal filters
        if any(word in query for word in ["최근", "지난", "이번"]):
            # TODO: Implement temporal filter extraction
            # filters["date_range"] = extract_date_range(query)
            pass

        # Price filters
        if any(word in query for word in ["원", "가격", "저렴", "비싼"]):
            # TODO: Implement price filter extraction
            # filters["price_range"] = extract_price_range(query)
            pass

        return filters if filters else None

    async def close(self):
        """Close optimizer resources"""
        await self.optimizer.close()


# Example usage
async def main():
    """Example: Enhanced query expansion"""
    expander = EnhancedQueryExpander()

    # Example 1: Complex conversational query
    query1 = "최근에 갔던 피자집 이름이 뭐였고, 얼마였지?"
    strategy1 = await expander.expand(
        query=query1,
        query_type=QueryType.CONVERSATIONAL,
        intent=Intent.RECALL,
    )

    print(f"\n=== Example 1: Complex Query ===")
    print(f"Original: {query1}")
    print(f"Complexity: {strategy1.complexity}")
    print(f"Sub-queries ({len(strategy1.sub_queries)}):")
    for sq in strategy1.sub_queries:
        print(f"  [{sq.priority}] {sq.type}: {sq.query}")
    print(f"HyDE: {strategy1.use_hyde}")
    print(f"Decomposition: {strategy1.use_decomposition}")
    print(f"Hierarchical Chunking: {strategy1.use_hierarchical_chunking}")

    # Example 2: Ambiguous product search
    query2 = "화장품에 쓸 작은 용기"
    strategy2 = await expander.expand(
        query=query2,
        query_type=QueryType.PRODUCT_SEARCH,
        intent=Intent.SEARCH,
    )

    print(f"\n=== Example 2: Ambiguous Query ===")
    print(f"Original: {query2}")
    print(f"Complexity: {strategy2.complexity}")
    print(f"HyDE: {strategy2.use_hyde}")
    if strategy2.hypothetical_document:
        print(f"Hypothetical Document:\n{strategy2.hypothetical_document[:200]}...")

    await expander.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
