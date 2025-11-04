#!/usr/bin/env python3
"""
Phase 2 Integration Test
Tests Click/Sample Tracking system end-to-end

Test Scenarios:
1. Search → Click product → Verify tracking
2. Search → View product → Verify view count
3. Search → Request sample → Verify sample tracking
4. Get session interactions summary
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_response(response_data, title="Response"):
    """Pretty print API response"""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}")
    print(json.dumps(response_data, indent=2, ensure_ascii=False))
    print()


def test_scenario_1():
    """Scenario #1: Search → Click Product → Verify Tracking"""
    print("\n" + "="*70)
    print("TEST SCENARIO #1: Product Click Tracking")
    print("="*70)

    # Step 1: Search for products
    print("\n[Step 1] Searching for '50ml 용기'...")
    response = requests.get(
        f"{BASE_URL}/api/v1/products/search",
        params={"query": "50ml 용기", "limit": 5}
    )

    if response.status_code != 200:
        print(f"❌ Search failed: {response.status_code}")
        return False

    data = response.json()
    session_id = data['session_id']
    print(f"✅ Found {data['total']} products")
    print(f"   Session ID: {session_id}")

    if data['total'] == 0:
        print("❌ No products found, cannot proceed")
        return False

    # Get first product ID
    first_product = data['products'][0]
    product_id = first_product.get('product_code')
    print(f"\n   First product ID: {product_id}")

    # Step 2: Track product click
    print(f"\n[Step 2] Clicking product {product_id}...")
    response = requests.post(
        f"{BASE_URL}/api/v1/product/{product_id}/click",
        params={"session_id": session_id}
    )

    if response.status_code != 200:
        print(f"❌ Click tracking failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

    data = response.json()
    print(f"✅ Click tracked successfully")
    print(f"   Product ID: {data['product_id']}")
    print(f"   Total clicked: {data['total_clicked']}")

    # Step 3: Verify in session interactions
    print(f"\n[Step 3] Verifying session interactions...")
    response = requests.get(
        f"{BASE_URL}/api/v1/session/{session_id}/interactions"
    )

    if response.status_code != 200:
        print(f"❌ Get interactions failed: {response.status_code}")
        return False

    data = response.json()
    print(f"✅ Session interactions retrieved")
    print(f"   Clicked products: {data['clicked_products']}")
    print(f"   Total clicks: {data['total_clicks']}")

    # Verify product_id is in clicked_products
    if product_id in data['clicked_products']:
        print(f"✅ Product click verified in session")
        return True
    else:
        print(f"❌ Product click NOT found in session")
        return False


def test_scenario_2():
    """Scenario #2: Product View Tracking"""
    print("\n" + "="*70)
    print("TEST SCENARIO #2: Product View Tracking")
    print("="*70)

    # Step 1: Search
    print("\n[Step 1] Searching for '100ml PET'...")
    response = requests.get(
        f"{BASE_URL}/api/v1/products/search",
        params={"query": "100ml PET", "limit": 5}
    )

    if response.status_code != 200:
        print(f"❌ Search failed: {response.status_code}")
        return False

    data = response.json()
    session_id = data['session_id']
    product_id = data['products'][0].get('product_code')
    print(f"✅ Found products, using product ID: {product_id}")

    # Step 2: Track view (first time)
    print(f"\n[Step 2] Viewing product (1st time)...")
    response = requests.post(
        f"{BASE_URL}/api/v1/product/{product_id}/view",
        params={"session_id": session_id}
    )

    if response.status_code != 200:
        print(f"❌ View tracking failed: {response.status_code}")
        return False

    data = response.json()
    print(f"✅ View tracked: count = {data['view_count']}")

    if data['view_count'] != 1:
        print(f"❌ Expected view_count=1, got {data['view_count']}")
        return False

    # Step 3: Track view (second time)
    print(f"\n[Step 3] Viewing product (2nd time)...")
    response = requests.post(
        f"{BASE_URL}/api/v1/product/{product_id}/view",
        params={"session_id": session_id}
    )

    if response.status_code != 200:
        print(f"❌ View tracking failed: {response.status_code}")
        return False

    data = response.json()
    print(f"✅ View tracked: count = {data['view_count']}")

    if data['view_count'] != 2:
        print(f"❌ Expected view_count=2, got {data['view_count']}")
        return False

    # Step 4: Verify in session
    print(f"\n[Step 4] Verifying session interactions...")
    response = requests.get(
        f"{BASE_URL}/api/v1/session/{session_id}/interactions"
    )

    data = response.json()
    print(f"✅ Total views: {data['total_views']}")
    print(f"   Viewed products: {data['viewed_products']}")

    return data['viewed_products'].get(product_id) == 2


def test_scenario_3():
    """Scenario #3: Sample Request Tracking"""
    print("\n" + "="*70)
    print("TEST SCENARIO #3: Sample Request Tracking")
    print("="*70)

    # Step 1: Search
    print("\n[Step 1] Searching for '펌프'...")
    response = requests.get(
        f"{BASE_URL}/api/v1/products/search",
        params={"query": "펌프", "limit": 5}
    )

    if response.status_code != 200:
        print(f"❌ Search failed: {response.status_code}")
        return False

    data = response.json()
    session_id = data['session_id']

    if data['total'] == 0:
        print("❌ No products found")
        return False

    product_id = data['products'][0].get('product_code')
    print(f"✅ Found products, using product ID: {product_id}")

    # Step 2: Request sample
    print(f"\n[Step 2] Requesting sample for {product_id}...")
    response = requests.post(
        f"{BASE_URL}/api/v1/product/{product_id}/sample",
        params={"session_id": session_id}
    )

    if response.status_code != 200:
        print(f"❌ Sample request tracking failed: {response.status_code}")
        return False

    data = response.json()
    print(f"✅ Sample request tracked")
    print(f"   Total sample requests: {data['total_sample_requests']}")

    # Step 3: Verify in session
    print(f"\n[Step 3] Verifying session interactions...")
    response = requests.get(
        f"{BASE_URL}/api/v1/session/{session_id}/interactions"
    )

    if response.status_code != 200:
        print(f"❌ Get interactions failed: {response.status_code}")
        return False

    data = response.json()
    print(f"✅ Session interactions retrieved")
    print(f"   Sample requested products: {data['sample_requested_products']}")
    print(f"   Total samples: {data['total_samples']}")

    # Verify product_id is in sample_requested_products
    if product_id in data['sample_requested_products']:
        print(f"✅ Sample request verified in session")
        return True
    else:
        print(f"❌ Sample request NOT found in session")
        return False


def main():
    print("\n" + "="*70)
    print("PHASE 2 INTEGRATION TEST")
    print("Testing Click/Sample Tracking System")
    print("="*70)

    # Run tests
    results = {
        "Scenario #1 (Product Click Tracking)": test_scenario_1(),
        "Scenario #2 (Product View Tracking)": test_scenario_2(),
        "Scenario #3 (Sample Request Tracking)": test_scenario_3(),
    }

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for scenario, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {scenario}")

    print(f"\n{'='*70}")
    print(f"TOTAL: {passed}/{total} tests passed")
    print(f"{'='*70}\n")

    return passed == total


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
