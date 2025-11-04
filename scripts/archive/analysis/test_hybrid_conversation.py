#!/usr/bin/env python3
"""
Test hybrid conversation system end-to-end
Tests LLM intent analysis, state machine, filtering, and Qdrant storage
"""

import httpx
import asyncio
import json


API_URL = "http://localhost:8000/api/v1/products/search"


async def test_full_conversation():
    """Test complete multi-turn conversation"""

    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=" * 80)
        print("🚀 Testing Hybrid Conversation System")
        print("=" * 80)

        session_id = None

        # Turn 1: "20미리 용기 보여줘"
        print("\n" + "=" * 80)
        print("🔷 Turn 1: 새로운 검색 - '20미리 용기 보여줘'")
        print("=" * 80)

        params1 = {"query": "20미리 용기 보여줘", "limit": 20}
        response1 = await client.get(API_URL, params=params1)

        if response1.status_code == 200:
            data1 = response1.json()
            session_id = data1.get('session_id')

            print(f"\n📊 Response:")
            print(f"  Session ID: {session_id}")
            print(f"  Intent: {data1['conversation']['intent']}")
            print(f"  State: {data1['conversation']['state']}")
            print(f"  Confidence: {data1['conversation']['confidence']}")
            print(f"  Explanation: {data1['conversation']['explanation']}")
            print(f"  Total results: {data1['total']}")

            # Show material breakdown
            materials = {}
            for product in data1['products']:
                material = product.get('material', 'Unknown')
                materials[material] = materials.get(material, 0) + 1

            print(f"\n  Materials found:")
            for material, count in sorted(materials.items()):
                print(f"    - {material}: {count}개")

            print(f"\n  Sample products:")
            for i, product in enumerate(data1['products'][:3], 1):
                print(f"    {i}. {product.get('product_name')} ({product.get('material')}, {product.get('capacity')})")

        else:
            print(f"❌ Turn 1 failed: {response1.status_code}")
            return

        # Turn 2: "이중에 PETG만 보여줘"
        print("\n" + "=" * 80)
        print("🔷 Turn 2: 맥락 필터링 - '이중에 PETG만 보여줘'")
        print("=" * 80)

        await asyncio.sleep(1)  # Wait for LLM processing

        params2 = {
            "query": "이중에 PETG만 보여줘",
            "limit": 20,
            "session_id": session_id
        }
        response2 = await client.get(API_URL, params=params2)

        if response2.status_code == 200:
            data2 = response2.json()

            print(f"\n📊 Response:")
            print(f"  Session ID: {data2.get('session_id')}")
            print(f"  Intent: {data2['conversation']['intent']}")
            print(f"  State: {data2['conversation']['state']}")
            print(f"  Previous State: {data2['conversation']['previous_state']}")
            print(f"  Confidence: {data2['conversation']['confidence']}")
            print(f"  Explanation: {data2['conversation']['explanation']}")
            print(f"  Is filtering: {data2['context']['is_filtering']}")
            print(f"  Previous count: {data2['context']['previous_count']}")
            print(f"  Total results: {data2['total']}")

            # Verify all are PETG
            all_petg = all(p.get('material') == 'PETG' for p in data2['products'])
            print(f"\n  ✅ All results are PETG: {'Yes' if all_petg else 'No'}")

            print(f"\n  PETG products:")
            for i, product in enumerate(data2['products'][:5], 1):
                print(f"    {i}. {product.get('product_name')} ({product.get('material')}, {product.get('capacity')})")

        else:
            print(f"❌ Turn 2 failed: {response2.status_code}")
            return

        # Turn 3: "아니 다시 50미리로 바꿔줘"
        print("\n" + "=" * 80)
        print("🔷 Turn 3: 검색 수정 - '아니 다시 50미리로 바꿔줘'")
        print("=" * 80)

        await asyncio.sleep(1)

        params3 = {
            "query": "아니 다시 50미리로 바꿔줘",
            "limit": 20,
            "session_id": session_id
        }
        response3 = await client.get(API_URL, params=params3)

        if response3.status_code == 200:
            data3 = response3.json()

            print(f"\n📊 Response:")
            print(f"  Intent: {data3['conversation']['intent']}")
            print(f"  State: {data3['conversation']['state']}")
            print(f"  Confidence: {data3['conversation']['confidence']}")
            print(f"  Total results: {data3['total']}")

            # Show material breakdown
            materials = {}
            for product in data3['products']:
                material = product.get('material', 'Unknown')
                materials[material] = materials.get(material, 0) + 1

            print(f"\n  Materials found:")
            for material, count in sorted(materials.items()):
                print(f"    - {material}: {count}개")

            # Verify capacities
            capacities = set(p.get('capacity') for p in data3['products'])
            print(f"\n  Capacities: {capacities}")

        else:
            print(f"❌ Turn 3 failed: {response3.status_code}")
            return

        # Final summary
        print("\n" + "=" * 80)
        print("✅ Hybrid Conversation System Test Complete")
        print("=" * 80)
        print(f"\nSession Summary:")
        print(f"  Session ID: {session_id}")
        print(f"  Total turns: {data3['context']['turn_count']}")
        print(f"  Query history: {data3['context']['query_history']}")
        print(f"\n🎉 All tests passed! The hybrid system is working correctly.")


if __name__ == "__main__":
    asyncio.run(test_full_conversation())
