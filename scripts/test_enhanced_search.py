#!/usr/bin/env python3
"""
Test Enhanced Search Logic

Tests problematic queries that previously returned false matches:
- "50ml" should NOT match "50파이 튜브" (neck size 50 ≠ capacity 50ml)
- "20파이" should NOT match "20ml 병" (neck size 20 ≠ capacity 20ml)
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Add skill scripts to path
skill_path = Path(__file__).parent.parent / '.claude/skills/rag-pipeline/scripts'
sys.path.insert(0, str(skill_path))

from skill import vector_search
import json


def test_query(query: str, expected_filters: dict = None):
    """
    Test a single query and display results

    Args:
        query: User query
        expected_filters: Expected filters that should be applied
    """
    print("\n" + "="*80)
    print(f"🔍 Testing Query: '{query}'")
    print("="*80)

    result = vector_search({
        'query': query,
        'top_k': 5,
        'collections': ['onehago_v2']  # Use enhanced collection
    })

    if result['status'] != 'success':
        print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
        return False

    print(f"\n📊 Query Analysis:")
    print(f"   Original Query: {result['query']}")
    print(f"   Refined Query: {result.get('refined_query', 'N/A')}")

    intent = result.get('intent', {})
    if intent:
        print(f"\n🎯 Extracted Intent:")
        if intent.get('capacity'):
            print(f"   Capacity: {intent['capacity']}{intent['capacity_unit']}")
        if intent.get('neck_size'):
            print(f"   Neck Size: {intent['neck_size']}mm")
        if intent.get('materials'):
            print(f"   Materials: {', '.join(intent['materials'])}")

    print(f"\n📦 Results ({len(result['results'])} products):\n")

    for i, res in enumerate(result['results'], 1):
        meta = res['metadata']
        print(f"   {i}. {meta.get('product_name', 'N/A')[:60]}")
        print(f"      Score: {res['score']:.4f}")
        print(f"      ID: {meta.get('product_id', 'N/A')}")

        # Show relevant specs
        if meta.get('capacity_value'):
            print(f"      Capacity: {meta['capacity_value']}{meta.get('capacity_unit', '')}")
        if meta.get('neck_size'):
            print(f"      Neck Size: {meta['neck_size']}mm")
        if meta.get('materials'):
            print(f"      Materials: {', '.join(meta['materials'])}")

    # Validate results
    if expected_filters:
        print(f"\n✅ Validation:")
        validation_passed = True

        for res in result['results']:
            meta = res['metadata']

            # Check capacity filter
            if 'capacity_value' in expected_filters:
                expected_cap = expected_filters['capacity_value']
                actual_cap = meta.get('capacity_value')

                if actual_cap is None:
                    print(f"   ⚠️  Product {meta.get('product_id')} has no capacity data")
                    validation_passed = False
                elif abs(actual_cap - expected_cap) > expected_cap * 0.1:  # 10% tolerance
                    print(f"   ❌ Product {meta.get('product_id')} capacity mismatch: {actual_cap} vs {expected_cap}")
                    validation_passed = False

            # Check neck size filter
            if 'neck_size' in expected_filters:
                expected_neck = expected_filters['neck_size']
                actual_neck = meta.get('neck_size')

                if actual_neck is None:
                    print(f"   ⚠️  Product {meta.get('product_id')} has no neck size data")
                    validation_passed = False
                elif abs(actual_neck - expected_neck) > 2:  # 2mm tolerance
                    print(f"   ❌ Product {meta.get('product_id')} neck size mismatch: {actual_neck} vs {expected_neck}")
                    validation_passed = False

            # Check material filter
            if 'materials' in expected_filters:
                expected_mats = set(expected_filters['materials'])
                actual_mats = set(meta.get('materials', []))

                if not expected_mats & actual_mats:  # No intersection
                    print(f"   ❌ Product {meta.get('product_id')} material mismatch: {actual_mats} vs {expected_mats}")
                    validation_passed = False

        if validation_passed:
            print(f"   ✅ All results match expected filters")
        else:
            print(f"   ❌ Some results don't match filters")

        return validation_passed

    return True


def main():
    """Run comprehensive test suite"""
    print("\n" + "="*80)
    print(" ENHANCED SEARCH LOGIC TEST")
    print("="*80)
    print("\nTesting problematic queries that previously caused false matches...\n")

    test_cases = [
        # Test 1: Capacity-based query (should filter by capacity)
        {
            'query': '50ml',
            'expected_filters': {'capacity_value': 50, 'capacity_unit': 'ml'},
            'description': 'Should find 50ml products, NOT 50파이 products'
        },

        # Test 2: Neck size query (should filter by neck size)
        {
            'query': '20파이 펌프',
            'expected_filters': {'neck_size': 20},
            'description': 'Should find 20mm neck size products, NOT 20ml products'
        },

        # Test 3: Material + capacity query
        {
            'query': '100cc PP 용기',
            'expected_filters': {'capacity_value': 100, 'capacity_unit': 'cc', 'materials': ['PP']},
            'description': 'Should find 100cc PP products only'
        },

        # Test 4: Material + neck size query
        {
            'query': 'PET 24파이',
            'expected_filters': {'neck_size': 24, 'materials': ['PET']},
            'description': 'Should find PET products with 24mm neck size'
        },

        # Test 5: No specific filter (general search)
        {
            'query': '화장품 용기',
            'expected_filters': None,
            'description': 'General search without specific filters'
        },
    ]

    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'='*80}")
        print(f"TEST CASE {i}/{len(test_cases)}")
        print(f"Description: {test_case['description']}")
        print(f"{'='*80}")

        passed = test_query(test_case['query'], test_case['expected_filters'])
        results.append({
            'test': test_case['description'],
            'query': test_case['query'],
            'passed': passed
        })

    # Summary
    print("\n\n" + "="*80)
    print(" TEST SUMMARY")
    print("="*80)

    total = len(results)
    passed = sum(1 for r in results if r['passed'])

    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"{i}. {status} - {result['test']}")

    print(f"\n📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 All tests passed! Enhanced search logic is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the results above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
