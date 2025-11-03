#!/usr/bin/env python3
"""
Freemold Parallel Crawler - Category Range Support

Usage:
    python3 freemold_parallel_crawler.py --start-idx 0 --end-idx 19

Supports parallel execution by crawling specific category indices.
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Credentials
LOGIN_URL = os.getenv('FREEMOLD_BASE_URL', 'https://www.freemold.net')
USERNAME = os.getenv('FREEMOLD_USERNAME')
PASSWORD = os.getenv('FREEMOLD_PASSWORD')

if not USERNAME or not PASSWORD:
    raise ValueError("FREEMOLD_USERNAME and FREEMOLD_PASSWORD must be set in .env")

# All 153 subcategories (A001001-A001153 pattern)
def get_all_categories():
    """Generate all category codes"""
    categories = []
    for i in range(1, 154):  # 1-153
        cat_code = f"A001{i:03d}"
        categories.append(cat_code)
    return categories

ALL_CATEGORIES = get_all_categories()

class FreemoldParallelCrawler:
    """Parallel-ready Freemold crawler with category range support"""

    def __init__(self, start_idx, end_idx, delay_min=0.5, delay_max=2.0, headless=True):
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.headless = headless

        self.output_dir = Path('data/freemold/universal')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.progress_file = self.output_dir / 'crawl_progress_universal.json'
        self.driver = None
        self.logged_in = False

        # Statistics
        self.stats = {
            'categories_processed': 0,
            'products_extracted': 0,
            'pages_crawled': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'end_time': None
        }

    def setup_driver(self):
        """Initialize Selenium driver"""
        options = Options()
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def login(self):
        """Login to Freemold"""
        if self.logged_in:
            return True

        try:
            print("🔐 Logging in...")
            self.driver.get(LOGIN_URL)
            time.sleep(2)

            # Find and fill login form
            username_field = self.driver.find_element(By.NAME, 'mb_id')
            password_field = self.driver.find_element(By.NAME, 'mb_password')

            username_field.send_keys(USERNAME)
            password_field.send_keys(PASSWORD)

            # Submit
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()

            time.sleep(3)

            self.logged_in = True
            print("✅ Login successful")
            return True

        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False

    def crawl_category(self, category_code):
        """Crawl a single category"""
        products = []
        page = 1

        print(f"\n📂 Category: {category_code}")

        while True:
            try:
                url = f"{LOGIN_URL}/shop/list.php?ca_id={category_code}&page={page}"
                self.driver.get(url)
                time.sleep(self.delay_min + (self.delay_max - self.delay_min) * __import__('random').random())

                # Extract products from current page
                product_elements = self.driver.find_elements(By.CSS_SELECTOR, '.item_wrap')

                if not product_elements:
                    print(f"   ✅ No more products on page {page}")
                    break

                page_products = 0
                for elem in product_elements:
                    try:
                        product = {
                            'category': category_code,
                            'name': elem.find_element(By.CSS_SELECTOR, '.item_name').text.strip(),
                            'price': elem.find_element(By.CSS_SELECTOR, '.item_price').text.strip() if elem.find_elements(By.CSS_SELECTOR, '.item_price') else 'N/A',
                            'image': elem.find_element(By.CSS_SELECTOR, 'img').get_attribute('src') if elem.find_elements(By.CSS_SELECTOR, 'img') else None,
                            'link': elem.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') if elem.find_elements(By.CSS_SELECTOR, 'a') else None,
                            'crawled_at': datetime.now().isoformat()
                        }
                        products.append(product)
                        page_products += 1
                    except Exception as e:
                        self.stats['errors'] += 1

                self.stats['pages_crawled'] += 1
                print(f"   Page {page}: {page_products} products")

                # Check for next page
                next_buttons = self.driver.find_elements(By.CSS_SELECTOR, '.pagination .next')
                if not next_buttons or 'disabled' in next_buttons[0].get_attribute('class'):
                    break

                page += 1

            except Exception as e:
                print(f"   ❌ Error on page {page}: {e}")
                self.stats['errors'] += 1
                break

        return products

    def save_progress(self, category_code, products):
        """Save progress to shared file with locking"""
        import fcntl

        # Read current progress with file lock
        progress = {}
        if self.progress_file.exists():
            with open(self.progress_file, 'r+') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    progress = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        # Update progress
        progress[category_code] = [p['name'] for p in products]

        # Write back with lock
        with open(self.progress_file, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(progress, f, ensure_ascii=False, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        # Also save detailed products
        category_file = self.output_dir / f'{category_code}_products.json'
        with open(category_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

    def crawl_range(self):
        """Crawl assigned category range"""
        print("=" * 70)
        print(f"🤖 Freemold Parallel Crawler")
        print(f"📊 Category range: {self.start_idx} - {self.end_idx}")
        print(f"⏱️  Delay: {self.delay_min}s - {self.delay_max}s")
        print("=" * 70)

        self.setup_driver()

        if not self.login():
            print("❌ Login failed, exiting")
            return

        # Crawl assigned categories
        for idx in range(self.start_idx, self.end_idx):
            if idx >= len(ALL_CATEGORIES):
                break

            category_code = ALL_CATEGORIES[idx]

            try:
                products = self.crawl_category(category_code)
                self.save_progress(category_code, products)

                self.stats['categories_processed'] += 1
                self.stats['products_extracted'] += len(products)

                print(f"✅ {category_code}: {len(products)} products saved")

            except Exception as e:
                print(f"❌ Failed to crawl {category_code}: {e}")
                self.stats['errors'] += 1

        # Final stats
        self.stats['end_time'] = datetime.now()
        duration = self.stats['end_time'] - self.stats['start_time']

        print("\n" + "=" * 70)
        print("CRAWLER SUMMARY")
        print("=" * 70)
        print(f"Categories: {self.stats['categories_processed']}")
        print(f"Products: {self.stats['products_extracted']}")
        print(f"Pages: {self.stats['pages_crawled']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Duration: {duration}")
        print("=" * 70)

        if self.driver:
            self.driver.quit()

def main():
    parser = argparse.ArgumentParser(description='Freemold Parallel Crawler')
    parser.add_argument('--start-idx', type=int, required=True, help='Start category index')
    parser.add_argument('--end-idx', type=int, required=True, help='End category index')
    parser.add_argument('--min-delay', type=float, default=0.5, help='Min delay between requests')
    parser.add_argument('--max-delay', type=float, default=2.0, help='Max delay between requests')
    parser.add_argument('--headless', action='store_true', default=True, help='Run headless')

    args = parser.parse_args()

    crawler = FreemoldParallelCrawler(
        start_idx=args.start_idx,
        end_idx=args.end_idx,
        delay_min=args.min_delay,
        delay_max=args.max_delay,
        headless=args.headless
    )

    crawler.crawl_range()

if __name__ == "__main__":
    main()
