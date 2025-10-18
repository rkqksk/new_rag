#!/usr/bin/env python3
"""
Cap&Pump 카테고리 페이지네이션 구조 확인
총 139개 제품 예상
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_servers.google_devtools.server import DevToolsAutomation


async def check_cap_pump_structure():
    """Cap&Pump 카테고리 구조 확인"""
    automation = DevToolsAutomation()

    category_url = "http://chungjinkorea.com/kr/product/list.php?part_idx=3"

    print(f"\n{'='*80}")
    print(f"Cap&Pump 카테고리 구조 확인")
    print(f"URL: {category_url}")
    print(f"{'='*80}\n")

    try:
        await automation.launch_browser(headless=True, browser_type="webkit")
        await automation.navigate(category_url)
        await asyncio.sleep(3)

        # 페이지 정보 확인
        check_js = """
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

            // 페이지네이션 버튼
            const pageLinks = Array.from(document.querySelectorAll('#ajax_list .paging a'));
            const pageNumbers = pageLinks
                .map(a => a.textContent.trim())
                .filter(text => /^\d{1,3}$/.test(text));

            const currentPage = document.querySelector('.cur');

            return {
                products_count: uniqueProducts.size,
                product_ids_sample: Array.from(uniqueProducts).slice(0, 10),
                pagination_buttons: pageNumbers,
                current_page: currentPage ? currentPage.textContent.trim() : null,
                max_page: Math.max(...pageNumbers.map(Number))
            };
        }
        """

        result = await automation.evaluate_javascript(check_js)

        if result.get('status') == 'success':
            data = result.get('result', {})

            print(f"✅ 첫 페이지 제품 수: {data['products_count']}개")
            print(f"✅ 제품 ID 샘플: {', '.join(data['product_ids_sample'][:5])}")
            print(f"✅ 페이지네이션 버튼: {', '.join(map(str, data['pagination_buttons']))}")
            print(f"✅ 현재 페이지: {data['current_page']}")
            print(f"✅ 최대 페이지: {data['max_page']}")

            # 예상 총 제품 수 계산
            estimated_total = (data['max_page'] - 1) * 10 + data['products_count']
            print(f"\n📊 예상 총 제품 수: {estimated_total}개")
            print(f"   (페이지 1-{data['max_page']-1}: 10개씩 = {(data['max_page']-1)*10}개")
            print(f"   + 마지막 페이지: {data['products_count']}개)")

            # 사용자 확인 값과 비교
            print(f"\n🔍 사용자 확인 값: 139개")
            print(f"   차이: {abs(139 - estimated_total)}개")

            if abs(139 - estimated_total) <= 5:
                print("   ✅ 예상치와 일치!")
            else:
                print("   ⚠️ 차이가 있습니다. 마지막 페이지 확인 필요")

        await automation.close_browser()

    except Exception as e:
        print(f"❌ 에러: {e}")
        await automation.close_browser()


async def test_page_2():
    """2페이지 클릭 테스트"""
    automation = DevToolsAutomation()

    category_url = "http://chungjinkorea.com/kr/product/list.php?part_idx=3"

    print(f"\n{'='*80}")
    print(f"2페이지 클릭 테스트")
    print(f"{'='*80}\n")

    try:
        await automation.launch_browser(headless=True, browser_type="webkit")
        await automation.navigate(category_url)
        await asyncio.sleep(3)

        # 2페이지 버튼 클릭
        click_js = """
        () => {
            const pageLinks = Array.from(document.querySelectorAll('#ajax_list .paging a'));
            const page2Link = pageLinks.find(a => a.textContent.trim() === '2');

            if (page2Link) {
                page2Link.click();
                return { clicked: true };
            }
            return { clicked: false };
        }
        """

        click_result = await automation.evaluate_javascript(click_js)

        if click_result.get('status') == 'success':
            if click_result.get('result', {}).get('clicked'):
                print("✅ 2페이지 버튼 클릭 성공")
                await asyncio.sleep(5)  # AJAX 로딩 대기

                # 2페이지 제품 확인
                check_js = """
                () => {
                    const products = document.querySelectorAll('a[href*="view.php"]');
                    const uniqueProducts = new Set();
                    products.forEach(a => {
                        if (a.href.includes('idx=')) {
                            const idx = a.href.split('idx=')[1].split('&')[0];
                            uniqueProducts.add(idx);
                        }
                    });

                    return {
                        products_count: uniqueProducts.size,
                        product_ids: Array.from(uniqueProducts).slice(0, 10)
                    };
                }
                """

                page2_result = await automation.evaluate_javascript(check_js)

                if page2_result.get('status') == 'success':
                    page2_data = page2_result.get('result', {})
                    print(f"✅ 2페이지 제품 수: {page2_data['products_count']}개")
                    print(f"✅ 제품 ID 샘플: {', '.join(page2_data['product_ids'][:5])}")
            else:
                print("❌ 2페이지 버튼 찾기 실패")

        await automation.close_browser()

    except Exception as e:
        print(f"❌ 에러: {e}")
        await automation.close_browser()


async def main():
    """Cap&Pump 구조 확인 및 테스트"""
    # 1. 기본 구조 확인
    await check_cap_pump_structure()

    # 2. 페이지 클릭 테스트
    await test_page_2()


if __name__ == "__main__":
    asyncio.run(main())
