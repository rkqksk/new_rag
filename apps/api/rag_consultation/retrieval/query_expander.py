"""
Query Expander - Query Expansion and Retrieval Strategy

Provides production-ready query expansion using synonyms, reformulation,
and retrieval strategy optimization.

Features:
- Synonym-based expansion
- Query reformulation
- Retrieval strategy selection
- Metadata filter generation

Usage:
    expander = QueryExpander()
    strategy = await expander.expand(
        query="How does RAG work?",
        query_type=QueryType.FACTUAL
    )
"""

import logging
from typing import Dict, List

from app.rag_consultation.models import (
    Intent,
    QueryType,
    RetrievalStrategy,
)

logger = logging.getLogger(__name__)


class QueryExpander:
    """Query expansion and retrieval strategy optimizer.

    Generates query variations and optimizes retrieval parameters
    based on query type and intent.

    Attributes:
        synonym_map: Common term synonyms for expansion
    """

    # Common manufacturing/AI domain synonyms
    SYNONYM_MAP: Dict[str, List[str]] = {
        "error": ["issue", "problem", "failure", "bug"],
        "fix": ["solve", "resolve", "repair", "correct"],
        "optimize": ["improve", "enhance", "tune", "refine"],
        "setup": ["configure", "install", "initialize", "deploy"],
        "RAG": ["retrieval augmented generation", "retrieval-based generation"],
        "LLM": ["large language model", "language model"],
        "embedding": ["vector representation", "semantic encoding"],
        "search": ["retrieval", "query", "lookup", "find"],
    }

    def __init__(self) -> None:
        """Initialize query expander."""
        logger.info("Query expander initialized")

    def _generate_synonyms(self, query: str) -> List[str]:
        """Generate synonym-based query variations.

        Args:
            query: Original query

        Returns:
            List of query variations with synonyms
        """
        variations = []
        query_lower = query.lower()

        for term, synonyms in self.SYNONYM_MAP.items():
            if term.lower() in query_lower:
                for synonym in synonyms:
                    variant = query_lower.replace(term.lower(), synonym)
                    if variant != query_lower:
                        variations.append(variant)

        return variations[:3]  # Limit to top 3 variations

    def _reformulate_query(
        self,
        query: str,
        query_type: QueryType,
    ) -> List[str]:
        """Reformulate query based on query type.

        Args:
            query: Original query
            query_type: Classified query type

        Returns:
            List of reformulated queries
        """
        reformulations = []

        if query_type == QueryType.FACTUAL:
            # Add "what is" pattern
            if not query.lower().startswith(("what", "define", "explain")):
                reformulations.append(f"What is {query}")
                reformulations.append(f"Explain {query}")

        elif query_type == QueryType.PROCEDURAL:
            # Add "how to" pattern
            if not query.lower().startswith(("how", "steps")):
                reformulations.append(f"How to {query}")
                reformulations.append(f"Steps for {query}")

        elif query_type == QueryType.TROUBLESHOOTING:
            # Add problem-solving patterns
            reformulations.append(f"Solve {query}")
            reformulations.append(f"Fix {query}")

        elif query_type == QueryType.COMPARISON:
            # Add comparison patterns
            if "vs" not in query.lower() and "versus" not in query.lower():
                reformulations.append(f"Compare {query}")
                reformulations.append(f"Difference between {query}")

        return reformulations[:2]  # Limit to top 2 reformulations

    def _select_retrieval_params(
        self,
        query_type: QueryType,
        intent: Intent,
    ) -> Dict[str, any]:
        """Select optimal retrieval parameters based on query characteristics.

        Args:
            query_type: Classified query type
            intent: Primary intent

        Returns:
            Dictionary of retrieval parameters
        """
        params = {
            "use_dense_retrieval": True,
            "use_sparse_retrieval": True,
            "use_hybrid": True,
            "rerank": True,
            "top_k": 5,
        }

        # Adjust top_k based on query type
        if query_type in {QueryType.COMPARISON, QueryType.EXPLORATORY}:
            params["top_k"] = 10  # More results for broad queries

        elif query_type in {QueryType.FACTUAL, QueryType.TROUBLESHOOTING}:
            params["top_k"] = 5  # Focused results

        # Adjust retrieval strategy based on intent
        if intent == Intent.PROBLEM_SOLVING:
            # Prioritize recent, relevant documents
            params["rerank"] = True
            params["use_hybrid"] = True

        elif intent == Intent.LEARNING:
            # Broader retrieval for educational content
            params["top_k"] = 8
            params["use_sparse_retrieval"] = True

        return params

    def _generate_filters(
        self,
        query_type: QueryType,
    ) -> Dict[str, str]:
        """Generate metadata filters based on query type.

        Args:
            query_type: Classified query type

        Returns:
            Dictionary of metadata filters
        """
        filters = {}

        # Add document type filters based on query type
        if query_type == QueryType.PROCEDURAL:
            filters["doc_type"] = "tutorial,guide,documentation"

        elif query_type == QueryType.TROUBLESHOOTING:
            filters["doc_type"] = "troubleshooting,faq,support"

        elif query_type == QueryType.FACTUAL:
            filters["doc_type"] = "documentation,reference,wiki"

        return filters

    async def expand(
        self,
        query: str,
        query_type: QueryType,
        intent: Intent,
    ) -> RetrievalStrategy:
        """Expand query and generate retrieval strategy.

        Args:
            query: Original query
            query_type: Classified query type
            intent: Primary intent

        Returns:
            RetrievalStrategy with expansions and parameters

        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            # Generate query variations
            synonym_variations = self._generate_synonyms(query)
            reformulations = self._reformulate_query(query, query_type)

            # Combine all variations (original + variations)
            expanded_queries = [query] + synonym_variations + reformulations

            # Remove duplicates while preserving order
            seen = set()
            unique_queries = []
            for q in expanded_queries:
                q_lower = q.lower().strip()
                if q_lower not in seen:
                    seen.add(q_lower)
                    unique_queries.append(q)

            # Select retrieval parameters
            params = self._select_retrieval_params(query_type, intent)

            # Generate filters
            filters = self._generate_filters(query_type)

            # Create retrieval strategy
            strategy = RetrievalStrategy(
                use_dense_retrieval=params["use_dense_retrieval"],
                use_sparse_retrieval=params["use_sparse_retrieval"],
                use_hybrid=params["use_hybrid"],
                rerank=params["rerank"],
                top_k=params["top_k"],
                expanded_queries=unique_queries,
                filters=filters,
            )

            logger.info(
                f"Expanded query into {len(unique_queries)} variations, " f"top_k={params['top_k']}"
            )

            return strategy

        except Exception as e:
            logger.error(f"Query expansion failed: {e}")
            raise RuntimeError(f"Expansion error: {e}") from e
