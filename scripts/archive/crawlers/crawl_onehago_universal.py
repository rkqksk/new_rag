#!/usr/bin/env python3
"""
Onehago Universal Crawler - 전체 카테고리 크롤링
사용자 확인: Page 103까지 존재 → 각 카테고리별로 최대 페이지까지 크롤링
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
import re


# 카테고리 설정 (사용자 확인: Page 103 존재)
CATEGORIES = {
    2: {'name': 'PACKAGING', 'max_page': 150},  # 넉넉하게 150페이지
    7: {'name': 'BOTTLE', 'max_page': 150},
    21: {'name': 'CONTAINER', 'max_page': 150}
}


class OnehagoUniversalCrawler:
    def __init__(self, output_dir="data/onehago/universal"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file = self.output_dir / "crawl_progress.json"
        self.progress = self.load_progress()

    def load_progress(self):
        """진행 상황 로드"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {}

    def save_progress(self, category_id, page):
        """진행 상황 저장"""
        self.progress[str(category_id)] = {
            'last_page': page,
            'updated_at': datetime.now().isoformat()
        }
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    async def crawl_category_page(self, page, category_id, page_num):
        """단일 페이지 크롤링"""
        url = f"https://www.onehago.com/mall/?cate_mode=list&cate={category_id}&CURRENT_PAGE={page_num}"

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)

            # 제품 추출
            products = []

            # 제품 링크 패턴: /mall/product_view.html?product_no=XXX
            product_links = await page.query_selector_all('a[href*="product_view.html"]')

            seen_ids = set()
            for link in product_links:
                href = await link.get_attribute('href')
                if href and 'product_no=' in href:
                    product_id = href.split('product_no=')[1].split('&')[0]

                    if product_id not in seen_ids:
                        seen_ids.add(product_id)
                        products.append({
                            'product_id': product_id,
                            'category_id': category_id,
                            'category_name': CATEGORIES[category_id]['name'],
                            'detail_url': f"https://www.onehago.com/mall/product_view.html?product_no={product_id}",
                            'found_on_page': page_num
                        })

            return products

        except Exception as e:
            print(f"  ❌ Error on page {page_num}: {e}")
            return []

    async def crawl_category(self, category_id):
        """카테고리 전체 크롤링"""
        cat_info = CATEGORIES[category_id]
        cat_name = cat_info['name']
        max_page = cat_info['max_page']

        # 진행 상황에서 시작 페이지 확인
        start_page = 1
        if str(category_id) in self.progress:
            start_page = self.progress[str(category_id)]['last_page'] + 1
            print(f"📂 Resuming {cat_name} from page {start_page}")

        all_products = []

        async with async_playwright() as p:
            # CDP 연결
            try:
                browser = await p.chromium.connect_over_cdp("http://localhost:9222", timeout=60000)
                contexts = browser.contexts
                page = contexts[0].pages[0]
            except:
                print("⚠️ CDP not available, launching new browser...")
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()

            print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"📦 {cat_name} (ID: {category_id})")
            print(f"   Pages: {start_page} → {max_page}")
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

            empty_page_count = 0
            for page_num in range(start_page, max_page + 1):
                products = await self.crawl_category_page(page, category_id, page_num)

                if products:
                    print(f"[{page_num}/{max_page}] ✅ {len(products)} products")
                    all_products.extend(products)
                    empty_page_count = 0

                    # 10페이지마다 저장
                    if page_num % 10 == 0:
                        self.save_partial_results(category_id, all_products)
                        self.save_progress(category_id, page_num)
                        print(f"  💾 Checkpoint: {len(all_products)} products saved")
                else:
                    print(f"[{page_num}/{max_page}] ⚠️ No products")
                    empty_page_count += 1

                    # 연속 5페이지 비어있으면 종료
                    if empty_page_count >= 5:
                        print(f"\n  ⏹️ Stopping: {empty_page_count} consecutive empty pages")
                        break

                await page.wait_for_timeout(3000)  # 3초 지연

            # 최종 저장
            if all_products:
                self.save_partial_results(category_id, all_products)
                self.save_progress(category_id, page_num)

            print(f"\n✅ {cat_name} complete: {len(all_products)} products\n")

            return all_products

    def save_partial_results(self, category_id, products):
        """부분 결과 저장"""
        output_file = self.output_dir / f"category_{category_id}_{CATEGORIES[category_id]['name']}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

    async def run(self):
        """전체 크롤링 실행"""
        print("=" * 60)
        print("🚀 Onehago Universal Crawler")
        print("=" * 60)
        print()

        all_products = []

        for category_id in CATEGORIES.keys():
            products = await self.crawl_category(category_id)
            all_products.extend(products)

        # 전체 병합 파일 저장
        output_file = self.output_dir / "all_products_universal.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)

        print("=" * 60)
        print(f"✅ COMPLETE: {len(all_products)} total products")
        print(f"📁 Saved to: {output_file}")
        print("=" * 60)


if __name__ == "__main__":
    crawler = OnehagoUniversalCrawler()
    asyncio.run(crawler.run())
