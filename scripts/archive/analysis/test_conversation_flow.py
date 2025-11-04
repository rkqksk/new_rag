"""
대화 흐름 테스트 스크립트
영업사원 수준의 대화 시나리오 검증
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.enhanced_contextual_rag import EnhancedContextualRAG


async def test_scenario_1_cumulative_filtering():
    """
    시나리오 1: 누적 필터링
    "50ml 용기" → "PET만" → "투명만"
    """
    print("\n" + "=" * 60)
    print("시나리오 1: 누적 필터링 테스트")
    print("=" * 60)

    rag = EnhancedContextualRAG()
    session_id = "test_session_1"

    # 1단계: 50ml 용기 검색
    print("\n[1단계] 사용자: 50미리 용기 보여줘")
    result1 = await rag.query(session_id, "50미리 용기 보여줘")
    print(f"→ 의도: {result1['intent']}, 액션: {result1['action']}, 상태: {result1['state']}")
    print(f"→ 응답: {result1['response']}")
    print(f"→ 제품 수: {result1['total_count']}")

    # 2단계: PET 재질만 필터링
    print("\n[2단계] 사용자: PET만 보여줘")
    result2 = await rag.query(session_id, "PET만 보여줘")
    print(f"→ 의도: {result2['intent']}, 액션: {result2['action']}, 상태: {result2['state']}")
    print(f"→ 응답: {result2['response']}")
    print(f"→ 제품 수: {result2['total_count']}")
    print(f"→ 적용된 필터: {result2.get('filters_applied')}")

    # 3단계: 투명만 추가 필터링
    print("\n[3단계] 사용자: 투명만")
    result3 = await rag.query(session_id, "투명만")
    print(f"→ 의도: {result3['intent']}, 액션: {result3['action']}, 상태: {result3['state']}")
    print(f"→ 응답: {result3['response']}")
    print(f"→ 제품 수: {result3['total_count']}")
    print(f"→ 적용된 필터: {result3.get('filters_applied')}")

    return result1, result2, result3


async def test_scenario_2_reference_resolution():
    """
    시나리오 2: 스마트 참조 해결
    "50ml 병" → "3번" → "호환되는 캡"
    """
    print("\n" + "=" * 60)
    print("시나리오 2: 스마트 참조 해결 테스트")
    print("=" * 60)

    rag = EnhancedContextualRAG()
    session_id = "test_session_2"

    # 1단계: 50ml 병 검색
    print("\n[1단계] 사용자: 50ml 병 보여줘")
    result1 = await rag.query(session_id, "50ml 병 보여줘")
    print(f"→ 의도: {result1['intent']}, 액션: {result1['action']}, 상태: {result1['state']}")
    print(f"→ 응답: {result1['response']}")
    print(f"→ 제품 수: {result1['total_count']}")

    # 제품 목록 표시 시뮬레이션
    if result1['products']:
        print("\n검색 결과:")
        for i, product in enumerate(result1['products'][:5], 1):
            print(f"  {i}. {product.get('product_name')} ({product.get('idx')})")

    # 2단계: 숫자 참조 ("3번")
    print("\n[2단계] 사용자: 3번 자세히 보여줘")
    result2 = await rag.query(session_id, "3번 자세히 보여줘")
    print(f"→ 의도: {result2['intent']}, 액션: {result2['action']}, 상태: {result2['state']}")
    print(f"→ 응답: {result2['response']}")

    # 3단계: 암묵적 참조 + 호환성
    print("\n[3단계] 사용자: 호환되는 캡 보여줘")
    result3 = await rag.query(session_id, "호환되는 캡 보여줘")
    print(f"→ 의도: {result3['intent']}, 액션: {result3['action']}, 상태: {result3['state']}")
    print(f"→ 응답: {result3['response']}")
    print(f"→ 제품 수: {result3['total_count']}")

    return result1, result2, result3


async def test_scenario_3_document_request():
    """
    시나리오 3: 문서 요청
    "100ml 병" → "2번" → "원산지 증명서 보여줘"
    """
    print("\n" + "=" * 60)
    print("시나리오 3: 문서 요청 테스트")
    print("=" * 60)

    rag = EnhancedContextualRAG()
    session_id = "test_session_3"

    # 1단계: 100ml 병 검색
    print("\n[1단계] 사용자: 100ml 병")
    result1 = await rag.query(session_id, "100ml 병")
    print(f"→ 의도: {result1['intent']}, 액션: {result1['action']}, 상태: {result1['state']}")
    print(f"→ 응답: {result1['response']}")

    # 제품 목록 표시
    if result1['products']:
        print("\n검색 결과:")
        for i, product in enumerate(result1['products'][:5], 1):
            print(f"  {i}. {product.get('product_name')} ({product.get('idx')})")

    # 2단계: 숫자 참조로 상세보기
    print("\n[2단계] 사용자: 2번")
    result2 = await rag.query(session_id, "2번")
    print(f"→ 의도: {result2['intent']}, 액션: {result2['action']}, 상태: {result2['state']}")
    print(f"→ 응답: {result2['response']}")

    # 3단계: 문서 요청
    print("\n[3단계] 사용자: 원산지 증명서 보여줘")
    result3 = await rag.query(session_id, "원산지 증명서 보여줘")
    print(f"→ 의도: {result3['intent']}, 액션: {result3['action']}, 상태: {result3['state']}")
    print(f"→ 응답: {result3['response']}")
    print(f"→ 문서 타입: {result3.get('document_type')}")

    return result1, result2, result3


async def test_scenario_4_pronoun_reference():
    """
    시나리오 4: 대명사 참조
    "PET 병" → "그거 가격은?"
    """
    print("\n" + "=" * 60)
    print("시나리오 4: 대명사 참조 테스트")
    print("=" * 60)

    rag = EnhancedContextualRAG()
    session_id = "test_session_4"

    # 1단계: PET 병 검색
    print("\n[1단계] 사용자: PET 병 찾아줘")
    result1 = await rag.query(session_id, "PET 병 찾아줘")
    print(f"→ 의도: {result1['intent']}, 액션: {result1['action']}, 상태: {result1['state']}")
    print(f"→ 응답: {result1['response']}")

    # 제품 목록 표시
    if result1['products']:
        print("\n검색 결과:")
        for i, product in enumerate(result1['products'][:3], 1):
            print(f"  {i}. {product.get('product_name')}")

    # 2단계: 대명사 참조 ("그거")
    print("\n[2단계] 사용자: 그거 자세히 보여줘")
    result2 = await rag.query(session_id, "그거 자세히 보여줘")
    print(f"→ 의도: {result2['intent']}, 액션: {result2['action']}, 상태: {result2['state']}")
    print(f"→ 응답: {result2['response']}")

    return result1, result2


async def test_scenario_5_reset():
    """
    시나리오 5: 대화 초기화
    "50ml 병" → "PET만" → "초기화" → "100ml 병"
    """
    print("\n" + "=" * 60)
    print("시나리오 5: 대화 초기화 테스트")
    print("=" * 60)

    rag = EnhancedContextualRAG()
    session_id = "test_session_5"

    # 1단계: 50ml 병 검색
    print("\n[1단계] 사용자: 50ml 병")
    result1 = await rag.query(session_id, "50ml 병")
    print(f"→ 응답: {result1['response']}")
    print(f"→ 제품 수: {result1['total_count']}")

    # 2단계: PET 필터 추가
    print("\n[2단계] 사용자: PET만")
    result2 = await rag.query(session_id, "PET만")
    print(f"→ 응답: {result2['response']}")
    print(f"→ 필터: {result2.get('filters_applied')}")

    # 3단계: 초기화
    print("\n[3단계] 사용자: 초기화")
    result3 = await rag.query(session_id, "초기화")
    print(f"→ 의도: {result3['intent']}, 액션: {result3['action']}, 상태: {result3['state']}")
    print(f"→ 응답: {result3['response']}")

    # 4단계: 새로운 검색 (필터 초기화 확인)
    print("\n[4단계] 사용자: 100ml 병")
    result4 = await rag.query(session_id, "100ml 병")
    print(f"→ 응답: {result4['response']}")
    print(f"→ 필터: {result4.get('filters_applied')}")

    return result1, result2, result3, result4


async def main():
    """모든 시나리오 실행"""
    print("\n" + "=" * 60)
    print("영업사원 수준 대화 흐름 테스트 시작")
    print("=" * 60)

    try:
        # 시나리오 1: 누적 필터링
        await test_scenario_1_cumulative_filtering()

        # 시나리오 2: 스마트 참조 해결
        await test_scenario_2_reference_resolution()

        # 시나리오 3: 문서 요청
        await test_scenario_3_document_request()

        # 시나리오 4: 대명사 참조
        await test_scenario_4_pronoun_reference()

        # 시나리오 5: 대화 초기화
        await test_scenario_5_reset()

        print("\n" + "=" * 60)
        print("모든 테스트 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
