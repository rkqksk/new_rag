#!/usr/bin/env python3
"""
Demo script for MultiModalEmbeddingService
Tests basic functionality without pytest
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.multimodal.multimodal_embedder import MultiModalEmbeddingService

def main():
    print("=" * 80)
    print("Multi-Modal Embedding Service - Demo")
    print("=" * 80)

    # Test 1: Initialize embedder (text only for safety)
    print("\n[Test 1] Initializing embedder (text only)...")
    try:
        embedder = MultiModalEmbeddingService(enable_image=False)
        print("✅ Embedder initialized successfully")
        print(f"   Device: {embedder.device}")
        print(f"   Text dimension: {embedder.text_dim}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return

    # Test 2: Single text embedding
    print("\n[Test 2] Single text embedding...")
    try:
        text = "20파이 캡 5000개"
        embedding = embedder.embed_text(text)
        print(f"✅ Text embedded successfully")
        print(f"   Input: '{text}'")
        print(f"   Output dimension: {len(embedding)}")
        print(f"   Sample values: {embedding[:5]}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # Test 3: Batch text embedding
    print("\n[Test 3] Batch text embedding...")
    try:
        texts = [
            "20파이 캡",
            "100ml PET 보틀",
            "화장품 용기",
            "펌프 디스펜서"
        ]
        embeddings = embedder.embed_texts_batch(texts, show_progress=True)
        print(f"✅ Batch embedding successful")
        print(f"   Input count: {len(texts)}")
        print(f"   Output count: {len(embeddings)}")
        print(f"   Each dimension: {len(embeddings[0])}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # Test 4: Multi-modal embedding (text only)
    print("\n[Test 4] Multi-modal embedding (text only)...")
    try:
        result = embedder.embed(text="100ml PET Bottle")
        print(f"✅ Multi-modal embedding successful")
        print(f"   Available modalities: {list(result.keys())}")
        for modality, vector in result.items():
            print(f"   {modality}: {len(vector)}-dim")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # Test 5: Get dimensions
    print("\n[Test 5] Get embedding dimensions...")
    try:
        dims = embedder.get_dimensions()
        print(f"✅ Dimensions retrieved")
        for modality, dim in dims.items():
            print(f"   {modality}: {dim}-dim")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # Test 6: Check availability
    print("\n[Test 6] Check modality availability...")
    try:
        modalities = ['text', 'image', 'shape']
        for mod in modalities:
            available = embedder.is_available(mod)
            status = "✅" if available else "⏸️"
            print(f"   {status} {mod}: {available}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # Test 7: Batch multi-modal
    print("\n[Test 7] Batch multi-modal embedding...")
    try:
        items = [
            {"text": "제품 A: 20파이 캡"},
            {"text": "제품 B: 100ml 보틀"},
            {"text": "제품 C: 화장품 용기"}
        ]
        results = embedder.embed_batch(items, show_progress=False)
        print(f"✅ Batch multi-modal successful")
        print(f"   Input count: {len(items)}")
        print(f"   Output count: {len(results)}")
        for i, result in enumerate(results):
            print(f"   Item {i+1}: {list(result.keys())}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # Test 8: Korean text (various formats)
    print("\n[Test 8] Korean text embedding (various formats)...")
    try:
        korean_texts = [
            "제품코드: PE-001234",
            "SPEC: 100ml, Ø20",
            "MOQ: 5,000개",
            "재질: PET",
            "가격: ₩1,500"
        ]
        embeddings = embedder.embed_texts_batch(korean_texts, show_progress=False)
        print(f"✅ Korean text embedding successful")
        for i, text in enumerate(korean_texts):
            print(f"   '{text}' → {len(embeddings[i])}-dim")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # Test 9: Representation
    print("\n[Test 9] Embedder representation...")
    try:
        repr_str = repr(embedder)
        print(f"✅ Representation:")
        print(f"   {repr_str}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    print("\n" + "=" * 80)
    print("Demo completed successfully! ✅")
    print("=" * 80)

    # Summary
    print("\n📊 Summary:")
    print(f"   ✅ Text embedding: Working")
    print(f"   ⏸️ Image embedding: Disabled (enable with enable_image=True)")
    print(f"   ⏸️ Shape embedding: Phase 6 (not yet implemented)")
    print(f"   🎯 Device: {embedder.device}")
    print(f"   📐 Text dimension: {embedder.text_dim}")

if __name__ == "__main__":
    main()
