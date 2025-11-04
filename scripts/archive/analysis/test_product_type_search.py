#!/usr/bin/env python3
"""
Test product type filtering in search
"""

import sys
sys.path.append('.')

from app.api_simple import search_products, load_products

def test_product_type_search():
    """Test that product type filtering works correctly"""

    print("=" * 80)
    print("PRODUCT TYPE SEARCH TEST")
    print("=" * 80)

    # Load products
    print("\n📦 Loading products...")
    products = load_products()
    print(f"Loaded {len(products)} products")

    # Test cases
    test_cases = [
        {
            "query": "24파이 펌프",
            "expected_type": "PUMP",
            "description": "24파이 펌프 검색 → PUMP 제품만 나와야 함"
        },
        {
            "query": "24파이 캡",
            "expected_type": "CAP",
            "description": "24파이 캡 검색 → CAP 제품만 나와야 함"
        },
        {
            "query": "50ml 병",
            "expected_type": "BOTTLE",
            "description": "50ml 병 검색 → BOTTLE 제품만 나와야 함"
        },
        {
            "query": "20파이",
            "expected_type": None,
            "description": "20파이 검색 (타입 없음) → 모든 타입 제품 나올 수 있음"
        },
    ]

    for test in test_cases:
        print(f"\n{'='*80}")
        print(f"🔍 Test: {test['description']}")
        print(f"Query: \"{test['query']}\"")
        print(f"Expected type: {test['expected_type']}")
        print("-" * 80)

        results = search_products(test['query'], products, limit=10)

        print(f"Results: {len(results)} products found")

        if not results:
            print("⚠️  No results found!")
            continue

        # Check product types
        product_types = set()
        for i, product in enumerate(results, 1):
            product_type = product.get('category_type', 'UNKNOWN')
            product_types.add(product_type)
            neck_size = product.get('neck_size', 'N/A')
            print(f"  {i}. {product.get('product_code')}: {product.get('product_name')}")
            print(f"     Type: {product_type}, Neck: {neck_size}")

        # Validate
        if test['expected_type']:
            if len(product_types) == 1 and test['expected_type'] in product_types:
                print(f"\n✅ PASS: All results are {test['expected_type']} type")
            else:
                print(f"\n❌ FAIL: Found types {product_types}, expected only {test['expected_type']}")
        else:
            print(f"\n✅ INFO: Found types {product_types} (no specific type expected)")

if __name__ == "__main__":
    test_product_type_search()
