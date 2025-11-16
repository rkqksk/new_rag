"""
Image-based product search service using OpenCLIP embeddings
"""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import open_clip
import torch
from fastapi import HTTPException, UploadFile
from PIL import Image
from qdrant_client import QdrantClient

from apps.api.utils.product_utils import (
    batch_validate_products,
    enrich_product_with_metadata,
    generate_image_urls,
)

logger = logging.getLogger(__name__)


class ImageSearchService:
    """Service for image-based product search with drag & drop support"""

    def __init__(self, qdrant_client: QdrantClient, device: str = "auto"):
        self.qdrant_client = qdrant_client

        # Auto-detect device (MPS for M4 Mac)
        if device == "auto":
            if torch.backends.mps.is_available():
                self.device = "mps"
            elif torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"
        else:
            self.device = device

        logger.info(f"ImageSearchService using device: {self.device}")

        # Load OpenCLIP model (same as embedding pipeline)
        try:
            self.model, self.preprocess, _ = open_clip.create_model_and_transforms(
                model_name="ViT-H-14", pretrained="laion2b-s32b-b79k", device=self.device
            )
            self.model.eval()  # Set to evaluation mode
            logger.info("✅ OpenCLIP model loaded for image search")
        except Exception as e:
            logger.error(f"Failed to load OpenCLIP: {e}")
            raise

    def embed_image(self, image_path: str) -> List[float]:
        """
        Generate 1024-dim image embedding using OpenCLIP

        Args:
            image_path: Path to image file

        Returns:
            1024-dimensional embedding vector
        """
        try:
            image = Image.open(image_path).convert("RGB")
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                image_embedding = self.model.encode_image(image_tensor)

            return image_embedding.squeeze(0).cpu().numpy().tolist()
        except Exception as e:
            logger.error(f"Image embedding error for {image_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

    async def search_by_image(
        self,
        image_file: UploadFile,
        query_text: Optional[str] = None,
        top_k: int = 10,
        collection: str = "products_all",
        material_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        return_all: bool = False,
        min_integrity_score: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Search for visually similar products using image upload

        Args:
            image_file: Uploaded image file (JPEG/JPG/PNG)
            query_text: Optional text filter (e.g., "50ml only", "PET material")
            top_k: Number of results to return (ignored if return_all=True)
            collection: Qdrant collection to search
            material_filter: Filter by material (PE, PET, PETG, PP, Other)
            category_filter: Filter by category (Bottle, Jar, CapPump)
            return_all: If True, return all filtered results
            min_integrity_score: Minimum integrity score for filtering (0.0~1.0)

        Returns:
            Search results with similarity scores, product details, image URLs, and integrity validation
        """
        search_start = datetime.now()
        search_id = str(uuid.uuid4())

        try:
            # Validate file type
            allowed_types = ["image/jpeg", "image/jpg", "image/png"]
            if image_file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {image_file.content_type}. Only JPEG/PNG supported.",
                )

            # Validate file size (5MB max)
            content = await image_file.read()
            file_size_mb = len(content) / (1024 * 1024)
            if file_size_mb > 5:
                raise HTTPException(
                    status_code=400, detail=f"File too large: {file_size_mb:.1f}MB. Maximum is 5MB."
                )

            # Save uploaded file temporarily
            upload_dir = Path("/tmp/rag_uploads")
            upload_dir.mkdir(exist_ok=True)

            temp_path = upload_dir / f"{search_id}_{image_file.filename}"
            with open(temp_path, "wb") as f:
                f.write(content)

            logger.info(f"Image uploaded: {image_file.filename} ({file_size_mb:.2f}MB)")

            # Generate image embedding
            image_embedding = self.embed_image(str(temp_path))

            # Build Qdrant filter
            qdrant_filter = None
            if material_filter or category_filter:
                conditions = []
                if material_filter:
                    conditions.append({"key": "category", "match": {"text": material_filter}})
                if category_filter:
                    conditions.append({"key": "category", "match": {"text": category_filter}})
                if conditions:
                    qdrant_filter = {"must": conditions}

            # Search in Qdrant using image vector (named vector)
            # Use larger limit if return_all=True
            search_limit = 200 if return_all else top_k
            search_results = self.qdrant_client.search(
                collection_name=collection,
                query_vector=("image", image_embedding),  # Use named "image" vector
                limit=search_limit,
                query_filter=qdrant_filter,
                with_payload=True,
            )

            # Format results with standard structure
            formatted_results = []
            for result in search_results:
                payload = result.payload
                formatted_results.append(
                    {
                        "product_id": payload.get("product_id", ""),
                        "product_name": payload.get("product_name", "N/A"),
                        "category": payload.get("category", ""),
                        "similarity_score": float(result.score),
                        "specifications": payload.get("specifications", {}),
                        "print_area_url": payload.get("print_area_url"),
                        "match_type": "hybrid" if query_text else "visual",
                    }
                )

            # Apply integrity validation and enrichment
            validated_results = batch_validate_products(
                formatted_results,
                require_images=False,
                require_specs=False,
                min_integrity_score=min_integrity_score,
            )

            enriched_results = [
                enrich_product_with_metadata(p, include_image_count=True, include_spec_count=True)
                for p in validated_results
            ]

            # Apply top_k limit if return_all=False
            if not return_all:
                enriched_results = enriched_results[:top_k]

            results = enriched_results

            processing_time = (datetime.now() - search_start).total_seconds() * 1000

            logger.info(
                f"Image search completed: {search_id}, "
                f"found {len(results)} results in {processing_time:.0f}ms"
            )

            return {
                "search_id": search_id,
                "search_type": "hybrid" if query_text else "image",
                "query_text": query_text,
                "image_filename": image_file.filename,
                "file_size_mb": round(file_size_mb, 2),
                "results": results,
                "count": len(results),
                "return_all": return_all,
                "min_integrity_score": min_integrity_score,
                "processing_time_ms": round(processing_time, 2),
                "timestamp": datetime.now().isoformat(),
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Image search error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            # Clean up temporary file
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")
