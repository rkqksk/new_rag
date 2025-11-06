"""
Multi-Modal Qdrant Uploader
Upload multi-modal embeddings (text/image/shape) to Qdrant with named vectors
"""

import logging
from typing import Optional, List, Dict, Any, Union
from uuid import uuid4
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, UpdateStatus

logger = logging.getLogger(__name__)


class MultiModalQdrantUploader:
    """
    Upload multi-modal embeddings to Qdrant

    Handles named vectors for text, image, and shape embeddings.

    Example:
        >>> uploader = MultiModalQdrantUploader(client)
        >>>
        >>> # Upload product with text + image
        >>> uploader.upload_product(
        ...     product_id="BOTTLE-001",
        ...     text_embedding=[...],  # 384-dim
        ...     image_embedding=[...], # 1024-dim
        ...     payload={"name": "100ml PET Bottle"}
        ... )
        >>>
        >>> # Batch upload
        >>> products = [
        ...     {
        ...         "product_id": "BOTTLE-001",
        ...         "text_embedding": [...],
        ...         "image_embedding": [...],
        ...         "payload": {...}
        ...     },
        ...     ...
        ... ]
        >>> uploader.upload_batch(products)
    """

    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str = "products_multimodal"
    ):
        """
        Initialize uploader

        Args:
            qdrant_client: QdrantClient instance
            collection_name: Target collection name
        """
        self.client = qdrant_client
        self.collection_name = collection_name

        # Verify collection exists
        self._verify_collection()

        logger.info(f"✅ MultiModalQdrantUploader initialized for '{collection_name}'")

    def _verify_collection(self):
        """Verify collection exists and has correct configuration"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            vectors = collection_info.config.params.vectors

            # Check required vectors
            required = {"text": 384, "image": 1024, "shape": 128}
            for vector_name, expected_size in required.items():
                if vector_name not in vectors:
                    logger.warning(f"⚠️ Vector '{vector_name}' not found in collection")
                elif vectors[vector_name].size != expected_size:
                    logger.warning(
                        f"⚠️ Vector '{vector_name}' size mismatch: "
                        f"{vectors[vector_name].size} != {expected_size}"
                    )

        except Exception as e:
            logger.error(f"❌ Collection verification failed: {e}")
            raise ValueError(
                f"Collection '{self.collection_name}' not found or invalid. "
                f"Run: python scripts/create_multimodal_collection.py"
            )

    def upload_product(
        self,
        product_id: str,
        text_embedding: Optional[List[float]] = None,
        image_embedding: Optional[List[float]] = None,
        shape_embedding: Optional[List[float]] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Upload single product with multi-modal embeddings

        Args:
            product_id: Unique product identifier
            text_embedding: 384-dim text vector (optional)
            image_embedding: 1024-dim image vector (optional)
            shape_embedding: 128-dim shape vector (optional, Phase 6)
            payload: Product metadata

        Returns:
            True if successful

        Raises:
            ValueError: If no embeddings provided
            ValueError: If embedding dimension mismatch

        Example:
            >>> uploader.upload_product(
            ...     product_id="BOTTLE-001",
            ...     text_embedding=[0.1, 0.2, ...],  # 384-dim
            ...     image_embedding=[0.3, 0.4, ...], # 1024-dim
            ...     payload={
            ...         "product_name": "100ml PET Bottle",
            ...         "category": "Bottle",
            ...         "specifications": {"capacity": "100ml"}
            ...     }
            ... )
        """
        # Validate inputs
        if not any([text_embedding, image_embedding, shape_embedding]):
            raise ValueError("At least one embedding (text/image/shape) must be provided")

        # Build named vectors
        vectors = {}

        if text_embedding:
            if len(text_embedding) != 384:
                raise ValueError(f"Text embedding must be 384-dim, got {len(text_embedding)}")
            vectors["text"] = text_embedding

        if image_embedding:
            if len(image_embedding) != 1024:
                raise ValueError(f"Image embedding must be 1024-dim, got {len(image_embedding)}")
            vectors["image"] = image_embedding

        if shape_embedding:
            if len(shape_embedding) != 128:
                raise ValueError(f"Shape embedding must be 128-dim, got {len(shape_embedding)}")
            vectors["shape"] = shape_embedding

        # Add metadata to payload
        if payload is None:
            payload = {}

        payload["product_id"] = product_id
        payload["uploaded_at"] = datetime.now().isoformat()
        payload["vector_types"] = list(vectors.keys())

        # Create point
        point = PointStruct(
            id=product_id,
            vector=vectors,
            payload=payload
        )

        # Upload
        try:
            result = self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )

            if result.status == UpdateStatus.COMPLETED:
                logger.debug(f"✅ Uploaded product: {product_id} ({list(vectors.keys())})")
                return True
            else:
                logger.error(f"❌ Upload failed: {result.status}")
                return False

        except Exception as e:
            logger.error(f"❌ Upload error for {product_id}: {e}")
            raise

    def upload_batch(
        self,
        products: List[Dict[str, Any]],
        batch_size: int = 100,
        show_progress: bool = True
    ) -> Dict[str, int]:
        """
        Batch upload multiple products

        Args:
            products: List of product dicts with embeddings
            batch_size: Number of products per batch
            show_progress: Show progress messages

        Returns:
            Statistics: {"success": int, "failed": int, "total": int}

        Example:
            >>> products = [
            ...     {
            ...         "product_id": "BOTTLE-001",
            ...         "text_embedding": [...],
            ...         "image_embedding": [...],
            ...         "payload": {"name": "Product 1"}
            ...     },
            ...     ...
            ... ]
            >>> stats = uploader.upload_batch(products)
            >>> print(f"Uploaded {stats['success']}/{stats['total']} products")
        """
        total = len(products)
        success_count = 0
        failed_count = 0

        logger.info(f"📦 Batch uploading {total} products (batch_size={batch_size})")

        for i in range(0, total, batch_size):
            batch = products[i:i+batch_size]
            points = []

            # Build points for this batch
            for product in batch:
                product_id = product.get("product_id")
                if not product_id:
                    product_id = str(uuid4())
                    logger.warning(f"⚠️ No product_id, generated: {product_id}")

                # Build vectors
                vectors = {}

                if "text_embedding" in product and product["text_embedding"]:
                    vectors["text"] = product["text_embedding"]

                if "image_embedding" in product and product["image_embedding"]:
                    vectors["image"] = product["image_embedding"]

                if "shape_embedding" in product and product["shape_embedding"]:
                    vectors["shape"] = product["shape_embedding"]

                if not vectors:
                    logger.warning(f"⚠️ No embeddings for {product_id}, skipping")
                    failed_count += 1
                    continue

                # Build payload
                payload = product.get("payload", {}).copy()
                payload["product_id"] = product_id
                payload["uploaded_at"] = datetime.now().isoformat()
                payload["vector_types"] = list(vectors.keys())

                # Create point
                point = PointStruct(
                    id=product_id,
                    vector=vectors,
                    payload=payload
                )
                points.append(point)

            # Upload batch
            if points:
                try:
                    result = self.client.upsert(
                        collection_name=self.collection_name,
                        points=points
                    )

                    if result.status == UpdateStatus.COMPLETED:
                        success_count += len(points)
                        if show_progress:
                            logger.info(f"  ✅ Batch {i//batch_size + 1}: {len(points)} products")
                    else:
                        failed_count += len(points)
                        logger.error(f"  ❌ Batch {i//batch_size + 1} failed: {result.status}")

                except Exception as e:
                    failed_count += len(points)
                    logger.error(f"  ❌ Batch {i//batch_size + 1} error: {e}")

        stats = {
            "success": success_count,
            "failed": failed_count,
            "total": total
        }

        logger.info(f"\n📊 Upload Summary:")
        logger.info(f"  ✅ Success: {stats['success']}")
        logger.info(f"  ❌ Failed: {stats['failed']}")
        logger.info(f"  📦 Total: {stats['total']}")

        return stats

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve product from Qdrant

        Args:
            product_id: Product identifier

        Returns:
            Product dict with vectors and payload, or None if not found
        """
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[product_id],
                with_vectors=True,
                with_payload=True
            )

            if result:
                point = result[0]
                return {
                    "id": point.id,
                    "vectors": point.vector,
                    "payload": point.payload
                }
            else:
                return None

        except Exception as e:
            logger.error(f"❌ Retrieve error for {product_id}: {e}")
            return None

    def delete_product(self, product_id: str) -> bool:
        """
        Delete product from Qdrant

        Args:
            product_id: Product identifier

        Returns:
            True if successful
        """
        try:
            result = self.client.delete(
                collection_name=self.collection_name,
                points_selector=[product_id]
            )

            logger.debug(f"🗑️ Deleted product: {product_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Delete error for {product_id}: {e}")
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics

        Returns:
            Statistics dict with count, vectors, etc.
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)

            return {
                "collection_name": self.collection_name,
                "points_count": collection_info.points_count,
                "vectors": {
                    name: {"size": params.size, "distance": params.distance}
                    for name, params in collection_info.config.params.vectors.items()
                },
                "status": collection_info.status
            }

        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {}

    def __repr__(self):
        stats = self.get_collection_stats()
        return (
            f"MultiModalQdrantUploader("
            f"collection='{self.collection_name}', "
            f"points={stats.get('points_count', 0)})"
        )
