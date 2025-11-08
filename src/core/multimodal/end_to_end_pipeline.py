"""
End-to-End Multi-Modal RAG Pipeline
Combines OCR → Embeddings → Qdrant → Search
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result from end-to-end pipeline"""

    product_id: str
    success: bool
    ocr_text: str
    embeddings: Dict[str, List[float]]
    metadata: Dict[str, Any]
    error: Optional[str] = None


class EndToEndPipeline:
    """
    Complete Multi-Modal RAG Pipeline

    Workflow:
    1. OCR: Extract text from PDF/image
    2. Embed: Generate text + image embeddings
    3. Upload: Store in Qdrant with named vectors
    4. Search: Hybrid search across modalities

    Example:
        >>> pipeline = EndToEndPipeline(
        ...     ocr_integration=ocr_integration,
        ...     qdrant_uploader=uploader,
        ...     search_engine=engine
        ... )
        >>> # Process and upload
        >>> results = pipeline.process_and_upload(["product1.pdf", "product2.jpg"])
        >>> # Search
        >>> search_results = pipeline.search("100ml bottle")
    """

    def __init__(
        self,
        ocr_integration: Any,  # OCRMultiModalIntegration
        qdrant_uploader: Any,  # MultiModalQdrantUploader
        search_engine: Optional[Any] = None,  # HybridSearchEngine
        auto_commit: bool = True,
    ):
        """
        Initialize end-to-end pipeline

        Args:
            ocr_integration: OCRMultiModalIntegration instance
            qdrant_uploader: MultiModalQdrantUploader instance
            search_engine: Optional HybridSearchEngine for searching
            auto_commit: Automatically commit to Qdrant after each upload
        """
        self.ocr_integration = ocr_integration
        self.uploader = qdrant_uploader
        self.search_engine = search_engine
        self.auto_commit = auto_commit

        logger.info("✅ End-to-end pipeline initialized")

    def process_document(
        self, file_path: Union[str, Path], product_id: Optional[str] = None, upload: bool = True
    ) -> PipelineResult:
        """
        Process single document through full pipeline

        Args:
            file_path: Path to PDF or image
            product_id: Optional product ID (defaults to filename)
            upload: Whether to upload to Qdrant

        Returns:
            PipelineResult with status and data
        """
        file_path = Path(file_path)

        try:
            # Step 1: OCR + Embedding
            logger.info(f"[1/3] Processing document: {file_path.name}")
            result = self.ocr_integration.process_document(file_path, product_id=product_id)

            product_id = result["product_id"]
            embeddings = result["embeddings"]
            metadata = result["metadata"]
            ocr_text = result["ocr_text"]

            # Step 2: Upload to Qdrant (optional)
            if upload:
                logger.info(f"[2/3] Uploading to Qdrant: {product_id}")

                # Prepare payload
                payload = {
                    "product_id": product_id,
                    "source_file": str(file_path),
                    "ocr_text": ocr_text,
                    "ocr_confidence": result["ocr_confidence"],
                    **metadata,
                }

                # Upload with named vectors
                success = self.uploader.upload_product(
                    product_id=product_id,
                    text_embedding=embeddings.get("text"),
                    image_embedding=embeddings.get("image"),
                    shape_embedding=embeddings.get("shape"),
                    payload=payload,
                )

                if not success:
                    raise RuntimeError("Failed to upload to Qdrant")

                logger.info(f"✅ Uploaded: {product_id}")

            # Step 3: Build result
            logger.info(f"[3/3] Complete: {product_id}")

            return PipelineResult(
                product_id=product_id,
                success=True,
                ocr_text=ocr_text,
                embeddings=embeddings,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"❌ Pipeline failed for {file_path}: {e}")

            return PipelineResult(
                product_id=product_id or file_path.stem,
                success=False,
                ocr_text="",
                embeddings={},
                metadata={},
                error=str(e),
            )

    def process_and_upload(
        self,
        file_paths: List[Union[str, Path]],
        product_ids: Optional[List[str]] = None,
        batch_size: int = 10,
        show_progress: bool = True,
    ) -> List[PipelineResult]:
        """
        Process and upload multiple documents in batches

        Args:
            file_paths: List of file paths
            product_ids: Optional list of product IDs
            batch_size: Batch size for uploads
            show_progress: Show progress bar

        Returns:
            List of PipelineResult objects
        """
        results = []

        if product_ids is None:
            product_ids = [None] * len(file_paths)

        # Progress tracking
        iterator = zip(file_paths, product_ids)
        total = len(file_paths)

        if show_progress:
            try:
                from tqdm import tqdm

                iterator = tqdm(iterator, total=total, desc="Processing pipeline")
            except ImportError:
                pass

        # Process each document
        for file_path, product_id in iterator:
            result = self.process_document(file_path, product_id=product_id, upload=True)
            results.append(result)

        # Summary
        successful = sum(1 for r in results if r.success)
        failed = total - successful

        logger.info(f"\n📊 Pipeline Summary:")
        logger.info(f"   Total: {total}")
        logger.info(f"   ✅ Successful: {successful}")
        logger.info(f"   ❌ Failed: {failed}")

        return results

    def search(
        self,
        query: str,
        query_image: Optional[Union[str, Path]] = None,
        fusion_strategy: str = "rrf",
        weights: Optional[Dict[str, float]] = None,
        limit: int = 10,
    ) -> List[Any]:  # List[SearchResult]
        """
        Search using text query and optional image

        Args:
            query: Text query
            query_image: Optional image path
            fusion_strategy: Fusion strategy ("rrf", "weighted", "learned")
            weights: Optional modality weights
            limit: Number of results

        Returns:
            List of SearchResult objects
        """
        if self.search_engine is None:
            raise RuntimeError("Search engine not configured")

        # Generate query embeddings
        embeddings = {}

        # Text embedding
        text_emb = self.ocr_integration.embedder.embed_text(query)
        embeddings["text"] = text_emb

        # Image embedding (optional)
        if query_image and self.ocr_integration.embedder.is_available("image"):
            image_emb = self.ocr_integration.embedder.embed_image(query_image)
            embeddings["image"] = image_emb

        # Hybrid search
        results = self.search_engine.search_hybrid(
            embeddings=embeddings, weights=weights, limit=limit
        )

        return results

    def search_by_document(
        self, file_path: Union[str, Path], limit: int = 10, exclude_self: bool = True
    ) -> List[Any]:  # List[SearchResult]
        """
        Search by similarity to a document (image/PDF)

        Args:
            file_path: Path to query document
            limit: Number of results
            exclude_self: Exclude the query document from results

        Returns:
            List of similar documents
        """
        if self.search_engine is None:
            raise RuntimeError("Search engine not configured")

        file_path = Path(file_path)

        # Process document to get embeddings
        result = self.ocr_integration.process_document(file_path, extract_metadata=False)

        embeddings = result["embeddings"]

        # Search
        results = self.search_engine.search_hybrid(
            embeddings=embeddings, limit=limit + 1 if exclude_self else limit
        )

        # Exclude query document if requested
        if exclude_self:
            query_id = file_path.stem
            results = [r for r in results if r.product_id != query_id]

        return results[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get pipeline statistics

        Returns:
            Dictionary with statistics
        """
        stats = {
            "ocr": {
                "available": self.ocr_integration.ocr.is_available(),
                "language": self.ocr_integration.ocr.lang,
                "gpu_enabled": self.ocr_integration.ocr.use_gpu,
            },
            "embeddings": {
                "text_available": self.ocr_integration.embedder.is_available("text"),
                "image_available": self.ocr_integration.embedder.is_available("image"),
                "shape_available": self.ocr_integration.embedder.is_available("shape"),
                "dimensions": self.ocr_integration.embedder.get_dimensions(),
            },
            "cache": self.ocr_integration.get_cache_stats(),
            "qdrant": {
                "collection": self.uploader.collection_name,
                "stats": self.uploader.get_collection_stats(),
            },
        }

        if self.search_engine:
            stats["search"] = {
                "fusion_strategy": self.search_engine.strategy_name,
                "collection": self.search_engine.collection_name,
            }

        return stats

    def validate_pipeline(self) -> Dict[str, bool]:
        """
        Validate all pipeline components

        Returns:
            Dictionary with validation results
        """
        validation = {}

        # Check OCR
        validation["ocr_available"] = self.ocr_integration.ocr.is_available()

        # Check embeddings
        validation["text_embedder_available"] = self.ocr_integration.embedder.is_available("text")
        validation["image_embedder_available"] = self.ocr_integration.embedder.is_available("image")

        # Check Qdrant connection
        try:
            stats = self.uploader.get_collection_stats()
            validation["qdrant_connected"] = True
            validation["collection_exists"] = True
        except Exception:
            validation["qdrant_connected"] = False
            validation["collection_exists"] = False

        # Check search engine
        validation["search_engine_available"] = self.search_engine is not None

        # Overall status
        validation["pipeline_ready"] = all(
            [
                validation["ocr_available"],
                validation["text_embedder_available"],
                validation["qdrant_connected"],
                validation["collection_exists"],
            ]
        )

        return validation

    def __repr__(self):
        return (
            f"EndToEndPipeline("
            f"ocr={self.ocr_integration.ocr.is_available()}, "
            f"embedder={self.ocr_integration.embedder.is_available('text')}, "
            f"search={self.search_engine is not None})"
        )
