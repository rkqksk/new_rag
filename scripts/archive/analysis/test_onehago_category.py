#!/usr/bin/env python3
"""
Onehago 카테고리 페이지 테스트
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright


async def test_category_page():
    """카테고리 페이지 테스트"""

    output_dir = Path("data/onehago/category_test")
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

        # 카테고리 페이지 테스트
        url = "https://onehago.com/mall/?cate=2"

        print(f"\n🔗 Testing: {url}")

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            # 스크린샷
            screenshot_path = output_dir / "category_2.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"✅ Screenshot: {screenshot_path}")

            # HTML 저장
            html_content = await page.content()
            html_path = output_dir / "category_2.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ HTML: {html_path}")

            # 페이지 타이틀
            title = await page.title()
            print(f"\n📦 Page Title: {title}")

            # 제품 카드 찾기
            print("\n🔍 Looking for product cards...")

            # .product 선택자
            products = await page.query_selector_all(".product")
            print(f"✅ Found {len(products)} .product elements")

            if products:
                # 첫 3개 제품 분석
                product_data = []

                for idx, product in enumerate(products[:5]):
                    print(f"\n📦 Product {idx + 1}:")

                    # HTML 구조 확인
                    html = await product.inner_html()

                    # 제품 ID 찾기 (prodWish 함수에서)
                    if "prodWish('" in html:
                        start = html.find("prodWish('") + 10
                        end = html.find("')", start)
                        product_id = html[start:end]
                        print(f"  ID: {product_id}")

                        # 링크 찾기
                        links = await product.query_selector_all("a")
                        for link in links:
                            href = await link.get_attribute("href")
                            onclick = await link.get_attribute("onclick")

                            if href and "javascript" not in href:
                                print(f"  Link (href): {href}")

                            if onclick:
                                print(f"  Link (onclick): {onclick[:100]}...")

                        # 이미지 찾기
                        img = await product.query_selector("img")
                        if img:
                            src = await img.get_attribute("src")
                            alt = await img.get_attribute("alt")
                            print(f"  Image: {src}")
                            if alt:
                                print(f"  Alt: {alt}")

                        # 텍스트 내용
                        text_content = await product.text_content()
                        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                        if lines:
                            print(f"  Text: {lines[:3]}")

                        product_data.append({
                            'id': product_id,
                            'html_snippet': html[:500]
                        })

                # 제품 데이터 저장
                with open(output_dir / "sample_products.json", 'w', encoding='utf-8') as f:
                    json.dump(product_data, f, ensure_ascii=False, indent=2)
                print(f"\n💾 Saved sample products to: sample_products.json")

            # onclick 이벤트 패턴 확인
            print("\n🔍 Checking onclick patterns...")
            all_links = await page.query_selector_all("a[onclick]")
            onclick_patterns = set()

            for link in all_links[:20]:
                onclick = await link.get_attribute("onclick")
                if onclick and "prod" in onclick.lower():
                    onclick_patterns.add(onclick[:100])

            print(f"Found {len(onclick_patterns)} unique onclick patterns:")
            for pattern in list(onclick_patterns)[:5]:
                print(f"  - {pattern}")

        except Exception as e:
            print(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()

        await page.close()


if __name__ == "__main__":
    asyncio.run(test_category_page())
