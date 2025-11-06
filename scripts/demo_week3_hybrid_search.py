#!/usr/bin/env python3
"""
Demo: Week 3 - Hybrid Search Engine
Demonstrates multi-modal search with fusion strategies
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_results(results, top_k=5):
    """Pretty print search results"""
    for i, result in enumerate(results[:top_k], 1):
        print(f"\n  {i}. {result.product_id}")
        print(f"     Score: {result.score:.4f}")
        print(f"     Rank: {result.rank}")

        # Modality scores
        if result.modality_scores:
            print(f"     Modality scores:")
            for modality, score in result.modality_scores.items():
                print(f"       - {modality}: {score:.4f}")

        # Payload
        if result.payload:
            name = result.payload.get('name', result.payload.get('product_name', 'N/A'))
            category = result.payload.get('category', 'N/A')
            print(f"     Name: {name}")
            print(f"     Category: {category}")


def main():
    print_section("Week 3 Demo: Hybrid Search Engine")
    print("Demonstrates multi-modal search with RRF/Weighted/Learned fusion\n")

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
        return

    # Step 3: Check collection
    print("\n[Step 3] Checking collection...")
    collection_name = "products_multimodal"
    collection_names = [col.name for col in collections.collections]

    if collection_name not in collection_names:
        print(f"❌ Collection '{collection_name}' not found")
        print("\nCreate collection first:")
        print("  python scripts/create_multimodal_collection.py")
        print("  python scripts/demo_week2_integration.py  # Upload sample data")
        return
    else:
        collection_info = client.get_collection(collection_name)
        print(f"✅ Collection '{collection_name}' exists")
        print(f"   Points: {collection_info.points_count}")

        if collection_info.points_count == 0:
            print("\n⚠️  Collection is empty. Upload some data first:")
            print("  python scripts/demo_week2_integration.py")
            return

    # Step 4: Initialize Hybrid Search Engines
    print("\n[Step 4] Initializing Hybrid Search Engines...")
    try:
        from src.core.multimodal.hybrid_search import HybridSearchEngine

        # RRF strategy
        engine_rrf = HybridSearchEngine(
            client,
            collection_name,
            fusion_strategy="rrf"
        )
        print("✅ RRF Search Engine initialized")

        # Weighted strategy
        engine_weighted = HybridSearchEngine(
            client,
            collection_name,
            fusion_strategy="weighted"
        )
        print("✅ Weighted Search Engine initialized")

        # Learned strategy (falls back to weighted)
        engine_learned = HybridSearchEngine(
            client,
            collection_name,
            fusion_strategy="learned"
        )
        print("✅ Learned Search Engine initialized (fallback mode)")

    except Exception as e:
        print(f"❌ Failed: {e}")
        return

    # ==================== Demo Scenarios ====================

    # Scenario 1: Text-only search
    print_section("Scenario 1: Text-Only Search")
    query_text = "100ml bottle"
    print(f"Query: '{query_text}'")

    text_emb = embedder.embed_text(query_text)
    results = engine_rrf.search_hybrid(
        embeddings={"text": text_emb},
        limit=5
    )

    print_results(results)

    # Scenario 2: Multi-modal search (text + image)
    print_section("Scenario 2: Multi-Modal Search (Text + Image)")
    print("Searching with both text and image embeddings...")
    print("(Image embedding simulated - use real image in production)")

    # Note: In production, use real image embedding
    # image_emb = embedder.embed_image("product.jpg")
    # For demo, simulate with text embedding
    results = engine_rrf.search_hybrid(
        embeddings={"text": text_emb},
        limit=5
    )

    print_results(results)

    # Scenario 3: Compare fusion strategies
    print_section("Scenario 3: Fusion Strategy Comparison")
    query_text = "plastic container"
    print(f"Query: '{query_text}'")

    text_emb = embedder.embed_text(query_text)
    embeddings = {"text": text_emb}

    print("\n📊 RRF Fusion:")
    results_rrf = engine_rrf.search_hybrid(embeddings, limit=3)
    print_results(results_rrf, top_k=3)

    print("\n📊 Weighted Fusion (equal weights):")
    results_weighted = engine_weighted.search_hybrid(embeddings, limit=3)
    print_results(results_weighted, top_k=3)

    print("\n📊 Weighted Fusion (text-heavy):")
    results_weighted_heavy = engine_weighted.search_hybrid(
        embeddings,
        weights={"text": 0.9, "image": 0.1},
        limit=3
    )
    print_results(results_weighted_heavy, top_k=3)

    # Scenario 4: Result explanation
    print_section("Scenario 4: Result Explanation")
    query_text = "cosmetic jar"
    print(f"Query: '{query_text}'")

    text_emb = embedder.embed_text(query_text)
    results = engine_rrf.search_hybrid(
        embeddings={"text": text_emb},
        limit=5
    )

    explanation = engine_rrf.explain_results(results, top_k=3)

    print(f"\n🔍 Fusion Strategy: {explanation['fusion_strategy']}")
    print(f"🔍 Total Results: {explanation['total_results']}")
    print(f"🔍 Top-K Analyzed: {explanation['top_k_analyzed']}")

    print("\n📊 Top 3 Results Breakdown:")
    for result_info in explanation['results']:
        print(f"\n  Rank {result_info['rank']}: {result_info['product_id']}")
        print(f"  Final Score: {result_info['final_score']:.4f}")

        if 'modality_contributions' in result_info:
            print(f"  Modality Contributions:")
            for modality, contrib in result_info['modality_contributions'].items():
                print(f"    - {modality}: {contrib['score']:.4f} ({contrib['contribution_pct']:.1f}%)")

    # Scenario 5: Performance benchmark
    print_section("Scenario 5: Performance Benchmark")
    import time

    query_texts = [
        "100ml bottle",
        "plastic cap",
        "cosmetic jar",
        "pump dispenser",
        "20파이 캡"
    ]

    print(f"Running {len(query_texts)} queries...\n")

    total_time = 0
    for i, query in enumerate(query_texts, 1):
        text_emb = embedder.embed_text(query)

        start = time.time()
        results = engine_rrf.search_hybrid(
            embeddings={"text": text_emb},
            limit=10
        )
        elapsed = time.time() - start
        total_time += elapsed

        print(f"  {i}. '{query}'")
        print(f"     Latency: {elapsed*1000:.1f}ms")
        print(f"     Results: {len(results)}")

    avg_latency = total_time / len(query_texts)
    print(f"\n📊 Average Latency: {avg_latency*1000:.1f}ms")
    print(f"📊 Total Time: {total_time:.2f}s")

    # Scenario 6: Strategy performance comparison
    print_section("Scenario 6: Strategy Performance Comparison")
    query_text = "bottle 100ml"
    text_emb = embedder.embed_text(query_text)
    embeddings = {"text": text_emb}

    strategies = {
        "RRF": engine_rrf,
        "Weighted": engine_weighted,
        "Learned": engine_learned
    }

    print(f"Query: '{query_text}'")
    print(f"Running each strategy 10 times...\n")

    for strategy_name, engine in strategies.items():
        # Warm-up
        engine.search_hybrid(embeddings, limit=10)

        # Benchmark
        start = time.time()
        for _ in range(10):
            engine.search_hybrid(embeddings, limit=10)
        elapsed = time.time() - start

        avg = elapsed / 10
        print(f"  {strategy_name:10s}: {avg*1000:.1f}ms avg")

    # Scenario 7: Weighted fusion tuning
    print_section("Scenario 7: Weight Tuning (Text-only demo)")
    query_text = "plastic bottle"
    text_emb = embedder.embed_text(query_text)

    print(f"Query: '{query_text}'")
    print("Testing different text weights...\n")

    weight_configs = [
        {"text": 1.0, "image": 0.0},
        {"text": 0.8, "image": 0.2},
        {"text": 0.6, "image": 0.4},
        {"text": 0.5, "image": 0.5},
    ]

    for weights in weight_configs:
        results = engine_weighted.search_hybrid(
            embeddings={"text": text_emb},
            weights=weights,
            limit=3
        )

        print(f"  Weights: {weights}")
        print(f"  Top result: {results[0].product_id} (score: {results[0].score:.4f})")

    # Summary
    print("\n" + "=" * 80)
    print("🎉 Week 3 Demo Complete!")
    print("=" * 80)
    print("\n✅ Components Demonstrated:")
    print("   - HybridSearchEngine (RRF/Weighted/Learned)")
    print("   - Multi-modal search (text + image)")
    print("   - Fusion strategy comparison")
    print("   - Result explanation")
    print("   - Performance benchmarking")
    print("\n📋 Next Steps:")
    print("   - Week 4: OCR pipeline integration")
    print("   - Phase 6: Shape embedding implementation")
    print("   - Production: Cross-encoder re-ranking")
    print("\n📚 Learn More:")
    print("   - docs/MULTIMODAL_RAG_STRATEGY.md")
    print("   - src/core/multimodal/README.md")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏸️  Demo interrupted")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
