#!/usr/bin/env python3
"""
Clean crawler 테스트 - 첫 1개 카테고리만 완전히 크롤링
"""

import asyncio
import sys
sys.path.insert(0, '.')

# Import the clean crawler
from scripts.crawl_onehago_full_clean import OneHagoCleanCrawler
import json


async def test():
    # 카테고리 로드
    with open("data/onehago/analysis/analysis_result.json") as f:
        data = json.load(f)

    # 첫 번째 카테고리만
    category = None
    for cat in data['categories']:
        href = cat.get('href', '')
        if 'cate=' in href:
            cate_id = href.split('cate=')[1].split('&')[0]
            category = {
                'id': cate_id,
                'name': cat['text'].strip()
            }
            break

    if not category:
        print("No category found!")
        return

    print(f"Testing with category: {category['name']}")

    # 크롤러 생성
    crawler = OneHagoCleanCrawler(
        delay_min=1.0,
        delay_max=2.0,
        output_dir="data/onehago/test_clean"
    )

    # 단일 카테고리 크롤링
    await crawler.crawl_all([category])

    # 결과 확인
    output_file = crawler.output_dir / "all_products_clean.json"
    with open(output_file) as f:
        products = json.load(f)

    print(f"\n✅ Test complete!")
    print(f"Total products: {len(products)}")

    # 상세 정보 있는 제품 수
    detailed = [p for p in products if 'specifications' in p]
    print(f"Products with specifications: {len(detailed)}/{len(products)}")

    if detailed:
        # 샘플 출력
        sample = detailed[0]
        print(f"\n📦 Sample product:")
        print(json.dumps(sample, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(test())
