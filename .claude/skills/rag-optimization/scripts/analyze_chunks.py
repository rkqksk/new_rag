#!/usr/bin/env python3
"""
Analyze chunk distribution and quality for PETER RAG system
"""
import sys
from pathlib import Path
from collections import Counter
from typing import List, Dict
import statistics

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

def count_tokens(text: str) -> int:
    """Simple token counter"""
    # Rough estimate: ~1.3 chars per token for Korean
    return int(len(text) / 1.3)

def analyze_chunks(collection_name: str = "products"):
    """
    Analyze chunk distribution in Qdrant collection
    """
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(host="localhost", port=6333)

        # Get collection info
        collection_info = client.get_collection(collection_name)
        print(f"Collection: {collection_name}")
        print(f"Total vectors: {collection_info.vectors_count}")
        print()

        # Sample chunks
        limit = 1000
        points = client.scroll(
            collection_name=collection_name,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )[0]

        if not points:
            print("No points found in collection")
            return

        # Analyze sizes
        chunk_sizes = []
        sources = []
        chunk_types = []

        for point in points:
            payload = point.payload

            if 'text' in payload:
                tokens = count_tokens(payload['text'])
                chunk_sizes.append(tokens)

            if 'source' in payload:
                sources.append(payload['source'])

            if 'chunk_type' in payload:
                chunk_types.append(payload['chunk_type'])

        # Statistics
        print("=" * 60)
        print("Chunk Size Analysis")
        print("=" * 60)
        print(f"Chunks analyzed: {len(chunk_sizes)}")
        print(f"Mean size: {statistics.mean(chunk_sizes):.1f} tokens")
        print(f"Median size: {statistics.median(chunk_sizes):.1f} tokens")
        print(f"Std dev: {statistics.stdev(chunk_sizes):.1f} tokens")
        print(f"Min size: {min(chunk_sizes)} tokens")
        print(f"Max size: {max(chunk_sizes)} tokens")
        print()

        # Distribution
        print("Size Distribution:")
        bins = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, float('inf')]
        bin_labels = ["0-100", "100-200", "200-300", "300-400", "400-500",
                      "500-600", "600-700", "700-800", "800-900", "900-1000", "1000+"]

        distribution = Counter()
        for size in chunk_sizes:
            for i, (low, high) in enumerate(zip(bins[:-1], bins[1:])):
                if low <= size < high:
                    distribution[bin_labels[i]] += 1
                    break

        for label in bin_labels:
            count = distribution[label]
            pct = count / len(chunk_sizes) * 100
            bar = "█" * int(pct / 2)
            print(f"{label:>10}: {count:>4} ({pct:>5.1f}%) {bar}")
        print()

        # Source analysis
        if sources:
            print("=" * 60)
            print("Source Distribution")
            print("=" * 60)
            source_counts = Counter(sources)
            for source, count in source_counts.most_common(10):
                print(f"{source}: {count}")
            print()

        # Type analysis
        if chunk_types:
            print("=" * 60)
            print("Chunk Type Distribution")
            print("=" * 60)
            type_counts = Counter(chunk_types)
            for chunk_type, count in type_counts.most_common():
                pct = count / len(chunk_types) * 100
                print(f"{chunk_type}: {count} ({pct:.1f}%)")
            print()

        # Quality metrics
        print("=" * 60)
        print("Quality Metrics")
        print("=" * 60)

        # Too small chunks (< 100 tokens)
        too_small = sum(1 for s in chunk_sizes if s < 100)
        print(f"Too small chunks (< 100): {too_small} ({too_small/len(chunk_sizes)*100:.1f}%)")

        # Too large chunks (> 800 tokens)
        too_large = sum(1 for s in chunk_sizes if s > 800)
        print(f"Too large chunks (> 800): {too_large} ({too_large/len(chunk_sizes)*100:.1f}%)")

        # Optimal range (200-600 tokens)
        optimal = sum(1 for s in chunk_sizes if 200 <= s <= 600)
        print(f"Optimal range (200-600): {optimal} ({optimal/len(chunk_sizes)*100:.1f}%)")
        print()

        # Recommendations
        print("=" * 60)
        print("Recommendations")
        print("=" * 60)

        avg_size = statistics.mean(chunk_sizes)
        if avg_size < 300:
            print("⚠️  Average chunk size is small. Consider:")
            print("   - Increasing chunk_size parameter")
            print("   - Reducing min_chunk_size threshold")
        elif avg_size > 700:
            print("⚠️  Average chunk size is large. Consider:")
            print("   - Decreasing chunk_size parameter")
            print("   - Using semantic chunking for better boundaries")
        else:
            print("✅ Chunk sizes are in good range")

        if too_small / len(chunk_sizes) > 0.1:
            print("\n⚠️  High proportion of small chunks (> 10%)")
            print("   - Review min_chunk_size setting")
            print("   - Check for incomplete documents")

        if too_large / len(chunk_sizes) > 0.1:
            print("\n⚠️  High proportion of large chunks (> 10%)")
            print("   - Enable semantic chunking")
            print("   - Reduce max chunk size")

    except ImportError:
        print("Error: qdrant-client not installed")
        print("Run: pip install qdrant-client")
    except Exception as e:
        print(f"Error analyzing chunks: {e}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze RAG chunk distribution")
    parser.add_argument("--collection", default="products", help="Qdrant collection name")

    args = parser.parse_args()

    analyze_chunks(args.collection)
