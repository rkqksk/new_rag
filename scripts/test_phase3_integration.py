"""
Phase 3 Integration Test: 규제/인증 Q&A
Test Korean regulatory knowledge base (식약처/환경부)
"""

import sys
import os
import httpx
import asyncio
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

BASE_URL = "http://localhost:8000"


async def test_scenario_1_regulatory_inquiry():
    """
    Scenario #1: 식약처 규제 문의
    - Query: "식약처 기준 충족하나요?"
    - Expected: REGULATORY_INQUIRY intent, 식약처 규제 답변
    """
    print("\n" + "=" * 70)
    print("Scenario #1: 식약처 규제 문의")
    print("=" * 70)

    async with httpx.AsyncClient() as client:
        # Step 1: Regulatory inquiry
        print("\n[Step 1] 식약처 기준 충족하나요?")
        response = await client.get(
            f"{BASE_URL}/api/v1/products/search",
            params={"query": "식약처 기준 충족하나요?"}
        )
        data = response.json()

        print(f"Status: {response.status_code}")
        print(f"Intent: {data.get('intent')}")

        # Check Q&A response
        if 'qa_response' in data:
            qa_response = data['qa_response']
            print(f"✅ Q&A Answer:\n{qa_response.get('answer')}")

            # Verify Korean regulatory content
            answer = qa_response.get('answer', '')
            if '식약처' in answer or '화장품법' in answer:
                print("✅ PASS: 식약처 규제 답변 포함")
                return True
            else:
                print("❌ FAIL: 식약처 규제 답변 없음")
                return False
        else:
            print("❌ FAIL: No Q&A response")
            return False


async def test_scenario_2_environmental_inquiry():
    """
    Scenario #2: 환경부 재활용 등급 문의
    - Query: "환경부 재활용 등급은?"
    - Expected: REGULATORY_INQUIRY intent, 환경부 규제 답변
    """
    print("\n" + "=" * 70)
    print("Scenario #2: 환경부 재활용 등급 문의")
    print("=" * 70)

    async with httpx.AsyncClient() as client:
        # Step 1: Environmental regulation inquiry
        print("\n[Step 1] 환경부 재활용 등급은?")
        response = await client.get(
            f"{BASE_URL}/api/v1/products/search",
            params={"query": "환경부 재활용 등급은?"}
        )
        data = response.json()

        print(f"Status: {response.status_code}")
        print(f"Intent: {data.get('intent')}")

        # Check Q&A response
        if 'qa_response' in data:
            qa_response = data['qa_response']
            print(f"✅ Q&A Answer:\n{qa_response.get('answer')}")

            # Verify environmental regulatory content
            answer = qa_response.get('answer', '')
            if '환경부' in answer or '재활용' in answer or 'EPR' in answer:
                print("✅ PASS: 환경부 재활용 규제 답변 포함")
                return True
            else:
                print("❌ FAIL: 환경부 재활용 규제 답변 없음")
                return False
        else:
            print("❌ FAIL: No Q&A response")
            return False


async def test_scenario_3_certification_inquiry():
    """
    Scenario #3: 시험성적서 문의
    - Query: "시험성적서 받을 수 있나요?"
    - Expected: CERTIFICATION_INQUIRY intent, 시험성적서 정보 답변
    """
    print("\n" + "=" * 70)
    print("Scenario #3: 시험성적서 문의")
    print("=" * 70)

    async with httpx.AsyncClient() as client:
        # Step 1: Test certificate inquiry
        print("\n[Step 1] 시험성적서 받을 수 있나요?")
        response = await client.get(
            f"{BASE_URL}/api/v1/products/search",
            params={"query": "시험성적서 받을 수 있나요?"}
        )
        data = response.json()

        print(f"Status: {response.status_code}")
        print(f"Intent: {data.get('intent')}")

        # Check Q&A response
        if 'qa_response' in data:
            qa_response = data['qa_response']
            print(f"✅ Q&A Answer:\n{qa_response.get('answer')}")

            # Verify certification content
            answer = qa_response.get('answer', '')
            if '시험성적서' in answer or 'KTR' in answer or '한국화학융합시험연구원' in answer:
                print("✅ PASS: 시험성적서 정보 포함")
                return True
            else:
                print("❌ FAIL: 시험성적서 정보 없음")
                return False
        else:
            print("❌ FAIL: No Q&A response")
            return False


async def test_scenario_4_kc_certification():
    """
    Scenario #4: KC 인증 문의
    - Query: "KC 인증 필요해요?"
    - Expected: CERTIFICATION_INQUIRY intent, KC 인증 정보 (불필요 안내)
    """
    print("\n" + "=" * 70)
    print("Scenario #4: KC 인증 문의")
    print("=" * 70)

    async with httpx.AsyncClient() as client:
        # Step 1: KC certification inquiry
        print("\n[Step 1] KC 인증 필요해요?")
        response = await client.get(
            f"{BASE_URL}/api/v1/products/search",
            params={"query": "KC 인증 필요해요?"}
        )
        data = response.json()

        print(f"Status: {response.status_code}")
        print(f"Intent: {data.get('intent')}")

        # Check Q&A response
        if 'qa_response' in data:
            qa_response = data['qa_response']
            print(f"✅ Q&A Answer:\n{qa_response.get('answer')}")

            # Verify KC certification content
            answer = qa_response.get('answer', '')
            if 'KC' in answer or 'kc' in answer.lower():
                print("✅ PASS: KC 인증 정보 포함")
                return True
            else:
                print("❌ FAIL: KC 인증 정보 없음")
                return False
        else:
            print("❌ FAIL: No Q&A response")
            return False


async def main():
    """Run all Phase 3 integration tests"""
    print("\n" + "=" * 70)
    print("Phase 3 통합 테스트 - 규제/인증 Q&A (한국 규제 우선)")
    print("=" * 70)

    # Test API server availability
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code != 200:
                print(f"❌ API server not available: {BASE_URL}")
                return
    except Exception as e:
        print(f"❌ API server connection failed: {e}")
        return

    results = []

    # Run scenarios
    results.append(await test_scenario_1_regulatory_inquiry())
    results.append(await test_scenario_2_environmental_inquiry())
    results.append(await test_scenario_3_certification_inquiry())
    results.append(await test_scenario_4_kc_certification())

    # Summary
    print("\n" + "=" * 70)
    print("테스트 결과 요약")
    print("=" * 70)
    print(f"총 테스트: {len(results)}개")
    print(f"통과: {sum(results)}개")
    print(f"실패: {len(results) - sum(results)}개")

    if all(results):
        print("\n✅ Phase 3 통합 테스트 전체 통과!")
    else:
        print("\n❌ 일부 테스트 실패")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
