#!/usr/bin/env python3
"""
Demo: Phase 6 - Shape Embedding & Image Matching
Tri-Modal RAG: Text (384) + Image (1024) + Shape (128)
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


def main():
    print_section("Phase 6 Demo: Shape Embedding & Tri-Modal RAG")
    print("Complete system: Text (384-dim) + Image (1024-dim) + Shape (128-dim)\n")

    # ==================== Step 1: Initialize Shape Components ====================
    print_section("Step 1: Initialize Shape Matching Components")

    try:
        from src.core.image_matching import (
            BackgroundRemover,
            ContourExtractor,
            ShapeDescriptor,
            ShapeEmbedder
        )

        # Background Remover
        bg_remover = BackgroundRemover(use_gpu=False)
        print(f"✅ BackgroundRemover: {bg_remover}")

        # Contour Extractor
        contour_extractor = ContourExtractor()
        print(f"✅ ContourExtractor: {contour_extractor}")

        # Shape Descriptor
        shape_descriptor = ShapeDescriptor(fourier_coeffs=60)
        print(f"✅ ShapeDescriptor: {shape_descriptor}")

        # Shape Embedder
        shape_embedder = ShapeEmbedder(target_dim=128)
        print(f"✅ ShapeEmbedder: {shape_embedder}")

    except Exception as e:
        print(f"❌ Failed to initialize shape components: {e}")
        print("\nInstall dependencies:")
        print("  pip install opencv-python rembg")
        return

    # ==================== Step 2: Initialize Tri-Modal Embedder ====================
    print_section("Step 2: Initialize Tri-Modal Embedding Service")

    try:
        from src.core.multimodal import MultiModalEmbeddingService

        embedder = MultiModalEmbeddingService(
            enable_image=False,  # Disable for faster demo
            enable_shape=True    # Enable shape embedding ⭐
        )

        print("✅ Tri-Modal Embedder initialized")
        print(f"   Device: {embedder.device}")

        dims = embedder.get_dimensions()
        print("\n📊 Embedding Dimensions:")
        for modality, dim in dims.items():
            available = "✅" if embedder.is_available(modality) else "❌"
            print(f"   {modality}: {dim}-dim {available}")

    except Exception as e:
        print(f"❌ Embedder initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # ==================== Scenario 1: Shape Components Demo ====================
    print_section("Scenario 1: Shape Components Demo")

    print("\n📝 Shape Pipeline:")
    print("  1. Background Removal (optional)")
    print("  2. Contour Extraction (OpenCV)")
    print("  3. Shape Descriptors (Hu Moments + Fourier)")
    print("  4. Dimensionality Projection (67-dim → 128-dim)")
    print("  5. Normalization to unit length")

    print("\n🔑 Key Features:")
    print("  ✓ Rotation invariant (Hu Moments)")
    print("  ✓ Scale invariant (normalization)")
    print("  ✓ Translation invariant (relative descriptors)")
    print("  ✓ Works with sketches and outlines")

    # ==================== Scenario 2: Tri-Modal System Architecture ====================
    print_section("Scenario 2: Tri-Modal System Architecture")

    print("\n🏗️ Complete Architecture:")
    print("""
    Input:
      ├── Text Query: "100ml bottle"
      │     ↓
      │   Text Embedding (Sentence Transformers)
      │     ↓
      │   384-dimensional vector
      │
      ├── Image: product_photo.jpg
      │     ↓
      │   Image Embedding (OpenCLIP ViT-H-14)
      │     ↓
      │   1024-dimensional vector
      │
      └── Shape: product_outline.jpg
            ↓
          Background Removal → Contour → Descriptors
            ↓
          Shape Embedding (Hu + Fourier)
            ↓
          128-dimensional vector

    Qdrant Named Vectors:
      ├── "text": [384 floats]
      ├── "image": [1024 floats]
      └── "shape": [128 floats]

    Hybrid Search:
      RRF Fusion → Top-K Results
    """)

    # ==================== Scenario 3: Shape Embedding Components ====================
    print_section("Scenario 3: Shape Embedding Components")

    print("\n🔧 Component Breakdown:")

    print("\n1️⃣ Background Removal (rembg/U2-Net):")
    print("   - Removes background from product images")
    print("   - Alpha matting for smooth edges")
    print(f"   - Available: {bg_remover.is_available()}")

    print("\n2️⃣ Contour Extraction (OpenCV):")
    print("   - Canny edge detection")
    print("   - Contour finding and filtering")
    print("   - Approximation for efficiency")
    print(f"   - Available: {contour_extractor.is_available()}")

    print("\n3️⃣ Shape Descriptors:")
    print("   - Hu Moments: 7-dim rotation-invariant features")
    print("   - Fourier Descriptors: 60-dim frequency features")
    print("   - Combined: 67-dim descriptor")
    print(f"   - Available: {shape_descriptor.is_available()}")

    print("\n4️⃣ Shape Embedder:")
    print(f"   - Input: 67-dim descriptor")
    print(f"   - Output: 128-dim embedding")
    print(f"   - Method: Random projection (Johnson-Lindenstrauss)")
    print(f"   - Available: {shape_embedder.is_available()}")

    # ==================== Scenario 4: Comparison with Previous Phases ====================
    print_section("Scenario 4: Multi-Modal Evolution")

    print("\n📈 Evolution Timeline:")
    print("""
    Phase 0-3: Foundation
      - Text embedding only (384-dim)
      - Semantic search
      - Quality: 0.79-0.82

    Phase 4.4 (Weeks 1-4): Multi-Modal Integration
      - Text + Image embeddings
      - OCR processing
      - Hybrid search (RRF/Weighted/Learned)
      - Quality: ~0.85

    Phase 6 (Current): Shape Embedding ⭐
      - Text + Image + Shape (Tri-Modal)
      - Visual similarity matching
      - Shape-based search
      - Expected quality: >0.90
    """)

    # ==================== Scenario 5: Use Cases ====================
    print_section("Scenario 5: Shape Embedding Use Cases")

    print("\n🎯 Use Cases:")

    print("\n1. Sketch-Based Search:")
    print("   User draws rough outline → Find similar products")
    print("   Example: Hand-drawn bottle shape → Matching bottles")

    print("\n2. Shape-First Search:")
    print("   User knows shape but not exact product")
    print("   Example: 'Rectangular jar' → All rectangular jars")

    print("\n3. Visual Similarity:")
    print("   Find products with similar contours")
    print("   Example: Similar pump dispensers")

    print("\n4. Hybrid Multi-Modal:")
    print("   Combine text + image + shape for best accuracy")
    print("   Example: '100ml' (text) + bottle.jpg (image) + outline (shape)")

    # ==================== Scenario 6: Integration with Existing System ====================
    print_section("Scenario 6: Integration with Existing Pipeline")

    print("\n🔗 Integration Points:")

    print("\n✅ MultiModalEmbeddingService:")
    print("   - embed_shape(image_path) → 128-dim vector")
    print("   - Integrated with embed() method")
    print("   - Batch processing support")

    print("\n✅ Qdrant Named Vectors:")
    print("   - Already supports 'shape' vector")
    print("   - No schema changes needed")
    print("   - Backward compatible")

    print("\n✅ HybridSearchEngine:")
    print("   - search_shape() method available")
    print("   - Tri-modal fusion in search_hybrid()")
    print("   - RRF/Weighted/Learned strategies")

    print("\n✅ End-to-End Pipeline:")
    print("   - OCR → Text/Image/Shape embeddings")
    print("   - Upload all 3 vectors to Qdrant")
    print("   - Hybrid search across all modalities")

    # ==================== Scenario 7: Performance Characteristics ====================
    print_section("Scenario 7: Performance Characteristics")

    print("\n⏱️ Processing Times (Estimated):")
    print("   Background Removal: 100-300ms per image")
    print("   Contour Extraction: 10-50ms per image")
    print("   Shape Descriptor: 5-20ms per contour")
    print("   Embedding Generation: <5ms per descriptor")
    print("   Total (with background removal): ~200-400ms")
    print("   Total (without background removal): ~50-100ms")

    print("\n💾 Storage:")
    print("   Shape embedding: 128 floats × 4 bytes = 512 bytes")
    print("   Plus Qdrant overhead: ~1KB per product")
    print("   For 25K products: ~25MB shape vectors")

    print("\n🎯 Accuracy (Expected):")
    print("   Text-only: 0.79-0.82")
    print("   Text + Image: 0.85-0.88")
    print("   Text + Image + Shape: >0.90 ⭐")

    # ==================== Summary ====================
    print("\n" + "=" * 80)
    print("🎉 Phase 6 Demo Complete!")
    print("=" * 80)

    print("\n✅ Implemented Components:")
    print("   - BackgroundRemover (rembg/U2-Net)")
    print("   - ContourExtractor (OpenCV)")
    print("   - ShapeDescriptor (Hu + Fourier)")
    print("   - ShapeEmbedder (128-dim)")
    print("   - Integrated with MultiModalEmbeddingService")

    print("\n🎯 Tri-Modal RAG System Complete:")
    print("   📝 Text: 384-dim (Sentence Transformers)")
    print("   🖼️ Image: 1024-dim (OpenCLIP ViT-H-14)")
    print("   🔶 Shape: 128-dim (Hu + Fourier) ⭐ NEW")

    print("\n📋 Next Steps:")
    print("   - Phase 5: Advanced RAG Integration")
    print("   - Phase 8: Real-Time Optimization")
    print("   - Phase 9: Enterprise Deployment")

    print("\n📚 Learn More:")
    print("   - docs/MULTIMODAL_RAG_STRATEGY.md")
    print("   - src/core/image_matching/README.md (to be created)")
    print("   - src/core/multimodal/README.md")

    print("\n💡 Try Shape Embedding:")
    print("   from src.core.multimodal import MultiModalEmbeddingService")
    print("   embedder = MultiModalEmbeddingService(enable_shape=True)")
    print("   shape_emb = embedder.embed_shape('product.jpg')")
    print("   print(f'Shape embedding: {len(shape_emb)}-dim')  # 128-dim")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏸️  Demo interrupted")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
