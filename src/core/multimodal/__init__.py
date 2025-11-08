"""
Multi-Modal RAG Components
Integrates text, image, and shape embeddings with OCR processing
"""

from .end_to_end_pipeline import EndToEndPipeline, PipelineResult
from .hybrid_search import (
    HybridSearchEngine,
    LearnedFusion,
    ReciprocalRankFusion,
    SearchResult,
    WeightedFusion,
)

# Phase 6: Image and Shape Matching
from .image_matching_service import ImageMatch, ImageMatchingService
from .multimodal_embedder import MultiModalEmbeddingService
from .ocr_integration import OCRMultiModalIntegration, OCRProcessor, OCRResult
from .qdrant_uploader import MultiModalQdrantUploader
from .tri_modal_search_service import SearchQuery, TriModalMatch, TriModalSearchService

__all__ = [
    # Embedding
    "MultiModalEmbeddingService",
    # Qdrant
    "MultiModalQdrantUploader",
    # Search
    "HybridSearchEngine",
    "SearchResult",
    "WeightedFusion",
    "ReciprocalRankFusion",
    "LearnedFusion",
    # OCR
    "OCRProcessor",
    "OCRMultiModalIntegration",
    "OCRResult",
    # Pipeline
    "EndToEndPipeline",
    "PipelineResult",
    # Phase 6: Image and Shape Matching
    "ImageMatchingService",
    "ImageMatch",
    "TriModalSearchService",
    "TriModalMatch",
    "SearchQuery",
]
