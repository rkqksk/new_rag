"""
Advanced RAG Integration (Phase 5)
Multi-collection search, parallel processing, score normalization, and intelligent routing
"""

from .integrated_rag_pipeline import IntegratedRAGPipeline, RAGResponse
from .multi_source_search_service import (
    MultiSourceSearchService,
    ScoreNormalizer,
    SearchResult,
    SearchSource,
)
from .query_router import AdvancedQueryRouter, QueryIntent, QueryType
from .score_fusion import FusionResult, FusionStrategy, ScoreFusion
from .unified_vector_store import CollectionConfig, UnifiedVectorStore

__all__ = [
    # Vector Store
    "UnifiedVectorStore",
    "CollectionConfig",
    # Multi-Source Search
    "MultiSourceSearchService",
    "SearchSource",
    "SearchResult",
    "ScoreNormalizer",
    # Query Routing
    "AdvancedQueryRouter",
    "QueryIntent",
    "QueryType",
    # Score Fusion
    "ScoreFusion",
    "FusionStrategy",
    "FusionResult",
    # Integrated Pipeline
    "IntegratedRAGPipeline",
    "RAGResponse",
]
