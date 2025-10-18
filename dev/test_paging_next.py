#!/usr/bin/env python3
"""
Cap&Pump paging-next 버튼 테스트
그룹 페이지네이션 확인
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_servers.google_devtools.server import DevToolsAutomation


async def test_paging_next():
    """paging-next 버튼으로 다음 그룹 이동 테스트"""
    automation = DevToolsAutomation()

    category_url = "http://chungjinkorea.com/kr/product/list.php?part_idx=3"

    print(f"\n{'='*80}")
    print(f"Cap&Pump paging-next 버튼 테스트")
    print(f"{'='*80}\n")

    try:
        await automation.launch_browser(headless=True, browser_type="webkit")
        await automation.navigate(category_url)
        await asyncio.sleep(3)

        # 1. 먼저 5페이지로 이동
        print("1️⃣ 5페이지로 이동...")
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

        result = await automation.evaluate_javascript(click_page_5_js)
        if result.get('status') == 'success' and result.get('result', {}).get('clicked'):
            print("   ✅ 5페이지 클릭 성공")
            await asyncio.sleep(5)

        # 2. paging-next 버튼 클릭
        print("\n2️⃣ paging-next 버튼 클릭...")
        click_next_js = """
        () => {
            const nextButton = document.querySelector('.paging-next');
            if (nextButton) {
                nextButton.click();
                return { clicked: true, disabled: nextButton.classList.contains('disabled') };
            }
            return { clicked: false };
        }
        """

        next_result = await automation.evaluate_javascript(click_next_js)
        if next_result.get('status') == 'success':
            data = next_result.get('result', {})
            if data.get('clicked'):
                print(f"   ✅ paging-next 버튼 클릭 성공")
                if data.get('disabled'):
                    print(f"   ⚠️ 버튼이 disabled 상태입니다")
                await asyncio.sleep(5)  # AJAX 로딩 대기

                # 3. 새로운 페이지 그룹 확인
                print("\n3️⃣ 새 페이지 그룹 확인...")
                check_new_group_js = """
                () => {
                    const products = document.querySelectorAll('a[href*="view.php"]');
                    const uniqueProducts = new Set();
                    products.forEach(a => {
                        if (a.href.includes('idx=')) {
                            const idx = a.href.split('idx=')[1].split('&')[0];
                            uniqueProducts.add(idx);
                        }
                    });

                    const pageLinks = Array.from(document.querySelectorAll('#ajax_list .paging a'));
                    const pageNumbers = pageLinks
                        .map(a => a.textContent.trim())
                        .filter(text => /^\d{1,3}$/.test(text))
                        .map(Number);

                    const currentPage = document.querySelector('.cur');

                    return {
                        products_count: uniqueProducts.size,
                        product_ids: Array.from(uniqueProducts).slice(0, 5),
                        page_numbers: pageNumbers,
                        current_page: currentPage ? currentPage.textContent.trim() : null
                    };
                }
                """

                new_group_result = await automation.evaluate_javascript(check_new_group_js)
                if new_group_result.get('status') == 'success':
                    new_data = new_group_result.get('result', {})

                    print(f"   제품 수: {new_data['products_count']}개")
                    print(f"   제품 ID: {', '.join(new_data['product_ids'])}")
                    print(f"   보이는 페이지: {', '.join(map(str, new_data['page_numbers']))}")
                    print(f"   현재 페이지: {new_data['current_page']}")

                    # 페이지 번호가 6 이상이면 성공
                    if any(p >= 6 for p in new_data['page_numbers']):
                        print(f"\n   ✅ 다음 그룹 이동 성공! (6페이지 이상 발견)")
                    else:
                        print(f"\n   ⚠️ 여전히 1-5 페이지 그룹")

            else:
                print(f"   ❌ paging-next 버튼 클릭 실패")

        # 4. paging-last 버튼으로 마지막 페이지 확인
        print("\n4️⃣ paging-last 버튼으로 마지막 페이지 이동...")
        click_last_js = """
        () => {
            const lastButton = document.querySelector('.paging-last');
            if (lastButton) {
                lastButton.click();
                return { clicked: true };
            }
            return { clicked: false };
        }
        """

        last_result = await automation.evaluate_javascript(click_last_js)
        if last_result.get('status') == 'success' and last_result.get('result', {}).get('clicked'):
            print(f"   ✅ paging-last 버튼 클릭 성공")
            await asyncio.sleep(5)

            # 마지막 페이지 정보 확인
            last_page_result = await automation.evaluate_javascript(check_new_group_js)
            if last_page_result.get('status') == 'success':
                last_data = last_page_result.get('result', {})

                print(f"\n   📄 마지막 페이지 정보:")
                print(f"      제품 수: {last_data['products_count']}개")
                print(f"      제품 ID: {', '.join(last_data['product_ids'])}")
                print(f"      보이는 페이지: {', '.join(map(str, last_data['page_numbers']))}")
                print(f"      현재 페이지: {last_data['current_page']}")

                # 총 제품 수 계산
                max_page = max(last_data['page_numbers'])
                last_page_count = last_data['products_count']
                estimated_total = (max_page - 1) * 10 + last_page_count

                print(f"\n   📊 예상 총 제품 수: {estimated_total}개")
                print(f"      (페이지 1-{max_page-1}: {(max_page-1)*10}개 + 마지막: {last_page_count}개)")
                print(f"      사용자 확인 값: 139개")
                print(f"      차이: {abs(139 - estimated_total)}개")

        await automation.close_browser()

    except Exception as e:
        print(f"❌ 에러: {e}")
        await automation.close_browser()


if __name__ == "__main__":
    asyncio.run(test_paging_next())
