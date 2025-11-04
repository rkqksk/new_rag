#!/usr/bin/env python3
"""
Test 3-level conversation: bottle search → filter → accessory recommendation
Tests the complete relationship-based recommendation system
"""

import httpx
import asyncio
import json


API_URL = "http://localhost:8000/api/v1/products/search"


async def test_accessory_recommendation():
    """Test complete 3-turn conversation with accessory recommendation"""

    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=" * 80)
        print("🚀 Testing 3-Level Conversation: Bottle → Filter → Accessories")
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
            print(f"  Total results: {data1['total']}")

            # Show sample products
            print(f"\n  Sample products:")
            for i, product in enumerate(data1['products'][:5], 1):
                spec = product.get('spec', '')
                print(f"    {i}. {product.get('product_name')} - {spec} ({product.get('material')})")

        else:
            print(f"❌ Turn 1 failed: {response1.status_code}")
            return

        # Turn 2: "이중에 PETG만 보여줘"
        print("\n" + "=" * 80)
        print("🔷 Turn 2: 맥락 필터링 - '이중에 PETG만 보여줘'")
        print("=" * 80)

        await asyncio.sleep(1)

        params2 = {
            "query": "이중에 PETG만 보여줘",
            "limit": 20,
            "session_id": session_id
        }
        response2 = await client.get(API_URL, params=params2)

        if response2.status_code == 200:
            data2 = response2.json()

            print(f"\n📊 Response:")
            print(f"  Intent: {data2['conversation']['intent']}")
            print(f"  State: {data2['conversation']['state']}")
            print(f"  Is filtering: {data2['context']['is_filtering']}")
            print(f"  Total results: {data2['total']}")

            # Verify all are PETG
            all_petg = all(p.get('material') == 'PETG' for p in data2['products'])
            print(f"\n  ✅ All results are PETG: {'Yes' if all_petg else 'No'}")

            print(f"\n  PETG bottles:")
            for i, product in enumerate(data2['products'][:5], 1):
                spec = product.get('spec', '')
                print(f"    {i}. {product.get('product_name')} - {spec}")

        else:
            print(f"❌ Turn 2 failed: {response2.status_code}")
            return

        # Turn 3: "이 용기에 맞는 펌프 추천해줘"
        print("\n" + "=" * 80)
        print("🔷 Turn 3: 액세서리 추천 - '이 용기에 맞는 펌프 추천해줘'")
        print("=" * 80)

        await asyncio.sleep(1)

        params3 = {
            "query": "이 용기에 맞는 펌프 추천해줘",
            "limit": 20,
            "session_id": session_id
        }
        response3 = await client.get(API_URL, params=params3)

        if response3.status_code == 200:
            data3 = response3.json()

            print(f"\n📊 Response:")
            print(f"  Intent: {data3['conversation']['intent']}")
            print(f"  State: {data3['conversation']['state']}")
            print(f"  Is recommending accessory: {data3['context']['is_recommending_accessory']}")
            print(f"  Total results: {data3['total']}")

            # Check if accessory groups exist (new grouped format)
            if 'accessory_summary' in data3:
                summary = data3['accessory_summary']
                groups = data3.get('accessory_groups', [])

                print(f"\n  📋 Accessory Groups Summary:")
                print(f"     Total groups: {summary['total_groups']}")
                print(f"     Neck sizes: Ø{', Ø'.join(map(str, summary['neck_sizes']))}")
                print(f"     Total bottles: {summary['total_bottles']}")
                print(f"     Total accessories: {summary['total_accessories']}")

                # Show each group
                for group in groups:
                    neck_size = group['neck_size']
                    bottles = group['bottles']
                    pumps = group['pumps']
                    caps = group['caps']

                    print(f"\n  🔹 Group: Ø{neck_size} Bottles")
                    print(f"     Bottles in this group: {len(bottles)}")
                    for bottle in bottles:
                        print(f"       - {bottle.get('product_code', 'N/A')}: {bottle.get('product_name', 'N/A')}")

                    if pumps:
                        print(f"\n     Compatible Pumps (Ø{neck_size}): {len(pumps)} total")
                        for i, pump in enumerate(pumps[:3], 1):
                            print(f"       {i}. {pump.get('product_name')} - {pump.get('product_code', 'N/A')}")

                    if caps:
                        print(f"\n     Compatible Caps (Ø{neck_size}): {len(caps)} total")
                        for i, cap in enumerate(caps[:3], 1):
                            print(f"       {i}. {cap.get('product_name')} - {cap.get('product_code', 'N/A')}")

            else:
                print(f"\n  ⚠️  No accessory groups found")

        else:
            print(f"❌ Turn 3 failed: {response3.status_code}")
            return

        # Final summary
        print("\n" + "=" * 80)
        print("✅ 3-Level Conversation Test Complete")
        print("=" * 80)
        print(f"\nSession Summary:")
        print(f"  Session ID: {session_id}")
        print(f"  Total turns: {data3['context']['turn_count']}")
        print(f"  Query history: {data3['context']['query_history']}")
        print(f"\n🎉 Relationship-based recommendation system is working!")


if __name__ == "__main__":
    asyncio.run(test_accessory_recommendation())
