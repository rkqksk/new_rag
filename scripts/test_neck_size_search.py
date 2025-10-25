#!/usr/bin/env python3
"""
Test neck size filtering in search
"""

import sys
sys.path.append('.')

from app.api_simple import search_products, load_products

def test_neck_size_search():
    """Test that neck size filtering works correctly"""

    print("=" * 80)
    print("NECK SIZE SEARCH TEST")
    print("=" * 80)

    # Load products
    print("\n📦 Loading products...")
    products = load_products()
    print(f"Loaded {len(products)} products")

    # Test cases
    test_cases = [
        {
            "query": "24파이 에센스 펌프",
            "expected_neck": "24파이",
            "expected_type": "PUMP",
            "description": "24파이 에센스 펌프 → 24파이 PUMP만"
        },
        {
            "query": "20파이 펌프",
            "expected_neck": "20파이",
            "expected_type": "PUMP",
            "description": "20파이 펌프 → 20파이 PUMP만"
        },
        {
            "query": "24파이 캡",
            "expected_neck": "24파이",
            "expected_type": "CAP",
            "description": "24파이 캡 → 24파이 CAP만"
        },
        {
            "query": "28파이 펌프",
            "expected_neck": "28파이",
            "expected_type": "PUMP",
            "description": "28파이 펌프 → 28파이 PUMP만"
        },
        {
            "query": "펌프",
            "expected_neck": None,
            "expected_type": "PUMP",
            "description": "펌프 (네크사이즈 없음) → 모든 네크사이즈 PUMP"
        },
    ]

    for test in test_cases:
        print(f"\n{'='*80}")
        print(f"🔍 Test: {test['description']}")
        print(f"Query: \"{test['query']}\"")
        print(f"Expected neck: {test['expected_neck']}, Expected type: {test['expected_type']}")
        print("-" * 80)

        results = search_products(test['query'], products, limit=10)

        print(f"Results: {len(results)} products found")

        if not results:
            print("⚠️  No results found!")
            continue

        # Check neck sizes and product types
        neck_sizes = set()
        product_types = set()
        for i, product in enumerate(results, 1):
            neck_size = product.get('neck_size', 'N/A')
            product_type = product.get('category_type', 'UNKNOWN')
            neck_sizes.add(neck_size)
            product_types.add(product_type)
            print(f"  {i}. {product.get('product_code')}: {product.get('product_name')}")
            print(f"     Neck: {neck_size}, Type: {product_type}")

        # Validate
        success = True

        # Check product type
        if test['expected_type']:
            if len(product_types) == 1 and test['expected_type'] in product_types:
                print(f"\n✅ Product Type OK: All results are {test['expected_type']}")
            else:
                print(f"\n❌ Product Type FAIL: Found {product_types}, expected {test['expected_type']}")
                success = False

        # Check neck size
        if test['expected_neck']:
            if len(neck_sizes) == 1 and test['expected_neck'] in neck_sizes:
                print(f"✅ Neck Size OK: All results are {test['expected_neck']}")
            else:
                print(f"❌ Neck Size FAIL: Found {neck_sizes}, expected {test['expected_neck']}")
                success = False
        else:
            print(f"✅ Neck Size INFO: Found {neck_sizes} (no specific size expected)")

        if success:
            print("\n🎉 PASS")
        else:
            print("\n💥 FAIL")

if __name__ == "__main__":
    test_neck_size_search()
