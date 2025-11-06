"""
Demo: Personalized Recommendation System

Demonstrates the complete personalization workflow:
1. User searches "50ml PET 용기" → Views/clicks product
2. User searches "캡" → Views 20파이 cap
3. User searches "펌프" → System automatically prioritizes compatible products
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.recommendation import PersonalizationService, RecommendationConfig


def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_results(results, title="Results"):
    """Print search results"""
    print(f"\n📊 {title} ({len(results)} items):\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. {result['name']}")
        print(f"   Category: {result.get('category', 'N/A')}")
        print(f"   Capacity: {result.get('capacity', 'N/A')}")
        print(f"   Material: {result.get('material', 'N/A')}")
        print(f"   Neck: {result.get('neck', 'N/A')}")

        # Show scores
        if 'personalized_score' in result:
            print(f"   Personalized Score: {result['personalized_score']:.3f}")
            print(f"   ├─ Original: {result['original_score']:.3f}")
            print(f"   ├─ Preference: {result['preference_score']:.3f}")
            print(f"   ├─ Compatibility: +{result['compatibility_boost']:.3f}")
            print(f"   └─ Recency: {result['recency_adjustment']:+.3f}")
        elif 'score' in result:
            print(f"   Vector Score: {result['score']:.3f}")

        print()


def main():
    """Run personalization demo"""

    print_section("🎯 Personalized Recommendation System Demo")

    print("""
이 데모는 다음 시나리오를 보여줍니다:

1️⃣ 사용자가 "50ml PET 용기"를 검색하고 제품 클릭
2️⃣ 사용자가 "캡"을 검색하고 20파이 캡 클릭
3️⃣ 사용자가 "펌프"를 검색
   → 시스템이 자동으로 50ml 호환 + 20파이 넥 펌프를 상단에 노출
""")

    # Initialize service
    print("🚀 Initializing PersonalizationService...")
    config = RecommendationConfig(
        vector_score_weight=0.6,
        preference_score_weight=0.4,
        enable_compatibility_boost=True,
        compatibility_boost=0.2
    )
    service = PersonalizationService(
        redis_client=None,  # Demo without Redis
        recommendation_config=config
    )
    print("✅ Service initialized\n")

    # Session ID
    session_id = "demo_session_001"

    # ========================================================================
    # Scenario 1: User searches "50ml PET 용기"
    # ========================================================================

    print_section("1️⃣ Scenario 1: User searches '50ml PET 용기'")

    query1 = "50ml PET 용기"
    print(f"🔍 Search Query: '{query1}'\n")

    # Track search
    service.track_search(session_id, query1)
    print("✅ Tracked search query")

    # Mock search results (bottles)
    search_results_1 = [
        {
            'id': 'bottle_001',
            'name': '50ml PET 병 - 원형',
            'category': 'Bottle',
            'capacity': '50ml',
            'material': 'PET',
            'neck': '20파이',
            'score': 0.92
        },
        {
            'id': 'bottle_002',
            'name': '50ml PP 병 - 사각',
            'category': 'Bottle',
            'capacity': '50ml',
            'material': 'PP',
            'neck': '24파이',
            'score': 0.85
        },
        {
            'id': 'bottle_003',
            'name': '100ml PET 병 - 원형',
            'category': 'Bottle',
            'capacity': '100ml',
            'material': 'PET',
            'neck': '20파이',
            'score': 0.78
        }
    ]

    # Personalize (no history yet, so same as original)
    personalized_1 = service.personalize_search_results(
        session_id=session_id,
        results=search_results_1,
        query=query1
    )

    print_results(personalized_1, "Initial Search Results (No personalization yet)")

    # User clicks on first product
    clicked_product = personalized_1[0]
    print(f"👆 User clicks on: '{clicked_product['name']}'")
    service.track_click(session_id, clicked_product['id'], clicked_product)
    print("✅ Tracked click\n")

    # Show profile
    profile_summary = service.get_profile_summary(session_id)
    print("📊 User Profile Updated:")
    print(profile_summary)

    # ========================================================================
    # Scenario 2: User searches "캡"
    # ========================================================================

    print_section("2️⃣ Scenario 2: User searches '캡'")

    query2 = "캡"
    print(f"🔍 Search Query: '{query2}'\n")

    # Track search
    service.track_search(session_id, query2)
    print("✅ Tracked search query")

    # Mock search results (caps)
    search_results_2 = [
        {
            'id': 'cap_001',
            'name': '24파이 스크류 캡 - 화이트',
            'category': 'Cap',
            'neck': '24파이',
            'material': 'PP',
            'score': 0.88
        },
        {
            'id': 'cap_002',
            'name': '20파이 스크류 캡 - 블랙',
            'category': 'Cap',
            'neck': '20파이',
            'material': 'PP',
            'score': 0.85
        },
        {
            'id': 'cap_003',
            'name': '20파이 원터치 캡 - 화이트',
            'category': 'Cap',
            'neck': '20파이',
            'material': 'PP',
            'score': 0.82
        },
        {
            'id': 'cap_004',
            'name': '28파이 스크류 캡 - 실버',
            'category': 'Cap',
            'neck': '28파이',
            'material': 'PP',
            'score': 0.80
        }
    ]

    # Personalize (should boost 20파이 caps due to compatibility!)
    personalized_2 = service.personalize_search_results(
        session_id=session_id,
        results=search_results_2,
        query=query2
    )

    print_results(personalized_2, "Personalized Search Results")

    print("💡 Notice:")
    print("   - 20파이 caps are boosted to the top!")
    print("   - They are compatible with the 50ml PET bottle (20파이 neck)")
    print("   - Original vector scores were 0.88, 0.85, 0.82...")
    print("   - But personalized scores prioritize compatibility\n")

    # User clicks on 20파이 cap
    clicked_cap = personalized_2[0]  # Should be 20파이 cap now
    print(f"👆 User clicks on: '{clicked_cap['name']}'")
    service.track_click(session_id, clicked_cap['id'], clicked_cap)
    print("✅ Tracked click\n")

    # Show profile
    profile_summary = service.get_profile_summary(session_id)
    print("📊 User Profile Updated:")
    print(profile_summary)

    # ========================================================================
    # Scenario 3: User searches "펌프"
    # ========================================================================

    print_section("3️⃣ Scenario 3: User searches '펌프'")

    query3 = "펌프"
    print(f"🔍 Search Query: '{query3}'\n")

    # Track search
    service.track_search(session_id, query3)
    print("✅ Tracked search query")

    # Mock search results (pumps)
    search_results_3 = [
        {
            'id': 'pump_001',
            'name': '24파이 펌프 디스펜서 - 대용량',
            'category': 'Pump',
            'neck': '24파이',
            'material': 'PP',
            'score': 0.90
        },
        {
            'id': 'pump_002',
            'name': '20파이 펌프 디스펜서 - 소형',
            'category': 'Pump',
            'neck': '20파이',
            'material': 'PP',
            'score': 0.87
        },
        {
            'id': 'pump_003',
            'name': '28파이 펌프 디스펜서 - 고급형',
            'category': 'Pump',
            'neck': '28파이',
            'material': 'PP',
            'score': 0.85
        },
        {
            'id': 'pump_004',
            'name': '20파이 미니 펌프 - 경량',
            'category': 'Pump',
            'neck': '20파이',
            'material': 'PP',
            'score': 0.83
        }
    ]

    # Personalize (should prioritize 20파이 pumps + 50ml compatibility!)
    personalized_3 = service.personalize_search_results(
        session_id=session_id,
        results=search_results_3,
        query=query3
    )

    print_results(personalized_3, "🎯 Personalized Search Results (Smart Recommendation!)")

    print("🎉 Success! The system automatically:")
    print("   ✅ Prioritized 20파이 neck pumps (compatible with user's bottle)")
    print("   ✅ Boosted compatibility scores")
    print("   ✅ Learned from user's previous choices")
    print("   ✅ No login required - all session-based!\n")

    # Explain recommendations
    print("📝 Recommendation Explanations:\n")
    for i, result in enumerate(personalized_3[:3], 1):
        explanation = service.explain_recommendation(session_id, result)
        print(f"{i}. {result['name']}")
        print(f"   Why? {explanation}\n")

    # ========================================================================
    # Summary
    # ========================================================================

    print_section("📊 Final Summary")

    profile_summary = service.get_profile_summary(session_id)
    print(profile_summary)

    print("\n" + "=" * 80)
    print("  ✅ Demo Complete!")
    print("=" * 80)
    print("""
핵심 기능:
1. ✅ 세션 기반 (로그인 불필요)
2. ✅ 자동 선호도 학습 (검색 + 클릭 기록)
3. ✅ 호환성 인식 추천 (용기-캡-펌프 매칭)
4. ✅ 실시간 개인화 (검색 결과 re-ranking)
5. ✅ 설명 가능한 추천 (왜 이 제품인지 설명)

적용 가능한 곳:
- /search API: 검색 결과 개인화
- /recommendations API: "회원님을 위한 추천"
- /products/{id}/related: 관련 제품 추천
- Frontend: 상단 노출 순서 자동 조정
""")


if __name__ == '__main__':
    main()
