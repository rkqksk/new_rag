#!/usr/bin/env python3
"""
Qdrant 50ml Container Data Analysis Script
Analyzes products containing "50ml" in the products_all collection
"""

import asyncio
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchText
import json
from typing import List, Dict, Any


async def analyze_50ml_products():
    """Analyze 50ml container products in Qdrant"""

    # Connect to Qdrant
    client = QdrantClient(host="localhost", port=6333)

    collection_name = "products_all"

    print(f"🔍 Connecting to Qdrant at localhost:6333")
    print(f"📦 Collection: {collection_name}\n")

    # 1. Get collection info
    try:
        collections = client.get_collections()
        collection_exists = any(c.name == collection_name for c in collections.collections)

        if not collection_exists:
            print(f"❌ Collection '{collection_name}' does not exist")
            print(f"Available collections: {[c.name for c in collections.collections]}")
            return

        print(f"✅ Collection exists: {collection_name}")

        # Get basic stats using count
        try:
            collection_info = client.get_collection(collection_name)
            print(f"   - Points count: {collection_info.points_count}")
        except:
            print(f"   - Using scroll to count points...")

        print()
    except Exception as e:
        print(f"❌ Error accessing collection: {e}")
        return

    # 2. Search for "50ml" products using scroll (get all matching)
    print("🔎 Searching for products containing '50ml'...\n")

    all_50ml_products = []
    offset = None

    # Scroll through all points to find 50ml products
    while True:
        scroll_result = client.scroll(
            collection_name=collection_name,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )

        points, next_offset = scroll_result

        # Filter points containing "50ml"
        for point in points:
            payload = point.payload
            # Check in various fields
            text_content = str(payload).lower()
            if "50ml" in text_content or "50 ml" in text_content:
                all_50ml_products.append({
                    "id": point.id,
                    "payload": payload
                })

        if next_offset is None:
            break
        offset = next_offset

    print(f"✅ Found {len(all_50ml_products)} products containing '50ml'\n")

    if not all_50ml_products:
        print("⚠️  No products found containing '50ml'")
        return

    # 3. Analyze payload structure
    print("📋 Analyzing payload structure...\n")

    all_fields = set()
    field_counts = {}

    for product in all_50ml_products:
        payload = product["payload"]
        for field in payload.keys():
            all_fields.add(field)
            field_counts[field] = field_counts.get(field, 0) + 1

    print("📊 Available fields in payloads:")
    for field in sorted(all_fields):
        count = field_counts[field]
        percentage = (count / len(all_50ml_products)) * 100
        print(f"   - {field}: {count}/{len(all_50ml_products)} ({percentage:.1f}%)")

    print()

    # Check if specification field exists
    has_specification = "specification" in all_fields
    has_image_url = "image_url" in all_fields

    print(f"🔍 Key field presence:")
    print(f"   - specification: {'✅ YES' if has_specification else '❌ NO'}")
    print(f"   - image_url: {'✅ YES' if has_image_url else '❌ NO'}")
    print()

    # 4. Show 5 sample products
    print("📝 Sample products (5 examples):\n")
    print("=" * 80)

    for i, product in enumerate(all_50ml_products[:5], 1):
        print(f"\n🔖 Product {i} (ID: {product['id']})")
        print(f"{'-' * 80}")
        payload = product["payload"]

        # Pretty print payload
        for key, value in payload.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"   {key}: {value[:100]}... (truncated)")
            else:
                print(f"   {key}: {value}")

    print("\n" + "=" * 80)

    # 5. Provide recommendations
    print("\n💡 Analysis & Recommendations:\n")

    if not has_specification:
        print("⚠️  'specification' field is MISSING")
        print("\n📌 Suggested approach to add specification field:")
        print("""
   Option 1: Extract from existing text/content field
   - Parse product descriptions
   - Extract structured specs (capacity, material, dimensions)
   - Update payloads with new 'specification' field

   Option 2: Re-ingest with enhanced crawler
   - Modify crawler to extract specification data
   - Update Qdrant ingestion pipeline
   - Add specification field during document processing

   Option 3: Hybrid approach
   - Use LLM to extract specs from text/content
   - Validate and structure the data
   - Batch update existing records
        """)
    else:
        print("✅ 'specification' field EXISTS")
        print("   → Review sample data above to verify quality")

    if not has_image_url:
        print("\n⚠️  'image_url' field is MISSING")
        print("   → Consider adding during re-ingestion")
    else:
        print("\n✅ 'image_url' field EXISTS")

    # 6. Export detailed analysis to JSON
    output_file = "/Users/oypnus/Project/rag-enterprise/claudedocs/50ml_analysis.json"
    analysis_data = {
        "total_50ml_products": len(all_50ml_products),
        "collection_info": {
            "name": collection_name,
            "points_count": getattr(collection_info, 'points_count', 'unknown') if 'collection_info' in locals() else 'unknown'
        },
        "field_analysis": {
            field: {
                "count": field_counts[field],
                "percentage": round((field_counts[field] / len(all_50ml_products)) * 100, 2)
            }
            for field in sorted(all_fields)
        },
        "has_specification": has_specification,
        "has_image_url": has_image_url,
        "sample_products": [
            {
                "id": str(p["id"]),
                "payload": p["payload"]
            }
            for p in all_50ml_products[:5]
        ],
        "all_product_ids": [str(p["id"]) for p in all_50ml_products]
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Detailed analysis exported to: {output_file}")
    print(f"   → {len(all_50ml_products)} products analyzed")


if __name__ == "__main__":
    asyncio.run(analyze_50ml_products())
