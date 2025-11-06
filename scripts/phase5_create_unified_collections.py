#!/usr/bin/env python3
"""
Create Unified Multi-Collection Qdrant Setup for Phase 5
Creates all required collections for integrated RAG system
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, NamedVector
from src.core.advanced_rag.unified_vector_store import UnifiedVectorStore, CollectionConfig

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def create_multimodal_collection(client: QdrantClient, collection_name: str = "products_multimodal"):
    """
    Create products_multimodal collection with named vectors

    Vectors:
    - text: 384-dim (sentence-transformers/all-MiniLM-L6-v2)
    - image: 1024-dim (OpenCLIP ViT-H-14)
    - shape: 128-dim (Hu Moments + Fourier Descriptors)
    """
    logger.info(f"📦 Creating collection: {collection_name}")

    try:
        # Check if exists
        existing = {col.name for col in client.get_collections().collections}

        if collection_name in existing:
            logger.warning(f"⚠️  Collection '{collection_name}' already exists, skipping")
            return True

        # Create with named vectors
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "text": VectorParams(size=384, distance=Distance.COSINE),
                "image": VectorParams(size=1024, distance=Distance.COSINE),
                "shape": VectorParams(size=128, distance=Distance.COSINE),
            }
        )

        logger.info(f"✅ Created '{collection_name}' with 3 named vectors (text:384, image:1024, shape:128)")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create '{collection_name}': {e}")
        return False


def create_documents_collection(client: QdrantClient, collection_name: str = "documents_semantic"):
    """
    Create documents_semantic collection for PDF/document embeddings

    Vectors:
    - text: 384-dim (sentence-transformers/all-MiniLM-L6-v2)
    """
    logger.info(f"📄 Creating collection: {collection_name}")

    try:
        existing = {col.name for col in client.get_collections().collections}

        if collection_name in existing:
            logger.warning(f"⚠️  Collection '{collection_name}' already exists, skipping")
            return True

        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )

        logger.info(f"✅ Created '{collection_name}' (text:384)")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create '{collection_name}': {e}")
        return False


def create_images_collection(client: QdrantClient, collection_name: str = "images_visual"):
    """
    Create images_visual collection for pure image embeddings

    Vectors:
    - image: 1024-dim (OpenCLIP ViT-H-14)
    """
    logger.info(f"🖼️  Creating collection: {collection_name}")

    try:
        existing = {col.name for col in client.get_collections().collections}

        if collection_name in existing:
            logger.warning(f"⚠️  Collection '{collection_name}' already exists, skipping")
            return True

        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )

        logger.info(f"✅ Created '{collection_name}' (image:1024)")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create '{collection_name}': {e}")
        return False


def create_tables_collection(client: QdrantClient, collection_name: str = "tables_structured"):
    """
    Create tables_structured collection for structured data embeddings

    Vectors:
    - text: 384-dim (sentence-transformers/all-MiniLM-L6-v2)
    """
    logger.info(f"📊 Creating collection: {collection_name}")

    try:
        existing = {col.name for col in client.get_collections().collections}

        if collection_name in existing:
            logger.warning(f"⚠️  Collection '{collection_name}' already exists, skipping")
            return True

        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )

        logger.info(f"✅ Created '{collection_name}' (text:384)")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create '{collection_name}': {e}")
        return False


def main():
    """Create all unified collections"""
    logger.info("=" * 70)
    logger.info("  Phase 5.1: Unified Vector Store Setup")
    logger.info("=" * 70)
    logger.info("")

    # Connect to Qdrant
    logger.info("🔗 Connecting to Qdrant...")
    client = QdrantClient(host="localhost", port=6333)

    logger.info("✅ Connected to Qdrant")
    logger.info("")

    # Create collections
    success_count = 0

    collections_to_create = [
        ("products_multimodal", create_multimodal_collection),
        ("documents_semantic", create_documents_collection),
        ("images_visual", create_images_collection),
        ("tables_structured", create_tables_collection),
    ]

    for collection_name, create_func in collections_to_create:
        if create_func(client, collection_name):
            success_count += 1
        logger.info("")

    # Initialize UnifiedVectorStore
    logger.info("🔧 Initializing UnifiedVectorStore...")
    store = UnifiedVectorStore(client)

    logger.info("")
    logger.info("=" * 70)
    logger.info(f"  ✅ Setup Complete: {success_count}/{len(collections_to_create)} collections")
    logger.info("=" * 70)
    logger.info("")

    # Show stats
    logger.info("📊 Collection Statistics:")
    logger.info("")

    for collection in store.get_enabled_collections():
        stats = store.get_collection_stats(collection.name)
        logger.info(f"  • {collection.name}:")
        logger.info(f"    - Points: {stats.get('points_count', 0)}")
        logger.info(f"    - Status: {stats.get('status', 'unknown')}")

    logger.info("")
    logger.info("🎉 Phase 5.1: Unified Vector Store is ready!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Upload data to collections")
    logger.info("  2. Implement Advanced Query Router (Phase 5.2)")
    logger.info("  3. Implement Score Normalization (Phase 5.3)")
    logger.info("")


if __name__ == "__main__":
    main()
