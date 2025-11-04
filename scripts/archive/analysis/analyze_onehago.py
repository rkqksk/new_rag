#!/usr/bin/env python3
"""
Onehago.com 사이트 분석 스크립트
- 제품 카테고리 구조 파악
- 제품 리스트 페이지 분석
- 상세 페이지 구조 분석
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright


async def analyze_site():
    """사이트 구조 분석"""

    output_dir = Path("data/onehago/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        # Chrome CDP 연결
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("✅ Connected to Chrome via CDP")
        except Exception as e:
            print(f"❌ CDP connection failed: {e}")
            return

        page = await browser.new_page()

        print("\n" + "="*60)
        print("🔍 Onehago.com Site Analysis")
        print("="*60)

        # 1. 홈페이지 분석
        print("\n📍 Step 1: Homepage Analysis")
        await page.goto("https://onehago.com", wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # 스크린샷
        await page.screenshot(path=str(output_dir / "homepage.png"))
        print(f"  ✅ Screenshot saved: homepage.png")

        # 카테고리 링크 수집
        categories = await page.eval_on_selector_all(
            "a[href*='cate=']",
            "elements => elements.map(el => ({text: el.textContent.trim(), href: el.href}))"
        )
        print(f"  ✅ Found {len(categories)} categories")

        # 2. BOTTLE 카테고리 분석
        print("\n📍 Step 2: BOTTLE Category Analysis")
        await page.goto("https://onehago.com/mall/?cate=7", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # 스크린샷
        await page.screenshot(path=str(output_dir / "bottle_category.png"), full_page=True)
        print(f"  ✅ Screenshot saved: bottle_category.png")

        # 페이지 HTML 저장
        html_content = await page.content()
        with open(output_dir / "bottle_category.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"  ✅ HTML saved: bottle_category.html")

        # 제품 요소 찾기
        print("\n  🔍 Looking for product elements...")

        # 다양한 선택자 시도
        selectors = [
            ".product",
            ".item",
            "[class*='product']",
            "[class*='item']",
            "a[href*='product']",
            "a[href*='pcode']",
            "a[href*='id=']"
        ]

        product_links = []
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"    ✅ Found {len(elements)} elements with selector: {selector}")

                    # 첫 3개 요소 분석
                    for idx, elem in enumerate(elements[:3]):
                        try:
                            html = await elem.inner_html()
                            print(f"\n    Element {idx + 1} ({selector}):")
                            print(f"    {html[:200]}...")

                            # 링크 찾기
                            links = await elem.query_selector_all("a")
                            for link in links:
                                href = await link.get_attribute("href")
                                if href:
                                    product_links.append(href)
                        except:
                            pass
            except Exception as e:
                print(f"    ❌ Selector {selector} failed: {e}")

        # 3. 첫 번째 제품 상세 페이지 분석
        if product_links:
            print(f"\n📍 Step 3: Product Detail Page Analysis")
            print(f"  Found {len(product_links)} product links")

            # 첫 번째 제품 링크
            first_product_url = product_links[0]
            if not first_product_url.startswith('http'):
                first_product_url = f"https://onehago.com{first_product_url}"

            print(f"  🔗 Analyzing: {first_product_url}")

            try:
                await page.goto(first_product_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)

                # 스크린샷
                await page.screenshot(path=str(output_dir / "product_detail.png"), full_page=True)
                print(f"  ✅ Screenshot saved: product_detail.png")

                # HTML 저장
                detail_html = await page.content()
                with open(output_dir / "product_detail.html", 'w', encoding='utf-8') as f:
                    f.write(detail_html)
                print(f"  ✅ HTML saved: product_detail.html")

                # 제품 정보 추출 시도
                print("\n  🔍 Extracting product information...")

                # 제품명
                try:
                    name_selectors = ["h1", ".product-name", ".title", "[class*='name']"]
                    for selector in name_selectors:
                        elem = await page.query_selector(selector)
                        if elem:
                            name = await elem.text_content()
                            print(f"    Name: {name.strip()}")
                            break
                except:
                    pass

                # 이미지
                try:
                    img_selectors = [
                        "img.product-image",
                        "img[src*='product']",
                        ".product-img img",
                        "img[alt]"
                    ]
                    for selector in img_selectors:
                        elem = await page.query_selector(selector)
                        if elem:
                            src = await elem.get_attribute("src")
                            print(f"    Image: {src}")
                            break
                except:
                    pass

                # 테이블 데이터
                try:
                    tables = await page.query_selector_all("table")
                    print(f"    Tables found: {len(tables)}")

                    for idx, table in enumerate(tables[:2]):
                        print(f"\n    Table {idx + 1}:")
                        rows = await table.query_selector_all("tr")
                        for row in rows[:5]:
                            cells = await row.query_selector_all("th, td")
                            if len(cells) >= 2:
                                key = await cells[0].text_content()
                                value = await cells[1].text_content()
                                print(f"      {key.strip()}: {value.strip()}")
                except:
                    pass

            except Exception as e:
                print(f"  ❌ Failed to analyze product page: {e}")

        # 4. 분석 결과 저장
        analysis_result = {
            'site': 'onehago.com',
            'analyzed_at': asyncio.get_event_loop().time(),
            'categories': categories,
            'product_links_found': len(product_links),
            'sample_product_links': product_links[:10],
            'status': 'completed'
        }

        with open(output_dir / "analysis_result.json", 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)

        print("\n" + "="*60)
        print("✅ Analysis Complete!")
        print("="*60)
        print(f"\nOutput directory: {output_dir}")
        print(f"- homepage.png")
        print(f"- bottle_category.png")
        print(f"- bottle_category.html")
        print(f"- product_detail.png (if found)")
        print(f"- product_detail.html (if found)")
        print(f"- analysis_result.json")

        await page.close()


if __name__ == "__main__":
    asyncio.run(analyze_site())
