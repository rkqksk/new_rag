"""
Score Normalization for Multi-Collection Search
Normalizes scores from different collections for fair comparison
"""

import logging
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class ScoreNormalizer:
    """
    Normalize scores from multiple collections

    Methods:
    - min-max normalization
    - z-score normalization
    - sigmoid normalization
    """

    def __init__(self, method: str = 'minmax'):
        """
        Initialize score normalizer

        Args:
            method: Normalization method ('minmax', 'zscore', 'sigmoid')
        """
        self.method = method

    def normalize(
        self,
        results_by_collection: Dict[str, List[Any]],
        score_attr: str = 'score'
    ) -> Dict[str, List[Any]]:
        """
        Normalize scores across collections

        Args:
            results_by_collection: {collection_name: [results]}
            score_attr: Attribute name for score

        Returns:
            Normalized results
        """
        if self.method == 'minmax':
            return self._normalize_minmax(results_by_collection, score_attr)
        elif self.method == 'zscore':
            return self._normalize_zscore(results_by_collection, score_attr)
        elif self.method == 'sigmoid':
            return self._normalize_sigmoid(results_by_collection, score_attr)
        else:
            raise ValueError(f"Unknown normalization method: {self.method}")

    def _normalize_minmax(
        self,
        results_by_collection: Dict[str, List[Any]],
        score_attr: str
    ) -> Dict[str, List[Any]]:
        """Min-max normalization to [0, 1]"""
        normalized = {}

        for collection_name, results in results_by_collection.items():
            if not results:
                normalized[collection_name] = []
                continue

            # Get scores
            scores = [getattr(r, score_attr) for r in results]

            # Min-max normalization
            min_score = min(scores)
            max_score = max(scores)

            if max_score == min_score:
                # All scores are the same
                norm_scores = [1.0] * len(scores)
            else:
                norm_scores = [
                    (s - min_score) / (max_score - min_score)
                    for s in scores
                ]

            # Update results
            norm_results = []
            for result, norm_score in zip(results, norm_scores):
                result_copy = result
                setattr(result_copy, score_attr, norm_score)
                norm_results.append(result_copy)

            normalized[collection_name] = norm_results

        return normalized

    def _normalize_zscore(
        self,
        results_by_collection: Dict[str, List[Any]],
        score_attr: str
    ) -> Dict[str, List[Any]]:
        """Z-score normalization"""
        normalized = {}

        for collection_name, results in results_by_collection.items():
            if not results:
                normalized[collection_name] = []
                continue

            # Get scores
            scores = np.array([getattr(r, score_attr) for r in results])

            # Z-score normalization
            mean = np.mean(scores)
            std = np.std(scores)

            if std == 0:
                norm_scores = [0.0] * len(scores)
            else:
                norm_scores = [(s - mean) / std for s in scores]

            # Update results
            norm_results = []
            for result, norm_score in zip(results, norm_scores):
                result_copy = result
                setattr(result_copy, score_attr, norm_score)
                norm_results.append(result_copy)

            normalized[collection_name] = norm_results

        return normalized

    def _normalize_sigmoid(
        self,
        results_by_collection: Dict[str, List[Any]],
        score_attr: str
    ) -> Dict[str, List[Any]]:
        """Sigmoid normalization"""
        normalized = {}

        for collection_name, results in results_by_collection.items():
            if not results:
                normalized[collection_name] = []
                continue

            # Get scores
            scores = [getattr(r, score_attr) for r in results]

            # Sigmoid normalization
            norm_scores = [1.0 / (1.0 + np.exp(-s)) for s in scores]

            # Update results
            norm_results = []
            for result, norm_score in zip(results, norm_scores):
                result_copy = result
                setattr(result_copy, score_attr, norm_score)
                norm_results.append(result_copy)

            normalized[collection_name] = norm_results

        return normalized
