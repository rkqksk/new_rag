#!/usr/bin/env python3
"""
청진코리아 전체 사이트 크롤링
Jar (4p, 37개) + Cap&Pump (14p, 137개) + Bottle (68p, ~680개)
= 총 86 페이지, ~854개 제품
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from chungjin_crawler import ChungjinCrawler


async def main():
    """전체 카테고리 크롤링"""
    crawler = ChungjinCrawler(output_dir="data/crawled_products")

    print("\n" + "="*80)
    print("청진코리아 전체 사이트 크롤링 시작")
    print("="*80)
    print("Jar:       4 페이지  (예상  37개 제품)")
    print("Cap&Pump: 14 페이지  (예상 137개 제품)")
    print("Bottle:   68 페이지  (예상 680개 제품)")
    print("="*80)
    print("총:       86 페이지  (예상 854개 제품)")
    print("예상 소요 시간: ~3.5-4시간")
    print("="*80)

    summary = await crawler.crawl_all_categories(delay=2)

    print("\n" + "="*80)
    print("전체 사이트 크롤링 완료!")
    print("="*80)
    print(f"총 제품: {summary['total_products']}개")
    print(f"성공: {summary['total_success']}개")
    print(f"실패: {summary['total_error']}개")
    print(f"성공률: {summary['total_success']/summary['total_products']*100:.1f}%")
    print("="*80)

    # 카테고리별 요약
    print("\n카테고리별 결과:")
    for cat_summary in summary['categories']:
        print(f"  {cat_summary['category']:10} - "
              f"{cat_summary['total_products']:3}개 제품 "
              f"(성공: {cat_summary['success']}, 실패: {cat_summary['error']})")


if __name__ == "__main__":
    asyncio.run(main())
