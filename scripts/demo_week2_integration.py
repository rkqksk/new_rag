#!/usr/bin/env python3
"""
Demo: Week 2 Integration
End-to-end demo of MultiModalEmbeddingService + QdrantUploader
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    print("=" * 80)
    print("Week 2 Integration Demo")
    print("MultiModalEmbeddingService + QdrantUploader")
    print("=" * 80)

    # Step 1: Initialize embedder
    print("\n[Step 1] Initializing MultiModalEmbeddingService...")
    try:
        from src.core.multimodal import MultiModalEmbeddingService

        embedder = MultiModalEmbeddingService(enable_image=False)
        print("✅ Embedder initialized")
        print(f"   Device: {embedder.device}")
        print(f"   Text dimension: {embedder.text_dim}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        print("\nInstall dependencies:")
        print("  pip install torch sentence-transformers")
        return

    # Step 2: Connect to Qdrant
    print("\n[Step 2] Connecting to Qdrant...")
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(host="localhost", port=6333)
        collections = client.get_collections()
        print(f"✅ Connected to Qdrant")
        print(f"   Found {len(collections.collections)} collections")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nMake sure Qdrant is running:")
        print("  docker-compose up -d qdrant")
        print("  # or")
        print("  colima start && docker-compose up -d qdrant")
        return

    # Step 3: Check if collection exists
    print("\n[Step 3] Checking collection...")
    collection_name = "products_multimodal"
    collection_names = [col.name for col in collections.collections]

    if collection_name not in collection_names:
        print(f"❌ Collection '{collection_name}' not found")
        print("\nCreate collection first:")
        print("  python scripts/create_multimodal_collection.py")
        return
    else:
        print(f"✅ Collection '{collection_name}' exists")

        # Get collection info
        collection_info = client.get_collection(collection_name)
        print(f"   Points: {collection_info.points_count}")
        print(f"   Vectors: {list(collection_info.config.params.vectors.keys())}")

    # Step 4: Initialize uploader
    print("\n[Step 4] Initializing MultiModalQdrantUploader...")
    try:
        from src.core.multimodal import MultiModalQdrantUploader

        uploader = MultiModalQdrantUploader(client, collection_name)
        print("✅ Uploader initialized")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return

    # Step 5: Generate sample embeddings
    print("\n[Step 5] Generating sample embeddings...")
    sample_products = [
        {
            "product_id": "DEMO-BOTTLE-001",
            "text": "100ml PET Bottle, Ø20 Neck, Transparent"
        },
        {
            "product_id": "DEMO-CAP-001",
            "text": "20파이 캡, 5000개 MOQ, White Color"
        },
        {
            "product_id": "DEMO-JAR-001",
            "text": "화장품 용기 50ml, 원형 디자인"
        }
    ]

    embeddings_data = []
    for product in sample_products:
        text_emb = embedder.embed_text(product["text"])
        embeddings_data.append({
            "product_id": product["product_id"],
            "text_embedding": text_emb,
            "payload": {
                "product_name": product["text"],
                "category": "Sample",
                "source": "demo_week2"
            }
        })

    print(f"✅ Generated {len(embeddings_data)} embeddings")
    for item in embeddings_data:
        print(f"   {item['product_id']}: {len(item['text_embedding'])}-dim")

    # Step 6: Upload to Qdrant
    print("\n[Step 6] Uploading to Qdrant...")
    try:
        stats = uploader.upload_batch(embeddings_data, show_progress=True)

        print(f"\n✅ Upload complete!")
        print(f"   Success: {stats['success']}")
        print(f"   Failed: {stats['failed']}")
        print(f"   Total: {stats['total']}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return

    # Step 7: Verify upload
    print("\n[Step 7] Verifying upload...")
    for product in sample_products:
        product_id = product["product_id"]
        retrieved = uploader.get_product(product_id)

        if retrieved:
            print(f"✅ {product_id}: Found")
            print(f"   Vectors: {list(retrieved['vectors'].keys())}")
            print(f"   Payload keys: {list(retrieved['payload'].keys())}")
        else:
            print(f"❌ {product_id}: Not found")

    # Step 8: Search test
    print("\n[Step 8] Testing search...")
    try:
        # Search with text embedding
        query_text = "100ml bottle"
        query_emb = embedder.embed_text(query_text)

        results = client.search(
            collection_name=collection_name,
            query_vector=("text", query_emb),  # Named vector search
            limit=3
        )

        print(f"✅ Search results for '{query_text}':")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.payload.get('product_name', 'N/A')}")
            print(f"      Score: {result.score:.4f}")
            print(f"      ID: {result.id}")

    except Exception as e:
        print(f"❌ Search failed: {e}")

    # Step 9: Collection stats
    print("\n[Step 9] Collection statistics...")
    stats = uploader.get_collection_stats()
    print(f"📊 Collection: {stats['collection_name']}")
    print(f"   Total points: {stats['points_count']}")
    print(f"   Status: {stats['status']}")
    print("\n   Vectors:")
    for vector_name, vector_info in stats['vectors'].items():
        print(f"     - {vector_name}: {vector_info['size']}-dim ({vector_info['distance']})")

    # Step 10: Cleanup (optional)
    print("\n[Step 10] Cleanup demo data? (y/n)")
    try:
        response = input("Delete demo products? ")
        if response.lower() == 'y':
            for product in sample_products:
                uploader.delete_product(product["product_id"])
            print("✅ Demo data deleted")
        else:
            print("⏸️ Demo data kept in collection")
    except:
        print("⏸️ Cleanup skipped")

    # Summary
    print("\n" + "=" * 80)
    print("🎉 Week 2 Integration Demo Complete!")
    print("=" * 80)
    print("\n✅ Components Working:")
    print("   - MultiModalEmbeddingService (text embeddings)")
    print("   - MultiModalQdrantUploader (upload/retrieve)")
    print("   - Qdrant named vector search")
    print("\n📋 Next Steps:")
    print("   - Week 3: Implement HybridSearchEngine")
    print("   - Week 4: OCR pipeline integration")
    print("\n📚 Learn More:")
    print("   - docs/MULTIMODAL_RAG_STRATEGY.md")
    print("   - src/core/multimodal/README.md")


if __name__ == "__main__":
    main()
