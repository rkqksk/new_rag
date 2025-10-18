#!/usr/bin/env python3
"""
페이지네이션 URL 패턴 테스트
수동으로 page 파라미터를 추가해서 작동 여부 확인
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_servers.google_devtools.server import DevToolsAutomation


async def test_page_url(base_url: str, page_num: int):
    """특정 페이지 URL 테스트"""
    automation = DevToolsAutomation()

    # 여러 가능한 URL 패턴 시도
    url_patterns = [
        f"{base_url}&page={page_num}",
        f"{base_url}&p={page_num}",
        f"{base_url}&paged={page_num}",
        f"{base_url}?page={page_num}",
        f"{base_url}#page={page_num}"
    ]

    print(f"\n{'='*80}")
    print(f"Base URL: {base_url}")
    print(f"Testing page {page_num}")
    print(f"{'='*80}\n")

    for i, test_url in enumerate(url_patterns, 1):
        try:
            await automation.launch_browser(headless=True, browser_type="webkit")
            await automation.navigate(test_url)
            await asyncio.sleep(3)

            # 제품 수 확인
            js_code = """
            () => {
                const products = document.querySelectorAll('a[href*="view.php"]');
                const uniqueProducts = new Set();

                products.forEach(a => {
                    if (a.href.includes('idx=')) {
                        const idx = a.href.split('idx=')[1].split('&')[0];
                        uniqueProducts.add(idx);
                    }
                });

                // 페이지네이션 정보
                const paginationLinks = Array.from(document.querySelectorAll('a')).filter(a => {
                    const text = a.textContent.trim();
                    return /^\d{1,3}$/.test(text);
                });

                const currentPage = document.querySelector('.cur, .active, [aria-current]');

                return {
                    product_count: uniqueProducts.size,
                    product_ids: Array.from(uniqueProducts).slice(0, 5),
                    pagination_visible: paginationLinks.length > 0,
                    current_page: currentPage ? currentPage.textContent.trim() : null
                };
            }
            """

            result = await automation.evaluate_javascript(js_code)

            if result.get('status') == 'success':
                data = result.get('result', {})

                if data['product_count'] > 0:
                    print(f"✅ 패턴 {i} 작동! {test_url}")
                    print(f"   제품 수: {data['product_count']}개")
                    print(f"   제품 ID 샘플: {', '.join(data['product_ids'])}")
                    print(f"   현재 페이지: {data['current_page']}")
                else:
                    print(f"❌ 패턴 {i} 실패 (제품 없음)")

            await automation.close_browser()

        except Exception as e:
            print(f"❌ 패턴 {i} 에러: {e}")
            await automation.close_browser()


async def test_scroll_pagination(base_url: str):
    """스크롤 기반 페이지네이션 테스트"""
    automation = DevToolsAutomation()

    print(f"\n{'='*80}")
    print(f"스크롤 기반 페이지네이션 테스트")
    print(f"URL: {base_url}")
    print(f"{'='*80}\n")

    try:
        await automation.launch_browser(headless=False, browser_type="webkit")
        await automation.navigate(base_url)
        await asyncio.sleep(3)

        # 초기 제품 수
        initial_js = """
        () => {
            const products = document.querySelectorAll('a[href*="view.php"]');
            const uniqueProducts = new Set();
            products.forEach(a => {
                if (a.href.includes('idx=')) {
                    const idx = a.href.split('idx=')[1].split('&')[0];
                    uniqueProducts.add(idx);
                }
            });
            return uniqueProducts.size;
        }
        """

        initial_result = await automation.evaluate_javascript(initial_js)
        initial_count = initial_result.get('result', 0)
        print(f"초기 제품 수: {initial_count}개")

        # 페이지 끝까지 스크롤
        print("페이지 끝까지 스크롤 중...")
        scroll_js = "window.scrollTo(0, document.body.scrollHeight);"
        await automation.evaluate_javascript(f"() => {{ {scroll_js} }}")
        await asyncio.sleep(3)

        # 스크롤 후 제품 수
        after_result = await automation.evaluate_javascript(initial_js)
        after_count = after_result.get('result', 0)
        print(f"스크롤 후 제품 수: {after_count}개")

        if after_count > initial_count:
            print("✅ 무한 스크롤 감지!")
        else:
            print("❌ 무한 스크롤 없음")

        # 페이지 2 버튼 찾기 및 클릭 시도
        print("\n'2' 페이지 버튼 찾는 중...")
        find_page2_js = """
        () => {
            const links = Array.from(document.querySelectorAll('a'));
            const page2 = links.find(a => a.textContent.trim() === '2');

            if (page2) {
                return {
                    found: true,
                    href: page2.href,
                    onclick: page2.getAttribute('onclick'),
                    visible: page2.offsetParent !== null
                };
            }
            return { found: false };
        }
        """

        page2_result = await automation.evaluate_javascript(find_page2_js)
        page2_data = page2_result.get('result', {})

        if page2_data.get('found'):
            print(f"✅ 페이지 2 버튼 발견!")
            print(f"   href: {page2_data.get('href')}")
            print(f"   onclick: {page2_data.get('onclick')}")
            print(f"   visible: {page2_data.get('visible')}")
        else:
            print("❌ 페이지 2 버튼 없음")

        print("\n5초 대기 (수동 확인)...")
        await asyncio.sleep(5)

        await automation.close_browser()

    except Exception as e:
        print(f"에러: {e}")
        await automation.close_browser()


async def main():
    """Jar 카테고리로 테스트 (4페이지)"""
    base_url = "http://chungjinkorea.com/kr/product/list.php?catcode=11"

    # 1. URL 패턴 테스트
    print("=== 1. URL 패턴 테스트 ===")
    await test_page_url(base_url, 2)

    # 2. 스크롤 페이지네이션 테스트
    print("\n=== 2. 스크롤 페이지네이션 테스트 ===")
    await test_scroll_pagination(base_url)


if __name__ == "__main__":
    asyncio.run(main())
