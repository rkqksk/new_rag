"""
비교 시스템 통합 테스트
"""

import asyncio
import json
from pathlib import Path

from src.services.comparison_engine import get_comparison_engine


def print_section(title: str):
    """섹션 제목 출력"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_success(message: str):
    """성공 메시지 출력"""
    print(f"✅ {message}")


def print_error(message: str):
    """에러 메시지 출력"""
    print(f"❌ {message}")


def print_info(message: str):
    """정보 메시지 출력"""
    print(f"ℹ️  {message}")


async def test_comparison_engine():
    """비교 엔진 기본 테스트"""
    print_section("테스트 1: 비교 엔진 초기화")

    engine = get_comparison_engine()
    print_success("ComparisonEngine 초기화 성공")
    print_info(f"비교 메트릭: {list(engine.comparison_metrics.keys())}")

    return engine


async def test_product_comparison(engine):
    """제품 비교 테스트"""
    print_section("테스트 2: 제품 비교 (2개 제품)")

    # 샘플 제품 idx (실제 데이터 있는 것으로)
    product_idxs = ["823", "209"]

    result = engine.compare_products(
        product_idxs=product_idxs,
        metrics=["재질", "용량", "가격", "호환성"]
    )

    if "error" in result:
        print_error(f"비교 실패: {result['error']}")
        return False

    print_success(f"{result['product_count']}개 제품 비교 완료")

    # 비교 매트릭스 출력
    print("\n📊 비교 매트릭스:")
    for row in result["comparison_matrix"]:
        metric = row["metric"]
        values = " | ".join([v["display"] for v in row["values"]])
        print(f"  {metric}: {values}")

    # 추천 출력
    if result.get("recommendation"):
        print(f"\n💡 추천:")
        print(f"  {result['recommendation']}")

    return True


async def test_multiple_products(engine):
    """다중 제품 비교 테스트"""
    print_section("테스트 3: 다중 제품 비교 (5개 제품)")

    product_idxs = ["823", "209", "248", "835", "321"]

    result = engine.compare_products(
        product_idxs=product_idxs,
        metrics=None  # 전체 메트릭
    )

    if "error" in result:
        print_error(f"비교 실패: {result['error']}")
        return False

    print_success(f"{result['product_count']}개 제품 비교 완료")
    print_info(f"비교 메트릭: {', '.join(result['metrics'])}")

    # 하이라이트 확인
    highlights_found = 0
    for row in result["comparison_matrix"]:
        for value in row["values"]:
            if value.get("highlight") == "best":
                highlights_found += 1

    print_info(f"발견된 하이라이트: {highlights_found}개")

    return True


async def test_filtering(engine):
    """필터링 테스트"""
    print_section("테스트 4: 동적 필터링")

    # 먼저 몇 개 제품 로드
    products = []
    for idx in ["823", "209", "248", "835", "321"]:
        product = engine._load_product(idx)
        if product:
            products.append(product)

    print_info(f"로드된 제품: {len(products)}개")

    # 재질 필터 테스트
    filters = {"재질": "PET"}
    filtered = engine.apply_filters(products, filters)
    print_success(f"재질 필터 (PET) 적용: {len(products)}개 → {len(filtered)}개")

    # 가격 필터 테스트
    filters = {"가격": {"min": 0, "max": 300}}
    filtered = engine.apply_filters(products, filters)
    print_success(f"가격 필터 (0-300원) 적용: {len(products)}개 → {len(filtered)}개")

    # 복합 필터 테스트
    filters = {
        "재질": "PET",
        "가격": {"max": 500},
        "호환성": 5
    }
    filtered = engine.apply_filters(products, filters)
    print_success(f"복합 필터 적용: {len(products)}개 → {len(filtered)}개")

    return True


async def test_error_handling(engine):
    """에러 처리 테스트"""
    print_section("테스트 5: 에러 처리")

    # 빈 제품 목록
    result = engine.compare_products(product_idxs=[], metrics=None)
    if "error" in result:
        print_success("빈 제품 목록 에러 처리 OK")
    else:
        print_error("빈 제품 목록 에러 처리 실패")

    # 존재하지 않는 제품
    result = engine.compare_products(
        product_idxs=["99999", "88888"],
        metrics=None
    )
    if "error" in result:
        print_success("존재하지 않는 제품 에러 처리 OK")
    else:
        print_error("존재하지 않는 제품 에러 처리 실패")

    return True


async def test_api_integration():
    """API 통합 테스트 (서버 실행 필요)"""
    print_section("테스트 6: API 통합 테스트")

    import httpx

    try:
        async with httpx.AsyncClient() as client:
            # 헬스 체크
            response = await client.get("http://localhost:8001/compare/health")
            if response.status_code == 200:
                print_success("헬스 체크 통과")
            else:
                print_error(f"헬스 체크 실패: {response.status_code}")
                return False

            # 메트릭 조회
            response = await client.get("http://localhost:8001/compare/metrics")
            if response.status_code == 200:
                metrics = response.json()
                print_success(f"메트릭 조회 성공: {metrics['total_count']}개")
            else:
                print_error(f"메트릭 조회 실패: {response.status_code}")
                return False

            # 제품 비교
            response = await client.post(
                "http://localhost:8001/compare/products",
                json={
                    "product_idxs": ["823", "209"],
                    "metrics": ["재질", "용량", "가격"]
                }
            )
            if response.status_code == 200:
                result = response.json()
                print_success(f"제품 비교 성공: {result['product_count']}개 제품")
            else:
                print_error(f"제품 비교 실패: {response.status_code}")
                return False

            return True

    except Exception as e:
        print_error(f"API 테스트 실패 (서버가 실행 중인지 확인): {e}")
        return False


async def main():
    """메인 테스트 실행"""
    print("\n" + "🧪" * 30)
    print("  비교 시스템 통합 테스트 시작")
    print("🧪" * 30)

    results = []

    # 테스트 1: 엔진 초기화
    try:
        engine = await test_comparison_engine()
        results.append(("엔진 초기화", True))
    except Exception as e:
        print_error(f"엔진 초기화 실패: {e}")
        results.append(("엔진 초기화", False))
        return

    # 테스트 2: 제품 비교
    try:
        success = await test_product_comparison(engine)
        results.append(("제품 비교 (2개)", success))
    except Exception as e:
        print_error(f"제품 비교 실패: {e}")
        results.append(("제품 비교 (2개)", False))

    # 테스트 3: 다중 제품 비교
    try:
        success = await test_multiple_products(engine)
        results.append(("다중 제품 비교 (5개)", success))
    except Exception as e:
        print_error(f"다중 제품 비교 실패: {e}")
        results.append(("다중 제품 비교 (5개)", False))

    # 테스트 4: 필터링
    try:
        success = await test_filtering(engine)
        results.append(("동적 필터링", success))
    except Exception as e:
        print_error(f"필터링 테스트 실패: {e}")
        results.append(("동적 필터링", False))

    # 테스트 5: 에러 처리
    try:
        success = await test_error_handling(engine)
        results.append(("에러 처리", success))
    except Exception as e:
        print_error(f"에러 처리 테스트 실패: {e}")
        results.append(("에러 처리", False))

    # 테스트 6: API 통합 (선택적)
    try:
        success = await test_api_integration()
        results.append(("API 통합", success))
    except Exception as e:
        print_error(f"API 통합 테스트 실패: {e}")
        results.append(("API 통합", False))

    # 결과 요약
    print_section("테스트 결과 요약")
    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}  {test_name}")

    print(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 모든 테스트 통과!")
    else:
        print(f"\n⚠️  {total - passed}개 테스트 실패")


if __name__ == "__main__":
    asyncio.run(main())
