#!/usr/bin/env python3
"""
Phase 1 Integration Test
Tests Product Attribute Q&A system end-to-end

Test Scenarios:
1. Search for products → Ask attribute question
2. Product attribute Q&A (토출량은?)
3. Delivery inquiry (납기는?)
4. Customization inquiry (색상 추가 가능?)
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
    """Scenario #1: Search → Product Attribute Q&A"""
    print("\n" + "="*70)
    print("TEST SCENARIO #1: Search → Product Attribute Q&A")
    print("="*70)

    # Step 1: Search for 50ml products
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
    print(f"   Intent: {data['conversation']['intent']}")

    if data['total'] == 0:
        print("❌ No products found, cannot proceed")
        return False

    # Show first product
    first_product = data['products'][0]
    print(f"\n   First product:")
    print(f"     - Name: {first_product.get('product_name')}")
    print(f"     - Code: {first_product.get('product_code')}")
    print(f"     - Capacity: {first_product.get('capacity')}")

    # Step 2: Ask attribute question (토출량은?)
    print("\n[Step 2] Asking '이 펌프 토출량은?'...")
    response = requests.get(
        f"{BASE_URL}/api/v1/products/search",
        params={"query": "이 펌프 토출량은?", "session_id": session_id}
    )

    if response.status_code != 200:
        print(f"❌ Q&A failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

    data = response.json()
    print(f"✅ Q&A Response received")
    print(f"   Intent: {data['conversation']['intent']}")

    # Check if Q&A response exists
    if 'qa_response' in data:
        qa_response = data['qa_response']
        print(f"\n   Q&A Answer:")
        print(f"     - Question: {qa_response.get('question')}")
        print(f"     - Answer: {qa_response.get('answer')}")

        if qa_response.get('product'):
            product = qa_response['product']
            print(f"     - Product: {product.get('product_name')} ({product.get('product_code')})")

        return True
    else:
        print("❌ No Q&A response in data")
        print_response(data, "Full Response")
        return False


def test_scenario_2():
    """Scenario #2: Delivery Inquiry"""
    print("\n" + "="*70)
    print("TEST SCENARIO #2: Delivery Inquiry")
    print("="*70)

    # Step 1: Search for a product
    print("\n[Step 1] Searching for 'BE050-R001'...")
    response = requests.get(
        f"{BASE_URL}/api/v1/products/search",
        params={"query": "BE050-R001"}
    )

    if response.status_code != 200:
        print(f"❌ Search failed: {response.status_code}")
        return False

    data = response.json()
    session_id = data['session_id']
    print(f"✅ Found product")
    print(f"   Session ID: {session_id}")

    # Step 2: Ask delivery question
    print("\n[Step 2] Asking '납기는?'...")
    response = requests.get(
        f"{BASE_URL}/api/v1/products/search",
        params={"query": "납기는?", "session_id": session_id}
    )

    if response.status_code != 200:
        print(f"❌ Q&A failed: {response.status_code}")
        return False

    data = response.json()
    print(f"✅ Q&A Response received")
    print(f"   Intent: {data['conversation']['intent']}")

    if 'qa_response' in data:
        qa_response = data['qa_response']
        print(f"\n   Answer: {qa_response.get('answer')}")
        return True
    else:
        print("❌ No Q&A response")
        return False


def test_scenario_3():
    """Scenario #3: Customization Inquiry"""
    print("\n" + "="*70)
    print("TEST SCENARIO #3: Customization Inquiry")
    print("="*70)

    # Step 1: Search
    print("\n[Step 1] Searching for '100ml PET 용기'...")
    response = requests.get(
        f"{BASE_URL}/api/v1/products/search",
        params={"query": "100ml PET 용기", "limit": 5}
    )

    if response.status_code != 200:
        print(f"❌ Search failed: {response.status_code}")
        return False

    data = response.json()
    session_id = data['session_id']
    print(f"✅ Found {data['total']} products")

    # Step 2: Ask customization question
    print("\n[Step 2] Asking '색상 추가 가능해?'...")
    response = requests.get(
        f"{BASE_URL}/api/v1/products/search",
        params={"query": "색상 추가 가능해?", "session_id": session_id}
    )

    if response.status_code != 200:
        print(f"❌ Q&A failed: {response.status_code}")
        return False

    data = response.json()
    print(f"✅ Q&A Response received")
    print(f"   Intent: {data['conversation']['intent']}")

    if 'qa_response' in data:
        qa_response = data['qa_response']
        print(f"\n   Answer: {qa_response.get('answer')}")
        return True
    else:
        print("❌ No Q&A response")
        return False


def main():
    print("\n" + "="*70)
    print("PHASE 1 INTEGRATION TEST")
    print("Testing Product Attribute Q&A System")
    print("="*70)

    # Run tests
    results = {
        "Scenario #1 (Product Attribute Q&A)": test_scenario_1(),
        "Scenario #2 (Delivery Inquiry)": test_scenario_2(),
        "Scenario #3 (Customization Inquiry)": test_scenario_3(),
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
