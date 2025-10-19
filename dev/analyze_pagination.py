#!/usr/bin/env python3
"""
청진코리아 페이지네이션 구조 분석
카테고리별 페이지 수 및 URL 패턴 파악
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_servers.google_devtools.server import DevToolsAutomation


async def analyze_category_pagination(category_name: str, base_url: str):
    """카테고리의 페이지네이션 분석"""
    automation = DevToolsAutomation()

    print(f"\n{'='*80}")
    print(f"카테고리 분석: {category_name}")
    print(f"URL: {base_url}")
    print(f"{'='*80}")

    try:
        await automation.launch_browser(headless=False, browser_type="webkit")
        await automation.navigate(base_url)
        await asyncio.sleep(3)

        # 페이지네이션 정보 추출
        js_code = """
        () => {
            const result = {};

            // 1. 페이지네이션 링크 찾기
            const paginationLinks = Array.from(document.querySelectorAll('a[href*="page="]'));
            result.pagination_links = paginationLinks.map(a => ({
                href: a.href,
                text: a.textContent.trim()
            }));

            // 2. 현재 페이지 정보
            const currentPage = document.querySelector('.pagination .active') ||
                               document.querySelector('a.active') ||
                               document.querySelector('[class*="current"]');

            result.current_page = currentPage ? currentPage.textContent.trim() : '1';

            // 3. 제품 링크 수집
            const productLinks = Array.from(document.querySelectorAll('a[href*="view.php"]'));
            result.product_links = productLinks.map(a => a.href).filter((v, i, a) => a.indexOf(v) === i);
            result.product_count = result.product_links.length;

            // 4. 페이지 셀렉터 패턴 탐지
            const allAs = Array.from(document.querySelectorAll('a'));
            result.all_hrefs = allAs.map(a => a.href).slice(0, 50);  // 샘플

            return result;
        }
        """

        result = await automation.evaluate_javascript(js_code)

        if result.get('status') == 'success':
            data = result.get('result', {})

            print(f"\n현재 페이지: {data.get('current_page')}")
            print(f"제품 수: {data.get('product_count')}개")

            print(f"\n페이지네이션 링크: {len(data.get('pagination_links', []))}개")
            for link in data.get('pagination_links', [])[:10]:
                print(f"  {link['text']}: {link['href']}")

            print(f"\n제품 링크 샘플: (처음 5개)")
            for plink in data.get('product_links', [])[:5]:
                print(f"  {plink}")

            # 최대 페이지 번호 추정
            page_numbers = []
            for link in data.get('pagination_links', []):
                try:
                    if 'page=' in link['href']:
                        page_num = int(link['href'].split('page=')[1].split('&')[0])
                        page_numbers.append(page_num)
                except (ValueError, KeyError, IndexError) as e:
                    logger.debug(f"Error parsing pagination link: {e}")

            if page_numbers:
                max_page = max(page_numbers)
                print(f"\n✅ 최대 페이지 번호: {max_page}")
            else:
                print(f"\n⚠️  페이지네이션 링크를 찾을 수 없습니다")

        await automation.close_browser()

    except Exception as e:
        print(f"에러: {e}")
        await automation.close_browser()


async def main():
    """3개 카테고리 분석"""
    categories = [
        ("Bottle", "http://chungjinkorea.com/kr/product/list.php?catcode=10"),
        ("Jar", "http://chungjinkorea.com/kr/product/list.php?catcode=11"),
        ("Cap&Pump", "http://chungjinkorea.com/kr/product/list.php?catcode=12")
    ]

    for name, url in categories:
        await analyze_category_pagination(name, url)
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
