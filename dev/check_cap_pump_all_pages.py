#!/usr/bin/env python3
"""
Cap&Pump 전체 페이지네이션 확인
5페이지 이후 추가 페이지 확인
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_servers.google_devtools.server import DevToolsAutomation


async def check_page_5_and_beyond():
    """5페이지 확인 및 추가 페이지 탐색"""
    automation = DevToolsAutomation()

    category_url = "http://chungjinkorea.com/kr/product/list.php?part_idx=3"

    print(f"\n{'='*80}")
    print(f"Cap&Pump 전체 페이지네이션 확인")
    print(f"{'='*80}\n")

    try:
        await automation.launch_browser(headless=False, browser_type="webkit")  # headless=False로 직접 확인
        await automation.navigate(category_url)
        await asyncio.sleep(3)

        # 5페이지로 이동
        click_page_5_js = """
        () => {
            const pageLinks = Array.from(document.querySelectorAll('#ajax_list .paging a'));
            const page5Link = pageLinks.find(a => a.textContent.trim() === '5');

            if (page5Link) {
                page5Link.click();
                return { clicked: true };
            }
            return { clicked: false };
        }
        """

        click_result = await automation.evaluate_javascript(click_page_5_js)

        if click_result.get('status') == 'success' and click_result.get('result', {}).get('clicked'):
            print("✅ 5페이지 버튼 클릭 성공")
            await asyncio.sleep(5)  # AJAX 로딩 대기

            # 5페이지에서 페이지네이션 확인
            check_page_5_js = """
            () => {
                // 제품 수
                const products = document.querySelectorAll('a[href*="view.php"]');
                const uniqueProducts = new Set();
                products.forEach(a => {
                    if (a.href.includes('idx=')) {
                        const idx = a.href.split('idx=')[1].split('&')[0];
                        uniqueProducts.add(idx);
                    }
                });

                // 페이지네이션 버튼 (모든 a 태그)
                const allPageLinks = Array.from(document.querySelectorAll('#ajax_list .paging a'));

                const pageInfo = allPageLinks.map(a => ({
                    text: a.textContent.trim(),
                    href: a.getAttribute('href'),
                    onclick: a.getAttribute('onclick'),
                    class: a.className
                }));

                // 숫자만 추출
                const pageNumbers = allPageLinks
                    .map(a => a.textContent.trim())
                    .filter(text => /^\d{1,3}$/.test(text))
                    .map(Number);

                const currentPage = document.querySelector('.cur');

                return {
                    products_count: uniqueProducts.size,
                    product_ids: Array.from(uniqueProducts).slice(0, 5),
                    all_links: pageInfo,
                    page_numbers: pageNumbers,
                    current_page: currentPage ? currentPage.textContent.trim() : null,
                    max_visible_page: Math.max(...pageNumbers)
                };
            }
            """

            page_5_result = await automation.evaluate_javascript(check_page_5_js)

            if page_5_result.get('status') == 'success':
                data = page_5_result.get('result', {})

                print(f"\n📄 5페이지 정보:")
                print(f"   제품 수: {data['products_count']}개")
                print(f"   제품 ID 샘플: {', '.join(data['product_ids'])}")
                print(f"   현재 페이지: {data['current_page']}")

                print(f"\n🔢 보이는 페이지 번호: {', '.join(map(str, data['page_numbers']))}")
                print(f"   최대 페이지: {data['max_visible_page']}")

                print(f"\n🔗 모든 페이지네이션 링크:")
                for i, link in enumerate(data['all_links'], 1):
                    print(f"   {i}. [{link['class']}] {link['text']} (href: {link['href']})")

                # "다음" 또는 "▶" 같은 버튼 찾기
                next_buttons = [
                    link for link in data['all_links']
                    if link['text'] in ['다음', '>', '▶', '»', 'next', 'Next']
                ]

                if next_buttons:
                    print(f"\n✅ '다음' 버튼 발견: {len(next_buttons)}개")
                    for btn in next_buttons:
                        print(f"   텍스트: {btn['text']}, 클래스: {btn['class']}")
                else:
                    print(f"\n⚠️ '다음' 버튼 없음")

        print(f"\n⏸️ 10초 대기 (수동 확인 가능)...")
        await asyncio.sleep(10)

        await automation.close_browser()

    except Exception as e:
        print(f"❌ 에러: {e}")
        await automation.close_browser()


if __name__ == "__main__":
    asyncio.run(check_page_5_and_beyond())
