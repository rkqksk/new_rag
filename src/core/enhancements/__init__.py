"""
Core Enhancements Module

Advanced features for improving RAG performance:
- Cross-encoder re-ranking for better relevance
- Query routing for intelligent search strategy selection
- Conversation memory for context-aware responses
- A/B testing framework for experimentation
"""

from .cross_encoder_reranker import CrossEncoderReranker, RerankingConfig
from .query_router import QueryRouter, QueryType, SearchStrategy
from .conversation_memory import ConversationMemory, Message, ConversationContext
from .ab_testing import (
    ABTestingFramework,
    Experiment,
    Variant,
    Metric,
    ExperimentStatus,
    FusionStrategy
)

__all__ = [
    # Cross-encoder re-ranking
    'CrossEncoderReranker',
    'RerankingConfig',

    # Query routing
    'QueryRouter',
    'QueryType',
    'SearchStrategy',

    # Conversation memory
    'ConversationMemory',
    'Message',
    'ConversationContext',

    # A/B testing
    'ABTestingFramework',
    'Experiment',
    'Variant',
    'Metric',
    'ExperimentStatus',
    'FusionStrategy'
]
