#!/usr/bin/env python3
"""
Freemold Universal Product Crawler - ALL Categories

Crawls product listings from freemold.net across ALL 8 main categories.
Based on site analysis: ~53,790 products across 1,793 pages

Categories:
- A001: 프리몰드 (1,588 pages, ~47,640 products)
- A002: OEM/ODM (125 pages, ~3,750 products)
- A003: 패키징/포장재 (57 pages, ~1,710 products)
- A004: 후가공/임가공 (19 pages, ~570 products)
- A006: 원료 (1 page, ~30 products)
- A007: 인증/임상기관 (1 page, ~30 products)
- A008: 금형/기계/시공 (1 page, ~30 products)
- A009: 디자인/마케팅 (1 page, ~30 products)

Total: 1,793 pages, ~53,790 products
Estimated Time: ~3 hours (with 6-second delay per page)
"""

import os
import time
import json
import re
import random
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# User-Agent 로테이션 (차단 회피)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0"
]

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Login credentials
LOGIN_URL = os.getenv('FREEMOLD_BASE_URL', 'https://www.freemold.net')
USERNAME = os.getenv('FREEMOLD_USERNAME')
PASSWORD = os.getenv('FREEMOLD_PASSWORD')

if not USERNAME or not PASSWORD:
    raise ValueError("FREEMOLD_USERNAME and FREEMOLD_PASSWORD must be set in .env file")

# ALL Categories configuration from site analysis
CATEGORIES = {
    'A001': {'name': '프리몰드', 'pages': 1588},
    'A002': {'name': 'OEM/ODM', 'pages': 125},
    'A003': {'name': '패키징/포장재', 'pages': 57},
    'A004': {'name': '후가공/임가공', 'pages': 19},
    'A006': {'name': '원료', 'pages': 1},
    'A007': {'name': '인증/임상기관', 'pages': 1},
    'A008': {'name': '금형/기계/시공', 'pages': 1},
    'A009': {'name': '디자인/마케팅', 'pages': 1}
}

class FreemoldUniversalCrawler:
    """Freemold.net universal product crawler for ALL categories"""

    def __init__(self, headless=True, output_dir='data/freemold/universal'):
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.driver = None
        self.logged_in = False

        # Create output structure
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            'total_pages': 0,
            'total_products': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }

        # Progress tracking
        self.progress_file = self.output_dir / 'crawl_progress_universal.json'
        self.load_progress()

    def load_progress(self):
        """Load progress from file"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                self.progress = json.load(f)
                print(f"📂 Progress loaded: {self.progress}")
        else:
            self.progress = {}

    def save_progress(self, category, page):
        """Save progress to file"""
        self.progress[category] = {
            'last_page': page,
            'updated_at': datetime.now().isoformat()
        }
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def get_resume_page(self, category):
        """Get page number to resume from"""
        if category in self.progress:
            return self.progress[category].get('last_page', 1) + 1
        return 1

    def setup_driver(self):
        """Setup Chrome driver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')

        # Random User-Agent (차단 회피)
        user_agent = random.choice(USER_AGENTS)
        chrome_options.add_argument(f'user-agent={user_agent}')

        self.driver = webdriver.Chrome(options=chrome_options)
        print(f"✅ Chrome driver initialized (headless={self.headless})")
        print(f"🔐 User-Agent: {user_agent[:50]}...")

    def login(self):
        """Login to freemold.net"""
        if self.logged_in:
            return True

        print("\n" + "="*70)
        print("LOGGING IN TO FREEMOLD.NET")
        print("="*70)

        try:
            self.driver.get(LOGIN_URL)
            time.sleep(3)

            # Remove overlay
            self.driver.execute_script("""
                var mask = document.getElementById('divMask');
                if (mask) mask.style.display = 'none';
            """)

            # Click login button
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

            # Submit
            password_input.submit()
            time.sleep(5)

            # Verify
            if "로그아웃" in self.driver.page_source or "Logout" in self.driver.page_source:
                print("✅ Login successful")
                self.logged_in = True
                return True
            else:
                print("❌ Login failed")
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def crawl_category_page(self, category_code, page_num):
        """Crawl a single category page"""
        url = f"https://www.freemold.net/Front/Product/?tp=ma&CatA={category_code}&Page={page_num}"

        try:
            self.driver.get(url)
            # Random delay: 3-8 seconds (차단 회피)
            delay = random.uniform(3.0, 8.0)
            time.sleep(delay)

            html = self.driver.page_source

            # Extract all mIdx and pIdx
            all_params = re.findall(r'(mIdx|pIdx)=(\d+)', html)

            products = []
            seen_products = set()
            current_mIdx = None

            for param_type, param_value in all_params:
                if param_type == 'mIdx':
                    current_mIdx = param_value
                elif param_type == 'pIdx':
                    if param_value not in seen_products:
                        seen_products.add(param_value)
                        products.append({
                            'pIdx': param_value,
                            'mIdx': current_mIdx,
                            'category_code': category_code,
                            'category_name': CATEGORIES[category_code]['name'],
                            'product_url': f"https://www.freemold.net/Front/Product/?tp=vi&pIdx={param_value}",
                            'company_url': f"https://www.freemold.net/Front/Company/?mIdx={current_mIdx}" if current_mIdx else None
                        })

            self.stats['total_pages'] += 1
            self.stats['total_products'] += len(products)

            return products

        except Exception as e:
            print(f"  ❌ Error on page {page_num}: {e}")
            self.stats['errors'] += 1
            return []

    def crawl_category(self, category_code):
        """Crawl all pages of a category"""
        category_info = CATEGORIES[category_code]
        category_name = category_info['name']
        total_pages = category_info['pages']

        # Check resume point
        start_page = self.get_resume_page(category_code)

        if start_page > total_pages:
            print(f"🔄 Resuming {category_code} from page {start_page}")
            print(f"\n✅ Category {category_code} already complete: 0 products\n")
            return []

        print(f"\n{'='*70}")
        print(f"CRAWLING: {category_name}")
        print(f"Category: {category_code}")
        print(f"Pages: {start_page} to {total_pages} (of {total_pages})")
        print(f"{'='*70}\n")

        all_products = []

        for page_num in range(start_page, total_pages + 1):
            print(f"[{page_num}/{total_pages}] Crawling page {page_num}...", end=' ')

            products = self.crawl_category_page(category_code, page_num)

            if products:
                all_products.extend(products)
                print(f"✓ {len(products)} products")
            else:
                print("⚠️ No products")

            # Save progress every 10 pages
            if page_num % 10 == 0:
                self.save_progress(category_code, page_num)

                # Save products so far
                output_file = self.output_dir / f'{category_code}_products_partial.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_products, f, ensure_ascii=False, indent=2)

                print(f"  💾 Checkpoint: {len(all_products)} products saved")

        # Final save for this category
        self.save_progress(category_code, total_pages)

        output_file = self.output_dir / f'{category_code}_products.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Category {category_code} complete: {len(all_products)} products")
        print(f"📁 Saved to: {output_file}\n")

        return all_products

    def crawl_all(self):
        """Crawl all categories"""
        print("\n" + "="*70)
        print("FREEMOLD UNIVERSAL CRAWLER - ALL CATEGORIES")
        print("="*70)
        print(f"Mode: FULL CRAWL")
        print(f"Categories: {len(CATEGORIES)}")
        print(f"Total Pages: {sum(c['pages'] for c in CATEGORIES.values())}")
        print(f"Output: {self.output_dir}")
        print("="*70)

        self.setup_driver()

        if not self.login():
            print("❌ Login failed. Exiting.")
            return

        self.stats['start_time'] = datetime.now()

        all_products = []

        for category_code in CATEGORIES.keys():
            products = self.crawl_category(category_code)
            all_products.extend(products)

        # Merge all products
        merged_file = self.output_dir / 'all_products_merged.json'
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)

        self.stats['end_time'] = datetime.now()
        duration = self.stats['end_time'] - self.stats['start_time']

        print("\n" + "="*70)
        print("CRAWLING SUMMARY")
        print("="*70)
        print(f"Pages Crawled: {self.stats['total_pages']}")
        print(f"Products Extracted: {self.stats['total_products']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Duration: {duration}")
        print(f"\n📁 Merged File: {merged_file}")
        print("="*70)

        self.driver.quit()
        print("\n✅ Browser closed")

def main():
    crawler = FreemoldUniversalCrawler(headless=True)
    crawler.crawl_all()

if __name__ == "__main__":
    main()
