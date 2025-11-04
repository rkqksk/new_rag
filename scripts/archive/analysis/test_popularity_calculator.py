#!/usr/bin/env python3
"""
인기도 스코어 계산 로직 테스트

시간 감쇠, 트렌드 부스트, 정규화 알고리즘 검증
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analytics.popularity_calculator import PopularityCalculator


def test_time_decay():
    """시간 감쇠 테스트"""
    print("=== 시간 감쇠 테스트 ===")
    calculator = PopularityCalculator()

    test_cases = [
        (0, 1.0),      # 오늘
        (7, 0.5),      # 7일 전 (반감기)
        (14, 0.25),    # 14일 전
        (21, 0.125),   # 21일 전
        (30, 0.088),   # 30일 전
    ]

    for days_ago, expected in test_cases:
        result = calculator.time_decay_factor(days_ago)
        print(f"{days_ago}일 전: {result:.3f} (기대: {expected:.3f}) {'✅' if abs(result - expected) < 0.01 else '❌'}")


def test_trend_boost():
    """트렌드 부스트 테스트"""
    print("\n=== 트렌드 부스트 테스트 ===")
    calculator = PopularityCalculator()

    test_cases = [
        (100, 300, 1.5, "3배 증가 (최대 부스트)"),
        (100, 200, 1.5, "2배 증가 (최대 부스트)"),
        (100, 150, 1.25, "1.5배 증가"),
        (100, 100, 1.0, "동일"),
        (100, 75, 0.95, "25% 감소"),
        (100, 50, 0.9, "50% 감소"),
        (100, 0, 0.8, "제로 (최소 패널티)"),
    ]

    for previous, recent, expected_boost, description in test_cases:
        result = calculator.trend_boost_factor(recent, previous)
        match = abs(result - expected_boost) < 0.1
        print(f"{description}: {result:.2f}x (기대: {expected_boost:.2f}x) {'✅' if match else '❌'}")


def test_normalize_scores():
    """정규화 테스트"""
    print("\n=== 정규화 테스트 ===")
    calculator = PopularityCalculator()

    test_scores = {
        'product_1': 1000,
        'product_2': 500,
        'product_3': 250,
        'product_4': 100,
        'product_5': 0,
    }

    normalized = calculator.normalize_scores(test_scores)

    print("원본 → 정규화 (0-100)")
    for product_idx, original in test_scores.items():
        norm = normalized[product_idx]
        print(f"{product_idx}: {original} → {norm:.2f}")

    # 검증
    max_norm = max(normalized.values())
    min_norm = min(normalized.values())
    print(f"\n최대: {max_norm:.2f} (기대: 100.00) {'✅' if abs(max_norm - 100.0) < 0.01 else '❌'}")
    print(f"최소: {min_norm:.2f} (기대: 0.00) {'✅' if abs(min_norm - 0.0) < 0.01 else '❌'}")


def test_weighted_score_calculation():
    """가중치 스코어 계산 테스트"""
    print("\n=== 가중치 스코어 계산 테스트 ===")
    calculator = PopularityCalculator()

    now = datetime.now()

    # 시나리오: 제품 A
    # - 샘플 신청 2건 (오늘, 7일 전)
    # - 클릭 5건 (오늘 2건, 7일 전 2건, 14일 전 1건)

    sample_events = [
        {'timestamp': now},                           # 오늘
        {'timestamp': now - timedelta(days=7)},       # 7일 전
    ]

    click_events = [
        {'timestamp': now},                           # 오늘
        {'timestamp': now},                           # 오늘
        {'timestamp': now - timedelta(days=7)},       # 7일 전
        {'timestamp': now - timedelta(days=7)},       # 7일 전
        {'timestamp': now - timedelta(days=14)},      # 14일 전
    ]

    # 샘플 신청 스코어 (가중치 10.0)
    sample_score = calculator._calculate_weighted_score(
        sample_events,
        calculator.WEIGHT_SAMPLE_REQUEST,
        now
    )

    # 클릭 스코어 (가중치 3.0)
    click_score = calculator._calculate_weighted_score(
        click_events,
        calculator.WEIGHT_CLICK,
        now
    )

    print(f"샘플 신청 스코어: {sample_score:.2f}")
    print(f"  오늘 1건 × 10.0 × 1.0 = 10.0")
    print(f"  7일 전 1건 × 10.0 × 0.5 = 5.0")
    print(f"  합계: 15.0 (실제: {sample_score:.2f}) {'✅' if abs(sample_score - 15.0) < 0.01 else '❌'}")

    print(f"\n클릭 스코어: {click_score:.2f}")
    print(f"  오늘 2건 × 3.0 × 1.0 = 6.0")
    print(f"  7일 전 2건 × 3.0 × 0.5 = 3.0")
    print(f"  14일 전 1건 × 3.0 × 0.25 = 0.75")
    print(f"  합계: 9.75 (실제: {click_score:.2f}) {'✅' if abs(click_score - 9.75) < 0.01 else '❌'}")

    total_score = sample_score + click_score
    print(f"\n총 스코어: {total_score:.2f} (기대: 24.75) {'✅' if abs(total_score - 24.75) < 0.01 else '❌'}")


def test_comprehensive_scenario():
    """종합 시나리오 테스트"""
    print("\n=== 종합 시나리오 테스트 ===")
    calculator = PopularityCalculator()

    print("\n시나리오: 3개 제품 비교")
    print("제품 A: 샘플 신청 많음, 최근 데이터")
    print("제품 B: 클릭 많음, 오래된 데이터")
    print("제품 C: 검색 많음, 상승세")

    now = datetime.now()

    # 제품 A: 샘플 신청 2건 (오늘), 클릭 3건 (오늘)
    product_a_samples = [
        {'timestamp': now},
        {'timestamp': now},
    ]
    product_a_clicks = [
        {'timestamp': now},
        {'timestamp': now},
        {'timestamp': now},
    ]
    product_a_score = (
        calculator._calculate_weighted_score(product_a_samples, 10.0, now) +
        calculator._calculate_weighted_score(product_a_clicks, 3.0, now)
    )

    # 제품 B: 클릭 10건 (30일 전)
    product_b_clicks = [
        {'timestamp': now - timedelta(days=30)} for _ in range(10)
    ]
    product_b_score = calculator._calculate_weighted_score(product_b_clicks, 3.0, now)

    # 제품 C: 검색 출현 50회
    product_c_score = 50 * 1.0  # 검색 가중치 1.0

    print(f"\n제품 A 스코어: {product_a_score:.2f}")
    print(f"  샘플 신청 2건 × 10.0 × 1.0 = 20.0")
    print(f"  클릭 3건 × 3.0 × 1.0 = 9.0")
    print(f"  합계: 29.0")

    print(f"\n제품 B 스코어: {product_b_score:.2f}")
    print(f"  클릭 10건 × 3.0 × 0.088 (30일 감쇠) = 2.64")

    print(f"\n제품 C 스코어: {product_c_score:.2f}")
    print(f"  검색 출현 50회 × 1.0 = 50.0")

    # 정규화
    scores = {
        'product_a': product_a_score,
        'product_b': product_b_score,
        'product_c': product_c_score,
    }
    normalized = calculator.normalize_scores(scores)

    print("\n정규화 후 (0-100):")
    for product_idx, norm_score in sorted(normalized.items(), key=lambda x: x[1], reverse=True):
        print(f"  {product_idx}: {norm_score:.2f}")

    print("\n결론:")
    print("  제품 C (검색 많음) > 제품 A (샘플+클릭) > 제품 B (오래된 클릭)")
    print("  검색 출현이 가장 높지만, 샘플 신청이 강력한 신호임을 확인")


def main():
    """모든 테스트 실행"""
    print("인기도 스코어 계산 로직 테스트\n")

    test_time_decay()
    test_trend_boost()
    test_normalize_scores()
    test_weighted_score_calculation()
    test_comprehensive_scenario()

    print("\n✅ 모든 테스트 완료")


if __name__ == "__main__":
    main()
