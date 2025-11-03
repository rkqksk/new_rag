#!/usr/bin/env python3
"""
Onehago Selenium Parallel Crawler

Usage:
    python3 onehago_selenium_parallel.py --category 2 --start-page 1 --end-page 50
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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Categories
CATEGORIES = {
    2: {'name': 'PACKAGING', 'max_page': 150},
    7: {'name': 'BOTTLE', 'max_page': 150},
    21: {'name': 'CONTAINER', 'max_page': 150}
}

class OnehagoSeleniumCrawler:
    """Selenium-based Onehago parallel crawler"""

    def __init__(self, category_id, start_page, end_page, delay_min=1.0, delay_max=3.0):
        self.category_id = category_id
        self.start_page = start_page
        self.end_page = end_page
        self.delay_min = delay_min
        self.delay_max = delay_max

        self.output_dir = Path('data/onehago/crawled')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.progress_file = self.output_dir / 'crawl_progress.json'
        self.products_file = self.output_dir / 'all_products.json'

        self.driver = None

        # Statistics
        self.stats = {
            'pages_crawled': 0,
            'products_extracted': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

    def setup_driver(self):
        """Initialize Selenium Chrome driver"""
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

    def crawl_page(self, page_num):
        """Crawl a single page"""
        url = f"https://www.onehago.com/mall/?cate_mode=list&cate={self.category_id}&CURRENT_PAGE={page_num}"

        try:
            self.driver.get(url)
            time.sleep(self.delay_min + (self.delay_max - self.delay_min) * random.random())

            # Extract products using correct selector
            products = []
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, ".product")

            seen_ids = set()
            for product in product_elements:
                try:
                    html = product.get_attribute('innerHTML')

                    # Extract product_id from prodWish() function
                    product_id = None
                    if "prodWish('" in html:
                        start = html.find("prodWish('") + 10
                        end = html.find("')", start)
                        product_id = html[start:end]

                    if not product_id or product_id in seen_ids:
                        continue

                    seen_ids.add(product_id)

                    # Extract product name from image alt/title
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

                    # Extract company_no from links
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
                        'category_id': self.category_id,
                        'category_name': CATEGORIES[self.category_id]['name'],
                        'detail_url': f"https://www.onehago.com/mall/?cate_mode=view&no={company_no}&cateno={self.category_id}",
                        'found_on_page': page_num,
                        'crawled_at': datetime.now().isoformat()
                    })
                except Exception as e:
                    continue

            return products

        except Exception as e:
            print(f"  ❌ Error on page {page_num}: {e}")
            self.stats['errors'] += 1
            return []

    def save_progress(self, page_num, products):
        """Save products with file locking"""
        # Load existing products with lock
        all_products = []
        if self.products_file.exists():
            with open(self.products_file, 'r+', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    all_products = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        # Add new products (deduplicate by product_id)
        existing_ids = {p['product_id'] for p in all_products}
        new_products = [p for p in products if p['product_id'] not in existing_ids]
        all_products.extend(new_products)

        # Save with lock
        with open(self.products_file, 'w', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(all_products, f, ensure_ascii=False, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def crawl_range(self):
        """Crawl assigned page range"""
        print("=" * 70)
        print(f"🤖 Onehago Selenium Crawler")
        print(f"📂 Category: {self.category_id} ({CATEGORIES[self.category_id]['name']})")
        print(f"📄 Pages: {self.start_page} - {self.end_page}")
        print(f"⏱️  Delay: {self.delay_min}s - {self.delay_max}s")
        print("=" * 70)

        self.setup_driver()

        # Crawl pages
        for page_num in range(self.start_page, self.end_page + 1):
            try:
                products = self.crawl_page(page_num)

                if not products:
                    print(f"  ⚠️  Page {page_num}: No products")
                    continue

                self.save_progress(page_num, products)
                self.stats['pages_crawled'] += 1
                self.stats['products_extracted'] += len(products)

                print(f"  ✅ Page {page_num}: {len(products)} products")

            except Exception as e:
                print(f"  ❌ Failed page {page_num}: {e}")
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
        print(f"Category: {self.category_id} ({CATEGORIES[self.category_id]['name']})")
        print(f"Pages: {self.stats['pages_crawled']}")
        print(f"Products: {self.stats['products_extracted']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Duration: {duration}")
        print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description='Onehago Selenium Parallel Crawler')
    parser.add_argument('--category', type=int, required=True, choices=[2, 7, 21])
    parser.add_argument('--start-page', type=int, required=True)
    parser.add_argument('--end-page', type=int, required=True)
    parser.add_argument('--min-delay', type=float, default=1.0)
    parser.add_argument('--max-delay', type=float, default=3.0)

    args = parser.parse_args()

    crawler = OnehagoSeleniumCrawler(
        category_id=args.category,
        start_page=args.start_page,
        end_page=args.end_page,
        delay_min=args.min_delay,
        delay_max=args.max_delay
    )

    crawler.crawl_range()

if __name__ == "__main__":
    main()
