"""
Cross-Encoder Re-Ranking
Improves search result quality by re-ranking with cross-encoder models
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RerankingConfig(BaseModel):
    """Configuration for cross-encoder re-ranking"""

    model_name: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Cross-encoder model name from HuggingFace",
    )
    device: str = Field(
        default="auto", description="Device to use: 'auto', 'cpu', 'cuda', or 'mps'"
    )
    top_k: Optional[int] = Field(
        default=None, description="Number of top results to return after re-ranking"
    )
    batch_size: int = Field(
        default=32, description="Batch size for cross-encoder prediction"
    )


class CrossEncoderReranker:
    """
    Cross-Encoder Re-Ranker for improved search quality

    Uses cross-encoder models to re-rank initial search results
    by computing query-document relevance scores.

    Models:
    - cross-encoder/ms-marco-MiniLM-L-6-v2 (fast, 80MB)
    - cross-encoder/ms-marco-MiniLM-L-12-v2 (better, 120MB)
    """

    def __init__(
        self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", device: str = "auto"
    ):
        """
        Initialize cross-encoder re-ranker

        Args:
            model_name: Cross-encoder model name
            device: Device to use ('auto', 'cpu', 'cuda', 'mps')
        """
        self.model_name = model_name
        self.device = device
        self.model = None

        # Try to import sentence-transformers
        try:
            from sentence_transformers import CrossEncoder

            self.CrossEncoder = CrossEncoder
            self.available = True
        except ImportError:
            logger.warning("sentence-transformers not installed")
            self.available = False
            self.CrossEncoder = None

        # Initialize model
        if self.available:
            self._init_model()

    def _init_model(self):
        """Initialize cross-encoder model"""
        try:
            import torch

            # Auto-detect device
            if self.device == "auto":
                if torch.backends.mps.is_available():
                    device = "mps"
                elif torch.cuda.is_available():
                    device = "cuda"
                else:
                    device = "cpu"
            else:
                device = self.device

            logger.info(f"Loading cross-encoder: {self.model_name} on {device}")

            self.model = self.CrossEncoder(self.model_name, device=device)

            logger.info(f"✅ Cross-encoder loaded on {device}")

        except Exception as e:
            logger.error(f"Failed to load cross-encoder: {e}")
            self.available = False
            self.model = None

    def is_available(self) -> bool:
        """Check if re-ranker is available"""
        return self.available and self.model is not None

    def rerank(
        self, query: str, results: List[Any], top_k: Optional[int] = None, text_field: str = "text"
    ) -> List[Any]:
        """
        Re-rank search results using cross-encoder

        Args:
            query: User query
            results: List of search results
            top_k: Number of top results to return (None = all)
            text_field: Field name containing text in result payload

        Returns:
            Re-ranked results
        """
        if not self.is_available():
            logger.warning("Cross-encoder not available, returning original results")
            return results[:top_k] if top_k else results

        if not results:
            return []

        # Prepare query-document pairs
        pairs = []
        for result in results:
            # Extract text from result
            if hasattr(result, "payload") and text_field in result.payload:
                text = result.payload[text_field]
            elif hasattr(result, text_field):
                text = getattr(result, text_field)
            else:
                # Fallback to product name or description
                text = self._extract_text(result)

            pairs.append([query, text])

        # Get cross-encoder scores
        try:
            scores = self.model.predict(pairs, show_progress_bar=False)
        except Exception as e:
            logger.error(f"Cross-encoder prediction failed: {e}")
            return results[:top_k] if top_k else results

        # Combine results with new scores
        scored_results = []
        for result, score in zip(results, scores):
            # Store original score
            if hasattr(result, "score"):
                result.original_score = result.score
                result.score = float(score)
            elif hasattr(result, "payload"):
                if not hasattr(result, "original_score"):
                    result.original_score = result.payload.get("score", 0.0)
                result.score = float(score)

            result.reranked = True
            scored_results.append((result, float(score)))

        # Sort by new scores (descending)
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # Return top-k
        reranked = [result for result, _ in scored_results]

        if top_k:
            return reranked[:top_k]

        return reranked

    def _extract_text(self, result: Any) -> str:
        """Extract text from result object"""
        # Try common text fields
        text_fields = [
            "text",
            "ocr_text",
            "content",
            "description",
            "product_name",
            "name",
            "title",
            "body",
        ]

        # Check payload
        if hasattr(result, "payload"):
            for field in text_fields:
                if field in result.payload:
                    return str(result.payload[field])

        # Check direct attributes
        for field in text_fields:
            if hasattr(result, field):
                return str(getattr(result, field))

        # Fallback
        return str(result)

    def rerank_with_explanation(
        self, query: str, results: List[Any], top_k: Optional[int] = None
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Re-rank with detailed explanation

        Args:
            query: User query
            results: List of search results
            top_k: Number of top results

        Returns:
            Tuple of (reranked_results, explanation)
        """
        if not self.is_available():
            return results[:top_k] if top_k else results, {"available": False}

        original_order = [getattr(r, "id", i) for i, r in enumerate(results)]

        # Re-rank
        reranked = self.rerank(query, results, top_k=top_k)

        # Build explanation
        explanation = {
            "available": True,
            "model": self.model_name,
            "original_count": len(results),
            "reranked_count": len(reranked),
            "score_changes": [],
        }

        for i, result in enumerate(reranked[:10]):  # Top 10 explanations
            if hasattr(result, "original_score") and hasattr(result, "score"):
                change = {
                    "rank": i + 1,
                    "id": getattr(result, "id", "unknown"),
                    "original_score": float(result.original_score),
                    "reranked_score": float(result.score),
                    "score_diff": float(result.score - result.original_score),
                }
                explanation["score_changes"].append(change)

        return reranked, explanation

    def benchmark_reranking(
        self, query: str, results: List[Any], ground_truth_ids: List[str]
    ) -> Dict[str, float]:
        """
        Benchmark re-ranking quality

        Args:
            query: Query text
            results: Search results
            ground_truth_ids: List of relevant result IDs

        Returns:
            Dictionary with metrics
        """
        if not self.is_available():
            return {"available": False}

        # Get original ranking
        original_ids = [getattr(r, "id", str(i)) for i, r in enumerate(results)]

        # Re-rank
        reranked = self.rerank(query, results)
        reranked_ids = [getattr(r, "id", str(i)) for i, r in enumerate(reranked)]

        # Calculate metrics
        def calculate_metrics(ranking, ground_truth, k=10):
            top_k = ranking[:k]
            relevant_in_top_k = len(set(top_k) & set(ground_truth))

            recall = relevant_in_top_k / len(ground_truth) if ground_truth else 0
            precision = relevant_in_top_k / k if k > 0 else 0

            return {
                "recall@k": recall,
                "precision@k": precision,
                "relevant_in_top_k": relevant_in_top_k,
            }

        original_metrics = calculate_metrics(original_ids, ground_truth_ids)
        reranked_metrics = calculate_metrics(reranked_ids, ground_truth_ids)

        return {
            "available": True,
            "original": original_metrics,
            "reranked": reranked_metrics,
            "improvement": {
                "recall": reranked_metrics["recall@k"] - original_metrics["recall@k"],
                "precision": reranked_metrics["precision@k"] - original_metrics["precision@k"],
            },
        }

    def __repr__(self):
        status = "available" if self.is_available() else "not available"
        return f"CrossEncoderReranker(model={self.model_name}, status={status})"
