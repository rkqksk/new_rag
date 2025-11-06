#!/usr/bin/env python3
"""
Migrate existing data to Multi-Modal collection
Converts single-vector collections to multi-vector (named vectors)
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_collection(
    client: QdrantClient,
    source_collection: str,
    target_collection: str = "products_multimodal",
    batch_size: int = 100,
    vector_name: str = "text",
    max_points: int = None
):
    """
    Migrate data from single-vector collection to multi-vector collection

    Args:
        client: QdrantClient instance
        source_collection: Source collection name (e.g., "products_atomic")
        target_collection: Target collection name (e.g., "products_multimodal")
        batch_size: Number of points per batch
        vector_name: Name for the vector in target collection (default: "text")
        max_points: Maximum points to migrate (None = all)

    Example:
        # Migrate products_atomic → products_multimodal
        # Single vector → Named "text" vector
        migrate_collection(
            client,
            source_collection="products_atomic",
            target_collection="products_multimodal",
            vector_name="text"
        )
    """
    logger.info("=" * 80)
    logger.info("Migrating Data to Multi-Modal Collection")
    logger.info("=" * 80)
    logger.info(f"Source: {source_collection}")
    logger.info(f"Target: {target_collection}")
    logger.info(f"Vector name: {vector_name}")

    # Check source collection
    try:
        source_info = client.get_collection(source_collection)
        total_points = source_info.points_count
        logger.info(f"✅ Source collection found: {total_points} points")
    except Exception as e:
        logger.error(f"❌ Source collection not found: {e}")
        return

    # Check target collection
    try:
        target_info = client.get_collection(target_collection)
        logger.info(f"✅ Target collection found: {target_info.points_count} points")
    except Exception as e:
        logger.error(f"❌ Target collection not found: {e}")
        logger.error(f"Create it first: python scripts/create_multimodal_collection.py")
        return

    # Determine migration count
    if max_points:
        points_to_migrate = min(total_points, max_points)
    else:
        points_to_migrate = total_points

    logger.info(f"📦 Migrating {points_to_migrate} points (batch_size={batch_size})")

    # Migration stats
    migrated = 0
    failed = 0

    # Scroll through source collection
    offset = None
    with tqdm(total=points_to_migrate, desc="Migrating") as pbar:
        while migrated < points_to_migrate:
            # Fetch batch from source
            try:
                result = client.scroll(
                    collection_name=source_collection,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=True
                )

                points, next_offset = result

                if not points:
                    break

                # Convert to multi-vector format
                multi_points = []
                for point in points:
                    # Extract vector (handle both list and dict formats)
                    if isinstance(point.vector, dict):
                        # Already multi-vector (shouldn't happen in source)
                        vector = point.vector.get(vector_name, point.vector)
                    else:
                        # Single vector → wrap in named vector
                        vector = point.vector

                    # Create multi-vector point
                    multi_point = PointStruct(
                        id=point.id,
                        vector={vector_name: vector},  # Named vector
                        payload=point.payload or {}
                    )
                    multi_points.append(multi_point)

                # Upload batch to target
                if multi_points:
                    try:
                        client.upsert(
                            collection_name=target_collection,
                            points=multi_points
                        )
                        migrated += len(multi_points)
                        pbar.update(len(multi_points))

                    except Exception as e:
                        logger.error(f"❌ Batch upload failed: {e}")
                        failed += len(multi_points)

                # Check if we've migrated enough
                if migrated >= points_to_migrate:
                    break

                # Update offset
                offset = next_offset
                if not offset:
                    break

            except Exception as e:
                logger.error(f"❌ Scroll error: {e}")
                break

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 Migration Summary")
    logger.info("=" * 80)
    logger.info(f"✅ Migrated: {migrated}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"📦 Total: {points_to_migrate}")

    # Verify target collection
    target_info_after = client.get_collection(target_collection)
    logger.info(f"\n✅ Target collection now has {target_info_after.points_count} points")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate to multi-modal collection")
    parser.add_argument("--host", default="localhost", help="Qdrant host")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant port")
    parser.add_argument("--source", default="products_atomic", help="Source collection")
    parser.add_argument("--target", default="products_multimodal", help="Target collection")
    parser.add_argument("--vector-name", default="text", help="Vector name in target")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size")
    parser.add_argument("--max-points", type=int, default=None, help="Max points to migrate")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (don't upload)")

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
        return

    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No data will be uploaded")

        # Just show what would be migrated
        try:
            source_info = client.get_collection(args.source)
            logger.info(f"Would migrate {source_info.points_count} points from '{args.source}'")
        except:
            logger.error(f"Source collection '{args.source}' not found")

        return

    # Run migration
    migrate_collection(
        client,
        source_collection=args.source,
        target_collection=args.target,
        batch_size=args.batch_size,
        vector_name=args.vector_name,
        max_points=args.max_points
    )

    logger.info("\n🎉 Migration complete!")
    logger.info("\nNext steps:")
    logger.info(f"  1. Verify data: python scripts/demo_week2_integration.py")
    logger.info(f"  2. Add image embeddings (if available)")
    logger.info(f"  3. Test hybrid search")


if __name__ == "__main__":
    main()
