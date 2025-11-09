#!/usr/bin/env python3
"""
Jar 카테고리 페이지네이션 테스트
4페이지로 가장 작은 카테고리
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from chungjin_crawler import ChungjinCrawler


async def main():
    """Jar 카테고리 크롤링 테스트"""
    crawler = ChungjinCrawler(output_dir="data/test_jar_category")

    summary = await crawler.crawl_category(
        category_name="Jar",
        category_url="http://chungjinkorea.com/kr/product/list.php?part_idx=2",
        max_pages=4,
        delay=2,
    )

    print("\n" + "=" * 80)
    print("Jar 카테고리 크롤링 결과")
    print("=" * 80)
    print(f"총 페이지: {summary['total_pages']}개")
    print(f"총 제품: {summary['total_products']}개")
    print(f"성공: {summary['success']}개")
    print(f"실패: {summary['error']}개")
    print(f"성공률: {summary['success']/summary['total_products']*100:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
