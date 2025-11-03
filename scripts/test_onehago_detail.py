#!/usr/bin/env python3
"""
Onehago 제품 상세 페이지 테스트 (올바른 URL 사용)
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright


async def test_detail_page():
    """제품 상세 페이지 테스트"""

    output_dir = Path("data/onehago/detail_test")
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

        # 제품 상세 페이지 테스트 (카테고리 페이지에서 찾은 URL 패턴)
        product_id = "57497"
        company_no = "180"
        url = f"https://onehago.com/mall/?cate_mode=view&pid={product_id}&no={company_no}"

        print(f"\n🔗 Testing: {url}")

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            # 스크린샷
            screenshot_path = output_dir / f"detail_{product_id}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"✅ Screenshot: {screenshot_path}")

            # HTML 저장
            html_content = await page.content()
            html_path = output_dir / f"detail_{product_id}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ HTML: {html_path}")

            # 페이지 타이틀
            title = await page.title()
            print(f"\n📦 Page Title: {title}")

            # 제품 정보 추출
            print("\n📋 Extracting product information...")

            product_info = {
                'product_id': product_id,
                'company_no': company_no,
                'url': url
            }

            # 제품명
            selectors = [
                "h1", "h2", "h3",
                ".product-name", ".pname",
                "[class*='name']", "[id*='name']",
                ".title"
            ]

            for selector in selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.text_content()
                        if text and len(text.strip()) > 3 and len(text.strip()) < 200:
                            print(f"  ✅ Name ({selector}): {text.strip()}")
                            product_info['product_name'] = text.strip()
                            break
                except:
                    pass

            # 이미지
            img_selectors = [
                "img[src*='productImages']",
                "img[src*='product']",
                ".product-image img",
                "img.main-image"
            ]

            for selector in img_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        src = await elem.get_attribute("src")
                        if src:
                            if not src.startswith('http'):
                                src = f"https://onehago.com{src}"
                            print(f"  ✅ Image: {src}")
                            product_info['image_url'] = src
                            break
                except:
                    pass

            # 가격 정보
            price_selectors = [
                ".price", "[class*='price']", "[id*='price']",
                "td:contains('가격')", "th:contains('가격')"
            ]

            for selector in price_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.text_content()
                        if text and ('원' in text or ',' in text):
                            print(f"  ✅ Price: {text.strip()}")
                            product_info['price'] = text.strip()
                            break
                except:
                    pass

            # MOQ
            try:
                moq_elem = await page.eval_on_selector_all(
                    "*",
                    """elements => {
                        for (let el of elements) {
                            if (el.textContent && el.textContent.includes('moq')) {
                                return el.textContent;
                            }
                        }
                        return null;
                    }"""
                )
                if moq_elem:
                    print(f"  ✅ MOQ: {moq_elem}")
                    product_info['moq'] = moq_elem
            except:
                pass

            # 테이블 데이터
            try:
                tables = await page.query_selector_all("table")
                if tables:
                    print(f"\n📊 Found {len(tables)} tables")

                    table_data = {}

                    for idx, table in enumerate(tables[:3]):
                        print(f"\nTable {idx + 1}:")
                        rows = await table.query_selector_all("tr")

                        for row in rows[:15]:
                            cells = await row.query_selector_all("th, td")

                            if len(cells) >= 2:
                                key = await cells[0].text_content()
                                value = await cells[1].text_content()

                                key = key.strip()
                                value = value.strip()

                                if key and value and len(key) < 50:
                                    print(f"  {key}: {value}")
                                    table_data[key] = value

                    if table_data:
                        product_info['specifications'] = table_data

            except Exception as e:
                print(f"  ⚠️ Table extraction failed: {e}")

            # 회사 정보
            try:
                company_elem = await page.query_selector("[class*='company'], [id*='company']")
                if company_elem:
                    company_name = await company_elem.text_content()
                    print(f"\n🏢 Company: {company_name.strip()}")
                    product_info['company_name'] = company_name.strip()
            except:
                pass

            # 제품 정보 저장
            with open(output_dir / f"product_{product_id}_data.json", 'w', encoding='utf-8') as f:
                json.dump(product_info, f, ensure_ascii=False, indent=2)

            print(f"\n💾 Saved product data to: product_{product_id}_data.json")

            print("\n" + "="*60)
            print("✅ Detail page test successful!")
            print("="*60)

        except Exception as e:
            print(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()

        await page.close()


if __name__ == "__main__":
    asyncio.run(test_detail_page())
