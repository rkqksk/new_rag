#!/usr/bin/env python3
"""
Bottle 카테고리 페이지네이션 테스트
68 페이지 (14개 그룹 예상), ~680개 제품 예상
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from chungjin_crawler import ChungjinCrawler


async def main():
    """Bottle 카테고리 크롤링 테스트"""
    crawler = ChungjinCrawler(output_dir="data/test_bottle_category")

    summary = await crawler.crawl_category(
        category_name="Bottle",
        category_url="http://chungjinkorea.com/kr/product/list.php?part_idx=1",
        max_pages=68,
        delay=2,
    )

    print("\n" + "=" * 80)
    print("Bottle 카테고리 크롤링 결과")
    print("=" * 80)
    print(f"총 페이지: {summary['total_pages']}개")
    print(f"총 제품: {summary['total_products']}개")
    print(f"성공: {summary['success']}개")
    print(f"실패: {summary['error']}개")
    print(f"성공률: {summary['success']/summary['total_products']*100:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
