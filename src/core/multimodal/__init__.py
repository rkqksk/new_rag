"""
Multi-Modal RAG Components
Integrates text, image, and shape embeddings with OCR processing
"""

from .multimodal_embedder import MultiModalEmbeddingService
from .qdrant_uploader import MultiModalQdrantUploader
from .hybrid_search import (
    HybridSearchEngine,
    SearchResult,
    WeightedFusion,
    ReciprocalRankFusion,
    LearnedFusion
)
from .ocr_integration import (
    OCRProcessor,
    OCRMultiModalIntegration,
    OCRResult
)
from .end_to_end_pipeline import (
    EndToEndPipeline,
    PipelineResult
)

# Phase 6: Image and Shape Matching
from .image_matching_service import ImageMatchingService, ImageMatch
from .tri_modal_search_service import (
    TriModalSearchService,
    TriModalMatch,
    SearchQuery
)

__all__ = [
    # Embedding
    'MultiModalEmbeddingService',
    # Qdrant
    'MultiModalQdrantUploader',
    # Search
    'HybridSearchEngine',
    'SearchResult',
    'WeightedFusion',
    'ReciprocalRankFusion',
    'LearnedFusion',
    # OCR
    'OCRProcessor',
    'OCRMultiModalIntegration',
    'OCRResult',
    # Pipeline
    'EndToEndPipeline',
    'PipelineResult',
    # Phase 6: Image and Shape Matching
    'ImageMatchingService',
    'ImageMatch',
    'TriModalSearchService',
    'TriModalMatch',
    'SearchQuery',
]
