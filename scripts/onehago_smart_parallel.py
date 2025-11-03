#!/usr/bin/env python3
"""
Onehago Smart Parallel Crawler - Category-Based Distribution

Crawls by category, not page ranges. Skips already-completed categories.

Usage:
    python3 onehago_smart_parallel.py --categories 2,7,39,207
"""

import json
import argparse
import time
import random
import fcntl
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class OnehagoSmartCrawler:
    """Smart category-based crawler"""

    def __init__(self, category_ids, delay_min=0.1, delay_max=0.3):
        self.category_ids = category_ids
        self.delay_min = delay_min
        self.delay_max = delay_max

        self.output_dir = Path('data/onehago/crawled')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.progress_file = self.output_dir / 'crawl_progress.json'
        self.products_file = self.output_dir / 'all_products.json'

        # Load valid categories metadata
        self.valid_categories = self.load_valid_categories()

        self.driver = None

        # Statistics
        self.stats = {
            'categories_crawled': 0,
            'pages_crawled': 0,
            'products_extracted': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

    def load_valid_categories(self):
        """Load category metadata"""
        valid_file = Path('data/onehago/valid_categories.json')
        if valid_file.exists():
            with open(valid_file, 'r') as f:
                cats = json.load(f)
                return {cat['id']: cat for cat in cats}
        return {}

    def is_category_completed(self, category_id):
        """Check if category already completed"""
        if not self.progress_file.exists():
            return False

        with open(self.progress_file, 'r') as f:
            progress = json.load(f)
            return str(category_id) in progress.get('completed_categories', [])

    def mark_category_completed(self, category_id):
        """Mark category as completed"""
        progress = {}
        if self.progress_file.exists():
            with open(self.progress_file, 'r+') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    progress = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        if 'completed_categories' not in progress:
            progress['completed_categories'] = []

        if str(category_id) not in progress['completed_categories']:
            progress['completed_categories'].append(str(category_id))

        progress['last_category'] = str(category_id)
        progress['last_updated'] = datetime.now().isoformat()

        with open(self.progress_file, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(progress, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def setup_driver(self):
        """Initialize Selenium"""
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def crawl_page(self, category_id, page_num):
        """Crawl a single page"""
        url = f"https://www.onehago.com/mall/?cate_mode=list&cate={category_id}&CURRENT_PAGE={page_num}"

        try:
            self.driver.get(url)
            time.sleep(self.delay_min + (self.delay_max - self.delay_min) * random.random())

            # Extract products
            products = []
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, ".product")

            seen_ids = set()
            for product in product_elements:
                try:
                    html = product.get_attribute('innerHTML')

                    # Extract product_id from prodWish()
                    product_id = None
                    if "prodWish('" in html:
                        start = html.find("prodWish('") + 10
                        end = html.find("')", start)
                        product_id = html[start:end]

                    if not product_id or product_id in seen_ids:
                        continue

                    seen_ids.add(product_id)

                    # Extract product name
                    product_name = ''
                    try:
                        img = product.find_element(By.TAG_NAME, "img")
                        img_alt = img.get_attribute("alt") or ""
                        img_title = img.get_attribute("title") or ""
                        if img_alt and "새창열기" not in img_alt and len(img_alt) > 3:
                            product_name = img_alt.strip()
                        elif img_title and len(img_title) > 3:
                            product_name = img_title.strip()
                    except:
                        pass

                    # Extract company_no
                    company_no = None
                    try:
                        links = product.find_elements(By.CSS_SELECTOR, "a[href*='cate_mode=view']")
                        for link in links:
                            href = link.get_attribute("href")
                            if href and "&no=" in href:
                                no_start = href.find("&no=") + 4
                                no_end = href.find("&", no_start)
                                company_no = href[no_start:no_end] if no_end != -1 else href[no_start:]
                                break
                    except:
                        pass

                    products.append({
                        'product_id': product_id,
                        'product_name': product_name,
                        'company_no': company_no,
                        'category_id': str(category_id),
                        'category_name': f'Category_{category_id}',
                        'detail_url': f"https://www.onehago.com/mall/?cate_mode=view&no={company_no}&cateno={category_id}",
                        'crawled_at': datetime.now().isoformat()
                    })
                except Exception as e:
                    continue

            return products

        except Exception as e:
            print(f"  ❌ Error on page {page_num}: {e}")
            self.stats['errors'] += 1
            return []

    def save_products(self, products):
        """Save products with deduplication"""
        # Load existing
        all_products = []
        if self.products_file.exists():
            with open(self.products_file, 'r', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    all_products = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        # Deduplicate
        existing_ids = {p['product_id'] for p in all_products}
        new_products = [p for p in products if p['product_id'] not in existing_ids]
        all_products.extend(new_products)

        # Save
        with open(self.products_file, 'w', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(all_products, f, ensure_ascii=False, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        return len(new_products)

    def crawl_category(self, category_id):
        """Crawl entire category"""
        if self.is_category_completed(category_id):
            print(f"⏭️  Category {category_id}: Already completed, skipping")
            return

        cat_info = self.valid_categories.get(str(category_id), {})
        max_pages = cat_info.get('pages', 10)

        print(f"\n📂 Category {category_id}: {max_pages} pages expected")

        category_products = []
        for page_num in range(1, max_pages + 1):
            products = self.crawl_page(category_id, page_num)

            if not products:
                # No products = likely end of category
                if page_num == 1:
                    print(f"  ⚠️  Page 1: No products (empty category?)")
                break

            category_products.extend(products)
            new_count = self.save_products(products)
            self.stats['pages_crawled'] += 1
            self.stats['products_extracted'] += new_count

            print(f"  ✅ Page {page_num}: {len(products)} products ({new_count} new)")

        # Mark category complete
        self.mark_category_completed(category_id)
        self.stats['categories_crawled'] += 1
        print(f"✅ Category {category_id}: {len(category_products)} products collected")

    def crawl_all(self):
        """Crawl all assigned categories"""
        print("=" * 70)
        print(f"🤖 Onehago Smart Crawler")
        print(f"📂 Categories: {self.category_ids}")
        print(f"⏱️  Delay: {self.delay_min}s - {self.delay_max}s")
        print("=" * 70)

        self.setup_driver()

        for category_id in self.category_ids:
            try:
                self.crawl_category(category_id)
            except Exception as e:
                print(f"❌ Failed category {category_id}: {e}")
                self.stats['errors'] += 1

        # Cleanup
        if self.driver:
            self.driver.quit()

        # Final stats
        self.stats['end_time'] = datetime.now()
        duration = self.stats['end_time'] - self.stats['start_time']

        print("\n" + "=" * 70)
        print("CRAWLER SUMMARY")
        print("=" * 70)
        print(f"Categories: {self.stats['categories_crawled']}/{len(self.category_ids)}")
        print(f"Pages: {self.stats['pages_crawled']}")
        print(f"Products: {self.stats['products_extracted']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Duration: {duration}")
        print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description='Onehago Smart Parallel Crawler')
    parser.add_argument('--categories', type=str, required=True, help='Comma-separated category IDs')
    parser.add_argument('--min-delay', type=float, default=0.1)
    parser.add_argument('--max-delay', type=float, default=0.3)

    args = parser.parse_args()

    category_ids = [int(c.strip()) for c in args.categories.split(',')]

    crawler = OnehagoSmartCrawler(
        category_ids=category_ids,
        delay_min=args.min_delay,
        delay_max=args.max_delay
    )

    crawler.crawl_all()

if __name__ == "__main__":
    main()
