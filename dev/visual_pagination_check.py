#!/usr/bin/env python3
"""
청진코리아 페이지네이션 시각적 검증
실제 브라우저로 페이지 구조 확인
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_servers.google_devtools.server import DevToolsAutomation


async def visual_inspect_pagination(category_name: str, base_url: str):
    """페이지네이션 시각적 검증"""
    automation = DevToolsAutomation()

    print(f"\n{'='*80}")
    print(f"카테고리: {category_name}")
    print(f"URL: {base_url}")
    print(f"{'='*80}")
    print("브라우저가 열리면 페이지네이션 영역을 확인하세요.")
    print("10초 후 DOM 구조를 분석합니다...")

    try:
        await automation.launch_browser(headless=False, browser_type="webkit")
        await automation.navigate(base_url)
        await asyncio.sleep(10)  # 시각적 확인 시간

        # 페이지네이션 관련 모든 요소 추출
        js_code = """
        () => {
            const result = {};

            // 1. 페이지 관련 모든 링크 (href 분석)
            const allLinks = Array.from(document.querySelectorAll('a'));
            result.all_links = allLinks.map(a => ({
                href: a.href,
                text: a.textContent.trim(),
                class: a.className,
                id: a.id
            })).filter(link => link.href && link.href.includes('list.php'));

            // 2. 숫자가 포함된 요소 (페이지 번호일 가능성)
            const numberedElements = Array.from(document.querySelectorAll('*')).filter(el => {
                const text = el.textContent.trim();
                return /^\d+$/.test(text) && text.length <= 3;  // 1~999
            }).map(el => ({
                tag: el.tagName,
                text: el.textContent.trim(),
                class: el.className,
                parent_class: el.parentElement?.className || '',
                onclick: el.onclick ? 'has onclick' : null
            }));

            // 3. 'page' 텍스트를 포함하는 요소
            const pageElements = Array.from(document.querySelectorAll('*')).filter(el =>
                el.textContent.toLowerCase().includes('page') ||
                el.className.toLowerCase().includes('page') ||
                el.className.toLowerCase().includes('pagination')
            ).map(el => ({
                tag: el.tagName,
                text: el.textContent.trim().substring(0, 100),
                class: el.className,
                id: el.id
            }));

            // 4. '다음', '이전', 'next', 'prev' 관련 요소
            const navElements = Array.from(document.querySelectorAll('*')).filter(el => {
                const text = el.textContent.toLowerCase();
                return text.includes('다음') || text.includes('이전') ||
                       text.includes('next') || text.includes('prev') ||
                       text.includes('>>') || text.includes('<<');
            }).map(el => ({
                tag: el.tagName,
                text: el.textContent.trim().substring(0, 50),
                class: el.className,
                href: el.href || null
            }));

            // 5. 현재 페이지 정보
            const currentPageIndicators = Array.from(document.querySelectorAll('.active, .current, [aria-current]'));
            result.current_page_elements = currentPageIndicators.map(el => ({
                tag: el.tagName,
                text: el.textContent.trim(),
                class: el.className,
                aria: el.getAttribute('aria-current')
            }));

            result.numbered_elements = numberedElements;
            result.page_elements = pageElements;
            result.nav_elements = navElements;

            // 6. 전체 HTML에서 'page=' 패턴 검색
            const htmlContent = document.documentElement.outerHTML;
            const pageParamMatches = htmlContent.match(/[?&]page=\d+/g) || [];
            result.page_param_occurrences = pageParamMatches.length;
            result.page_param_samples = [...new Set(pageParamMatches)].slice(0, 10);

            return result;
        }
        """

        result = await automation.evaluate_javascript(js_code)

        if result.get('status') == 'success':
            data = result.get('result', {})

            print(f"\n=== 분석 결과 ===")

            print(f"\n1. list.php 관련 링크: {len(data.get('all_links', []))}개")
            for link in data.get('all_links', [])[:10]:
                print(f"   {link['text'][:30]:30} → {link['href']}")

            print(f"\n2. 숫자 요소: {len(data.get('numbered_elements', []))}개")
            for elem in data.get('numbered_elements', [])[:10]:
                print(f"   <{elem['tag']}> {elem['text']} - class: {elem['class']}")

            print(f"\n3. 'page' 관련 요소: {len(data.get('page_elements', []))}개")
            for elem in data.get('page_elements', [])[:5]:
                print(f"   <{elem['tag']}> class: {elem['class']}")

            print(f"\n4. 네비게이션 요소: {len(data.get('nav_elements', []))}개")
            for elem in data.get('nav_elements', []):
                print(f"   <{elem['tag']}> {elem['text'][:30]} - {elem['href']}")

            print(f"\n5. 현재 페이지 표시: {len(data.get('current_page_elements', []))}개")
            for elem in data.get('current_page_elements', []):
                print(f"   <{elem['tag']}> {elem['text']} - class: {elem['class']}")

            print(f"\n6. HTML에서 'page=' 패턴: {data.get('page_param_occurrences', 0)}개")
            for sample in data.get('page_param_samples', []):
                print(f"   {sample}")

        print("\n브라우저를 5초 더 열어둡니다. 수동으로 확인하세요...")
        await asyncio.sleep(5)

        await automation.close_browser()

    except Exception as e:
        print(f"에러: {e}")
        await automation.close_browser()


async def main():
    """Jar 카테고리만 테스트 (4페이지로 가장 작음)"""
    await visual_inspect_pagination(
        "Jar",
        "http://chungjinkorea.com/kr/product/list.php?catcode=11"
    )


if __name__ == "__main__":
    asyncio.run(main())
