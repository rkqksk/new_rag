#!/usr/bin/env python3
"""
Cap&Pump 카테고리 페이지네이션 테스트
14 페이지 (3개 그룹), 137개 제품 예상
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from chungjin_crawler import ChungjinCrawler


async def main():
    """Cap&Pump 카테고리 크롤링 테스트"""
    crawler = ChungjinCrawler(output_dir="data/test_cap_pump_category")

    summary = await crawler.crawl_category(
        category_name="Cap&Pump",
        category_url="http://chungjinkorea.com/kr/product/list.php?part_idx=3",
        max_pages=14,
        delay=2
    )

    print("\n" + "="*80)
    print("Cap&Pump 카테고리 크롤링 결과")
    print("="*80)
    print(f"총 페이지: {summary['total_pages']}개")
    print(f"총 제품: {summary['total_products']}개")
    print(f"성공: {summary['success']}개")
    print(f"실패: {summary['error']}개")
    print(f"성공률: {summary['success']/summary['total_products']*100:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
