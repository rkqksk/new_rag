#!/usr/bin/env python3
"""
Test enriched API responses with all categories and expert data
"""
import requests
import json

API_URL = "http://localhost:8000"

def test_search_with_enrichment(query, limit=3):
    """Test search API and display enrichment data"""
    print(f"\n{'='*80}")
    print(f"🔍 Query: {query}")
    print(f"{'='*80}")

    response = requests.get(f"{API_URL}/api/v1/products/search", params={
        'query': query,
        'limit': limit
    })

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return

    data = response.json()
    print(f"\n📊 Total results: {data['total']}")
    print(f"✅ Showing first {len(data['products'])} products:\n")

    for i, product in enumerate(data['products'], 1):
        print(f"\n[{i}] {product['product_id']}: {product['product_name']}")
        print(f"  📦 Material: {product['material']} | Capacity: {product['capacity']}")
        print(f"  🏷️  Category: {product['category']} | Tags: {product['tags']}")
        print(f"  🏭 Source: {product['source']}")

        # Material details
        mat_details = product.get('material_details', {})
        if mat_details and mat_details.get('type'):
            print(f"\n  📝 Material Details:")
            print(f"     Type: {mat_details.get('type')} ({mat_details.get('full_name', 'N/A')})")
            print(f"     Resin Code: {mat_details.get('resin_code', 'N/A')}")
            print(f"     Properties: {', '.join(mat_details.get('properties', []))}")
            print(f"     Common Uses: {', '.join(mat_details.get('common_uses', []))}")

        # Capacity category
        cap_cat = product.get('capacity_category', {})
        if cap_cat and cap_cat.get('size'):
            print(f"\n  📏 Capacity Category:")
            print(f"     Size: {cap_cat.get('size')} ({cap_cat.get('range')})")
            print(f"     Use Case: {cap_cat.get('use_case')}")

        # Product category
        prod_cat = product.get('product_category', '')
        if prod_cat:
            print(f"\n  🔖 Product Category: {prod_cat}")

        # Regulatory compliance (summary)
        reg = product.get('regulatory_compliance', {})
        if reg:
            fda = reg.get('fda', {})
            eu = reg.get('eu', {})
            print(f"\n  ⚖️  Regulatory: FDA: {bool(fda)}, EU: {bool(eu)}")

    print(f"\n{'='*80}\n")

def test_all_categories():
    """Test that all categories are loaded"""
    print(f"\n{'='*80}")
    print(f"📊 Testing All Categories")
    print(f"{'='*80}\n")

    response = requests.get(f"{API_URL}/api/v1/products")

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return

    data = response.json()
    total = data['total']
    print(f"✅ Total products: {total}")

    # Count by category
    categories = {}
    for product in data['products']:
        cat = product.get('category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1

    print(f"\n📈 Breakdown by category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    # Test 1: All categories loaded
    test_all_categories()

    # Test 2: Search with enrichment - Korean PET
    test_search_with_enrichment("50미리 페트", limit=2)

    # Test 3: Search Cap products
    test_search_with_enrichment("캡", limit=2)

    # Test 4: Search Jar products
    test_search_with_enrichment("자", limit=2)

    print("✅ All tests completed!")
