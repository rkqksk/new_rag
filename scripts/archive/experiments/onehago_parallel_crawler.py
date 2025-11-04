#!/usr/bin/env python3
"""
Onehago Parallel Crawler - Category/Page Range Support

Usage:
    python3 onehago_parallel_crawler.py --category 2 --start-page 1 --end-page 50

Supports 8 parallel execution by distributing categories and page ranges.
"""

import asyncio
import json
import argparse
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
import random

# Categories (user confirmed: up to page 103+)
CATEGORIES = {
    2: {'name': 'PACKAGING', 'max_page': 150},
    7: {'name': 'BOTTLE', 'max_page': 150},
    21: {'name': 'CONTAINER', 'max_page': 150}
}

class OnehagoParallelCrawler:
    """Parallel-ready Onehago crawler with page range support"""

    def __init__(self, category_id, start_page, end_page, delay_min=0.5, delay_max=2.0):
        self.category_id = category_id
        self.start_page = start_page
        self.end_page = end_page
        self.delay_min = delay_min
        self.delay_max = delay_max

        self.output_dir = Path('data/onehago/crawled')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.progress_file = self.output_dir / 'crawl_progress.json'

        # Statistics
        self.stats = {
            'pages_crawled': 0,
            'products_extracted': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'end_time': None
        }

    async def crawl_page(self, page, page_num):
        """Crawl a single page"""
        url = f"https://www.onehago.com/mall/?cate_mode=list&cate={self.category_id}&CURRENT_PAGE={page_num}"

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(self.delay_min + (self.delay_max - self.delay_min) * random.random())

            # Extract products
            products = []
            product_links = await page.query_selector_all('a[href*="product_view.html"]')

            seen_ids = set()
            for link in product_links:
                href = await link.get_attribute('href')
                if href and 'product_no=' in href:
                    product_id = href.split('product_no=')[1].split('&')[0]

                    if product_id not in seen_ids:
                        seen_ids.add(product_id)

                        # Get product details from link
                        try:
                            product_name = await link.text_content()
                            product_name = product_name.strip() if product_name else ''
                        except:
                            product_name = ''

                        products.append({
                            'product_id': product_id,
                            'product_name': product_name,
                            'category_id': self.category_id,
                            'category_name': CATEGORIES[self.category_id]['name'],
                            'detail_url': f"https://www.onehago.com/mall/product_view.html?product_no={product_id}",
                            'found_on_page': page_num,
                            'crawled_at': datetime.now().isoformat()
                        })

            return products

        except Exception as e:
            print(f"  ❌ Error on page {page_num}: {e}")
            self.stats['errors'] += 1
            return []

    def save_progress(self, page_num, products):
        """Save progress to shared file with file locking"""
        import fcntl

        # Read current products with lock
        all_products = []
        products_file = self.output_dir / 'all_products.json'

        if products_file.exists():
            with open(products_file, 'r+') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    all_products = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        # Add new products (avoid duplicates by product_id)
        existing_ids = {p['product_id'] for p in all_products}
        new_products = [p for p in products if p['product_id'] not in existing_ids]
        all_products.extend(new_products)

        # Write back with lock
        with open(products_file, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(all_products, f, ensure_ascii=False, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        # Update progress
        progress = {}
        if self.progress_file.exists():
            with open(self.progress_file, 'r+') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    progress = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        category_key = f"cat_{self.category_id}"
        if category_key not in progress:
            progress[category_key] = {}

        progress[category_key][f"page_{page_num}"] = {
            'products': len(products),
            'updated_at': datetime.now().isoformat()
        }

        with open(self.progress_file, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(progress, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    async def crawl_range(self):
        """Crawl assigned page range"""
        print("=" * 70)
        print(f"🤖 Onehago Parallel Crawler")
        print(f"📂 Category: {self.category_id} ({CATEGORIES[self.category_id]['name']})")
        print(f"📄 Pages: {self.start_page} - {self.end_page}")
        print(f"⏱️  Delay: {self.delay_min}s - {self.delay_max}s")
        print("=" * 70)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            # Crawl assigned page range
            for page_num in range(self.start_page, self.end_page + 1):
                try:
                    products = await self.crawl_page(page, page_num)

                    if not products:
                        print(f"  ⚠️  Page {page_num}: No products (likely end of category)")
                        # Don't break - might be temporary issue
                        continue

                    self.save_progress(page_num, products)
                    self.stats['pages_crawled'] += 1
                    self.stats['products_extracted'] += len(products)

                    print(f"  ✅ Page {page_num}: {len(products)} products")

                except Exception as e:
                    print(f"  ❌ Failed page {page_num}: {e}")
                    self.stats['errors'] += 1

            await browser.close()

        # Final stats
        self.stats['end_time'] = datetime.now()
        duration = self.stats['end_time'] - self.stats['start_time']

        print("\n" + "=" * 70)
        print("CRAWLER SUMMARY")
        print("=" * 70)
        print(f"Category: {self.category_id} ({CATEGORIES[self.category_id]['name']})")
        print(f"Pages: {self.stats['pages_crawled']}")
        print(f"Products: {self.stats['products_extracted']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Duration: {duration}")
        print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description='Onehago Parallel Crawler')
    parser.add_argument('--category', type=int, required=True, choices=[2, 7, 21], help='Category ID')
    parser.add_argument('--start-page', type=int, required=True, help='Start page number')
    parser.add_argument('--end-page', type=int, required=True, help='End page number')
    parser.add_argument('--min-delay', type=float, default=0.5, help='Min delay between requests')
    parser.add_argument('--max-delay', type=float, default=2.0, help='Max delay between requests')

    args = parser.parse_args()

    crawler = OnehagoParallelCrawler(
        category_id=args.category,
        start_page=args.start_page,
        end_page=args.end_page,
        delay_min=args.min_delay,
        delay_max=args.max_delay
    )

    asyncio.run(crawler.crawl_range())

if __name__ == "__main__":
    main()
