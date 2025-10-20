"""
Intent Detector - Multi-label Intent Classification

Provides production-ready multi-label intent detection using pattern matching
and semantic analysis.

Features:
- Multi-label intent detection (6 intent types)
- Keyword-based pattern matching
- Semantic similarity scoring
- Confidence thresholding
- Redis caching

Usage:
    detector = IntentDetector(redis_client=redis_client)
    intent = await detector.detect("I need help fixing this error")
    print(intent.primary_intent)  # Intent.PROBLEM_SOLVING
"""

import hashlib
import logging
import re
from typing import Dict, List, Optional

from sentence_transformers import SentenceTransformer
from redis.asyncio import Redis
import numpy as np

from app.rag_consultation.models import Intent, IntentDetection

logger = logging.getLogger(__name__)


class IntentDetector:
    """Multi-label intent detector with pattern matching and semantic analysis.

    Detects user intents using keyword patterns and semantic similarity.
    Supports multiple simultaneous intents with confidence scores.

    Attributes:
        model: Sentence transformer model for semantic analysis
        redis_client: Optional Redis client for caching
        intent_threshold: Minimum confidence for intent detection
        cache_ttl: Cache expiration time in seconds
    """

    # Intent detection patterns (keywords and phrases)
    INTENT_PATTERNS: Dict[Intent, List[str]] = {
        Intent.INFORMATION_SEEKING: [
            r"\b(what|who|where|when|which|define|explain|tell me|show me)\b",
            r"\b(information|details|data|facts|documentation)\b",
            r"\b(is|are|does|can|will|would)\b.*\?",
        ],
        Intent.PROBLEM_SOLVING: [
            r"\b(fix|solve|resolve|debug|troubleshoot|error|issue|problem)\b",
            r"\b(not working|failing|broken|bug|crash)\b",
            r"\b(help|assist|support)\b.*\b(with|in|for)\b",
        ],
        Intent.DECISION_MAKING: [
            r"\b(choose|select|decide|pick|recommend|suggest)\b",
            r"\b(should|would|could|better|best|optimal)\b",
            r"\b(which|what).*\b(option|choice|alternative|approach)\b",
        ],
        Intent.LEARNING: [
            r"\b(learn|understand|study|know|tutorial|guide|teach)\b",
            r"\b(how to|how does|how can|explain how)\b",
            r"\b(example|demonstration|walkthrough|step-by-step)\b",
        ],
        Intent.VALIDATION: [
            r"\b(correct|right|accurate|valid|verify|confirm|check)\b",
            r"\b(is this|am I|are we).*\b(correct|right|wrong)\b",
            r"\b(make sure|ensure|validate)\b",
        ],
        Intent.CLARIFICATION: [
            r"\b(clarify|elaborate|more detail|specify|what do you mean)\b",
            r"\b(confused|unclear|don't understand|not clear)\b",
            r"\b(can you explain|could you clarify)\b",
        ],
    }

    # Prototype sentences for semantic similarity
    INTENT_PROTOTYPES: Dict[Intent, List[str]] = {
        Intent.INFORMATION_SEEKING: [
            "What is this feature?",
            "Tell me about the system",
            "Show me the documentation",
        ],
        Intent.PROBLEM_SOLVING: [
            "How do I fix this error?",
            "The system is not working",
            "Help me debug this issue",
        ],
        Intent.DECISION_MAKING: [
            "Which approach should I use?",
            "What's the best option?",
            "Recommend a solution",
        ],
        Intent.LEARNING: [
            "How does this work?",
            "Teach me about X",
            "I want to learn this concept",
        ],
        Intent.VALIDATION: [
            "Is this correct?",
            "Verify my approach",
            "Am I doing this right?",
        ],
        Intent.CLARIFICATION: [
            "What do you mean?",
            "Can you elaborate?",
            "I don't understand",
        ],
    }

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        redis_client: Optional[Redis] = None,
        intent_threshold: float = 0.3,
        cache_ttl: int = 3600,
    ) -> None:
        """Initialize intent detector.

        Args:
            model_name: Sentence transformer model name
            redis_client: Optional Redis client for caching
            intent_threshold: Minimum confidence threshold
            cache_ttl: Cache TTL in seconds
        """
        self.model_name = model_name
        self.redis_client = redis_client
        self.intent_threshold = intent_threshold
        self.cache_ttl = cache_ttl

        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded intent detection model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}") from e

        # Pre-compute prototype embeddings
        self._prototype_embeddings = self._compute_prototype_embeddings()
        logger.info("Intent detector initialized successfully")

    def _compute_prototype_embeddings(self) -> Dict[Intent, np.ndarray]:
        """Compute prototype embeddings for each intent.

        Returns:
            Dictionary mapping intents to mean prototype embeddings
        """
        embeddings = {}
        for intent, prototypes in self.INTENT_PROTOTYPES.items():
            try:
                prototype_embeds = self.model.encode(prototypes)
                embeddings[intent] = np.mean(prototype_embeds, axis=0)
            except Exception as e:
                logger.error(f"Failed to compute embeddings for {intent}: {e}")
                embeddings[intent] = np.zeros(
                    self.model.get_sentence_embedding_dimension()
                )
        return embeddings

    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for query.

        Args:
            query: User query

        Returns:
            Cache key string
        """
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return f"intent_detection:{query_hash}"

    async def _get_cached_result(self, query: str) -> Optional[IntentDetection]:
        """Retrieve cached intent detection result.

        Args:
            query: User query

        Returns:
            Cached IntentDetection if available
        """
        if not self.redis_client:
            return None

        try:
            cache_key = self._get_cache_key(query)
            cached = await self.redis_client.get(cache_key)
            if cached:
                return IntentDetection.model_validate_json(cached)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")

        return None

    async def _cache_result(self, query: str, detection: IntentDetection) -> None:
        """Cache intent detection result.

        Args:
            query: User query
            detection: Detection result
        """
        if not self.redis_client:
            return

        try:
            cache_key = self._get_cache_key(query)
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                detection.model_dump_json(),
            )
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    def _compute_pattern_scores(self, query: str) -> Dict[Intent, float]:
        """Compute intent scores based on pattern matching.

        Args:
            query: User query

        Returns:
            Dictionary mapping intents to pattern match scores
        """
        scores = {}
        query_lower = query.lower()

        for intent, patterns in self.INTENT_PATTERNS.items():
            match_count = 0
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    match_count += 1

            # Normalize by number of patterns
            scores[intent] = match_count / len(patterns)

        return scores

    def _compute_semantic_scores(
        self,
        query_embedding: np.ndarray,
    ) -> Dict[Intent, float]:
        """Compute intent scores based on semantic similarity.

        Args:
            query_embedding: Query embedding vector

        Returns:
            Dictionary mapping intents to semantic similarity scores
        """
        scores = {}
        for intent, prototype_embedding in self._prototype_embeddings.items():
            similarity = np.dot(query_embedding, prototype_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(prototype_embedding)
            )
            # Normalize to 0-1 range
            scores[intent] = float((similarity + 1) / 2)

        return scores

    async def detect(self, query: str) -> IntentDetection:
        """Detect intents from user query.

        Args:
            query: User query string

        Returns:
            IntentDetection with detected intents and scores

        Raises:
            ValueError: If query is empty
            RuntimeError: If detection fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        query = query.strip()

        # Check cache
        cached_result = await self._get_cached_result(query)
        if cached_result:
            return cached_result

        try:
            # Compute pattern-based scores
            pattern_scores = self._compute_pattern_scores(query)

            # Compute semantic scores
            query_embedding = self.model.encode(query)
            semantic_scores = self._compute_semantic_scores(query_embedding)

            # Combine scores (weighted average)
            combined_scores = {}
            for intent in Intent:
                combined_scores[intent] = (
                    0.6 * semantic_scores[intent] + 0.4 * pattern_scores[intent]
                )

            # Filter intents above threshold
            detected_intents = {
                intent: score
                for intent, score in combined_scores.items()
                if score >= self.intent_threshold
            }

            # If no intents detected, use highest scoring intent
            if not detected_intents:
                primary_intent = max(combined_scores.items(), key=lambda x: x[1])[0]
                detected_intents = {primary_intent: combined_scores[primary_intent]}
            else:
                primary_intent = max(detected_intents.items(), key=lambda x: x[1])[0]

            # Create detection result
            detection = IntentDetection(
                intents=detected_intents,
                primary_intent=primary_intent,
            )

            # Cache result
            await self._cache_result(query, detection)

            logger.info(
                f"Detected intents: {[i.value for i in detected_intents.keys()]}"
            )

            return detection

        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            raise RuntimeError(f"Detection error: {e}") from e
