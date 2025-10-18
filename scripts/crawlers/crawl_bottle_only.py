#!/usr/bin/env python3
"""
Bottle 카테고리만 크롤링 (Jar, Cap&Pump는 이미 완료)
68 페이지, ~680개 제품 예상
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from chungjin_crawler import ChungjinCrawler


async def main():
    """Bottle 카테고리 크롤링"""
    crawler = ChungjinCrawler(output_dir="data/crawled_products")

    print("\n" + "="*80)
    print("Bottle 카테고리 크롤링 시작")
    print("="*80)
    print("페이지: 68개")
    print("예상 제품: ~680개")
    print("예상 소요 시간: ~2.5-3시간")
    print("="*80)

    summary = await crawler.crawl_category(
        category_name="Bottle",
        category_url="http://chungjinkorea.com/kr/product/list.php?part_idx=1",
        max_pages=68,
        delay=2
    )

    print("\n" + "="*80)
    print("Bottle 카테고리 크롤링 완료!")
    print("="*80)
    print(f"총 제품: {summary['total_products']}개")
    print(f"성공: {summary['success']}개")
    print(f"실패: {summary['error']}개")
    print(f"성공률: {summary['success']/summary['total_products']*100:.1f}%")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
