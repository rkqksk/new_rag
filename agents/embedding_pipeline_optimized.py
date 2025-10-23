"""
Optimized embedding pipeline for Qdrant
- Direct Qdrant API calls instead of scroll
- Batch embedding generation for better performance
- Text vector generation only (846 unique products)
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class OptimizedEmbeddingPipeline:
    def __init__(self):
        self.data_dir = Path("/Users/oypnus/Project/rag-enterprise/data/crawled_products_final")
        self.qdrant = QdrantClient(host="localhost", port=6333)
        self.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        logger.info(f"✅ Embedding model loaded: all-MiniLM-L6-v2 (384 dim)")

    def get_all_points_efficient(self, collection_name: str) -> List[Dict[str, Any]]:
        """Get all 846 unique points from Qdrant efficiently"""
        logger.info(f"📥 Loading all points from Qdrant collection: {collection_name}")

        # Get collection info first
        col_info = self.qdrant.get_collection(collection_name)
        total_points = col_info.points_count
        logger.info(f"   Collection has {total_points} points")

        # Get all points using scroll with proper limit
        points = []
        scroll_limit = 100
        offset = None

        while True:
            # Use with_vectors=False to get faster results
            response = self.qdrant.scroll(
                collection_name=collection_name,
                limit=scroll_limit,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )

            batch_points, next_offset = response

            if not batch_points:
                break

            points.extend(batch_points)
            logger.info(f"   ✓ Loaded {len(points)} points (next_offset: {next_offset})")

            # Stop when we reach total_points (to avoid duplicates from pagination)
            if len(points) >= total_points:
                points = points[:total_points]
                break

            offset = next_offset
            if offset is None:
                break

        logger.info(f"✅ Loaded {len(points)} unique points")
        return points

    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_embeddings = self.embedder.encode(batch_texts, convert_to_numpy=True)
            embeddings.extend(batch_embeddings.tolist())

            if (i + batch_size) % (batch_size * 10) == 0:
                logger.info(f"   Generated embeddings: {min(i + batch_size, len(texts))}/{len(texts)}")

        return embeddings

    def fix_qdrant_vectors(self):
        """Fix Qdrant by adding text vector embeddings"""
        collection_name = "products_all"

        # Step 1: Load all points
        all_points = self.get_all_points_efficient(collection_name)

        # Step 2: Prepare texts for embedding
        logger.info("\n🔄 Preparing texts for embedding...")
        texts_and_ids = []

        for point in all_points:
            payload = point.payload
            product_id = payload.get("product_id", "")
            product_name = payload.get("product_name", "Unknown")
            category = payload.get("category", "Unknown")

            # Text to embed: product_name + category
            text_to_embed = f"{product_name} {category}"
            texts_and_ids.append((product_id, text_to_embed, point.id))

        logger.info(f"✅ Prepared {len(texts_and_ids)} texts for embedding")

        # Step 3: Generate embeddings in batches
        logger.info("\n🔄 Generating text embeddings (batch processing)...")
        texts_only = [t[1] for t in texts_and_ids]
        embeddings = self.generate_embeddings_batch(texts_only, batch_size=32)

        logger.info(f"✅ Generated {len(embeddings)} embeddings")

        # Step 4: Create points with vectors
        logger.info("\n🔄 Creating points with vector data...")
        points_to_upsert = []

        for idx, (product_id, text, point_id) in enumerate(texts_and_ids):
            # Get original point data
            original_point = next((p for p in all_points if p.id == point_id), None)
            if not original_point:
                continue

            # Create new point with text vector (named vector)
            point_struct = PointStruct(
                id=point_id,
                vector={"text": embeddings[idx]},  # Named vector
                payload=original_point.payload
            )
            points_to_upsert.append(point_struct)

            if (idx + 1) % 100 == 0:
                logger.info(f"   Prepared points: {idx + 1}/{len(texts_and_ids)}")

        logger.info(f"✅ Prepared {len(points_to_upsert)} points for upload")

        # Step 5: Upsert to Qdrant in batches
        logger.info(f"\n📤 Upserting {len(points_to_upsert)} points to Qdrant...")
        batch_size = 50

        for i in range(0, len(points_to_upsert), batch_size):
            batch = points_to_upsert[i:i+batch_size]
            self.qdrant.upsert(
                collection_name=collection_name,
                points=batch
            )
            logger.info(f"   Uploaded: {min(i+batch_size, len(points_to_upsert))}/{len(points_to_upsert)}")
            time.sleep(0.1)  # Small delay between batches

        # Step 6: Verify results
        logger.info("\n✅ Verifying vector indexing...")
        collection_info = self.qdrant.get_collection(collection_name)

        logger.info("\n" + "="*60)
        logger.info("📊 FINAL STATUS:")
        logger.info(f"   Points count: {collection_info.points_count}")
        logger.info(f"   Indexed vectors count: {collection_info.indexed_vectors_count}")
        logger.info(f"   Segments: {collection_info.segments_count}")
        logger.info("="*60)

        if collection_info.indexed_vectors_count > 0:
            logger.info("\n✅ SUCCESS! Vectors have been indexed successfully!")
            return True
        else:
            logger.warning("\n⚠️  WARNING: indexed_vectors_count is still 0. Vectors may need indexing.")
            return False


if __name__ == "__main__":
    pipeline = OptimizedEmbeddingPipeline()
    success = pipeline.fix_qdrant_vectors()

    if success:
        logger.info("\n🎉 Step 1 COMPLETE: Embedding pipeline successfully generated vectors!")
    else:
        logger.warning("\n❌ Issues detected. Review the logs above.")
