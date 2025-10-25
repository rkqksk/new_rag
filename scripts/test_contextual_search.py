#!/usr/bin/env python3
"""
Test contextual search functionality
Simulates conversation flow: "20미리 용기" → "이중에 PETG만"
"""

import httpx
import json
import asyncio

API_URL = "http://localhost:8000/api/v1/products/search"


async def test_contextual_search():
    """Test two-step contextual search"""

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 80)
        print("🧪 Testing Contextual Search")
        print("=" * 80)

        # Step 1: Initial search - "20미리 용기"
        print("\n📍 Step 1: Search for '20미리 용기'")
        print("-" * 80)

        response1 = await client.get(
            API_URL,
            params={"query": "20미리 용기", "limit": 20}
        )

        if response1.status_code == 200:
            data1 = response1.json()
            session_id = data1.get('session_id')
            products1 = data1.get('products', [])
            context1 = data1.get('context', {})

            print(f"✅ Query: {data1.get('query')}")
            print(f"✅ Session ID: {session_id}")
            print(f"✅ Total results: {data1.get('total')}")
            print(f"✅ Contextual: {context1.get('is_contextual')}")
            print(f"\n📦 Materials found:")

            # Count by material
            material_counts = {}
            for product in products1:
                material = product.get('material', 'Unknown')
                material_counts[material] = material_counts.get(material, 0) + 1

            for material, count in sorted(material_counts.items()):
                print(f"  - {material}: {count}개")

            # Show first 3 products
            print(f"\n📋 First 3 products:")
            for i, product in enumerate(products1[:3], 1):
                print(f"  {i}. {product.get('product_name')} ({product.get('material')}, {product.get('capacity')})")

            # Step 2: Contextual search - "이중에 PETG만"
            print("\n" + "=" * 80)
            print("📍 Step 2: Filter with '이중에 PETG만'")
            print("-" * 80)

            response2 = await client.get(
                API_URL,
                params={
                    "query": "이중에 PETG만",
                    "limit": 20,
                    "session_id": session_id  # Use same session
                }
            )

            if response2.status_code == 200:
                data2 = response2.json()
                products2 = data2.get('products', [])
                context2 = data2.get('context', {})

                print(f"✅ Query: {data2.get('query')}")
                print(f"✅ Session ID: {data2.get('session_id')}")
                print(f"✅ Contextual: {context2.get('is_contextual')}")
                print(f"✅ Previous count: {context2.get('previous_count')}")
                print(f"✅ Filtered count: {context2.get('filtered_count')}")
                print(f"✅ Total results: {data2.get('total')}")

                # Verify all are PETG
                all_petg = all(p.get('material') == 'PETG' for p in products2)
                print(f"\n🔍 All results are PETG: {'✅ Yes' if all_petg else '❌ No'}")

                # Show filtered products
                print(f"\n📋 Filtered PETG products:")
                for i, product in enumerate(products2[:5], 1):
                    print(f"  {i}. {product.get('product_name')} ({product.get('material')}, {product.get('capacity')})")

                # Step 3: Test without session ID (should start new search)
                print("\n" + "=" * 80)
                print("📍 Step 3: Test '이중에 PETG만' WITHOUT session (should fail contextual)")
                print("-" * 80)

                response3 = await client.get(
                    API_URL,
                    params={"query": "이중에 PETG만", "limit": 20}
                    # No session_id - should do new search
                )

                if response3.status_code == 200:
                    data3 = response3.json()
                    context3 = data3.get('context', {})

                    print(f"✅ Query: {data3.get('query')}")
                    print(f"✅ Contextual detected: {context3.get('is_contextual')}")
                    print(f"✅ Reason: {context3.get('reason', 'new search')}")
                    print(f"✅ New session ID generated: {data3.get('session_id')}")

            else:
                print(f"❌ Step 2 failed: {response2.status_code}")
                print(response2.text)
        else:
            print(f"❌ Step 1 failed: {response1.status_code}")
            print(response1.text)

        print("\n" + "=" * 80)
        print("✅ Contextual Search Test Complete")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_contextual_search())
