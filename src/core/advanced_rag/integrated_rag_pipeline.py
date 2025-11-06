"""
Integrated Multi-Source RAG Pipeline for Phase 5.4
End-to-end pipeline combining query routing, multi-source search, and score fusion
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio

from .unified_vector_store import UnifiedVectorStore
from .multi_source_search_service import MultiSourceSearchService, SearchResult
from .query_router import AdvancedQueryRouter, QueryIntent
from .score_fusion import ScoreFusion, FusionStrategy, FusionResult

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """Complete RAG response"""
    query: str
    intent: QueryIntent
    results: List[FusionResult]
    total_results: int
    search_time_ms: float
    sources_searched: List[str]
    fusion_strategy: str


class IntegratedRAGPipeline:
    """
    Integrated Multi-Source RAG Pipeline

    Complete end-to-end pipeline:
    1. Query Analysis (AdvancedQueryRouter)
    2. Multi-Source Search (MultiSourceSearchService)
    3. Score Fusion (ScoreFusion)
    4. Response Generation

    Example:
        >>> pipeline = IntegratedRAGPipeline(vector_store, embedder)
        >>> response = await pipeline.search("100ml PET 병 사용설명서")
        >>> for result in response.results[:5]:
        ...     print(f"{result.item_id}: {result.final_score:.3f}")
    """

    def __init__(
        self,
        vector_store: UnifiedVectorStore,
        embedder,  # Text embedding service
        fusion_strategy: FusionStrategy = FusionStrategy.RRF,
        enable_query_routing: bool = True,
        enable_filters: bool = True
    ):
        """
        Initialize Integrated RAG Pipeline

        Args:
            vector_store: UnifiedVectorStore instance
            embedder: Text embedding service (must have encode_text method)
            fusion_strategy: Score fusion strategy
            enable_query_routing: Enable intelligent query routing
            enable_filters: Enable filter building from entities
        """
        self.vector_store = vector_store
        self.embedder = embedder

        # Initialize components
        self.query_router = AdvancedQueryRouter() if enable_query_routing else None
        self.search_service = MultiSourceSearchService(vector_store)
        self.fusion_engine = ScoreFusion(strategy=fusion_strategy)

        self.enable_query_routing = enable_query_routing
        self.enable_filters = enable_filters

        logger.info(
            f"✅ IntegratedRAGPipeline initialized "
            f"(routing={enable_query_routing}, fusion={fusion_strategy.value})"
        )

    async def search(
        self,
        query: str,
        top_k: int = 20,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> RAGResponse:
        """
        Execute end-to-end RAG search

        Args:
            query: User query
            top_k: Number of final results to return
            custom_weights: Optional custom weights (overrides query routing)

        Returns:
            RAGResponse with fused results

        Example:
            >>> response = await pipeline.search("100ml PET 병", top_k=10)
            >>> print(f"Found {len(response.results)} results")
            >>> print(f"Search time: {response.search_time_ms:.1f}ms")
        """
        import time
        start_time = time.time()

        # Step 1: Query Analysis
        if self.enable_query_routing and self.query_router:
            intent = self.query_router.analyze_query(query)
            logger.info(
                f"Query routed to: {intent.target_collections} "
                f"(type: {intent.query_type.value}, confidence: {intent.confidence:.2f})"
            )
        else:
            # Default: search all enabled collections
            from .multi_source_search_service import SearchSource
            intent = QueryIntent(
                query_type=SearchSource.PRODUCTS,
                target_collections=['products_multimodal'],
                confidence=1.0,
                extracted_entities={},
                search_strategy="single"
            )

        # Step 2: Generate embeddings
        text_embedding = await self._generate_embedding(query)

        # Build query embeddings for each target collection
        query_embeddings = {}
        for collection_name in intent.target_collections:
            query_embeddings[collection_name] = text_embedding

        # Step 3: Build filters (if enabled)
        filters = None
        if self.enable_filters and self.query_router:
            if self.query_router.should_use_filters(intent):
                filter_dict = self.query_router.build_filters(intent)
                if filter_dict:
                    # Apply same filter to all collections
                    filters = {
                        collection: filter_dict
                        for collection in intent.target_collections
                    }
                    logger.debug(f"Applied filters: {filter_dict}")

        # Step 4: Multi-source search
        search_results = await self.search_service.search_all_sources(
            query_embeddings=query_embeddings,
            sources=None,  # Will use intent.target_collections
            limit_per_source=top_k * 2,  # Get more for fusion
            filters=filters
        )

        # Step 5: Convert to fusion format
        source_results_map = self._group_by_source(search_results)

        # Step 6: Get fusion weights
        if custom_weights:
            weights = custom_weights
        elif self.query_router:
            weights = self.query_router.get_search_weights(intent)
        else:
            # Equal weights
            weights = {
                src: 1.0 / len(intent.target_collections)
                for src in intent.target_collections
            }

        # Step 7: Score fusion
        fused_results = self.fusion_engine.fuse_scores(
            source_results=source_results_map,
            weights=weights
        )

        # Step 8: Limit to top_k
        final_results = fused_results[:top_k]

        # Calculate elapsed time
        elapsed_ms = (time.time() - start_time) * 1000

        # Build response
        response = RAGResponse(
            query=query,
            intent=intent,
            results=final_results,
            total_results=len(fused_results),
            search_time_ms=elapsed_ms,
            sources_searched=intent.target_collections,
            fusion_strategy=self.fusion_engine.strategy.value
        )

        logger.info(
            f"✅ Search complete: {len(final_results)}/{len(fused_results)} results "
            f"in {elapsed_ms:.1f}ms"
        )

        return response

    def search_sync(
        self,
        query: str,
        top_k: int = 20,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> RAGResponse:
        """
        Synchronous version of search()

        Args:
            query: User query
            top_k: Number of final results
            custom_weights: Optional custom weights

        Returns:
            RAGResponse
        """
        # Run async search in event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.search(query, top_k, custom_weights)
                )
                return future.result()
        else:
            # Run in current loop
            return loop.run_until_complete(
                self.search(query, top_k, custom_weights)
            )

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding"""
        # Check if embedder has async method
        if hasattr(self.embedder, 'encode_text_async'):
            return await self.embedder.encode_text_async(text)
        else:
            # Run sync method in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self.embedder.encode_text,
                text
            )

    def _group_by_source(
        self,
        search_results: List[SearchResult]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group search results by source

        Args:
            search_results: List of SearchResult

        Returns:
            Dict of {source_name: [results]}
        """
        grouped = {}

        for result in search_results:
            source_name = result.source.value

            if source_name not in grouped:
                grouped[source_name] = []

            grouped[source_name].append({
                'id': result.id,
                'score': result.score,
                'normalized_score': result.normalized_score,
                'payload': result.payload
            })

        return grouped

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        return {
            'vector_store': self.vector_store.get_all_stats(),
            'search_service': self.search_service.get_stats(),
            'fusion_strategy': self.fusion_engine.strategy.value,
            'query_routing_enabled': self.enable_query_routing,
            'filters_enabled': self.enable_filters
        }

    def __repr__(self):
        return (
            f"IntegratedRAGPipeline("
            f"routing={self.enable_query_routing}, "
            f"fusion={self.fusion_engine.strategy.value})"
        )
