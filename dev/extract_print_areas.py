#!/usr/bin/env python3
"""
인쇄영역 다운로드 링크 추출 및 파일 다운로드
- "인쇄영역 다운로드" 텍스트가 포함된 링크 찾기
- 파일 다운로드 후 files/print_area/ 저장
"""

import asyncio
import aiohttp
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_servers.google_devtools.server import DevToolsAutomation


class PrintAreaExtractor:
    def __init__(self, output_dir: str = "files/print_area"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.automation = DevToolsAutomation()

    async def check_and_download_print_area(self, url: str, idx: str):
        """인쇄영역 다운로드 링크 확인 및 다운로드"""
        print(f"\n{'='*80}")
        print(f"제품 분석: idx={idx}")
        print(f"URL: {url}")
        print(f"{'='*80}")

        try:
            await self.automation.launch_browser(headless=True, browser_type="webkit")
            await self.automation.navigate(url)
            await asyncio.sleep(3)

            # 인쇄영역 다운로드 링크 찾기
            js_code = """
            () => {
                // "인쇄영역 다운로드" 텍스트가 포함된 링크 찾기
                const links = Array.from(document.querySelectorAll('a'));
                const printLink = links.find(link =>
                    link.textContent.includes('인쇄영역') &&
                    link.textContent.includes('다운로드')
                );

                if (printLink) {
                    return {
                        found: true,
                        href: printLink.href,
                        text: printLink.textContent.trim()
                    };
                } else {
                    return {
                        found: false
                    };
                }
            }
            """

            result = await self.automation.evaluate_javascript(js_code)

            if result.get('status') == 'success':
                data = result.get('result', {})

                if data.get('found'):
                    print(f"✅ 인쇄영역 발견!")
                    print(f"   링크: {data['href']}")
                    print(f"   텍스트: {data['text']}")

                    # 파일 다운로드
                    download_url = data['href']
                    await self.download_file(download_url, idx)

                    await self.automation.close_browser()
                    return {
                        'idx': idx,
                        'has_print_area': True,
                        'download_url': download_url,
                        'saved_path': str(self.output_dir / f"idx_{idx}.pdf")
                    }
                else:
                    print(f"❌ 인쇄영역 없음")
                    await self.automation.close_browser()
                    return {
                        'idx': idx,
                        'has_print_area': False
                    }

        except Exception as e:
            print(f"에러: {e}")
            await self.automation.close_browser()
            return {
                'idx': idx,
                'error': str(e)
            }

    async def download_file(self, url: str, idx: str):
        """파일 다운로드"""
        output_path = self.output_dir / f"idx_{idx}.pdf"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()

                        with open(output_path, 'wb') as f:
                            f.write(content)

                        print(f"   ✓ 다운로드 완료: {output_path}")
                        print(f"   파일 크기: {len(content)} bytes")
                    else:
                        print(f"   ✗ 다운로드 실패: HTTP {response.status}")
        except Exception as e:
            print(f"   ✗ 다운로드 에러: {e}")


async def main():
    """8개 샘플 제품 인쇄영역 추출"""
    product_urls = {
        "Bottle": [
            ("960", "http://chungjinkorea.com/kr/product/view.php?idx=960"),
            ("969", "http://chungjinkorea.com/kr/product/view.php?idx=969"),
            ("967", "http://chungjinkorea.com/kr/product/view.php?idx=967"),
            ("912", "http://chungjinkorea.com/kr/product/view.php?idx=912")
        ],
        "Jar": [
            ("928", "http://chungjinkorea.com/kr/product/view.php?idx=928"),
            ("937", "http://chungjinkorea.com/kr/product/view.php?idx=937")
        ],
        "Cap&Pump": [
            ("946", "http://chungjinkorea.com/kr/product/view.php?idx=946"),
            ("934", "http://chungjinkorea.com/kr/product/view.php?idx=934")
        ]
    }

    extractor = PrintAreaExtractor()
    results = []

    for category, products in product_urls.items():
        print(f"\n{'='*80}")
        print(f"카테고리: {category}")
        print(f"{'='*80}")

        for idx, url in products:
            result = await extractor.check_and_download_print_area(url, idx)
            results.append(result)
            await asyncio.sleep(2)  # 서버 부하 방지

    # 결과 요약
    print(f"\n\n{'='*80}")
    print("인쇄영역 추출 결과 요약")
    print(f"{'='*80}")

    has_print = [r for r in results if r.get('has_print_area')]
    no_print = [r for r in results if not r.get('has_print_area') and 'error' not in r]
    errors = [r for r in results if 'error' in r]

    print(f"\n✅ 인쇄영역 있음: {len(has_print)}개")
    for r in has_print:
        print(f"   - idx={r['idx']}: {r['saved_path']}")

    print(f"\n❌ 인쇄영역 없음: {len(no_print)}개")
    for r in no_print:
        print(f"   - idx={r['idx']}")

    if errors:
        print(f"\n⚠️  에러 발생: {len(errors)}개")
        for r in errors:
            print(f"   - idx={r['idx']}: {r['error']}")


if __name__ == "__main__":
    asyncio.run(main())
