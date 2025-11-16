"""
Image search routes for visual product search with drag & drop support
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.dependencies import get_qdrant_client
from app.services.image_search_service import ImageSearchService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/search", tags=["Image Search"])


@router.post("/image")
async def search_by_image(
    image: UploadFile = File(..., description="Container image (JPEG/JPG/PNG, max 5MB)"),
    query: Optional[str] = Form(
        None, description="Optional text filter (e.g., '50ml only', 'PET material')"
    ),
    top_k: int = Form(10, description="Number of results to return (max 50)", ge=1, le=50),
    material: Optional[str] = Form(
        None, description="Filter by material: PE, PET, PETG, PP, Other"
    ),
    category: Optional[str] = Form(None, description="Filter by category: Bottle, Jar, CapPump"),
    qdrant_client=Depends(get_qdrant_client),
):
    """
    🔍 **Image-based product search with drag & drop**

    Upload a container image to find visually similar products.

    **How it works**:
    1. Drag & drop or click to upload container image (JPEG/PNG, max 5MB)
    2. Optionally add text filters: "50ml only", "PET material", etc.
    3. Get ranked results by visual similarity (%)

    **Example use cases**:
    - Upload reference container → Find similar designs
    - Image + "50ml" → Find visually similar 50ml containers
    - Image + "PET" material filter → Similar PET containers only

    **Technical details**:
    - Uses OpenCLIP-ViT-H-14 (1024-dim image embeddings)
    - Cosine similarity search in Qdrant vector database
    - Typical response time: <500ms

    **Returns**:
    - `results[]`: List of products with similarity scores
    - `similarity_score`: 0.0-1.0 (higher = more similar)
    - `image_url`: Product image for visual comparison
    """
    try:
        logger.info(f"Image search request: {image.filename}, query={query}, top_k={top_k}")

        # Initialize service
        service = ImageSearchService(qdrant_client)

        # Execute search
        results = await service.search_by_image(
            image_file=image,
            query_text=query,
            top_k=top_k,
            collection="products_all",
            material_filter=material,
            category_filter=category,
        )

        logger.info(
            f"Image search completed: {results['search_id']}, "
            f"found {results['count']} results in {results['processing_time_ms']}ms"
        )

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image search endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
