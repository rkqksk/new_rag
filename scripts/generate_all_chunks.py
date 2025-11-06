#!/usr/bin/env python3
"""
전체 데이터셋 Atomic Chunks 생성 스크립트
Generate All Atomic Chunks from Product Dataset

목적: 모든 제품 데이터를 Atomic Chunks로 변환하여 저장
"""

import sys
import json
from pathlib import Path
from typing import List, Dict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.advanced_chunk_generator import (
    AdvancedChunkGenerator,
    AtomicChunk,
    generate_all_chunks_atomic,
    get_chunk_statistics
)


def load_bottle_jar_products() -> List[Dict]:
    """Bottle/Jar 제품 데이터 로드"""
    data_path = PROJECT_ROOT / "data/processed/products/metadata/product_dictionary_with_accessories.json"

    if not data_path.exists():
        print(f"Warning: {data_path} not found")
        return []

    with open(data_path, 'r', encoding='utf-8') as f:
        products_dict = json.load(f)

    # Convert dict values to list
    products = list(products_dict.values())
    print(f"Loaded {len(products)} Bottle/Jar products")
    return products


def load_cap_pump_products() -> List[Dict]:
    """Cap/Pump 제품 데이터 로드"""
    data_path = PROJECT_ROOT / "data/processed/products/metadata/cap_pump_product_list_complete.json"

    if not data_path.exists():
        print(f"Warning: {data_path} not found")
        return []

    with open(data_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    print(f"Loaded {len(products)} Cap/Pump products")
    return products


def save_chunks(chunks: List[AtomicChunk], output_path: Path):
    """청크 데이터 저장"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict format
    chunks_data = [chunk.to_dict() for chunk in chunks]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks_data, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(chunks)} chunks to {output_path}")


def main():
    """메인 실행 함수"""
    print("="*80)
    print("ATOMIC CHUNKS GENERATION")
    print("="*80)

    # Step 1: 데이터 로드
    print("\n[Step 1] Loading product data...")
    bottle_jar_products = load_bottle_jar_products()
    cap_pump_products = load_cap_pump_products()

    all_products = bottle_jar_products + cap_pump_products
    print(f"\nTotal products: {len(all_products)}")

    if not all_products:
        print("Error: No products found!")
        return 1

    # Step 2: Atomic Chunks 생성
    print("\n[Step 2] Generating atomic chunks...")
    chunks = generate_all_chunks_atomic(all_products)

    print(f"\nGenerated {len(chunks)} atomic chunks")
    print(f"Average {len(chunks) / len(all_products):.1f} chunks per product")

    # Step 3: 통계
    print("\n[Step 3] Statistics")
    print("─"*80)
    stats = get_chunk_statistics(chunks)

    print(f"\nTotal Chunks: {stats['total_chunks']}")

    print(f"\nBy Category:")
    for cat, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}")

    print(f"\nBy Field Type (Top 10):")
    sorted_fields = sorted(stats['by_field_type'].items(), key=lambda x: x[1], reverse=True)
    for field, count in sorted_fields[:10]:
        print(f"  {field}: {count}")

    print(f"\nBy Priority:")
    for priority, count in sorted(stats['by_priority'].items()):
        print(f"  {priority}: {count}")

    # Step 4: 저장
    print("\n[Step 4] Saving chunks...")
    output_path = PROJECT_ROOT / "data/embeddings/atomic_chunks.json"
    save_chunks(chunks, output_path)

    # Step 5: 샘플 출력
    print("\n[Step 5] Sample chunks (first 5)")
    print("─"*80)
    for idx, chunk in enumerate(chunks[:5], 1):
        print(f"\n{idx}. [{chunk.field_type.value.upper()}] (Priority: {chunk.priority})")
        print(f"   ID: {chunk.chunk_id}")
        print(f"   Text: {chunk.text}")
        print(f"   Product: {chunk.metadata.get('product_name', 'N/A')}")

    print("\n" + "="*80)
    print("✅ ATOMIC CHUNKS GENERATION COMPLETED")
    print("="*80)
    print(f"\nOutput: {output_path}")
    print(f"Total Chunks: {len(chunks)}")
    print(f"Ready for embedding generation!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
