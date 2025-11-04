#!/usr/bin/env python3
"""
인기도 기반 검색 랭킹 테스트

검색 결과가 인기도에 따라 재정렬되는지 검증
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.popularity_ranker import PopularityRanker


async def test_basic_reranking():
    """기본 재정렬 테스트"""
    print("=== 기본 재정렬 테스트 ===")

    ranker = PopularityRanker()

    # 가상의 인기도 스코어 주입
    ranker.popularity_cache = {
        'product_1': {'normalized_score': 100.0, 'trend_percentage': 50.0},
        'product_2': {'normalized_score': 80.0, 'trend_percentage': 10.0},
        'product_3': {'normalized_score': 30.0, 'trend_percentage': 0.0},
        'product_4': {'normalized_score': 10.0, 'trend_percentage': -20.0},
        'product_5': {'normalized_score': 0.0, 'trend_percentage': 0.0},
    }
    ranker.cache_timestamp = datetime.now()

    # 검색 결과 (관련성 순서: 3 > 2 > 4 > 1 > 5)
    search_results = [
        {'product_idx': 'product_3', 'relevance_score': 95.0, 'metadata': {'name': 'Product 3'}},
        {'product_idx': 'product_2', 'relevance_score': 90.0, 'metadata': {'name': 'Product 2'}},
        {'product_idx': 'product_4', 'relevance_score': 85.0, 'metadata': {'name': 'Product 4'}},
        {'product_idx': 'product_1', 'relevance_score': 80.0, 'metadata': {'name': 'Product 1'}},
        {'product_idx': 'product_5', 'relevance_score': 75.0, 'metadata': {'name': 'Product 5'}},
    ]

    print("\n원본 검색 결과 (관련성 순):")
    for i, result in enumerate(search_results, 1):
        pid = result['product_idx']
        rel = result['relevance_score']
        pop = ranker.popularity_cache.get(pid, {}).get('normalized_score', 0)
        print(f"{i}. {pid}: 관련성={rel:.1f}, 인기도={pop:.1f}")

    # 재정렬
    reranked = await ranker.rerank(
        search_results=search_results,
        relevance_weight=0.7,
        popularity_weight=0.3,
        boost_trending=True
    )

    print("\n재정렬 결과 (관련성 0.7 + 인기도 0.3):")
    for i, result in enumerate(reranked, 1):
        pid = result['product_idx']
        rel = result['relevance_score']
        pop = result['popularity_score']
        final = result['final_score']
        trend = result['trend_boost']
        print(f"{i}. {pid}: 관련성={rel:.1f}, 인기도={pop:.1f}, "
              f"트렌드={trend:.2f}x, 최종={final:.1f}")

    # 검증
    print("\n검증:")
    # Product 1 (인기도 100, 트렌드 50%) 이 상위로 올라와야 함
    top_product = reranked[0]['product_idx']
    print(f"1위 제품: {top_product} {'✅' if top_product == 'product_1' else '⚠️ (기대: product_1)'}")

    # Product 2 (인기도 80, 관련성 90) 도 상위권
    second_product = reranked[1]['product_idx']
    print(f"2위 제품: {second_product} {'✅' if second_product in ['product_1', 'product_2'] else '⚠️'}")


async def test_context_filters():
    """컨텍스트 필터 테스트"""
    print("\n\n=== 컨텍스트 필터 테스트 ===")

    ranker = PopularityRanker()

    # 카테고리별 스코어 포함
    ranker.popularity_cache = {
        'product_pet_50': {
            'normalized_score': 60.0,
            'score_by_material': {'PET': 90.0, 'HDPE': 30.0},
            'score_by_capacity': {'50': 85.0, '100': 40.0},
            'trend_percentage': 0.0
        },
        'product_hdpe_50': {
            'normalized_score': 70.0,
            'score_by_material': {'PET': 20.0, 'HDPE': 95.0},
            'score_by_capacity': {'50': 80.0, '100': 50.0},
            'trend_percentage': 0.0
        },
        'product_pet_100': {
            'normalized_score': 80.0,
            'score_by_material': {'PET': 85.0, 'HDPE': 25.0},
            'score_by_capacity': {'50': 30.0, '100': 90.0},
            'trend_percentage': 0.0
        },
    }
    ranker.cache_timestamp = datetime.now()

    # 검색 결과
    search_results = [
        {'product_idx': 'product_pet_50', 'relevance_score': 90.0, 'metadata': {}},
        {'product_idx': 'product_hdpe_50', 'relevance_score': 85.0, 'metadata': {}},
        {'product_idx': 'product_pet_100', 'relevance_score': 80.0, 'metadata': {}},
    ]

    # 시나리오 1: PET 재질 필터
    print("\n시나리오 1: PET 재질 필터")
    context_filters = {'material': 'PET', 'capacity_ml': 50}

    reranked = await ranker.rerank(
        search_results=search_results,
        relevance_weight=0.5,
        popularity_weight=0.5,
        context_filters=context_filters,
        boost_trending=False
    )

    print("결과 (PET + 50ml 컨텍스트):")
    for i, result in enumerate(reranked, 1):
        pid = result['product_idx']
        pop = result['popularity_score']
        final = result['final_score']
        print(f"{i}. {pid}: 인기도={pop:.1f}, 최종={final:.1f}")

    # 검증: product_pet_50 이 1위여야 함 (PET + 50ml 모두 높음)
    top = reranked[0]['product_idx']
    print(f"✅ 1위: {top} (기대: product_pet_50)" if top == 'product_pet_50' else f"⚠️ 1위: {top}")

    # 시나리오 2: HDPE 재질 필터
    print("\n시나리오 2: HDPE 재질 필터")
    context_filters = {'material': 'HDPE'}

    reranked = await ranker.rerank(
        search_results=search_results,
        relevance_weight=0.5,
        popularity_weight=0.5,
        context_filters=context_filters,
        boost_trending=False
    )

    print("결과 (HDPE 컨텍스트):")
    for i, result in enumerate(reranked, 1):
        pid = result['product_idx']
        pop = result['popularity_score']
        final = result['final_score']
        print(f"{i}. {pid}: 인기도={pop:.1f}, 최종={final:.1f}")

    # 검증: product_hdpe_50 이 1위여야 함
    top = reranked[0]['product_idx']
    print(f"✅ 1위: {top} (기대: product_hdpe_50)" if top == 'product_hdpe_50' else f"⚠️ 1위: {top}")


async def test_trending_boost():
    """트렌드 부스트 테스트"""
    print("\n\n=== 트렌드 부스트 테스트 ===")

    ranker = PopularityRanker()

    # 트렌드 차이가 큰 제품들
    ranker.popularity_cache = {
        'stable_product': {
            'normalized_score': 80.0,
            'trend_percentage': 0.0  # 안정세
        },
        'rising_product': {
            'normalized_score': 60.0,
            'trend_percentage': 60.0  # 60% 상승
        },
        'declining_product': {
            'normalized_score': 70.0,
            'trend_percentage': -30.0  # 30% 하락
        },
    }
    ranker.cache_timestamp = datetime.now()

    search_results = [
        {'product_idx': 'stable_product', 'relevance_score': 90.0, 'metadata': {}},
        {'product_idx': 'rising_product', 'relevance_score': 85.0, 'metadata': {}},
        {'product_idx': 'declining_product', 'relevance_score': 88.0, 'metadata': {}},
    ]

    print("\n트렌드 부스트 ON:")
    reranked_with_boost = await ranker.rerank(
        search_results=search_results,
        relevance_weight=0.5,
        popularity_weight=0.5,
        boost_trending=True  # 트렌드 부스트 활성화
    )

    for i, result in enumerate(reranked_with_boost, 1):
        pid = result['product_idx']
        pop = result['popularity_score']
        trend = result['trend_boost']
        final = result['final_score']
        trend_pct = ranker.popularity_cache[pid]['trend_percentage']
        print(f"{i}. {pid}: 인기도={pop:.1f}, 트렌드={trend_pct:+.1f}% (부스트 {trend:.2f}x), 최종={final:.1f}")

    print("\n트렌드 부스트 OFF:")
    reranked_no_boost = await ranker.rerank(
        search_results=search_results,
        relevance_weight=0.5,
        popularity_weight=0.5,
        boost_trending=False  # 트렌드 부스트 비활성화
    )

    for i, result in enumerate(reranked_no_boost, 1):
        pid = result['product_idx']
        pop = result['popularity_score']
        final = result['final_score']
        print(f"{i}. {pid}: 인기도={pop:.1f}, 최종={final:.1f}")

    # 검증
    print("\n검증:")
    top_with_boost = reranked_with_boost[0]['product_idx']
    top_no_boost = reranked_no_boost[0]['product_idx']

    print(f"트렌드 부스트 ON: {top_with_boost} (rising_product 가 올라와야 함)")
    print(f"트렌드 부스트 OFF: {top_no_boost} (stable_product 가 1위여야 함)")


async def test_new_product_protection():
    """신제품 보호 테스트"""
    print("\n\n=== 신제품 보호 테스트 ===")

    ranker = PopularityRanker()

    # 신제품 (인기도 낮음)
    ranker.popularity_cache = {
        'old_popular': {'normalized_score': 90.0, 'trend_percentage': 0.0},
        'new_unknown': {'normalized_score': 5.0, 'trend_percentage': 0.0},  # 인기도 매우 낮음
    }
    ranker.cache_timestamp = datetime.now()

    search_results = [
        {
            'product_idx': 'old_popular',
            'relevance_score': 85.0,
            'metadata': {'created_at': '2024-01-01T00:00:00'}  # 오래된 제품
        },
        {
            'product_idx': 'new_unknown',
            'relevance_score': 90.0,
            'metadata': {'created_at': datetime.now().isoformat()}  # 신제품
        },
    ]

    print("\n신제품 보호 ON:")
    reranked_protected = await ranker.rerank(
        search_results=search_results,
        relevance_weight=0.5,
        popularity_weight=0.5,
        protect_new_products=True  # 신제품 보호
    )

    for i, result in enumerate(reranked_protected, 1):
        pid = result['product_idx']
        pop = result['popularity_score']
        final = result['final_score']
        is_new = ranker._is_new_product(result['metadata'])
        print(f"{i}. {pid}: 인기도={pop:.1f}, 최종={final:.1f}, 신제품={is_new}")

    print("\n신제품 보호 OFF:")
    reranked_no_protection = await ranker.rerank(
        search_results=search_results,
        relevance_weight=0.5,
        popularity_weight=0.5,
        protect_new_products=False  # 신제품 보호 비활성화
    )

    for i, result in enumerate(reranked_no_protection, 1):
        pid = result['product_idx']
        pop = result['popularity_score']
        final = result['final_score']
        print(f"{i}. {pid}: 인기도={pop:.1f}, 최종={final:.1f}")

    # 검증
    # 검증
    print("\n=== 검증 ===")

    # new_unknown 제품 찾기
    new_protected = [r for r in reranked_protected if r['product_idx'] == 'new_unknown'][0]
    new_no_protection = [r for r in reranked_no_protection if r['product_idx'] == 'new_unknown'][0]

    new_product_pop_protected = new_protected['popularity_score']
    new_product_pop_no_protection = new_no_protection['popularity_score']

    print(f"[보호 ON] new_unknown 인기도: {new_product_pop_protected:.1f} (기대: >= 20.0)")
    print(f"[보호 OFF] new_unknown 인기도: {new_product_pop_no_protection:.1f} (기대: 5.0)")

    if new_product_pop_protected >= 20.0 and new_product_pop_no_protection == 5.0:
        print("✅ 신제품 보호 정상 작동")
    else:
        print(f"❌ 신제품 보호 오류 (보호ON={new_product_pop_protected:.1f}, 보호OFF={new_product_pop_no_protection:.1f})")


async def main():
    """모든 테스트 실행"""
    print("인기도 기반 검색 랭킹 테스트\n")

    await test_basic_reranking()
    await test_context_filters()
    await test_trending_boost()
    await test_new_product_protection()

    print("\n\n✅ 모든 테스트 완료")


if __name__ == "__main__":
    asyncio.run(main())
