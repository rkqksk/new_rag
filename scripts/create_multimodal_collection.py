"""
Create Qdrant Multi-Modal Collection
Sets up named vectors for text, image, and shape embeddings
"""

import logging
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_multimodal_collection(
    client: QdrantClient,
    collection_name: str = "products_multimodal",
    recreate: bool = False
):
    """
    Create Qdrant collection with named vectors for multi-modal embeddings

    Collection Schema:
    - text: 384-dim (Sentence Transformers all-MiniLM-L6-v2)
    - image: 1024-dim (OpenCLIP ViT-H-14)
    - shape: 128-dim (Custom descriptors, Phase 6)

    Args:
        client: QdrantClient instance
        collection_name: Name of collection to create
        recreate: If True, delete existing collection first

    Returns:
        True if successful
    """
    logger.info("=" * 80)
    logger.info("Creating Multi-Modal Qdrant Collection")
    logger.info("=" * 80)

    # Check if collection exists
    collections = client.get_collections().collections
    collection_names = [col.name for col in collections]
    exists = collection_name in collection_names

    if exists:
        if recreate:
            logger.warning(f"⚠️ Collection '{collection_name}' exists. Deleting...")
            client.delete_collection(collection_name)
            logger.info("✅ Collection deleted")
        else:
            logger.info(f"✅ Collection '{collection_name}' already exists")
            return True

    # Create collection with named vectors
    logger.info(f"📦 Creating collection: {collection_name}")
    logger.info("Vectors:")
    logger.info("  - text: 384-dim (Sentence Transformers)")
    logger.info("  - image: 1024-dim (OpenCLIP ViT-H-14)")
    logger.info("  - shape: 128-dim (Custom descriptors, Phase 6)")

    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "text": VectorParams(
                    size=384,
                    distance=Distance.COSINE
                ),
                "image": VectorParams(
                    size=1024,
                    distance=Distance.COSINE
                ),
                "shape": VectorParams(
                    size=128,
                    distance=Distance.COSINE
                )
            }
        )

        logger.info("✅ Collection created successfully!")

        # Verify collection
        collection_info = client.get_collection(collection_name)
        logger.info("\n📊 Collection Info:")
        logger.info(f"  Name: {collection_info.config.params.vectors}")
        logger.info(f"  Points: {collection_info.points_count}")
        logger.info(f"  Status: {collection_info.status}")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to create collection: {e}")
        raise


def verify_collection(
    client: QdrantClient,
    collection_name: str = "products_multimodal"
):
    """
    Verify collection exists and has correct configuration

    Args:
        client: QdrantClient instance
        collection_name: Name of collection to verify

    Returns:
        True if valid
    """
    logger.info(f"\n🔍 Verifying collection: {collection_name}")

    try:
        collection_info = client.get_collection(collection_name)

        # Check vectors config
        vectors = collection_info.config.params.vectors

        required_vectors = {
            "text": 384,
            "image": 1024,
            "shape": 128
        }

        logger.info("Checking vector configurations:")
        for vector_name, expected_size in required_vectors.items():
            if vector_name in vectors:
                actual_size = vectors[vector_name].size
                if actual_size == expected_size:
                    logger.info(f"  ✅ {vector_name}: {actual_size}-dim (correct)")
                else:
                    logger.error(f"  ❌ {vector_name}: {actual_size}-dim (expected {expected_size})")
                    return False
            else:
                logger.warning(f"  ⚠️ {vector_name}: not found")

        logger.info(f"\n✅ Collection verification passed!")
        logger.info(f"  Total points: {collection_info.points_count}")

        return True

    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Create Qdrant multi-modal collection")
    parser.add_argument("--host", default="localhost", help="Qdrant host")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant port")
    parser.add_argument("--collection", default="products_multimodal", help="Collection name")
    parser.add_argument("--recreate", action="store_true", help="Recreate if exists")

    args = parser.parse_args()

    # Connect to Qdrant
    logger.info(f"🔌 Connecting to Qdrant at {args.host}:{args.port}")
    client = QdrantClient(host=args.host, port=args.port)

    # Test connection
    try:
        collections = client.get_collections()
        logger.info(f"✅ Connected! Found {len(collections.collections)} collections")
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        logger.error("Make sure Qdrant is running:")
        logger.error("  docker-compose up -d qdrant")
        return

    # Create collection
    success = create_multimodal_collection(
        client,
        collection_name=args.collection,
        recreate=args.recreate
    )

    if success:
        # Verify
        verify_collection(client, args.collection)

        logger.info("\n" + "=" * 80)
        logger.info("🎉 Multi-Modal Collection Ready!")
        logger.info("=" * 80)
        logger.info("\nNext steps:")
        logger.info("  1. Use MultiModalQdrantUploader to add data")
        logger.info("  2. Run migration script to import existing data")
        logger.info("  3. Test with hybrid search")
        logger.info("\nUsage:")
        logger.info(f"  from qdrant_client import QdrantClient")
        logger.info(f"  client = QdrantClient(host='{args.host}', port={args.port})")
        logger.info(f"  # Upload with named vectors")
        logger.info(f"  client.upsert(")
        logger.info(f"      collection_name='{args.collection}',")
        logger.info(f"      points=[{{")
        logger.info(f"          'id': 'product-001',")
        logger.info(f"          'vector': {{")
        logger.info(f"              'text': [384-dim vector],")
        logger.info(f"              'image': [1024-dim vector],")
        logger.info(f"              'shape': [128-dim vector]")
        logger.info(f"          }},")
        logger.info(f"          'payload': {{'name': 'Product 1'}}")
        logger.info(f"      }}]")
        logger.info(f"  )")


if __name__ == "__main__":
    main()
