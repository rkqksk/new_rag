#!/usr/bin/env python3
"""
제품 상세 페이지 구조 분석 스크립트
- 샘플 제품 페이지 분석하여 필요한 필드 추출 전략 수립
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright


async def analyze_product_page(product_url: str):
    """제품 상세 페이지 구조 분석"""

    async with async_playwright() as p:
        # Chrome 연결
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("✅ Connected to Chrome debugging instance")
        except:
            print("🔄 Launching new browser...")
            browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()

        try:
            print(f"\n🌐 Loading: {product_url}")
            await page.goto(product_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            # 스크린샷
            output_dir = Path("data/freemold/analysis")
            output_dir.mkdir(parents=True, exist_ok=True)

            screenshot_path = output_dir / "product_detail_screenshot.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"📸 Screenshot: {screenshot_path}")

            # HTML 구조
            html = await page.content()
            html_path = output_dir / "product_detail_structure.html"
            html_path.write_text(html, encoding='utf-8')
            print(f"💾 HTML: {html_path}")

            # 주요 정보 추출 시도
            print("\n🔍 Extracting information...")

            # 1. 제품명
            product_name_selectors = [
                "h1", "h2.product-name", ".product-title",
                "#productName", ".prd-name"
            ]
            product_name = None
            for selector in product_name_selectors:
                try:
                    el = await page.query_selector(selector)
                    if el:
                        product_name = (await el.text_content()).strip()
                        if product_name and len(product_name) > 3:
                            print(f"  ✅ Product Name ({selector}): {product_name}")
                            break
                except:
                    pass

            # 2. 이미지
            image_selectors = [
                "img.product-image", ".product-img img",
                "#productImage", ".prd-img img", "img[src*='product']"
            ]
            images = []
            for selector in image_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for el in elements:
                        src = await el.get_attribute('src')
                        if src and 'product' in src.lower():
                            images.append(src)
                    if images:
                        print(f"  ✅ Images ({selector}): {len(images)} found")
                        for idx, img in enumerate(images[:3], 1):
                            print(f"      {idx}. {img}")
                        break
                except:
                    pass

            # 3. 가격/MOQ
            price_selectors = [
                ".price", "#price", ".prd-price",
                "span:has-text('가격')", "td:has-text('가격')"
            ]
            price_info = []
            for selector in price_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for el in elements:
                        text = (await el.text_content()).strip()
                        if text and ('원' in text or '가격' in text or 'MOQ' in text):
                            price_info.append(text)
                except:
                    pass
            if price_info:
                print(f"  ✅ Price info: {price_info[:3]}")

            # 4. 테이블 데이터 (스펙)
            print("\n  📊 Table data:")
            tables = await page.query_selector_all("table")
            for idx, table in enumerate(tables[:3], 1):
                try:
                    rows = await table.query_selector_all("tr")
                    print(f"\n    Table {idx}: {len(rows)} rows")
                    for row_idx, row in enumerate(rows[:5], 1):
                        cells = await row.query_selector_all("th, td")
                        cell_texts = []
                        for cell in cells:
                            cell_texts.append((await cell.text_content()).strip())
                        print(f"      Row {row_idx}: {' | '.join(cell_texts)}")
                except:
                    pass

            # 5. 제조사 정보
            company_selectors = [
                "a[href*='Company']", ".company-name",
                ".manufacturer", "#companyName"
            ]
            company_name = None
            for selector in company_selectors:
                try:
                    el = await page.query_selector(selector)
                    if el:
                        company_name = (await el.text_content()).strip()
                        if company_name:
                            print(f"\n  ✅ Company ({selector}): {company_name}")
                            break
                except:
                    pass

            # 6. 모든 텍스트 분석 (키워드 추출)
            body_text = await page.eval_on_selector("body", "el => el.innerText")

            # 용량 패턴
            import re
            capacities = re.findall(r'(\d+(?:\.\d+)?)\s*(ml|ML|L|g|cc)', body_text)
            if capacities:
                print(f"\n  📏 Capacities found: {capacities[:5]}")

            # 재질 패턴
            materials = re.findall(r'(PET|PETG|PP|PE|HDPE|LDPE|PVC|ABS|AS|PC)', body_text)
            if materials:
                print(f"  🧪 Materials found: {set(materials)}")

            # 넥사이즈 패턴
            neck_sizes = re.findall(r'(\d+/\d+)', body_text)
            if neck_sizes:
                print(f"  🔩 Neck sizes found: {set(neck_sizes)[:5]}")

            # 결과 저장
            analysis_result = {
                "url": product_url,
                "product_name": product_name,
                "images": images[:10],
                "price_info": price_info,
                "company_name": company_name,
                "capacities": capacities[:10],
                "materials": list(set(materials)),
                "neck_sizes": list(set(neck_sizes))[:10],
                "analyzed_at": str(asyncio.get_event_loop().time())
            }

            result_path = output_dir / "analysis_result.json"
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Analysis saved: {result_path}")

            print("\n" + "="*60)
            print("✅ Analysis complete!")
            print("="*60)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await context.close()
            if browser.is_connected():
                await browser.close()


async def main():
    # 샘플 제품 URL (B001에서 첫 번째 제품)
    sample_url = "https://www.freemold.net/Front/Product/?tp=vi&pIdx=88939"

    print("="*60)
    print("🔬 Freemold Product Detail Page Analyzer")
    print("="*60)

    await analyze_product_page(sample_url)


if __name__ == "__main__":
    asyncio.run(main())
