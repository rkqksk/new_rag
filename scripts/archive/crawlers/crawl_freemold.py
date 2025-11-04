#!/usr/bin/env python3
"""
Freemold.net 크롤링 스크립트
- 제품 목록 및 상세 정보 수집
- Chrome DevTools Protocol 사용
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

try:
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    print("❌ Playwright not installed. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "playwright"], check=True)
    subprocess.run(["playwright", "install", "chromium"], check=True)
    from playwright.async_api import async_playwright, Page, Browser


class FreemoldCrawler:
    """Freemold.net 크롤러"""

    def __init__(self, output_dir: str = "data/freemold_products"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = "https://www.freemold.net"
        self.products: List[Dict[str, Any]] = []

    async def crawl(self):
        """크롤링 실행"""
        async with async_playwright() as p:
            # Chrome 연결 (기존 remote debugging 인스턴스 사용)
            try:
                browser = await p.chromium.connect_over_cdp("http://localhost:9222")
                print("✅ Connected to existing Chrome instance")
            except Exception as e:
                print(f"⚠️ Could not connect to remote Chrome: {e}")
                print("🔄 Launching new browser...")
                browser = await p.chromium.launch(headless=False)

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = await context.new_page()

            try:
                # 1. 메인 페이지 방문
                print(f"\n🌐 Navigating to {self.base_url}...")
                await page.goto(self.base_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)

                # 2. 사이트 구조 분석
                await self.analyze_site_structure(page)

                # 3. 제품 카테고리 찾기
                categories = await self.find_product_categories(page)
                print(f"\n📦 Found {len(categories)} categories")

                # 4. 각 카테고리별 제품 수집
                for idx, category in enumerate(categories, 1):
                    print(f"\n[{idx}/{len(categories)}] Processing: {category['name']}")
                    await self.crawl_category(page, category)

                # 5. 결과 저장
                await self.save_results()

            except Exception as e:
                print(f"❌ Error during crawling: {e}")
                import traceback
                traceback.print_exc()

            finally:
                await context.close()
                if browser.is_connected():
                    await browser.close()

    async def analyze_site_structure(self, page: Page):
        """사이트 구조 분석"""
        print("\n🔍 Analyzing site structure...")

        # 페이지 제목
        title = await page.title()
        print(f"  Title: {title}")

        # 주요 링크들
        links = await page.eval_on_selector_all(
            "a[href]",
            """(elements) => elements.slice(0, 20).map(el => ({
                text: el.textContent.trim(),
                href: el.href
            }))"""
        )

        print(f"\n  Main links (first 20):")
        for link in links[:10]:
            print(f"    - {link['text']}: {link['href']}")

        # 스크린샷 저장
        screenshot_path = self.output_dir / "homepage_screenshot.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"\n  📸 Screenshot saved: {screenshot_path}")

        # HTML 구조 저장
        html = await page.content()
        html_path = self.output_dir / "homepage_structure.html"
        html_path.write_text(html, encoding='utf-8')
        print(f"  💾 HTML saved: {html_path}")

    async def find_product_categories(self, page: Page) -> List[Dict[str, str]]:
        """제품 카테고리 찾기"""
        # 일반적인 카테고리 선택자들 시도
        category_selectors = [
            "nav a[href*='product']",
            "nav a[href*='category']",
            ".menu a[href*='product']",
            ".category-link",
            "a[href*='category']",
            ".product-category a"
        ]

        categories = []
        for selector in category_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    for el in elements:
                        text = await el.text_content()
                        href = await el.get_attribute('href')
                        if text and href:
                            categories.append({
                                'name': text.strip(),
                                'url': href if href.startswith('http') else f"{self.base_url}{href}"
                            })
                    if categories:
                        break
            except:
                continue

        # 중복 제거
        unique_categories = []
        seen_urls = set()
        for cat in categories:
            if cat['url'] not in seen_urls:
                unique_categories.append(cat)
                seen_urls.add(cat['url'])

        return unique_categories

    async def crawl_category(self, page: Page, category: Dict[str, str]):
        """특정 카테고리의 제품들 크롤링"""
        try:
            await page.goto(category['url'], wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            # 제품 목록 찾기
            product_selectors = [
                ".product-item",
                ".product",
                "article.product",
                ".woocommerce-LoopProduct-link",
                "a[href*='product']"
            ]

            products = []
            for selector in product_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"    Found {len(elements)} products with selector: {selector}")
                        products = elements
                        break
                except:
                    continue

            # 각 제품 정보 추출
            for idx, product_el in enumerate(products[:10], 1):  # 처음 10개만
                try:
                    product_data = await self.extract_product_info(page, product_el, category['name'])
                    if product_data:
                        self.products.append(product_data)
                        print(f"      [{idx}] {product_data.get('name', 'Unknown')}")
                except Exception as e:
                    print(f"      ❌ Error extracting product {idx}: {e}")

        except Exception as e:
            print(f"    ❌ Error crawling category: {e}")

    async def extract_product_info(self, page: Page, element, category: str) -> Dict[str, Any]:
        """제품 정보 추출"""
        try:
            # 제품명
            name = await element.text_content() or "Unknown"

            # 링크
            href = await element.get_attribute('href')
            url = href if href and href.startswith('http') else f"{self.base_url}{href}" if href else ""

            # 이미지
            img = await element.query_selector('img')
            image_url = await img.get_attribute('src') if img else None

            return {
                'name': name.strip(),
                'url': url,
                'category': category,
                'image_url': image_url,
                'crawled_at': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"        Error extracting info: {e}")
            return None

    async def save_results(self):
        """결과 저장"""
        if not self.products:
            print("\n⚠️ No products collected")
            return

        # JSON 저장
        output_file = self.output_dir / f"products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Saved {len(self.products)} products to: {output_file}")

        # 요약 출력
        print(f"\n📊 Summary:")
        print(f"  Total products: {len(self.products)}")
        categories = set(p['category'] for p in self.products)
        print(f"  Categories: {len(categories)}")
        for cat in categories:
            count = sum(1 for p in self.products if p['category'] == cat)
            print(f"    - {cat}: {count} products")


async def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🤖 Freemold.net Crawler")
    print("=" * 60)

    crawler = FreemoldCrawler()
    await crawler.crawl()

    print("\n" + "=" * 60)
    print("✅ Crawling completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
