#!/usr/bin/env python3
"""
Test dosage-based pump recommendation system
"""

import sys
sys.path.append('.')

from app.api_simple import search_products, load_products

def test_dosage_search():
    """Test that dosage filtering works correctly"""

    print("=" * 80)
    print("DOSAGE SEARCH TEST")
    print("=" * 80)

    # Load products
    print("\n📦 Loading products...")
    products = load_products()
    print(f"Loaded {len(products)} products")

    # Test cases
    test_cases = [
        {
            "query": "0.12cc 펌프",
            "expected_dosage": 0.12,
            "expected_type": "PUMP",
            "description": "0.12cc 펌프 → 0.12cc PUMP만"
        },
        {
            "query": "0.1cc 미스트",
            "expected_dosage": 0.1,
            "expected_type": "PUMP",
            "description": "0.1cc 미스트 → 0.1cc PUMP만"
        },
        {
            "query": "0.15cc 스프레이",
            "expected_dosage": 0.15,
            "expected_type": "PUMP",
            "description": "0.15cc 스프레이 → 0.15cc PUMP만"
        },
        {
            "query": "토출량 0.12 펌프",
            "expected_dosage": 0.12,
            "expected_type": "PUMP",
            "description": "토출량 0.12 펌프 → 0.12cc PUMP만"
        },
        {
            "query": "24파이 0.12cc 펌프",
            "expected_dosage": 0.12,
            "expected_neck": "24파이",
            "expected_type": "PUMP",
            "description": "24파이 0.12cc 펌프 → 24파이 0.12cc PUMP만"
        },
    ]

    for test in test_cases:
        print(f"\n{'='*80}")
        print(f"🔍 Test: {test['description']}")
        print(f"Query: \"{test['query']}\"")
        print(f"Expected dosage: {test.get('expected_dosage')}, Expected type: {test.get('expected_type')}")
        print("-" * 80)

        results = search_products(test['query'], products, limit=10)

        print(f"Results: {len(results)} products found")

        if not results:
            print("⚠️  No results found!")
            continue

        # Check dosages and product types
        dosages = set()
        product_types = set()
        neck_sizes = set()

        for i, product in enumerate(results, 1):
            dosage_value = product.get('specifications', {}).get('dosage_value')
            dosage_str = product.get('specifications', {}).get('dosage')
            product_type = product.get('category_type', 'UNKNOWN')
            neck_size = product.get('neck_size', 'N/A')

            dosages.add(dosage_value)
            product_types.add(product_type)
            neck_sizes.add(neck_size)

            print(f"  {i}. {product.get('product_code')}: {product.get('product_name')}")
            print(f"     Dosage: {dosage_str} ({dosage_value}), Type: {product_type}, Neck: {neck_size}")

        # Validate
        success = True

        # Check product type
        if test.get('expected_type'):
            if len(product_types) == 1 and test['expected_type'] in product_types:
                print(f"\n✅ Product Type OK: All results are {test['expected_type']}")
            else:
                print(f"\n❌ Product Type FAIL: Found {product_types}, expected {test['expected_type']}")
                success = False

        # Check dosage
        if test.get('expected_dosage'):
            if len(dosages) == 1 and test['expected_dosage'] in dosages:
                print(f"✅ Dosage OK: All results are {test['expected_dosage']}cc")
            else:
                print(f"❌ Dosage FAIL: Found {dosages}, expected {test['expected_dosage']}")
                success = False

        # Check neck size if specified
        if test.get('expected_neck'):
            if len(neck_sizes) == 1 and test['expected_neck'] in neck_sizes:
                print(f"✅ Neck Size OK: All results are {test['expected_neck']}")
            else:
                print(f"❌ Neck Size FAIL: Found {neck_sizes}, expected {test['expected_neck']}")
                success = False

        if success:
            print("\n🎉 PASS")
        else:
            print("\n💥 FAIL")


def test_dosage_recommendation():
    """Test dosage-based pump recommendation for bottles"""

    print("\n" + "=" * 80)
    print("DOSAGE RECOMMENDATION TEST")
    print("=" * 80)

    from app.conversation.compatibility import (
        find_compatible_accessories,
        get_recommended_dosage_for_capacity
    )

    # Load products
    print("\n📦 Loading products...")
    products = load_products()
    print(f"Loaded {len(products)} products")

    # Test cases: different bottle sizes
    test_cases = [
        {
            "query": "50ml 병",
            "expected_dosage_range": (0.1, 0.15),
            "description": "50ml 용기 → 0.1-0.15cc 펌프 추천 (미스트)"
        },
        {
            "query": "100ml 병",
            "expected_dosage_range": (0.12, 0.2),
            "description": "100ml 용기 → 0.12-0.2cc 펌프 추천 (에센스)"
        },
        {
            "query": "150ml 병",
            "expected_dosage_range": (0.2, 0.3),
            "description": "150ml 용기 → 0.2-0.3cc 펌프 추천 (일반)"
        },
        {
            "query": "250ml 병",
            "expected_dosage_range": (0.3, 0.5),
            "description": "250ml 용기 → 0.3-0.5cc 펌프 추천 (로션)"
        },
    ]

    for test in test_cases:
        print(f"\n{'='*80}")
        print(f"🔍 Test: {test['description']}")
        print(f"Query: \"{test['query']}\"")
        print(f"Expected dosage range: {test['expected_dosage_range']}")
        print("-" * 80)

        # Search for bottles
        bottles = search_products(test['query'], products, limit=5)

        if not bottles:
            print("⚠️  No bottles found!")
            continue

        print(f"\nFound {len(bottles)} bottles:")
        for i, bottle in enumerate(bottles, 1):
            print(f"  {i}. {bottle.get('product_code')}: {bottle.get('product_name')} ({bottle.get('capacity')})")

        # Find compatible accessories
        accessories = find_compatible_accessories(bottles, products, limit=5)

        if not accessories['groups']:
            print("\n⚠️  No compatible accessories found!")
            continue

        # Check recommendations
        for group in accessories['groups']:
            neck_size = group['neck_size']
            recommended_range = group.get('recommended_dosage_range', (0, 0))
            avg_capacity = group.get('avg_bottle_capacity', 0)
            pumps = group['pumps']

            print(f"\n📍 Neck Size: {neck_size}파이")
            print(f"   Avg Bottle Capacity: {avg_capacity:.1f}ml")
            print(f"   Recommended Dosage: {recommended_range[0]}-{recommended_range[1]}cc")
            print(f"   Compatible Pumps: {len(pumps)}")

            # Show top 3 recommended pumps
            print("\n   Top Recommended Pumps (sorted by dosage suitability):")
            for i, pump in enumerate(pumps[:3], 1):
                dosage = pump.get('dosage', 0)
                suitability = pump.get('dosage_suitability', 0)
                print(f"     {i}. {pump.get('product_name')}")
                print(f"        Dosage: {dosage}cc, Suitability: {suitability:.0f}%")

            # Validate recommendation range
            if recommended_range == test['expected_dosage_range']:
                print(f"\n   ✅ Dosage Range OK: {recommended_range}")
            else:
                print(f"\n   ❌ Dosage Range FAIL: Got {recommended_range}, expected {test['expected_dosage_range']}")

        print("\n🎉 Test Complete")


if __name__ == "__main__":
    # Run both tests
    test_dosage_search()
    print("\n" + "=" * 80)
    test_dosage_recommendation()
