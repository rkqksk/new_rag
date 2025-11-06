#!/usr/bin/env python3
"""
Demo: Week 4 - End-to-End OCR Pipeline
Complete workflow: PDF/Image → OCR → Embeddings → Qdrant → Search
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


def print_subsection(title: str):
    """Print subsection header"""
    print(f"\n  📌 {title}")
    print("  " + "-" * 76)


def main():
    print_section("Week 4 Demo: End-to-End OCR Pipeline")
    print("Complete Multi-Modal RAG: PDF/Image → OCR → Embeddings → Qdrant → Search\n")

    # ==================== Step 1: Initialize Components ====================
    print_subsection("Step 1: Initialize OCR Processor")

    try:
        from src.core.multimodal.ocr_integration import OCRProcessor

        ocr_processor = OCRProcessor(
            lang='korean',
            use_gpu=False,  # Set to True if GPU available
            enable_layout_analysis=False
        )

        if ocr_processor.is_available():
            print("✅ OCR Processor initialized")
            print(f"   Language: {ocr_processor.lang}")
            print(f"   GPU: {ocr_processor.use_gpu}")
        else:
            print("❌ OCR Processor not available (PaddleOCR not installed)")
            print("\nInstall dependencies:")
            print("  pip install paddlepaddle paddleocr pdf2image")
            print("\nNote: This demo will continue with mock mode for demonstration")

    except Exception as e:
        print(f"⚠️  OCR initialization warning: {e}")
        print("Continuing with limited functionality...")
        ocr_processor = None

    # ==================== Step 2: Initialize Embedder ====================
    print_subsection("Step 2: Initialize Multi-Modal Embedder")

    try:
        from src.core.multimodal import MultiModalEmbeddingService

        embedder = MultiModalEmbeddingService(
            enable_image=False,  # Disable image for faster demo
            enable_shape=False
        )

        print("✅ Embedder initialized")
        print(f"   Device: {embedder.device}")
        print(f"   Text embedding: {embedder.text_dim}-dim")

    except Exception as e:
        print(f"❌ Embedder initialization failed: {e}")
        print("\nInstall dependencies:")
        print("  pip install torch sentence-transformers")
        return

    # ==================== Step 3: Connect to Qdrant ====================
    print_subsection("Step 3: Connect to Qdrant")

    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(host="localhost", port=6333)
        collections = client.get_collections()

        print("✅ Connected to Qdrant")
        print(f"   Collections: {len(collections.collections)}")

    except Exception as e:
        print(f"❌ Qdrant connection failed: {e}")
        print("\nStart Qdrant:")
        print("  docker-compose up -d qdrant")
        return

    # ==================== Step 4: Check Collection ====================
    print_subsection("Step 4: Verify Collection")

    collection_name = "products_multimodal"
    collection_names = [col.name for col in collections.collections]

    if collection_name not in collection_names:
        print(f"❌ Collection '{collection_name}' not found")
        print("\nCreate collection:")
        print("  python scripts/create_multimodal_collection.py")
        return
    else:
        collection_info = client.get_collection(collection_name)
        print(f"✅ Collection '{collection_name}' ready")
        print(f"   Points: {collection_info.points_count}")

    # ==================== Step 5: Initialize Pipeline ====================
    print_subsection("Step 5: Initialize Pipeline Components")

    try:
        from src.core.multimodal.ocr_integration import OCRMultiModalIntegration
        from src.core.multimodal import MultiModalQdrantUploader, HybridSearchEngine
        from src.core.multimodal.end_to_end_pipeline import EndToEndPipeline

        # Skip OCR integration if not available
        if ocr_processor and ocr_processor.is_available():
            ocr_integration = OCRMultiModalIntegration(
                ocr_processor=ocr_processor,
                embedding_service=embedder,
                cache_embeddings=True
            )
            print("✅ OCR Integration initialized")
        else:
            print("⚠️  Skipping OCR (not available) - using text-only mode")
            ocr_integration = None

        # Uploader
        uploader = MultiModalQdrantUploader(
            qdrant_client=client,
            collection_name=collection_name
        )
        print("✅ Qdrant Uploader initialized")

        # Search Engine
        search_engine = HybridSearchEngine(
            qdrant_client=client,
            collection_name=collection_name,
            fusion_strategy="rrf"
        )
        print("✅ Hybrid Search Engine initialized")

        # Full Pipeline (if OCR available)
        if ocr_integration:
            pipeline = EndToEndPipeline(
                ocr_integration=ocr_integration,
                qdrant_uploader=uploader,
                search_engine=search_engine
            )
            print("✅ End-to-End Pipeline ready")

    except Exception as e:
        print(f"❌ Pipeline initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # ==================== Scenario 1: Pipeline Validation ====================
    print_section("Scenario 1: Pipeline Validation")

    if ocr_integration:
        validation = pipeline.validate_pipeline()

        print("\n📊 Component Status:")
        print(f"   OCR Available: {'✅' if validation['ocr_available'] else '❌'}")
        print(f"   Text Embedder: {'✅' if validation['text_embedder_available'] else '❌'}")
        print(f"   Image Embedder: {'✅' if validation['image_embedder_available'] else '❌'}")
        print(f"   Qdrant Connected: {'✅' if validation['qdrant_connected'] else '❌'}")
        print(f"   Collection Exists: {'✅' if validation['collection_exists'] else '❌'}")
        print(f"\n   Pipeline Ready: {'✅ YES' if validation['pipeline_ready'] else '❌ NO'}")

    # ==================== Scenario 2: Pipeline Statistics ====================
    print_section("Scenario 2: Pipeline Statistics")

    if ocr_integration:
        stats = pipeline.get_statistics()

        print("\n📊 OCR Configuration:")
        print(f"   Available: {stats['ocr']['available']}")
        print(f"   Language: {stats['ocr']['language']}")
        print(f"   GPU Enabled: {stats['ocr']['gpu_enabled']}")

        print("\n📊 Embedding Dimensions:")
        for modality, dim in stats['embeddings']['dimensions'].items():
            available = stats['embeddings'][f'{modality}_available']
            status = '✅' if available else '❌'
            print(f"   {modality}: {dim}-dim {status}")

        print("\n📊 Qdrant Collection:")
        print(f"   Name: {stats['qdrant']['collection']}")
        print(f"   Points: {stats['qdrant']['stats']['points_count']}")

        print("\n📊 Search Engine:")
        print(f"   Strategy: {stats['search']['fusion_strategy']}")

    # ==================== Scenario 3: Text-Only Workflow ====================
    print_section("Scenario 3: Text-Only Workflow (No OCR Required)")

    print("\nDemonstrating text embedding and search workflow...")

    # Sample text (simulated OCR output)
    sample_texts = [
        {
            'product_id': 'demo-bottle-100ml',
            'text': '100ml PET 병 화장품 용기\n투명\nMOQ: 5000개\n가격: 120원'
        },
        {
            'product_id': 'demo-jar-50ml',
            'text': '50ml 크림 용기\nPP 소재\n최소주문: 3000개'
        },
        {
            'product_id': 'demo-cap-20mm',
            'text': '20파이 캡\n스크류 타입\nMOQ: 10000개'
        }
    ]

    print(f"\n  Processing {len(sample_texts)} sample products...")

    for item in sample_texts:
        # Generate text embedding
        text_emb = embedder.embed_text(item['text'])

        # Upload to Qdrant
        success = uploader.upload_product(
            product_id=item['product_id'],
            text_embedding=text_emb,
            payload={
                'product_id': item['product_id'],
                'ocr_text': item['text'],
                'demo_mode': True
            }
        )

        if success:
            print(f"  ✅ Uploaded: {item['product_id']}")
        else:
            print(f"  ❌ Failed: {item['product_id']}")

    # ==================== Scenario 4: Hybrid Search ====================
    print_section("Scenario 4: Hybrid Search Demo")

    queries = [
        "100ml bottle",
        "cream jar 50ml",
        "20mm cap"
    ]

    for query in queries:
        print(f"\n🔍 Query: '{query}'")

        # Generate query embedding
        query_emb = embedder.embed_text(query)

        # Search
        results = search_engine.search_hybrid(
            embeddings={'text': query_emb},
            limit=3
        )

        print(f"  Found {len(results)} results:")
        for i, result in enumerate(results[:3], 1):
            print(f"\n  {i}. {result.product_id}")
            print(f"     Score: {result.score:.4f}")
            if 'ocr_text' in result.payload:
                preview = result.payload['ocr_text'].replace('\n', ' ')[:60]
                print(f"     Text: {preview}...")

    # ==================== Scenario 5: OCR Processing (if available) ====================
    if ocr_integration and ocr_processor.is_available():
        print_section("Scenario 5: OCR Processing Demo")

        print("\n📄 OCR Processing is available!")
        print("To test OCR:")
        print("  1. Place PDF or image files in a directory")
        print("  2. Use pipeline.process_and_upload(file_paths)")
        print("\nExample:")
        print("  file_paths = ['product1.pdf', 'product2.jpg']")
        print("  results = pipeline.process_and_upload(file_paths)")
        print("  for result in results:")
        print("      if result.success:")
        print("          print(f'Processed: {result.product_id}')")
        print("          print(f'OCR Text: {result.ocr_text[:100]}...')")

    else:
        print_section("Scenario 5: OCR Processing (Not Available)")
        print("\n⚠️  PaddleOCR not installed - OCR demo skipped")
        print("\nTo enable OCR processing:")
        print("  pip install paddlepaddle paddleocr pdf2image")

    # ==================== Scenario 6: Cache Performance ====================
    print_section("Scenario 6: Embedding Cache Performance")

    if ocr_integration:
        print("\n📊 Cache Statistics:")
        cache_stats = ocr_integration.get_cache_stats()

        if cache_stats['enabled']:
            print(f"  Status: ✅ Enabled")
            print(f"  Entries: {cache_stats['entries']}")
            print(f"  Size: {cache_stats['size_mb']:.2f} MB")
        else:
            print(f"  Status: ❌ Disabled")

        print("\n💡 Cache Benefits:")
        print("  - Avoid re-embedding same documents")
        print("  - Faster batch processing")
        print("  - Reduced API calls (if using cloud embedders)")

    # ==================== Scenario 7: Performance Benchmark ====================
    print_section("Scenario 7: Performance Benchmark")

    import time

    print("\n⏱️  Benchmarking text embedding + upload pipeline...")

    # Benchmark parameters
    num_iterations = 10
    sample_text = "100ml PET bottle for cosmetics, MOQ: 5000"

    total_time = 0
    for i in range(num_iterations):
        start = time.time()

        # Embed
        text_emb = embedder.embed_text(sample_text)

        # Upload
        uploader.upload_product(
            product_id=f"benchmark-{i}",
            text_embedding=text_emb,
            payload={'text': sample_text}
        )

        elapsed = time.time() - start
        total_time += elapsed

    avg_time = total_time / num_iterations

    print(f"\n  Iterations: {num_iterations}")
    print(f"  Average Time: {avg_time*1000:.1f}ms")
    print(f"  Throughput: {1/avg_time:.1f} documents/second")

    # Search benchmark
    print("\n⏱️  Benchmarking hybrid search...")

    total_time = 0
    for i in range(num_iterations):
        query_emb = embedder.embed_text(sample_text)

        start = time.time()
        results = search_engine.search_hybrid(
            embeddings={'text': query_emb},
            limit=10
        )
        elapsed = time.time() - start
        total_time += elapsed

    avg_time = total_time / num_iterations

    print(f"\n  Iterations: {num_iterations}")
    print(f"  Average Time: {avg_time*1000:.1f}ms")
    print(f"  Throughput: {1/avg_time:.1f} queries/second")

    # Summary
    print("\n" + "=" * 80)
    print("🎉 Week 4 Demo Complete!")
    print("=" * 80)

    print("\n✅ Demonstrated Components:")
    print("   - OCR Processor (PaddleOCR)")
    print("   - OCR Multi-Modal Integration")
    print("   - End-to-End Pipeline")
    print("   - Text embedding + upload workflow")
    print("   - Hybrid search")
    print("   - Performance benchmarking")

    print("\n📋 Next Steps:")
    print("   - Test with real PDF/image documents")
    print("   - Enable GPU acceleration for faster OCR")
    print("   - Enable image embeddings for visual search")
    print("   - Tune fusion weights for optimal search")

    print("\n📚 Learn More:")
    print("   - docs/OCR_PARSING_STRATEGY.md")
    print("   - docs/MULTIMODAL_RAG_STRATEGY.md")
    print("   - src/core/multimodal/README.md")

    print("\n💡 Production Checklist:")
    print("   ✓ Install PaddleOCR for OCR processing")
    print("   ✓ Enable GPU for faster embedding/OCR")
    print("   ✓ Configure embedding cache for performance")
    print("   ✓ Tune batch sizes based on available memory")
    print("   ✓ Monitor Qdrant collection size")
    print("   ✓ Implement error handling and retry logic")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏸️  Demo interrupted")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
