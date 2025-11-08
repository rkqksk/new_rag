"""
Intelligent Model Router

Routes queries to the optimal LLM engine (NexaAI or Ollama) based on
query complexity, modality, and performance requirements.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import re
import logging

logger = logging.getLogger(__name__)


class ModelEngine(str, Enum):
    """Available model engines"""
    NEXA = "nexa"
    OLLAMA = "ollama"


class QueryComplexity(BaseModel):
    """Query complexity analysis result"""

    score: float = Field(
        description="Complexity score (0-1)",
        ge=0.0,
        le=1.0
    )
    has_multimodal: bool = Field(
        default=False,
        description="Whether query requires multimodal processing"
    )
    has_reasoning: bool = Field(
        default=False,
        description="Whether query requires complex reasoning"
    )
    entity_count: int = Field(
        default=0,
        description="Number of entities detected"
    )
    token_count: int = Field(
        description="Approximate token count"
    )
    requires_vision: bool = Field(
        default=False,
        description="Whether query requires vision-language model"
    )


class RoutingDecision(BaseModel):
    """Routing decision with reasoning"""

    engine: ModelEngine = Field(
        description="Selected engine"
    )
    model: str = Field(
        description="Specific model to use"
    )
    reason: str = Field(
        description="Reason for this routing decision"
    )
    complexity_score: float = Field(
        description="Query complexity score"
    )
    confidence: float = Field(
        default=1.0,
        description="Confidence in routing decision (0-1)"
    )


class ModelRouter:
    """
    Intelligent Model Selection Router

    Routes queries to the most appropriate engine based on:
    - Query complexity
    - Multimodal requirements
    - Reasoning depth
    - Performance characteristics
    """

    def __init__(
        self,
        simple_threshold: float = 0.3,
        complex_threshold: float = 0.7,
        enable_nexa: bool = True,
        enable_ollama: bool = True
    ):
        """
        Initialize model router

        Args:
            simple_threshold: Threshold for simple queries (< this → simple)
            complex_threshold: Threshold for complex queries (> this → complex)
            enable_nexa: Whether NexaAI engine is available
            enable_ollama: Whether Ollama engine is available
        """
        self.simple_threshold = simple_threshold
        self.complex_threshold = complex_threshold
        self.enable_nexa = enable_nexa
        self.enable_ollama = enable_ollama

        # Routing rules
        self.routing_rules = {
            "simple": {
                "engine": ModelEngine.NEXA,
                "model": "Qwen3-1.7B",
                "description": "Fast inference for simple queries"
            },
            "medium": {
                "engine": ModelEngine.NEXA,
                "model": "Qwen3-VL-4B-Instruct",
                "description": "Balanced performance for medium complexity"
            },
            "complex": {
                "engine": ModelEngine.OLLAMA,
                "model": "qwen2.5:7b-instruct",
                "description": "High quality for complex reasoning"
            },
            "vision": {
                "engine": ModelEngine.NEXA,
                "model": "Qwen3-VL-4B-Instruct",
                "description": "Vision-language processing"
            }
        }

        # Entity extraction patterns
        self.entity_patterns = {
            "capacity": re.compile(r'\d+\s*(ml|ML|L|리터|밀리리터)', re.IGNORECASE),
            "neck": re.compile(r'\d+\s*(파이|Φ|ø|phi)', re.IGNORECASE),
            "material": re.compile(
                r'\b(PP|PE|PET|PETG|PS|HDPE|LDPE|LLDPE|폴리프로필렌|폴리에틸렌)\b',
                re.IGNORECASE
            ),
            "moq": re.compile(r'\d+\s*(개|ea|pcs|개입)', re.IGNORECASE),
            "price": re.compile(r'\d+\s*(원|won|₩)', re.IGNORECASE),
            "color": re.compile(
                r'\b(빨강|파랑|노랑|초록|검정|하양|투명|red|blue|yellow|green|black|white|clear)\b',
                re.IGNORECASE
            )
        }

        # Reasoning keywords (Korean + English)
        self.reasoning_keywords = [
            "왜", "어떻게", "무엇", "비교", "분석", "설명", "차이",
            "why", "how", "what", "compare", "analyze", "explain", "difference"
        ]

        # Multimodal keywords
        self.multimodal_keywords = [
            "이미지", "사진", "그림", "영상", "동영상", "비디오",
            "image", "photo", "picture", "video", "visual"
        ]

        logger.info(
            f"ModelRouter initialized (simple < {simple_threshold}, "
            f"complex > {complex_threshold})"
        )

    def analyze_complexity(self, query: str) -> QueryComplexity:
        """
        Analyze query complexity

        Args:
            query: User query

        Returns:
            QueryComplexity analysis
        """
        # Token count (approximate)
        token_count = len(query.split())

        # Extract entities
        entities = self._extract_entities(query)
        entity_count = len(entities)

        # Check for reasoning keywords
        has_reasoning = any(
            keyword in query.lower()
            for keyword in self.reasoning_keywords
        )

        # Check for multimodal requirements
        has_multimodal = any(
            keyword in query.lower()
            for keyword in self.multimodal_keywords
        )

        # Check if vision-language model is required
        requires_vision = has_multimodal

        # Calculate complexity score
        # Factors:
        # - Token count (20%)
        # - Entity count (30%)
        # - Reasoning requirement (30%)
        # - Multimodal requirement (20%)
        score = (
            0.2 * min(token_count / 100, 1.0) +
            0.3 * min(entity_count / 10, 1.0) +
            0.3 * (1.0 if has_reasoning else 0.0) +
            0.2 * (1.0 if has_multimodal else 0.0)
        )

        complexity = QueryComplexity(
            score=score,
            has_multimodal=has_multimodal,
            has_reasoning=has_reasoning,
            entity_count=entity_count,
            token_count=token_count,
            requires_vision=requires_vision
        )

        logger.debug(
            f"Complexity analysis: score={score:.2f}, "
            f"entities={entity_count}, reasoning={has_reasoning}, "
            f"multimodal={has_multimodal}"
        )

        return complexity

    def route(
        self,
        query: str,
        force_engine: Optional[ModelEngine] = None,
        force_model: Optional[str] = None
    ) -> RoutingDecision:
        """
        Route query to appropriate engine and model

        Args:
            query: User query
            force_engine: Force specific engine (optional)
            force_model: Force specific model (optional)

        Returns:
            RoutingDecision with engine, model, and reasoning
        """
        # Analyze query complexity
        complexity = self.analyze_complexity(query)

        # Handle forced routing
        if force_engine:
            rule = self._get_rule_for_engine(force_engine, complexity)
            return RoutingDecision(
                engine=force_engine,
                model=force_model or rule["model"],
                reason="forced_routing",
                complexity_score=complexity.score,
                confidence=1.0
            )

        # Check engine availability
        if not self.enable_nexa and not self.enable_ollama:
            raise RuntimeError("No LLM engines available")

        # Force NexaAI for vision-language tasks
        if complexity.requires_vision:
            if not self.enable_nexa:
                raise RuntimeError("Vision tasks require NexaAI but it's disabled")

            return RoutingDecision(
                engine=ModelEngine.NEXA,
                model=self.routing_rules["vision"]["model"],
                reason="vision_language_required",
                complexity_score=complexity.score,
                confidence=1.0
            )

        # Route based on complexity score
        if complexity.score < self.simple_threshold:
            # Simple query → NexaAI (fast)
            if self.enable_nexa:
                rule = self.routing_rules["simple"]
                return RoutingDecision(
                    engine=ModelEngine.NEXA,
                    model=rule["model"],
                    reason="simple_query_fast_inference",
                    complexity_score=complexity.score,
                    confidence=0.9
                )
            else:
                # Fallback to Ollama
                rule = self.routing_rules["complex"]
                return RoutingDecision(
                    engine=ModelEngine.OLLAMA,
                    model=rule["model"],
                    reason="nexa_unavailable_fallback",
                    complexity_score=complexity.score,
                    confidence=0.7
                )

        elif complexity.score < self.complex_threshold:
            # Medium complexity → NexaAI (balanced)
            if self.enable_nexa:
                rule = self.routing_rules["medium"]
                return RoutingDecision(
                    engine=ModelEngine.NEXA,
                    model=rule["model"],
                    reason="medium_complexity_balanced",
                    complexity_score=complexity.score,
                    confidence=0.85
                )
            else:
                # Fallback to Ollama
                rule = self.routing_rules["complex"]
                return RoutingDecision(
                    engine=ModelEngine.OLLAMA,
                    model=rule["model"],
                    reason="nexa_unavailable_fallback",
                    complexity_score=complexity.score,
                    confidence=0.7
                )

        else:
            # Complex query → Ollama (high quality)
            if self.enable_ollama:
                rule = self.routing_rules["complex"]
                return RoutingDecision(
                    engine=ModelEngine.OLLAMA,
                    model=rule["model"],
                    reason="complex_reasoning_high_quality",
                    complexity_score=complexity.score,
                    confidence=0.95
                )
            else:
                # Fallback to NexaAI
                rule = self.routing_rules["medium"]
                return RoutingDecision(
                    engine=ModelEngine.NEXA,
                    model=rule["model"],
                    reason="ollama_unavailable_fallback",
                    complexity_score=complexity.score,
                    confidence=0.6
                )

    def _extract_entities(self, query: str) -> List[str]:
        """
        Extract entities from query

        Args:
            query: User query

        Returns:
            List of detected entity types
        """
        entities = []

        for entity_type, pattern in self.entity_patterns.items():
            if pattern.search(query):
                entities.append(entity_type)

        return entities

    def _get_rule_for_engine(
        self,
        engine: ModelEngine,
        complexity: QueryComplexity
    ) -> Dict:
        """
        Get routing rule for specific engine

        Args:
            engine: Target engine
            complexity: Query complexity

        Returns:
            Routing rule dict
        """
        if engine == ModelEngine.NEXA:
            if complexity.requires_vision:
                return self.routing_rules["vision"]
            elif complexity.score < self.simple_threshold:
                return self.routing_rules["simple"]
            else:
                return self.routing_rules["medium"]
        else:  # OLLAMA
            return self.routing_rules["complex"]

    def get_stats(self) -> Dict:
        """
        Get router statistics

        Returns:
            Statistics dict
        """
        return {
            "simple_threshold": self.simple_threshold,
            "complex_threshold": self.complex_threshold,
            "enable_nexa": self.enable_nexa,
            "enable_ollama": self.enable_ollama,
            "routing_rules": self.routing_rules
        }
