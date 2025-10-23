#!/usr/bin/env python3
"""Find exact 50ml products in Qdrant"""

from qdrant_client import QdrantClient
import json
import re


def find_exact_50ml():
    client = QdrantClient(host="localhost", port=6333)
    collection_name = "products_all"

    print("🔍 Searching for EXACT 50ml products...\n")

    exact_50ml = []
    offset = None

    # Pattern to match exactly 50ml (not 150ml, 250ml, etc.)
    pattern = re.compile(r'\b50\s*ml\b', re.IGNORECASE)

    while True:
        scroll_result = client.scroll(
            collection_name=collection_name,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )

        points, next_offset = scroll_result

        for point in points:
            payload = point.payload
            product_name = payload.get('product_name', '')

            # Check if product name contains exactly "50ml" (not 150ml, 250ml, etc.)
            if pattern.search(product_name):
                exact_50ml.append({
                    "id": point.id,
                    "product_name": product_name,
                    "category": payload.get('category', ''),
                    "payload": payload
                })

        if next_offset is None:
            break
        offset = next_offset

    print(f"✅ Found {len(exact_50ml)} EXACT 50ml products\n")

    if exact_50ml:
        print("📋 Exact 50ml products:")
        print("=" * 80)
        for i, product in enumerate(exact_50ml, 1):
            print(f"\n{i}. {product['product_name']}")
            print(f"   Category: {product['category']}")
            print(f"   ID: {product['id']}")
            print(f"   Full payload: {json.dumps(product['payload'], ensure_ascii=False, indent=2)}")
            print("-" * 80)

        # Save to file
        output_file = "/Users/oypnus/Project/rag-enterprise/claudedocs/exact_50ml_products.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(exact_50ml, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Saved to: {output_file}")
    else:
        print("⚠️  No exact 50ml products found in the database")
        print("\nSearching for similar products...")

        # Search for products that might be 50ml
        similar = []
        offset = None

        while True:
            scroll_result = client.scroll(
                collection_name=collection_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )

            points, next_offset = scroll_result

            for point in points:
                payload = point.payload
                product_name = payload.get('product_name', '').lower()

                # Look for variations
                if any(term in product_name for term in ['50', 'ml', '용기', 'bottle', 'container']):
                    if '50' in product_name:
                        similar.append({
                            "product_name": payload.get('product_name'),
                            "category": payload.get('category')
                        })

            if next_offset is None:
                break
            offset = next_offset

        print(f"\nFound {len(similar)} products containing '50':")
        for prod in similar[:10]:  # Show first 10
            print(f"  - {prod['product_name']} ({prod['category']})")


if __name__ == "__main__":
    find_exact_50ml()
