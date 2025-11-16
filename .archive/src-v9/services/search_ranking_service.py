"""
Search Ranking Service
Advanced ranking algorithms: BM25, TF-IDF, Learning to Rank
Version: v8.5.0
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import math
from collections import Counter, defaultdict
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with ranking scores"""
    id: str
    content: str
    metadata: Dict[str, Any]
    vector_score: float = 0.0
    bm25_score: float = 0.0
    tf_idf_score: float = 0.0
    final_score: float = 0.0
    rank: int = 0


class SearchRankingService:
    """Advanced search ranking with multiple algorithms"""

    def __init__(
        self,
        k1: float = 1.5,  # BM25 term frequency saturation
        b: float = 0.75,  # BM25 length normalization
        use_idf: bool = True  # Use IDF (Inverse Document Frequency)
    ):
        """
        Initialize search ranking service

        Args:
            k1: BM25 k1 parameter (term frequency saturation)
            b: BM25 b parameter (length normalization)
            use_idf: Whether to use IDF in scoring
        """
        self.k1 = k1
        self.b = b
        self.use_idf = use_idf

        # Document statistics
        self.doc_count = 0
        self.avg_doc_length = 0
        self.doc_frequencies: Dict[str, int] = defaultdict(int)
        self.idf_scores: Dict[str, float] = {}

        logger.info(f"Search ranking service initialized (k1={k1}, b={b})")

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text

        Args:
            text: Input text

        Returns:
            List of tokens
        """
        # Simple tokenization (can be enhanced with NLTK/spaCy)
        text = text.lower()

        # Remove punctuation
        for char in '.,!?;:()[]{}"\'/\\':
            text = text.replace(char, ' ')

        tokens = text.split()
        return [t.strip() for t in tokens if len(t.strip()) > 1]

    def compute_bm25(
        self,
        query_tokens: List[str],
        doc_tokens: List[str],
        doc_length: int,
        avg_doc_length: float
    ) -> float:
        """
        Compute BM25 score

        Args:
            query_tokens: Query tokens
            doc_tokens: Document tokens
            doc_length: Document length
            avg_doc_length: Average document length

        Returns:
            BM25 score
        """
        score = 0.0
        doc_freq = Counter(doc_tokens)

        for token in query_tokens:
            if token not in doc_freq:
                continue

            # Term frequency in document
            tf = doc_freq[token]

            # IDF score
            idf = self.idf_scores.get(token, 0.0) if self.use_idf else 1.0

            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / avg_doc_length))

            score += idf * (numerator / denominator)

        return score

    def compute_tf_idf(
        self,
        query_tokens: List[str],
        doc_tokens: List[str]
    ) -> float:
        """
        Compute TF-IDF score

        Args:
            query_tokens: Query tokens
            doc_tokens: Document tokens

        Returns:
            TF-IDF score
        """
        score = 0.0
        doc_freq = Counter(doc_tokens)
        doc_length = len(doc_tokens)

        if doc_length == 0:
            return 0.0

        for token in query_tokens:
            if token not in doc_freq:
                continue

            # Term frequency (normalized)
            tf = doc_freq[token] / doc_length

            # IDF score
            idf = self.idf_scores.get(token, 0.0)

            score += tf * idf

        return score

    def build_index(self, documents: List[Dict[str, Any]]):
        """
        Build search index with document statistics

        Args:
            documents: List of documents with 'content' field
        """
        logger.info(f"Building search index for {len(documents)} documents")

        self.doc_count = len(documents)

        # Compute document statistics
        total_length = 0
        all_tokens = set()

        for doc in documents:
            content = doc.get('content', '')
            tokens = self.tokenize(content)
            total_length += len(tokens)

            # Track unique terms per document
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_frequencies[token] += 1
                all_tokens.add(token)

        # Average document length
        self.avg_doc_length = total_length / self.doc_count if self.doc_count > 0 else 0

        # Compute IDF scores
        for token in all_tokens:
            df = self.doc_frequencies[token]
            # IDF = log((N - df + 0.5) / (df + 0.5) + 1)
            # Using BM25 IDF variant
            idf = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)
            self.idf_scores[token] = max(0, idf)

        logger.info(f"Index built: {len(all_tokens)} unique terms, avg_length={self.avg_doc_length:.1f}")

    def rank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        vector_scores: Optional[List[float]] = None,
        algorithm: str = 'bm25',
        weights: Optional[Dict[str, float]] = None
    ) -> List[SearchResult]:
        """
        Rank search results using specified algorithm

        Args:
            query: Search query
            results: List of search results
            vector_scores: Optional vector similarity scores
            algorithm: Ranking algorithm (bm25, tfidf, hybrid)
            weights: Optional score weights for hybrid ranking

        Returns:
            Ranked search results
        """
        if not results:
            return []

        query_tokens = self.tokenize(query)

        # Default weights for hybrid ranking
        if weights is None:
            weights = {
                'vector': 0.5,
                'bm25': 0.3,
                'tfidf': 0.2,
            }

        ranked_results = []

        for i, result in enumerate(results):
            content = result.get('content', '')
            doc_tokens = self.tokenize(content)
            doc_length = len(doc_tokens)

            # Initialize search result
            search_result = SearchResult(
                id=result.get('id', str(i)),
                content=content,
                metadata=result.get('metadata', {}),
                vector_score=vector_scores[i] if vector_scores and i < len(vector_scores) else 0.0
            )

            # Compute BM25 score
            if algorithm in ['bm25', 'hybrid']:
                search_result.bm25_score = self.compute_bm25(
                    query_tokens,
                    doc_tokens,
                    doc_length,
                    self.avg_doc_length
                )

            # Compute TF-IDF score
            if algorithm in ['tfidf', 'hybrid']:
                search_result.tf_idf_score = self.compute_tf_idf(
                    query_tokens,
                    doc_tokens
                )

            # Compute final score
            if algorithm == 'bm25':
                search_result.final_score = search_result.bm25_score
            elif algorithm == 'tfidf':
                search_result.final_score = search_result.tf_idf_score
            elif algorithm == 'hybrid':
                search_result.final_score = (
                    weights.get('vector', 0) * search_result.vector_score +
                    weights.get('bm25', 0) * search_result.bm25_score +
                    weights.get('tfidf', 0) * search_result.tf_idf_score
                )
            else:
                # Default to vector score
                search_result.final_score = search_result.vector_score

            ranked_results.append(search_result)

        # Sort by final score (descending)
        ranked_results.sort(key=lambda x: x.final_score, reverse=True)

        # Assign ranks
        for rank, result in enumerate(ranked_results, 1):
            result.rank = rank

        logger.info(f"Ranked {len(ranked_results)} results using {algorithm}")

        return ranked_results

    def rerank_with_features(
        self,
        query: str,
        results: List[SearchResult],
        feature_extractors: Optional[List[callable]] = None
    ) -> List[SearchResult]:
        """
        Re-rank results using feature-based learning-to-rank

        Args:
            query: Search query
            results: Initial search results
            feature_extractors: List of feature extraction functions

        Returns:
            Re-ranked results
        """
        if not results:
            return []

        # Default feature extractors
        if feature_extractors is None:
            feature_extractors = [
                self._extract_query_term_coverage,
                self._extract_position_bias,
                self._extract_freshness_score,
                self._extract_popularity_score,
            ]

        query_tokens = self.tokenize(query)

        # Extract features for each result
        for result in results:
            features = []
            for extractor in feature_extractors:
                feature_value = extractor(query, query_tokens, result)
                features.append(feature_value)

            # Simple weighted combination (can be replaced with ML model)
            # Weights: [term_coverage, position_bias, freshness, popularity]
            weights = [0.4, 0.1, 0.2, 0.3]
            rerank_score = sum(f * w for f, w in zip(features, weights))

            # Combine with original score
            result.final_score = 0.7 * result.final_score + 0.3 * rerank_score

        # Re-sort
        results.sort(key=lambda x: x.final_score, reverse=True)

        # Update ranks
        for rank, result in enumerate(results, 1):
            result.rank = rank

        logger.info(f"Re-ranked {len(results)} results with features")

        return results

    def _extract_query_term_coverage(
        self,
        query: str,
        query_tokens: List[str],
        result: SearchResult
    ) -> float:
        """Extract query term coverage feature"""
        doc_tokens = set(self.tokenize(result.content))
        query_token_set = set(query_tokens)

        if not query_token_set:
            return 0.0

        covered = len(query_token_set.intersection(doc_tokens))
        coverage = covered / len(query_token_set)

        return coverage

    def _extract_position_bias(
        self,
        query: str,
        query_tokens: List[str],
        result: SearchResult
    ) -> float:
        """Extract position bias feature (decay by rank)"""
        # Simple position decay: 1 / log(rank + 1)
        if result.rank == 0:
            return 1.0

        return 1.0 / math.log2(result.rank + 1)

    def _extract_freshness_score(
        self,
        query: str,
        query_tokens: List[str],
        result: SearchResult
    ) -> float:
        """Extract freshness score feature"""
        # Check if metadata has timestamp
        created_at = result.metadata.get('created_at')
        updated_at = result.metadata.get('updated_at')

        if not created_at and not updated_at:
            return 0.5  # Neutral score

        # Use most recent timestamp
        timestamp_str = updated_at or created_at

        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            now = datetime.now()
            age_days = (now - timestamp).days

            # Exponential decay: exp(-age_days / 30)
            freshness = math.exp(-age_days / 30)
            return freshness

        except Exception:
            return 0.5

    def _extract_popularity_score(
        self,
        query: str,
        query_tokens: List[str],
        result: SearchResult
    ) -> float:
        """Extract popularity score feature"""
        # Check for popularity indicators in metadata
        views = result.metadata.get('views', 0)
        clicks = result.metadata.get('clicks', 0)
        likes = result.metadata.get('likes', 0)

        # Normalize popularity (simple heuristic)
        popularity = math.log1p(views + clicks * 2 + likes * 3)

        # Normalize to 0-1 range (assuming max popularity ~ 1000)
        normalized = min(1.0, popularity / math.log1p(1000))

        return normalized

    def explain_ranking(self, result: SearchResult) -> Dict[str, Any]:
        """
        Explain ranking for a result

        Args:
            result: Search result

        Returns:
            Explanation dictionary
        """
        return {
            'id': result.id,
            'rank': result.rank,
            'final_score': round(result.final_score, 4),
            'scores': {
                'vector': round(result.vector_score, 4),
                'bm25': round(result.bm25_score, 4),
                'tfidf': round(result.tf_idf_score, 4),
            },
            'content_preview': result.content[:100] + '...' if len(result.content) > 100 else result.content
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            'doc_count': self.doc_count,
            'avg_doc_length': round(self.avg_doc_length, 2),
            'unique_terms': len(self.idf_scores),
            'top_idf_terms': sorted(
                self.idf_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }


# Singleton instance
_search_ranking_service = None


def get_search_ranking_service(
    k1: float = 1.5,
    b: float = 0.75
) -> SearchRankingService:
    """Get search ranking service singleton"""
    global _search_ranking_service
    if _search_ranking_service is None:
        _search_ranking_service = SearchRankingService(k1=k1, b=b)
    return _search_ranking_service
