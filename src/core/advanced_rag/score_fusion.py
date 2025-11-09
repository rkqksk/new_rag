"""
Enhanced Score Fusion Strategies for Phase 5.3
Advanced methods for combining scores from multiple sources
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class FusionStrategy(Enum):
    """Score fusion strategies"""

    WEIGHTED_SUM = "weighted_sum"  # Simple weighted average
    RRF = "reciprocal_rank_fusion"  # Rank-based fusion
    BORDA_COUNT = "borda_count"  # Voting-based
    CONDORCET = "condorcet"  # Pairwise comparison
    CombSUM = "comb_sum"  # Unnormalized sum
    CombMNZ = "comb_mnz"  # Multiply by number of non-zero
    LEARNED = "learned"  # ML-based (future)


@dataclass
class FusionResult:
    """Fusion result with scores"""

    item_id: str
    final_score: float
    source_scores: Dict[str, float]  # {source: score}
    rank: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class ScoreFusion:
    """
    Advanced Score Fusion Engine

    Implements multiple fusion strategies for combining scores from
    different sources (collections)

    Strategies:
    1. Weighted Sum: w1*score1 + w2*score2 + ...
    2. RRF: 1/(k + rank_i) for each source
    3. Borda Count: Points based on ranking position
    4. CombSUM: Simple sum of scores
    5. CombMNZ: Sum multiplied by number of non-zero scores

    Example:
        >>> fusion = ScoreFusion(strategy=FusionStrategy.RRF)
        >>> results = fusion.fuse_scores(source_results, weights)
    """

    def __init__(
        self,
        strategy: FusionStrategy = FusionStrategy.WEIGHTED_SUM,
        rrf_k: float = 60,
        normalize_before_fusion: bool = True,
    ):
        """
        Initialize Score Fusion Engine

        Args:
            strategy: Fusion strategy to use
            rrf_k: Constant for RRF (default: 60)
            normalize_before_fusion: Normalize scores before fusion
        """
        self.strategy = strategy
        self.rrf_k = rrf_k
        self.normalize_before_fusion = normalize_before_fusion

        logger.info(f"✅ ScoreFusion initialized (strategy: {strategy.value})")

    def fuse_scores(
        self,
        source_results: Dict[str, List[Dict[str, Any]]],
        weights: Optional[Dict[str, float]] = None,
    ) -> List[FusionResult]:
        """
        Fuse scores from multiple sources

        Args:
            source_results: Dict of {source_name: [results]}
                Each result: {"id": str, "score": float, "payload": dict}
            weights: Optional weights for each source (for weighted strategies)

        Returns:
            List of FusionResult sorted by final_score (descending)

        Example:
            >>> source_results = {
            ...     "products": [
            ...         {"id": "P1", "score": 0.9, "payload": {...}},
            ...         {"id": "P2", "score": 0.8, "payload": {...}}
            ...     ],
            ...     "documents": [
            ...         {"id": "P1", "score": 0.7, "payload": {...}},
            ...         {"id": "D1", "score": 0.85, "payload": {...}}
            ...     ]
            ... }
            >>> weights = {"products": 0.6, "documents": 0.4}
            >>> results = fusion.fuse_scores(source_results, weights)
        """
        # Normalize weights
        if weights is None:
            weights = {src: 1.0 / len(source_results) for src in source_results.keys()}
        else:
            # Normalize to sum to 1.0
            total = sum(weights.values())
            weights = {k: v / total for k, v in weights.items()}

        # Normalize scores if needed
        if self.normalize_before_fusion:
            source_results = self._normalize_all_scores(source_results)

        # Apply fusion strategy
        if self.strategy == FusionStrategy.WEIGHTED_SUM:
            fused = self._weighted_sum(source_results, weights)
        elif self.strategy == FusionStrategy.RRF:
            fused = self._reciprocal_rank_fusion(source_results)
        elif self.strategy == FusionStrategy.BORDA_COUNT:
            fused = self._borda_count(source_results)
        elif self.strategy == FusionStrategy.CombSUM:
            fused = self._comb_sum(source_results)
        elif self.strategy == FusionStrategy.CombMNZ:
            fused = self._comb_mnz(source_results)
        else:
            logger.warning(f"Unknown strategy {self.strategy}, using weighted_sum")
            fused = self._weighted_sum(source_results, weights)

        # Sort by final score
        fused.sort(key=lambda x: x.final_score, reverse=True)

        # Assign ranks
        for rank, result in enumerate(fused, start=1):
            result.rank = rank

        logger.debug(f"Fused {len(fused)} results using {self.strategy.value}")

        return fused

    def _normalize_all_scores(
        self, source_results: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Normalize scores within each source to [0, 1]"""
        normalized = {}

        for source, results in source_results.items():
            if not results:
                normalized[source] = []
                continue

            scores = [r["score"] for r in results]
            min_score = min(scores)
            max_score = max(scores)

            if max_score == min_score:
                # All same score
                norm_results = [{**r, "score": 1.0} for r in results]
            else:
                norm_results = [
                    {**r, "score": (r["score"] - min_score) / (max_score - min_score)}
                    for r in results
                ]

            normalized[source] = norm_results

        return normalized

    def _weighted_sum(
        self, source_results: Dict[str, List[Dict[str, Any]]], weights: Dict[str, float]
    ) -> List[FusionResult]:
        """
        Weighted Sum Fusion

        Formula: final_score = Σ(weight_i * score_i)
        """
        # Collect all unique item IDs
        all_ids = set()
        for results in source_results.values():
            all_ids.update(r["id"] for r in results)

        # Build score map: {source: {id: score}}
        score_map = {}
        for source, results in source_results.items():
            score_map[source] = {r["id"]: r["score"] for r in results}

        # Compute weighted sum for each item
        fused = []
        for item_id in all_ids:
            source_scores = {}
            weighted_sum = 0.0

            for source, weight in weights.items():
                score = score_map.get(source, {}).get(item_id, 0.0)
                source_scores[source] = score
                weighted_sum += weight * score

            fused.append(
                FusionResult(item_id=item_id, final_score=weighted_sum, source_scores=source_scores)
            )

        return fused

    def _reciprocal_rank_fusion(
        self, source_results: Dict[str, List[Dict[str, Any]]]
    ) -> List[FusionResult]:
        """
        Reciprocal Rank Fusion (RRF)

        Formula: RRF(d) = Σ 1 / (k + rank_i(d))
        where k is a constant (default: 60)

        Paper: "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods"
        """
        # Collect all unique item IDs
        all_ids = set()
        for results in source_results.values():
            all_ids.update(r["id"] for r in results)

        # Build rank map: {source: {id: rank}}
        rank_map = {}
        for source, results in source_results.items():
            # Sort by score descending
            sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
            rank_map[source] = {r["id"]: rank for rank, r in enumerate(sorted_results, start=1)}

        # Compute RRF score for each item
        fused = []
        for item_id in all_ids:
            source_scores = {}
            rrf_score = 0.0

            for source, ranks in rank_map.items():
                if item_id in ranks:
                    rank = ranks[item_id]
                    score = 1.0 / (self.rrf_k + rank)
                    source_scores[source] = score
                    rrf_score += score
                else:
                    source_scores[source] = 0.0

            fused.append(
                FusionResult(item_id=item_id, final_score=rrf_score, source_scores=source_scores)
            )

        return fused

    def _borda_count(self, source_results: Dict[str, List[Dict[str, Any]]]) -> List[FusionResult]:
        """
        Borda Count Fusion

        Each item gets points based on its rank: (n - rank + 1)
        where n is the total number of items in that source
        """
        all_ids = set()
        for results in source_results.values():
            all_ids.update(r["id"] for r in results)

        # Build rank map with Borda points
        borda_map = {}
        for source, results in source_results.items():
            sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
            n = len(sorted_results)

            borda_map[source] = {
                r["id"]: (n - rank + 1) for rank, r in enumerate(sorted_results, start=1)
            }

        # Compute Borda count for each item
        fused = []
        for item_id in all_ids:
            source_scores = {}
            total_points = 0

            for source, points_map in borda_map.items():
                points = points_map.get(item_id, 0)
                source_scores[source] = points
                total_points += points

            fused.append(
                FusionResult(item_id=item_id, final_score=total_points, source_scores=source_scores)
            )

        return fused

    def _comb_sum(self, source_results: Dict[str, List[Dict[str, Any]]]) -> List[FusionResult]:
        """
        CombSUM: Simple sum of scores

        Formula: final_score = Σ score_i
        """
        all_ids = set()
        for results in source_results.values():
            all_ids.update(r["id"] for r in results)

        score_map = {}
        for source, results in source_results.items():
            score_map[source] = {r["id"]: r["score"] for r in results}

        fused = []
        for item_id in all_ids:
            source_scores = {}
            total_score = 0.0

            for source in source_results.keys():
                score = score_map.get(source, {}).get(item_id, 0.0)
                source_scores[source] = score
                total_score += score

            fused.append(
                FusionResult(item_id=item_id, final_score=total_score, source_scores=source_scores)
            )

        return fused

    def _comb_mnz(self, source_results: Dict[str, List[Dict[str, Any]]]) -> List[FusionResult]:
        """
        CombMNZ: Sum multiplied by number of non-zero scores

        Formula: final_score = (Σ score_i) * number_of_non_zero_scores

        This gives bonus to items that appear in multiple sources
        """
        all_ids = set()
        for results in source_results.values():
            all_ids.update(r["id"] for r in results)

        score_map = {}
        for source, results in source_results.items():
            score_map[source] = {r["id"]: r["score"] for r in results}

        fused = []
        for item_id in all_ids:
            source_scores = {}
            total_score = 0.0
            non_zero_count = 0

            for source in source_results.keys():
                score = score_map.get(source, {}).get(item_id, 0.0)
                source_scores[source] = score

                if score > 0:
                    total_score += score
                    non_zero_count += 1

            # Multiply by number of non-zero sources
            final_score = total_score * non_zero_count if non_zero_count > 0 else 0.0

            fused.append(
                FusionResult(
                    item_id=item_id,
                    final_score=final_score,
                    source_scores=source_scores,
                    metadata={"non_zero_sources": non_zero_count},
                )
            )

        return fused

    def __repr__(self):
        return (
            f"ScoreFusion("
            f"strategy={self.strategy.value}, "
            f"rrf_k={self.rrf_k}, "
            f"normalize={self.normalize_before_fusion})"
        )
