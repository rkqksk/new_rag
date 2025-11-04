"""
동의어 처리 테스트 스크립트
다양한 표현 방식의 쿼리를 정확히 이해하는지 검증
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.synonym_manager import get_synonym_manager
from src.services.enhanced_contextual_rag import EnhancedContextualRAG


def test_synonym_extraction():
    """동의어 추출 테스트"""
    print("\n" + "=" * 60)
    print("동의어 추출 테스트")
    print("=" * 60)

    synonym_manager = get_synonym_manager()

    # 테스트 케이스
    test_cases = [
        ("24파이 로션펌프", {
            'expected_neck_size': '24',
            'expected_product_type': 'pump'
        }),
        ("50미리 투명 PET병", {
            'expected_capacity': 50.0,
            'expected_transparency': 'transparent',
            'expected_material': 'PET',
            'expected_product_type': 'bottle'
        }),
        ("24/410 펌프", {
            'expected_neck_size': '24/410',
            'expected_product_type': 'pump'
        }),
        ("24펌프", {
            'expected_neck_size': '24',
            'expected_product_type': 'pump'
        }),
        ("100mL 피이티 용기", {
            'expected_capacity': 100.0,
            'expected_material': 'PET',
            'expected_product_type': 'bottle'
        }),
        ("투명한 50ml 로션 펌프", {
            'expected_capacity': 50.0,
            'expected_transparency': 'transparent',
            'expected_product_type': 'pump'
        }),
    ]

    for query, expected in test_cases:
        print(f"\n📝 쿼리: \"{query}\"")

        # 정규화
        normalized = synonym_manager.normalize_query(query)
        print(f"   정규화: \"{normalized}\"")

        # 필터 추출
        filters = synonym_manager.get_search_filters(query)
        print(f"   추출된 필터: {filters}")

        # 검증
        passed = True
        for key, expected_value in expected.items():
            actual_key = key.replace('expected_', '')
            actual_value = filters.get(actual_key)

            if actual_value == expected_value:
                print(f"   ✅ {actual_key}: {actual_value}")
            else:
                print(f"   ❌ {actual_key}: {actual_value} (예상: {expected_value})")
                passed = False

        if passed:
            print(f"   🎉 테스트 통과!")
        else:
            print(f"   ⚠️ 테스트 실패")


async def test_conversation_scenario():
    """동의어 처리 대화 시나리오"""
    print("\n" + "=" * 60)
    print("동의어 처리 대화 시나리오 테스트")
    print("=" * 60)

    rag = EnhancedContextualRAG()
    session_id = "synonym_test_session"

    # 시나리오 1: "로션 펌프" → "24파이만" → "여기에 맞는 용기"
    print("\n시나리오 1: 펌프 → 네크 사이즈 필터 → 호환 용기")
    print("-" * 60)

    # 1단계: 로션 펌프 검색
    print("\n[1단계] 사용자: 로션 펌프 보여줘")
    result1 = await rag.query(session_id, "로션 펌프 보여줘")
    print(f"→ 의도: {result1['intent']}")
    print(f"→ 응답: {result1['response']}")
    print(f"→ 제품 수: {result1['total_count']}")
    print(f"→ 추출된 필터: {result1.get('filters_applied', {})}")

    # 2단계: 24파이만 필터링
    print("\n[2단계] 사용자: 24파이만 보여줘")
    result2 = await rag.query(session_id, "24파이만 보여줘")
    print(f"→ 의도: {result2['intent']}")
    print(f"→ 응답: {result2['response']}")
    print(f"→ 제품 수: {result2['total_count']}")
    print(f"→ 추출된 필터: {result2.get('filters_applied', {})}")

    # 제품 목록 표시
    if result2['products']:
        print("\n검색 결과:")
        for i, product in enumerate(result2['products'][:3], 1):
            neck = product.get('specifications', {}).get('neck_size', 'N/A')
            print(f"  {i}. {product.get('product_name')} (네크: {neck})")

    # 3단계: 첫 번째 제품 선택
    print("\n[3단계] 사용자: 첫 번째")
    result3 = await rag.query(session_id, "첫 번째")
    print(f"→ 의도: {result3['intent']}")
    print(f"→ 선택된 제품: {result3['products'][0]['product_name'] if result3['products'] else 'N/A'}")

    # 4단계: 호환되는 용기 검색
    print("\n[4단계] 사용자: 여기에 맞는 용기 보여줘")
    result4 = await rag.query(session_id, "여기에 맞는 용기 보여줘")
    print(f"→ 의도: {result4['intent']}")
    print(f"→ 응답: {result4['response']}")
    print(f"→ 제품 수: {result4['total_count']}")

    # 시나리오 2: 다양한 표현 테스트
    print("\n\n시나리오 2: 다양한 동의어 표현 테스트")
    print("-" * 60)

    session_id2 = "synonym_test_session_2"

    queries = [
        "24펌프",                    # "24파이 펌프"와 동일
        "50미리 피이티 병",          # "50ml PET 병"과 동일
        "투명한 로션펌프",           # "투명 로션 펌프"와 동일
        "24/410 캡",                 # "24파이 캡"과 동일
    ]

    for query in queries:
        print(f"\n[쿼리] {query}")
        result = await rag.query(session_id2, query)
        print(f"→ 의도: {result['intent']}")
        print(f"→ 제품 수: {result['total_count']}")
        print(f"→ 추출된 필터: {result.get('filters_applied', {})}")


async def main():
    """모든 테스트 실행"""
    print("\n" + "=" * 60)
    print("동의어 처리 시스템 테스트 시작")
    print("=" * 60)

    try:
        # 1. 동의어 추출 테스트
        test_synonym_extraction()

        # 2. 대화 시나리오 테스트
        await test_conversation_scenario()

        print("\n" + "=" * 60)
        print("모든 테스트 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
