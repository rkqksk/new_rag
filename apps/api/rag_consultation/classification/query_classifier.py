"""
Query Classifier - BERT-based Query Type Classification

Provides production-ready query type classification using sentence transformers
with caching and error handling.

Features:
- 7 query type classification (factual, procedural, comparison, etc.)
- BERT-based semantic similarity
- Redis caching for repeated queries
- Configurable confidence thresholds
- Comprehensive error handling

Usage:
    classifier = QueryClassifier(redis_client=redis_client)
    analysis = await classifier.classify("How does RAG work?")
    print(analysis.query_type)  # QueryType.FACTUAL
"""

import hashlib
import logging
from typing import Dict, Optional

import numpy as np
from redis.asyncio import Redis
from sentence_transformers import SentenceTransformer

from apps.api.rag_consultation.models import QueryAnalysis, QueryType

logger = logging.getLogger(__name__)


class QueryClassifier:
    """BERT-based query type classifier with caching.

    Classifies user queries into 7 types using semantic similarity
    to prototype queries for each category.

    Attributes:
        model: Sentence transformer model
        redis_client: Optional Redis client for caching
        confidence_threshold: Minimum confidence for classification
        cache_ttl: Cache expiration time in seconds
    """

    # Prototype queries for each query type
    QUERY_PROTOTYPES: Dict[QueryType, list[str]] = {
        QueryType.FACTUAL: [
            "What is machine learning?",
            "Define neural networks",
            "Explain the concept of RAG",
            "What does this term mean?",
        ],
        QueryType.PROCEDURAL: [
            "How do I configure the system?",
            "Steps to deploy the application",
            "How to set up authentication?",
            "What's the process for installation?",
        ],
        QueryType.COMPARISON: [
            "Difference between X and Y",
            "Compare approach A versus B",
            "Which is better: X or Y?",
            "What are the trade-offs?",
        ],
        QueryType.TROUBLESHOOTING: [
            "Error connecting to database",
            "System is not responding",
            "Why is this failing?",
            "How to fix this bug?",
        ],
        QueryType.RECOMMENDATION: [
            "Best practices for deployment",
            "Suggest an approach for X",
            "What should I use for Y?",
            "Recommend a solution",
        ],
        QueryType.EXPLORATORY: [
            "Tell me about recent advances",
            "What are the possibilities?",
            "Explore options for implementation",
            "Research on topic X",
        ],
        QueryType.CONVERSATIONAL: [
            "Thanks for the help",
            "Can you clarify?",
            "Yes, that makes sense",
            "What did you mean by that?",
        ],
    }

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        redis_client: Optional[Redis] = None,
        confidence_threshold: float = 0.3,
        cache_ttl: int = 3600,
    ) -> None:
        """Initialize query classifier.

        Args:
            model_name: Sentence transformer model name
            redis_client: Optional Redis client for caching
            confidence_threshold: Minimum confidence threshold
            cache_ttl: Cache TTL in seconds

        Raises:
            RuntimeError: If model loading fails
        """
        self.model_name = model_name
        self.redis_client = redis_client
        self.confidence_threshold = confidence_threshold
        self.cache_ttl = cache_ttl

        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded sentence transformer model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise RuntimeError(f"Model loading failed: {e}") from e

        # Pre-compute prototype embeddings
        self._prototype_embeddings = self._compute_prototype_embeddings()
        logger.info("Query classifier initialized successfully")

    def _compute_prototype_embeddings(self) -> Dict[QueryType, np.ndarray]:
        """Compute and cache prototype embeddings for each query type.

        Returns:
            Dictionary mapping query types to mean prototype embeddings
        """
        embeddings = {}
        for query_type, prototypes in self.QUERY_PROTOTYPES.items():
            try:
                prototype_embeds = self.model.encode(prototypes)
                # Use mean embedding as representative
                mean_embedding = np.mean(prototype_embeds, axis=0)
                embeddings[query_type] = mean_embedding
            except Exception as e:
                logger.error(f"Failed to compute embeddings for {query_type}: {e}")
                # Use zero vector as fallback
                embeddings[query_type] = np.zeros(self.model.get_sentence_embedding_dimension())

        return embeddings

    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for query.

        Args:
            query: User query

        Returns:
            Cache key string
        """
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return f"query_classification:{query_hash}"

    async def _get_cached_result(self, query: str) -> Optional[QueryAnalysis]:
        """Retrieve cached classification result.

        Args:
            query: User query

        Returns:
            Cached QueryAnalysis if available, None otherwise
        """
        if not self.redis_client:
            return None

        try:
            cache_key = self._get_cache_key(query)
            cached = await self.redis_client.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return QueryAnalysis.model_validate_json(cached)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")

        return None

    async def _cache_result(self, query: str, analysis: QueryAnalysis) -> None:
        """Cache classification result.

        Args:
            query: User query
            analysis: Classification result
        """
        if not self.redis_client:
            return

        try:
            cache_key = self._get_cache_key(query)
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                analysis.model_dump_json(),
            )
            logger.debug(f"Cached result for query: {query[:50]}...")
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    def _compute_similarity_scores(
        self,
        query_embedding: np.ndarray,
    ) -> Dict[QueryType, float]:
        """Compute cosine similarity scores for all query types.

        Args:
            query_embedding: Query embedding vector

        Returns:
            Dictionary mapping query types to similarity scores
        """
        scores = {}
        for query_type, prototype_embedding in self._prototype_embeddings.items():
            # Cosine similarity
            similarity = np.dot(query_embedding, prototype_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(prototype_embedding)
            )
            # Convert to 0-1 range (cosine similarity is -1 to 1)
            normalized_score = (similarity + 1) / 2
            scores[query_type] = float(normalized_score)

        return scores

    async def classify(self, query: str) -> QueryAnalysis:
        """Classify query into query type.

        Args:
            query: User query string

        Returns:
            QueryAnalysis with classification results

        Raises:
            ValueError: If query is empty
            RuntimeError: If classification fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        query = query.strip()

        # Check cache first
        cached_result = await self._get_cached_result(query)
        if cached_result:
            return cached_result

        try:
            # Compute query embedding
            query_embedding = self.model.encode(query)

            # Compute similarity scores
            scores = self._compute_similarity_scores(query_embedding)

            # Determine primary query type (highest score)
            primary_type = max(scores.items(), key=lambda x: x[1])[0]
            confidence = scores[primary_type]

            # Apply confidence threshold
            if confidence < self.confidence_threshold:
                logger.warning(f"Low confidence ({confidence:.2f}) for query: {query[:50]}...")
                # Default to conversational if confidence is low
                primary_type = QueryType.CONVERSATIONAL

            # Create analysis result
            analysis = QueryAnalysis(
                query=query,
                query_type=primary_type,
                query_type_scores=scores,
                confidence=confidence,
            )

            # Cache result
            await self._cache_result(query, analysis)

            logger.info(
                f"Classified query as {primary_type.value} " f"(confidence: {confidence:.2f})"
            )

            return analysis

        except Exception as e:
            logger.error(f"Query classification failed: {e}")
            raise RuntimeError(f"Classification error: {e}") from e
