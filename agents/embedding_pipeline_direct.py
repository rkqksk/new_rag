"""
Direct HTTP-based embedding pipeline for Qdrant
- Uses requests library to avoid client version issues
- Direct API calls for maximum control and reliability
"""

import json
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any
import time
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DirectEmbeddingPipeline:
    def __init__(self):
        self.qdrant_url = "http://localhost:6333"
        self.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        logger.info(f"✅ Embedding model loaded: all-MiniLM-L6-v2 (384 dim)")

    def get_all_points_direct(self, collection_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all points directly using HTTP API"""
        logger.info(f"📥 Loading points from collection: {collection_name}")

        url = f"{self.qdrant_url}/collections/{collection_name}/points/scroll"

        all_points = []
        offset = None
        iteration = 0

        while True:
            iteration += 1
            payload = {
                "limit": limit,
                "with_payload": True,
                "with_vector": False
            }

            if offset:
                payload["offset"] = offset

            try:
                response = requests.post(url, json=payload, timeout=30)
                response.raise_for_status()

                data = response.json()
                points = data.get("result", {}).get("points", [])
                next_offset = data.get("result", {}).get("next_page_offset")

                if not points:
                    logger.info(f"   No more points, stopping at iteration {iteration}")
                    break

                all_points.extend(points)
                logger.info(f"   Iteration {iteration}: loaded {len(points)} points, total: {len(all_points)}")

                # Safety check: stop after loading ~1000 points (we only need 846)
                if len(all_points) >= 1000:
                    logger.info(f"   Reached max load threshold, truncating to first 846")
                    all_points = all_points[:846]
                    break

                # If no next offset, we're done
                if next_offset is None:
                    break

                offset = next_offset
                time.sleep(0.1)  # Small delay between requests

            except Exception as e:
                logger.error(f"Error loading points: {e}")
                break

        logger.info(f"✅ Loaded {len(all_points)} points total")
        return all_points

    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_embeddings = self.embedder.encode(batch_texts, convert_to_numpy=True)
            embeddings.extend(batch_embeddings.tolist())

            progress = min(i + batch_size, len(texts))
            if progress % (batch_size * 10) == 0:
                logger.info(f"   Generated embeddings: {progress}/{len(texts)}")

        logger.info(f"✅ Generated {len(embeddings)} embeddings")
        return embeddings

    def upsert_points_direct(self, collection_name: str, points: List[Dict[str, Any]]):
        """Upsert points directly using HTTP API"""
        logger.info(f"📤 Upserting {len(points)} points to Qdrant...")

        url = f"{self.qdrant_url}/collections/{collection_name}/points"

        batch_size = 50

        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]

            payload = {"points": batch}

            try:
                response = requests.put(url, json=payload, timeout=60)
                response.raise_for_status()

                progress = min(i + batch_size, len(points))
                logger.info(f"   Uploaded: {progress}/{len(points)}")
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error upserting batch {i//batch_size}: {e}")
                return False

        logger.info("✅ All points uploaded successfully")
        return True

    def verify_vectors(self, collection_name: str):
        """Verify vector indexing using HTTP API"""
        logger.info("\n✅ Verifying vector indexing...")

        url = f"{self.qdrant_url}/collections/{collection_name}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            result = data.get("result", {})

            points_count = result.get("points_count", 0)
            indexed_vectors = result.get("indexed_vectors_count", 0)

            logger.info("\n" + "="*60)
            logger.info("📊 FINAL STATUS:")
            logger.info(f"   Points count: {points_count}")
            logger.info(f"   Indexed vectors count: {indexed_vectors}")
            logger.info("="*60)

            if indexed_vectors > 0:
                logger.info("\n✅ SUCCESS! Vectors have been indexed!")
                return True
            else:
                logger.warning("\n⚠️  Indexed vectors count is 0")
                return False

        except Exception as e:
            logger.error(f"Error verifying vectors: {e}")
            return False

    def run(self):
        """Main pipeline"""
        collection_name = "products_all"

        # Step 1: Load points
        all_points = self.get_all_points_direct(collection_name)

        if not all_points:
            logger.error("❌ No points loaded from Qdrant")
            return False

        # Step 2: Prepare embedding texts
        logger.info("\n🔄 Preparing texts for embedding...")
        embedding_data = []

        for point in all_points:
            payload = point.get("payload", {})
            product_id = payload.get("product_id", "")
            product_name = payload.get("product_name", "Unknown")
            category = payload.get("category", "Unknown")

            text_to_embed = f"{product_name} {category}"
            embedding_data.append({
                "point_id": point["id"],
                "product_id": product_id,
                "text": text_to_embed,
                "payload": payload
            })

        logger.info(f"✅ Prepared {len(embedding_data)} texts")

        # Step 3: Generate embeddings
        logger.info("\n🔄 Generating embeddings (batch size: 32)...")
        texts = [d["text"] for d in embedding_data]
        embeddings = self.generate_embeddings_batch(texts, batch_size=32)

        # Step 4: Prepare points for upsert
        logger.info("\n🔄 Preparing points with vectors...")
        points_to_upsert = []

        for idx, emb_data in enumerate(embedding_data):
            point = {
                "id": emb_data["point_id"],
                "vector": {
                    "text": embeddings[idx]
                },
                "payload": emb_data["payload"]
            }
            points_to_upsert.append(point)

            if (idx + 1) % 100 == 0:
                logger.info(f"   Prepared: {idx + 1}/{len(embedding_data)}")

        logger.info(f"✅ Prepared {len(points_to_upsert)} points with vectors")

        # Step 5: Upsert to Qdrant
        logger.info("\n🔄 Upserting vectors to Qdrant...")
        success = self.upsert_points_direct(collection_name, points_to_upsert)

        if not success:
            logger.error("❌ Upsert failed")
            return False

        # Step 6: Verify
        return self.verify_vectors(collection_name)


if __name__ == "__main__":
    pipeline = DirectEmbeddingPipeline()
    success = pipeline.run()

    if success:
        logger.info("\n🎉 Step 1 COMPLETE: Vectors generated and indexed successfully!")
    else:
        logger.error("\n❌ Pipeline failed. Check logs above.")
