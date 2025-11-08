"""
Multi-Source Search Service for Phase 5
Unified search across multiple Qdrant collections with score normalization
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from qdrant_client import QdrantClient

from .unified_vector_store import UnifiedVectorStore

logger = logging.getLogger(__name__)


class SearchSource(Enum):
    """Search source types"""

    PRODUCTS = "products_multimodal"
    DOCUMENTS = "documents_semantic"
    IMAGES = "images_visual"
    TABLES = "tables_structured"


@dataclass
class SearchResult:
    """Unified search result"""

    id: str
    source: SearchSource
    score: float
    normalized_score: float
    payload: Dict[str, Any]
    vector_type: Optional[str] = None  # text, image, shape


class ScoreNormalizer:
    """
    Score Normalization for cross-source comparison

    Methods:
    - min_max: Min-max normalization to [0, 1]
    - z_score: Z-score standardization
    - reciprocal_rank: Rank-based normalization
    """

    @staticmethod
    def min_max_normalize(scores: List[float]) -> List[float]:
        """
        Min-max normalization to [0, 1]

        Formula: (x - min) / (max - min)
        """
        if not scores:
            return []

        min_score = min(scores)
        max_score = max(scores)

        if max_score == min_score:
            return [1.0] * len(scores)

        return [(score - min_score) / (max_score - min_score) for score in scores]

    @staticmethod
    def z_score_normalize(scores: List[float]) -> List[float]:
        """
        Z-score standardization

        Formula: (x - mean) / std
        """
        if not scores:
            return []

        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        std = variance**0.5

        if std == 0:
            return [0.0] * len(scores)

        return [(score - mean) / std for score in scores]

    @staticmethod
    def reciprocal_rank_normalize(scores: List[float], k: float = 60) -> List[float]:
        """
        Reciprocal Rank Fusion (RRF) normalization

        Formula: 1 / (k + rank)
        where rank starts from 1

        Args:
            scores: List of scores (higher is better)
            k: Constant (default: 60, as per RRF paper)

        Returns:
            Normalized scores
        """
        if not scores:
            return []

        # Sort by score (descending) and get ranks
        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        # Calculate RRF scores
        rrf_scores = [0.0] * len(scores)
        for rank, idx in enumerate(sorted_indices, start=1):
            rrf_scores[idx] = 1.0 / (k + rank)

        return rrf_scores


class MultiSourceSearchService:
    """
    Multi-Source Search Service

    Features:
    - Search across multiple collections in parallel
    - Score normalization for fair comparison
    - Result fusion and ranking
    - Filtering and pagination
    """

    def __init__(self, vector_store: UnifiedVectorStore, normalization_method: str = "min_max"):
        """
        Initialize Multi-Source Search Service

        Args:
            vector_store: UnifiedVectorStore instance
            normalization_method: Normalization method (min_max, z_score, rrf)
        """
        self.store = vector_store
        self.normalizer = ScoreNormalizer()
        self.normalization_method = normalization_method

        logger.info(f"✅ MultiSourceSearchService initialized (method: {normalization_method})")

    async def search_all_sources(
        self,
        query_embeddings: Dict[str, List[float]],
        sources: Optional[List[SearchSource]] = None,
        limit_per_source: int = 20,
        filters: Optional[Dict[SearchSource, Dict]] = None,
    ) -> List[SearchResult]:
        """
        Search across multiple sources in parallel

        Args:
            query_embeddings: Dict of {collection_name: embedding}
            sources: List of sources to search (None = all enabled)
            limit_per_source: Max results per source
            filters: Optional filters per source

        Returns:
            List of unified SearchResult objects (sorted by normalized score)

        Example:
            >>> # Text search across products and documents
            >>> embeddings = {
            ...     SearchSource.PRODUCTS.value: text_embedding,  # 384-dim
            ...     SearchSource.DOCUMENTS.value: text_embedding  # 384-dim
            ... }
            >>> results = await service.search_all_sources(
            ...     query_embeddings=embeddings,
            ...     sources=[SearchSource.PRODUCTS, SearchSource.DOCUMENTS],
            ...     limit_per_source=10
            ... )
        """
        # Determine sources to search
        if sources is None:
            sources = [SearchSource(col.name) for col in self.store.get_enabled_collections()]
        else:
            # Filter only enabled sources
            enabled_names = {col.name for col in self.store.get_enabled_collections()}
            sources = [src for src in sources if src.value in enabled_names]

        if not sources:
            logger.warning("No enabled sources to search")
            return []

        # Build queries for parallel search
        queries = {}
        filters_dict = filters or {}

        for source in sources:
            collection_name = source.value

            if collection_name in query_embeddings:
                source_filter = filters_dict.get(source)
                queries[collection_name] = (query_embeddings[collection_name], source_filter)

        # Parallel search
        logger.debug(f"🔍 Searching {len(queries)} collections in parallel...")

        raw_results = await self.store.search_parallel(queries, limit=limit_per_source)

        # Convert to unified format
        all_results = []
        source_groups = {}  # For per-source normalization

        for collection_name, points in raw_results.items():
            source = SearchSource(collection_name)
            source_results = []

            for point in points:
                result = SearchResult(
                    id=str(point.id),
                    source=source,
                    score=point.score,
                    normalized_score=0.0,  # Will be computed
                    payload=point.payload,
                    vector_type=None,  # Can be extracted from payload if needed
                )
                source_results.append(result)
                all_results.append(result)

            source_groups[source] = source_results

        # Normalize scores per source
        logger.debug(f"📊 Normalizing scores (method: {self.normalization_method})...")
        self._normalize_scores(source_groups)

        # Sort by normalized score (descending)
        all_results.sort(key=lambda r: r.normalized_score, reverse=True)

        logger.info(f"✅ Found {len(all_results)} results across {len(source_groups)} sources")

        return all_results

    def _normalize_scores(self, source_groups: Dict[SearchSource, List[SearchResult]]):
        """
        Normalize scores within each source group

        Args:
            source_groups: Dict of {source: [results]}
        """
        for source, results in source_groups.items():
            if not results:
                continue

            scores = [r.score for r in results]

            # Apply normalization method
            if self.normalization_method == "min_max":
                normalized = self.normalizer.min_max_normalize(scores)
            elif self.normalization_method == "z_score":
                normalized = self.normalizer.z_score_normalize(scores)
            elif self.normalization_method == "rrf":
                normalized = self.normalizer.reciprocal_rank_normalize(scores)
            else:
                logger.warning(
                    f"Unknown normalization method: {self.normalization_method}, using min_max"
                )
                normalized = self.normalizer.min_max_normalize(scores)

            # Update normalized scores
            for result, norm_score in zip(results, normalized):
                result.normalized_score = norm_score

    def search_products_only(
        self,
        text_embedding: List[float],
        image_embedding: Optional[List[float]] = None,
        shape_embedding: Optional[List[float]] = None,
        limit: int = 20,
    ) -> List[SearchResult]:
        """
        Convenience method: Search products only

        Args:
            text_embedding: 384-dim text vector
            image_embedding: 1024-dim image vector (optional)
            shape_embedding: 128-dim shape vector (optional)
            limit: Max results

        Returns:
            List of SearchResult
        """
        # Build multi-vector query
        vectors = {"text": text_embedding}

        if image_embedding:
            vectors["image"] = image_embedding

        if shape_embedding:
            vectors["shape"] = shape_embedding

        # Search using underlying store
        results = self.store.client.search(
            collection_name=SearchSource.PRODUCTS.value, query_vector=vectors, limit=limit
        )

        # Convert to SearchResult
        return [
            SearchResult(
                id=str(point.id),
                source=SearchSource.PRODUCTS,
                score=point.score,
                normalized_score=point.score,  # Already normalized by Qdrant
                payload=point.payload,
            )
            for point in results
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get search service statistics"""
        stats = self.store.get_all_stats()

        return {
            "sources": len(stats),
            "total_points": sum(s.get("points_count", 0) for s in stats.values()),
            "collections": stats,
            "normalization_method": self.normalization_method,
        }

    def __repr__(self):
        enabled = len(self.store.get_enabled_collections())
        return (
            f"MultiSourceSearchService("
            f"sources={enabled}, "
            f"method={self.normalization_method})"
        )
