"""
Hybrid Search Engine for Multi-Modal RAG
Combines text, image, and shape vectors with fusion strategies
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import ScoredPoint

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with multi-modal scores"""

    product_id: str
    score: float
    payload: Dict[str, Any]
    modality_scores: Dict[str, float]  # Individual scores per modality
    rank: int


class FusionStrategy:
    """Base class for fusion strategies"""

    def fuse(
        self,
        results_by_modality: Dict[str, List[ScoredPoint]],
        weights: Optional[Dict[str, float]] = None,
    ) -> List[SearchResult]:
        """
        Fuse results from multiple modalities

        Args:
            results_by_modality: {modality: [scored_points]}
            weights: Optional modality weights

        Returns:
            List of fused SearchResult objects
        """
        raise NotImplementedError


class WeightedFusion(FusionStrategy):
    """Weighted linear fusion strategy"""

    def fuse(
        self,
        results_by_modality: Dict[str, List[ScoredPoint]],
        weights: Optional[Dict[str, float]] = None,
    ) -> List[SearchResult]:
        """
        Combine scores with weighted average

        Formula: final_score = Σ(weight_i × score_i)
        """
        if weights is None:
            # Equal weights
            weights = {mod: 1.0 / len(results_by_modality) for mod in results_by_modality}

        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}

        # Collect all product IDs
        all_product_ids = set()
        for results in results_by_modality.values():
            for result in results:
                all_product_ids.add(result.id)

        # Compute weighted scores
        fused_results = []
        for product_id in all_product_ids:
            modality_scores = {}
            weighted_score = 0.0

            for modality, results in results_by_modality.items():
                # Find score for this product in this modality
                score = 0.0
                payload = None
                for result in results:
                    if result.id == product_id:
                        score = result.score
                        payload = result.payload or {}
                        break

                modality_scores[modality] = score
                weighted_score += weights.get(modality, 0.0) * score

            fused_results.append(
                SearchResult(
                    product_id=product_id,
                    score=weighted_score,
                    payload=payload or {},
                    modality_scores=modality_scores,
                    rank=0,  # Will be set after sorting
                )
            )

        # Sort by score and assign ranks
        fused_results.sort(key=lambda x: x.score, reverse=True)
        for i, result in enumerate(fused_results):
            result.rank = i + 1

        return fused_results


class ReciprocalRankFusion(FusionStrategy):
    """Reciprocal Rank Fusion (RRF) strategy"""

    def __init__(self, k: int = 60):
        """
        Args:
            k: Constant for RRF formula (default: 60)
        """
        self.k = k

    def fuse(
        self,
        results_by_modality: Dict[str, List[ScoredPoint]],
        weights: Optional[Dict[str, float]] = None,
    ) -> List[SearchResult]:
        """
        Combine results using Reciprocal Rank Fusion

        Formula: RRF(d) = Σ(1 / (k + rank_i(d)))

        Benefits:
        - No score normalization needed
        - Robust to score scale differences
        - No hyperparameter tuning required
        """
        if weights is None:
            weights = {mod: 1.0 for mod in results_by_modality}

        # Build rank maps for each modality
        rank_maps = {}
        for modality, results in results_by_modality.items():
            rank_map = {}
            for rank, result in enumerate(results, start=1):
                rank_map[result.id] = rank
            rank_maps[modality] = rank_map

        # Collect all product IDs
        all_product_ids = set()
        for results in results_by_modality.values():
            for result in results:
                all_product_ids.add(result.id)

        # Compute RRF scores
        fused_results = []
        for product_id in all_product_ids:
            rrf_score = 0.0
            modality_scores = {}
            payload = None

            for modality, rank_map in rank_maps.items():
                if product_id in rank_map:
                    rank = rank_map[product_id]
                    rrf_contribution = 1.0 / (self.k + rank)
                    modality_scores[modality] = rrf_contribution
                    rrf_score += weights.get(modality, 1.0) * rrf_contribution

                    # Get payload
                    if payload is None:
                        for result in results_by_modality[modality]:
                            if result.id == product_id:
                                payload = result.payload or {}
                                break
                else:
                    modality_scores[modality] = 0.0

            fused_results.append(
                SearchResult(
                    product_id=product_id,
                    score=rrf_score,
                    payload=payload or {},
                    modality_scores=modality_scores,
                    rank=0,
                )
            )

        # Sort and assign ranks
        fused_results.sort(key=lambda x: x.score, reverse=True)
        for i, result in enumerate(fused_results):
            result.rank = i + 1

        return fused_results


class LearnedFusion(FusionStrategy):
    """
    Learned fusion strategy using ML model

    Note: Requires training data with relevance labels
    Currently returns weighted fusion as placeholder
    """

    def __init__(self, model_path: Optional[Path] = None):
        """
        Args:
            model_path: Path to trained fusion model
        """
        self.model_path = model_path
        self.model = None

        if model_path and model_path.exists():
            logger.info(f"Loading fusion model from {model_path}")
            # TODO: Load trained model
        else:
            logger.warning("No fusion model provided, using weighted fusion")

    def fuse(
        self,
        results_by_modality: Dict[str, List[ScoredPoint]],
        weights: Optional[Dict[str, float]] = None,
    ) -> List[SearchResult]:
        """
        Use ML model to predict optimal fusion

        Falls back to weighted fusion if no model trained
        """
        if self.model is None:
            logger.debug("Using weighted fusion fallback")
            return WeightedFusion().fuse(results_by_modality, weights)

        # TODO: Implement learned fusion with trained model
        # Features: [score_text, score_image, score_shape, rank_text, ...]
        # Target: relevance label or click-through rate

        return WeightedFusion().fuse(results_by_modality, weights)


class HybridSearchEngine:
    """
    Hybrid Search Engine for Multi-Modal RAG

    Combines text, image, and shape vectors with configurable fusion strategies
    """

    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str = "products_multimodal",
        fusion_strategy: Literal["weighted", "rrf", "learned"] = "rrf",
        rrf_k: int = 60,
    ):
        """
        Initialize Hybrid Search Engine

        Args:
            qdrant_client: Qdrant client instance
            collection_name: Collection name
            fusion_strategy: Fusion strategy ("weighted", "rrf", "learned")
            rrf_k: RRF constant (only for RRF strategy)
        """
        self.client = qdrant_client
        self.collection_name = collection_name

        # Initialize fusion strategy
        if fusion_strategy == "weighted":
            self.fusion = WeightedFusion()
        elif fusion_strategy == "rrf":
            self.fusion = ReciprocalRankFusion(k=rrf_k)
        elif fusion_strategy == "learned":
            self.fusion = LearnedFusion()
        else:
            raise ValueError(f"Unknown fusion strategy: {fusion_strategy}")

        self.strategy_name = fusion_strategy

        # Verify collection
        try:
            self.client.get_collection(collection_name)
            logger.info(f"✅ Connected to collection '{collection_name}'")
        except Exception as e:
            raise ValueError(f"Collection '{collection_name}' not found: {e}")

    def search_text(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ScoredPoint]:
        """Search using text embedding"""
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=("text", query_embedding),
            limit=limit,
            query_filter=filters,
        )

    def search_image(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ScoredPoint]:
        """Search using image embedding"""
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=("image", query_embedding),
            limit=limit,
            query_filter=filters,
        )

    def search_shape(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ScoredPoint]:
        """Search using shape embedding"""
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=("shape", query_embedding),
            limit=limit,
            query_filter=filters,
        )

    def search_hybrid(
        self,
        embeddings: Dict[str, List[float]],
        weights: Optional[Dict[str, float]] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        retrieve_limit: int = None,
    ) -> List[SearchResult]:
        """
        Hybrid search across multiple modalities

        Args:
            embeddings: {"text": [...], "image": [...], "shape": [...]}
            weights: Optional weights for each modality
            limit: Number of final results to return
            filters: Qdrant filters to apply
            retrieve_limit: How many results to retrieve per modality (default: limit * 3)

        Returns:
            List of fused SearchResult objects

        Example:
            >>> results = engine.search_hybrid(
            ...     embeddings={"text": text_emb, "image": img_emb},
            ...     weights={"text": 0.6, "image": 0.4},
            ...     limit=10
            ... )
        """
        if not embeddings:
            raise ValueError("At least one embedding must be provided")

        # Default: retrieve 3x more results per modality for better fusion
        if retrieve_limit is None:
            retrieve_limit = limit * 3

        # Search each modality
        results_by_modality = {}

        if "text" in embeddings:
            logger.debug(f"Searching text modality (top {retrieve_limit})")
            results_by_modality["text"] = self.search_text(
                embeddings["text"], limit=retrieve_limit, filters=filters
            )

        if "image" in embeddings:
            logger.debug(f"Searching image modality (top {retrieve_limit})")
            results_by_modality["image"] = self.search_image(
                embeddings["image"], limit=retrieve_limit, filters=filters
            )

        if "shape" in embeddings:
            logger.debug(f"Searching shape modality (top {retrieve_limit})")
            results_by_modality["shape"] = self.search_shape(
                embeddings["shape"], limit=retrieve_limit, filters=filters
            )

        # Fuse results
        logger.debug(f"Fusing results with {self.strategy_name} strategy")
        fused_results = self.fusion.fuse(results_by_modality, weights)

        # Return top-K
        return fused_results[:limit]

    def search_hybrid_with_rerank(
        self,
        embeddings: Dict[str, List[float]],
        query_text: str,
        weights: Optional[Dict[str, float]] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        rerank_top_k: int = 50,
    ) -> List[SearchResult]:
        """
        Hybrid search with cross-encoder re-ranking

        Args:
            embeddings: Embeddings for each modality
            query_text: Original query text for re-ranking
            weights: Modality weights
            limit: Final number of results
            filters: Qdrant filters
            rerank_top_k: Number of candidates to re-rank

        Returns:
            Re-ranked search results
        """
        # Get initial results
        initial_results = self.search_hybrid(
            embeddings=embeddings, weights=weights, limit=rerank_top_k, filters=filters
        )

        # TODO: Implement cross-encoder re-ranking
        # For now, return initial results
        logger.warning("Cross-encoder re-ranking not yet implemented")

        return initial_results[:limit]

    def explain_results(self, results: List[SearchResult], top_k: int = 5) -> Dict[str, Any]:
        """
        Explain fusion results with modality contribution analysis

        Args:
            results: Search results to analyze
            top_k: Number of top results to explain

        Returns:
            Explanation dictionary
        """
        top_results = results[:top_k]

        explanation = {
            "fusion_strategy": self.strategy_name,
            "total_results": len(results),
            "top_k_analyzed": len(top_results),
            "results": [],
        }

        for result in top_results:
            result_info = {
                "rank": result.rank,
                "product_id": result.product_id,
                "final_score": result.score,
                "modality_scores": result.modality_scores,
                "payload": result.payload,
            }

            # Analyze modality contributions
            if result.modality_scores:
                contributions = {}
                total = sum(result.modality_scores.values())
                if total > 0:
                    for modality, score in result.modality_scores.items():
                        contributions[modality] = {
                            "score": score,
                            "contribution_pct": (score / total) * 100,
                        }
                result_info["modality_contributions"] = contributions

            explanation["results"].append(result_info)

        return explanation

    def __repr__(self):
        return (
            f"HybridSearchEngine("
            f"collection='{self.collection_name}', "
            f"strategy='{self.strategy_name}')"
        )
