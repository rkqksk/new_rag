#!/usr/bin/env python3
"""
Freemold Product Crawler - Category-Based Approach

Crawls product listings from freemold.net across 4 bottle categories.
Company profile pages are not accessible, so we extract company IDs (mIdx)
from category pages along with product IDs (pIdx).

Strategy:
1. Login to freemold.net
2. Iterate through all category pages (B001-B004)
3. Extract products with both mIdx (company ID) and pIdx (product ID)
4. Save to structured JSON files
5. Post-process: filter by mIdx for company-specific data

Total Products: ~37,260 across 1,242 pages
Estimated Time: ~2 hours (with 3-second delay per page)
"""

import os
import time
import json
import re
import csv
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Login credentials from environment
LOGIN_URL = os.getenv('FREEMOLD_BASE_URL', 'https://www.freemold.net')
USERNAME = os.getenv('FREEMOLD_USERNAME')
PASSWORD = os.getenv('FREEMOLD_PASSWORD')

if not USERNAME or not PASSWORD:
    raise ValueError("FREEMOLD_USERNAME and FREEMOLD_PASSWORD must be set in .env file")

# Category configuration
CATEGORIES = {
    'B001': {'name': '다이렉트 브로우 (Direct Blow)', 'pages': 857},
    'B002': {'name': '인젝션 브로우 (Injection Blow)', 'pages': 168},
    'B003': {'name': '헤비 브로우 (Heavy Blow)', 'pages': 177},
    'B004': {'name': '다층 브로우 (Multi-layer Blow)', 'pages': 40}
}

class FreemoldCrawler:
    """Freemold.net product crawler with session management and error handling"""

    def __init__(self, headless=True, output_dir='data/freemold'):
        """
        Initialize crawler

        Args:
            headless: Run browser in headless mode
            output_dir: Output directory for crawled data
        """
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.driver = None
        self.logged_in = False

        # Create output structure
        self.crawled_dir = self.output_dir / 'crawled_products'
        self.crawled_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            'total_pages': 0,
            'total_products': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }

        # Progress tracking
        self.progress_file = self.output_dir / 'crawl_progress.json'
        self.load_progress()

    def setup_driver(self):
        """Setup Chrome driver with proper options"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')

        self.driver = webdriver.Chrome(options=chrome_options)
        print(f"✅ Chrome driver initialized (headless={self.headless})")

    def login(self):
        """Login to freemold.net with session management"""
        if self.logged_in:
            return True

        print("\n" + "="*70)
        print("LOGGING IN TO FREEMOLD.NET")
        print("="*70)

        try:
            self.driver.get(LOGIN_URL)
            time.sleep(3)

            # Remove overlay that blocks clicks
            self.driver.execute_script("""
                var mask = document.getElementById('divMask');
                if (mask) mask.style.display = 'none';
            """)

            # Click login button using JavaScript
            self.driver.execute_script("""
                var loginBtn = document.querySelector('#divTopLoginArea > span:nth-child(1)');
                if (loginBtn) {
                    loginBtn.click();
                } else if (typeof loginLayer === 'function') {
                    loginLayer();
                }
            """)

            time.sleep(2)

            # Enter credentials
            wait = WebDriverWait(self.driver, 10)
            username_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")

            username_input.clear()
            username_input.send_keys(USERNAME)
            password_input.clear()
            password_input.send_keys(PASSWORD)

            # Submit login
            password_input.submit()
            time.sleep(5)

            # Verify login success
            if "로그아웃" in self.driver.page_source or "Logout" in self.driver.page_source:
                print("✅ Login successful - session established")
                self.logged_in = True
                return True
            else:
                print("❌ Login failed - could not verify session")
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def crawl_category_page(self, category_code, page_num):
        """
        Crawl a single category page

        Args:
            category_code: Category code (B001-B004)
            page_num: Page number

        Returns:
            List of products with mIdx and pIdx
        """
        url = f"https://www.freemold.net/Front/Product/?tp=ma&CatA=A001&CatB={category_code}&Page={page_num}"

        try:
            self.driver.get(url)
            time.sleep(3)  # Polite delay

            html = self.driver.page_source

            # Extract all mIdx and pIdx values in order
            # Pattern: mIdx=X, pIdx=Y, pIdx=Y (duplicate), mIdx=Z, pIdx=W, pIdx=W...
            all_params = re.findall(r'(mIdx|pIdx)=(\d+)', html)

            # Build products by pairing mIdx with pIdx
            products = []
            seen_products = set()
            current_mIdx = None

            for param_type, param_value in all_params:
                if param_type == 'mIdx':
                    current_mIdx = param_value
                elif param_type == 'pIdx':
                    # Only add unique pIdx (skip duplicates)
                    if param_value not in seen_products:
                        seen_products.add(param_value)
                        products.append({
                            'pIdx': param_value,
                            'mIdx': current_mIdx,
                            'category_code': category_code,
                            'category_name': CATEGORIES[category_code]['name'],
                            'product_url': f'https://www.freemold.net/Front/Product/?tp=vi&pIdx={param_value}',
                            'company_url': f'https://www.freemold.net/Front/Company/?mIdx={current_mIdx}' if current_mIdx else None,
                            'crawled_at': datetime.now().isoformat()
                        })

            self.stats['total_pages'] += 1
            self.stats['total_products'] += len(products)

            print(f"  Page {page_num}: {len(products)} products extracted")

            return products

        except Exception as e:
            print(f"  ❌ Error on page {page_num}: {e}")
            self.stats['errors'] += 1
            return []

    def crawl_category(self, category_code, start_page=1, end_page=None):
        """
        Crawl all pages in a category

        Args:
            category_code: Category code (B001-B004)
            start_page: Starting page number
            end_page: Ending page number (None = all pages)
        """
        category_info = CATEGORIES[category_code]
        max_pages = category_info['pages']

        if end_page is None:
            end_page = max_pages
        else:
            end_page = min(end_page, max_pages)

        print("\n" + "="*70)
        print(f"CRAWLING: {category_info['name']}")
        print(f"Category: {category_code}")
        print(f"Pages: {start_page} to {end_page} (of {max_pages})")
        print("="*70)

        all_products = []

        for page_num in range(start_page, end_page + 1):
            products = self.crawl_category_page(category_code, page_num)
            all_products.extend(products)

            # Save progress every 10 pages
            if page_num % 10 == 0:
                self.save_category_data(category_code, all_products)
                self.save_progress(category_code, page_num)
                print(f"  💾 Progress saved (page {page_num})")

        # Final save
        self.save_category_data(category_code, all_products)
        self.save_progress(category_code, end_page)

        print(f"\n✅ Category {category_code} complete: {len(all_products)} products")

        return all_products

    def save_category_data(self, category_code, products):
        """Save category data to JSON and CSV"""
        category_dir = self.crawled_dir / category_code
        category_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON
        json_file = category_dir / f'{category_code}_products.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

        # Save CSV
        if products:
            csv_file = category_dir / f'{category_code}_products.csv'
            with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=products[0].keys())
                writer.writeheader()
                writer.writerows(products)

    def load_progress(self):
        """Load crawling progress"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                self.progress = json.load(f)
        else:
            self.progress = {}

    def save_progress(self, category_code, last_page):
        """Save crawling progress"""
        self.progress[category_code] = {
            'last_page': last_page,
            'updated_at': datetime.now().isoformat()
        }

        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)

    def crawl_all(self, test_mode=False):
        """
        Crawl all categories

        Args:
            test_mode: If True, only crawl first 5 pages of each category
        """
        self.stats['start_time'] = datetime.now().isoformat()

        print("\n" + "="*70)
        print("FREEMOLD CRAWLER - CATEGORY-BASED APPROACH")
        print("="*70)
        print(f"Mode: {'TEST (5 pages per category)' if test_mode else 'FULL CRAWL'}")
        print(f"Categories: {len(CATEGORIES)}")
        print(f"Total Pages: {sum(c['pages'] for c in CATEGORIES.values())}")
        print(f"Output: {self.crawled_dir}")
        print("="*70)

        # Setup
        self.setup_driver()

        try:
            # Login
            if not self.login():
                print("❌ Login failed - aborting")
                return

            # Crawl each category
            for category_code in CATEGORIES.keys():
                if test_mode:
                    self.crawl_category(category_code, start_page=1, end_page=5)
                else:
                    # Resume from last page if interrupted
                    start_page = 1
                    if category_code in self.progress:
                        start_page = self.progress[category_code]['last_page'] + 1
                        print(f"\n🔄 Resuming {category_code} from page {start_page}")

                    self.crawl_category(category_code, start_page=start_page)

            # Summary
            self.stats['end_time'] = datetime.now().isoformat()
            self.print_summary()

        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted by user")
            self.print_summary()
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()
                print("\n✅ Browser closed")

    def print_summary(self):
        """Print crawling summary"""
        print("\n" + "="*70)
        print("CRAWLING SUMMARY")
        print("="*70)
        print(f"Pages Crawled: {self.stats['total_pages']}")
        print(f"Products Extracted: {self.stats['total_products']}")
        print(f"Errors: {self.stats['errors']}")

        if self.stats['start_time'] and self.stats['end_time']:
            start = datetime.fromisoformat(self.stats['start_time'])
            end = datetime.fromisoformat(self.stats['end_time'])
            duration = end - start
            print(f"Duration: {duration}")

        print(f"\n📁 Output Directory: {self.crawled_dir}")
        print("="*70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Freemold Product Crawler')
    parser.add_argument('--test', action='store_true', help='Test mode (5 pages per category)')
    parser.add_argument('--category', type=str, choices=list(CATEGORIES.keys()), help='Crawl specific category')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode')
    parser.add_argument('--visible', action='store_true', help='Show browser window')

    args = parser.parse_args()

    headless = args.headless and not args.visible

    crawler = FreemoldCrawler(headless=headless)

    if args.category:
        # Crawl specific category
        crawler.setup_driver()
        try:
            if crawler.login():
                if args.test:
                    crawler.crawl_category(args.category, start_page=1, end_page=5)
                else:
                    crawler.crawl_category(args.category)
            crawler.print_summary()
        finally:
            if crawler.driver:
                crawler.driver.quit()
    else:
        # Crawl all categories
        crawler.crawl_all(test_mode=args.test)


if __name__ == "__main__":
    main()
