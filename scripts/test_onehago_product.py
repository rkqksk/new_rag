#!/usr/bin/env python3
"""
Onehago 제품 상세 페이지 테스트
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def test_product_page():
    """제품 페이지 테스트"""

    output_dir = Path("data/onehago/test")
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

        # 제품 ID 테스트
        product_id = "57513"
        url = f"https://onehago.com/mall/product.php?id={product_id}"

        print(f"\n🔗 Testing: {url}")

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            # 스크린샷
            screenshot_path = output_dir / f"product_{product_id}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"✅ Screenshot: {screenshot_path}")

            # HTML 저장
            html_content = await page.content()
            html_path = output_dir / f"product_{product_id}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ HTML: {html_path}")

            # 제품명 추출
            try:
                title = await page.title()
                print(f"\n📦 Page Title: {title}")
            except:
                pass

            # 제품 정보 추출
            print("\n📋 Extracting product info...")

            # 제품명 시도
            selectors = ["h1", "h2", ".product-name", ".pname", "[class*='name']", "[id*='name']"]
            for selector in selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.text_content()
                        if text and len(text.strip()) > 0:
                            print(f"  Name ({selector}): {text.strip()}")
                            break
                except:
                    pass

            # 이미지
            img_selectors = ["img[src*='product']", "img[src*='Product']", "img.pimg", "img.product-image"]
            for selector in img_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        src = await elem.get_attribute("src")
                        if src:
                            print(f"  Image: {src}")
                            break
                except:
                    pass

            # 가격
            price_selectors = [".price", "[class*='price']", "[id*='price']"]
            for selector in price_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.text_content()
                        if text and len(text.strip()) > 0:
                            print(f"  Price: {text.strip()}")
                            break
                except:
                    pass

            # 테이블 데이터
            try:
                tables = await page.query_selector_all("table")
                if tables:
                    print(f"\n📊 Found {len(tables)} tables")

                    for idx, table in enumerate(tables[:2]):
                        print(f"\nTable {idx + 1}:")
                        rows = await table.query_selector_all("tr")
                        for row in rows[:10]:
                            cells = await row.query_selector_all("th, td")
                            if len(cells) >= 2:
                                key = await cells[0].text_content()
                                value = await cells[1].text_content()
                                print(f"  {key.strip()}: {value.strip()}")
            except Exception as e:
                print(f"  ⚠️ Table extraction failed: {e}")

        except Exception as e:
            print(f"❌ Failed: {e}")

        await page.close()


if __name__ == "__main__":
    asyncio.run(test_product_page())
