"""
Advanced RAG Integration (Phase 5)
Multi-collection search, parallel processing, score normalization, and intelligent routing
"""

from .unified_vector_store import UnifiedVectorStore, CollectionConfig
from .multi_source_search_service import (
    MultiSourceSearchService,
    SearchSource,
    SearchResult,
    ScoreNormalizer
)

__all__ = [
    # Vector Store
    "UnifiedVectorStore",
    "CollectionConfig",

    # Multi-Source Search
    "MultiSourceSearchService",
    "SearchSource",
    "SearchResult",
    "ScoreNormalizer",
]
