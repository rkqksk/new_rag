#!/usr/bin/env python3
"""
인기도 스코어 계산 실행 스크립트

주기적으로 실행하여 product_popularity 테이블 업데이트
Cron: 0 */6 * * * (6시간마다)
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analytics.popularity_calculator import get_popularity_calculator


async def load_product_metadata() -> dict:
    """
    제품 메타데이터 로드

    실제로는 DB 또는 products.json에서 로드
    """
    # TODO: 실제 제품 데이터 로드
    # import json
    # products = {}
    # for file in Path("data/crawled_products_final").rglob("*.json"):
    #     with open(file) as f:
    #         product = json.load(f)
    #         products[product['idx']] = {
    #             'product_code': product.get('product_code'),
    #             'product_name': product.get('product_name'),
    #             'category': product.get('category'),
    #             'material': product['specifications'].get('material'),
    #             'capacity_ml': product['specifications'].get('capacity_ml'),
    #             'neck_size': product['specifications'].get('neck_size'),
    #         }
    # return products

    return {}


async def main():
    """메인 실행"""
    print(f"[{datetime.now()}] 인기도 스코어 계산 시작")

    try:
        # 1. 계산기 초기화
        calculator = get_popularity_calculator()

        # 2. 제품 메타데이터 로드
        print("제품 메타데이터 로드 중...")
        product_metadata = await load_product_metadata()
        print(f"총 {len(product_metadata)}개 제품")

        # 3. 인기도 스코어 계산 (최근 30일)
        print("인기도 스코어 계산 중...")
        product_scores = await calculator.calculate_product_scores(window_days=30)
        print(f"총 {len(product_scores)}개 제품 스코어 계산 완료")

        # 4. 카테고리별 스코어 계산
        print("카테고리별 스코어 계산 중...")
        category_scores = await calculator.calculate_category_scores(
            product_scores,
            product_metadata
        )
        print(f"카테고리별 스코어 계산 완료")

        # 5. DB 업데이트
        print("product_popularity 테이블 업데이트 중...")
        await calculator.update_popularity_table(
            product_scores,
            category_scores,
            product_metadata
        )
        print("DB 업데이트 완료")

        # 6. 결과 요약
        print("\n=== 계산 결과 요약 ===")
        print(f"총 제품 수: {len(product_scores)}")

        # 상위 10개 제품
        top_10 = sorted(
            product_scores.items(),
            key=lambda x: x[1]['normalized_score'],
            reverse=True
        )[:10]

        print("\n상위 10개 제품:")
        for i, (product_idx, scores) in enumerate(top_10, 1):
            metadata = product_metadata.get(product_idx, {})
            print(f"{i}. {product_idx} ({metadata.get('product_name', 'Unknown')})")
            print(f"   스코어: {scores['normalized_score']:.2f}")
            print(f"   샘플신청: {scores['sample_request_count']}, 클릭: {scores['click_count']}")
            print(f"   트렌드: {scores['trend_percentage']:+.1f}% (부스트: {scores['trend_boost']:.2f}x)")

        # 트렌드 상승 제품
        trending_up = [
            (idx, scores) for idx, scores in product_scores.items()
            if scores['trend_percentage'] > 50
        ]
        trending_up.sort(key=lambda x: x[1]['trend_percentage'], reverse=True)

        if trending_up:
            print(f"\n급상승 제품 ({len(trending_up)}개):")
            for product_idx, scores in trending_up[:5]:
                metadata = product_metadata.get(product_idx, {})
                print(f"  - {product_idx} ({metadata.get('product_name', 'Unknown')})")
                print(f"    트렌드: {scores['trend_percentage']:+.1f}%")

        print(f"\n[{datetime.now()}] 인기도 스코어 계산 완료")

    except Exception as e:
        print(f"[ERROR] 인기도 스코어 계산 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
