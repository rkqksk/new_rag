#!/usr/bin/env python3
"""
페이지네이션 링크의 실제 href 추출
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_servers.google_devtools.server import DevToolsAutomation


async def extract_pagination_hrefs(category_name: str, base_url: str):
    """페이지네이션 링크의 href 추출"""
    automation = DevToolsAutomation()

    print(f"\n{'='*80}")
    print(f"카테고리: {category_name}")
    print(f"URL: {base_url}")
    print(f"{'='*80}")

    try:
        await automation.launch_browser(headless=True, browser_type="webkit")
        await automation.navigate(base_url)
        await asyncio.sleep(3)

        # 숫자 페이지 링크만 정확히 추출
        js_code = """
        () => {
            // 1~3자리 숫자만 포함하는 <a> 태그 찾기
            const allLinks = Array.from(document.querySelectorAll('a'));

            const pageLinks = allLinks.filter(a => {
                const text = a.textContent.trim();
                // 정확히 숫자만 (1~999)
                return /^\d{1,3}$/.test(text);
            }).map(a => ({
                text: a.textContent.trim(),
                href: a.href,
                class: a.className,
                onclick: a.getAttribute('onclick'),
                parent: a.parentElement?.tagName || null
            }));

            // 중복 제거 (href 기준)
            const uniqueLinks = [];
            const seenHrefs = new Set();

            for (const link of pageLinks) {
                if (!seenHrefs.has(link.href)) {
                    seenHrefs.add(link.href);
                    uniqueLinks.push(link);
                }
            }

            // 숫자 순으로 정렬
            uniqueLinks.sort((a, b) => parseInt(a.text) - parseInt(b.text));

            return uniqueLinks;
        }
        """

        result = await automation.evaluate_javascript(js_code)

        if result.get('status') == 'success':
            links = result.get('result', [])

            print(f"\n페이지네이션 링크: {len(links)}개\n")

            for link in links:
                current_marker = " ← 현재 페이지" if link['class'] == 'cur' else ""
                print(f"페이지 {link['text']}: {link['href']}{current_marker}")
                if link['onclick']:
                    print(f"  onclick: {link['onclick']}")
                print(f"  class: {link['class']}")
                print()

        await automation.close_browser()

    except Exception as e:
        print(f"에러: {e}")
        await automation.close_browser()


async def main():
    """3개 카테고리 모두 테스트"""
    categories = [
        ("Jar (4페이지)", "http://chungjinkorea.com/kr/product/list.php?catcode=11"),
        ("Cap&Pump (14페이지)", "http://chungjinkorea.com/kr/product/list.php?catcode=12"),
        ("Bottle (68페이지)", "http://chungjinkorea.com/kr/product/list.php?catcode=10")
    ]

    for name, url in categories:
        await extract_pagination_hrefs(name, url)
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
