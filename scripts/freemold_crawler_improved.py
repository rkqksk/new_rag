#!/usr/bin/env python3
"""
Improved Freemold Crawler with Anti-Ban Features

Improvements:
1. Random delays between requests (2-5 seconds)
2. Realistic User-Agent rotation
3. Retry logic for failed requests
4. Session refresh every N pages
5. Exponential backoff on errors
6. Polite crawling with respect to server load
"""

import os
import json
import time
import random
import argparse
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv('FREEMOLD_USERNAME')
PASSWORD = os.getenv('FREEMOLD_PASSWORD')

# Realistic User-Agents (rotate to avoid detection)
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

CATEGORIES = {
    'B001': '다이렉트 브로우 (Direct Blow)',
    'B002': '인젝션 브로우 (Injection Blow)',
    'B003': '헤비 브로우 (Heavy Blow)',
    'B004': '다층 브로우 (Multi-layer Blow)',
}

class ImprovedFreemoldCrawler:
    def __init__(self, headless=True, output_dir='data/freemold/crawled_products'):
        self.driver = None
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Anti-ban settings
        self.min_delay = 2.0  # Minimum delay between requests (seconds)
        self.max_delay = 5.0  # Maximum delay between requests (seconds)
        self.session_refresh_interval = 100  # Refresh session every N pages
        self.max_retries = 3  # Max retries per page
        self.backoff_factor = 2  # Exponential backoff multiplier

        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'session_refreshes': 0,
        }

    def setup_driver(self):
        """Initialize Chrome driver with anti-detection features"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless')

        # Anti-detection measures
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Random User-Agent
        user_agent = random.choice(USER_AGENTS)
        chrome_options.add_argument(f'user-agent={user_agent}')

        # Window size
        chrome_options.add_argument('--window-size=1920,1080')

        self.driver = webdriver.Chrome(options=chrome_options)

        # Remove webdriver property
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })

        print(f"✅ Chrome driver initialized (headless={self.headless})")
        print(f"   User-Agent: {user_agent[:50]}...")

    def random_delay(self, min_extra=0, max_extra=0):
        """Add random delay to mimic human behavior"""
        base_delay = random.uniform(self.min_delay, self.max_delay)
        extra_delay = random.uniform(min_extra, max_extra) if max_extra > 0 else 0
        total_delay = base_delay + extra_delay
        time.sleep(total_delay)
        return total_delay

    def login(self):
        """Login to freemold.net"""
        print("\n" + "="*70)
        print("LOGGING IN TO FREEMOLD.NET")
        print("="*70)

        try:
            self.driver.get('https://www.freemold.net')
            self.random_delay()

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
            time.sleep(0.5)  # Human-like typing delay
            password_input.clear()
            password_input.send_keys(PASSWORD)

            password_input.submit()
            time.sleep(5)

            # Verify login
            if "로그아웃" in self.driver.page_source or "Logout" in self.driver.page_source:
                print("✅ Login successful - session established")
                return True
            else:
                print("❌ Login failed - could not verify session")
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def refresh_session(self):
        """Refresh session to avoid timeout"""
        print("\n🔄 Refreshing session...")
        try:
            self.driver.get('https://www.freemold.net')
            self.random_delay()

            # Verify still logged in
            if "로그아웃" in self.driver.page_source:
                print("✅ Session still active")
                self.stats['session_refreshes'] += 1
                return True
            else:
                print("⚠️ Session expired - attempting re-login")
                return self.login()
        except Exception as e:
            print(f"❌ Session refresh failed: {e}")
            return False

    def crawl_category_page(self, category_code, page_num, max_retries=None):
        """Crawl a single category page with retry logic"""
        if max_retries is None:
            max_retries = self.max_retries

        url = f"https://www.freemold.net/Front/Product/?mcate1={category_code}&page={page_num}"

        for attempt in range(max_retries):
            try:
                self.stats['total_requests'] += 1

                # Random delay before request
                delay = self.random_delay(min_extra=0.5, max_extra=1.5)

                self.driver.get(url)
                time.sleep(2)  # Wait for page load

                # Extract products
                products = []
                product_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='Product/?tp=vi&pIdx=']")

                for link in product_links:
                    try:
                        product_url = link.get_attribute('href')
                        if 'pIdx=' in product_url:
                            # Extract pIdx
                            pIdx = product_url.split('pIdx=')[1].split('&')[0]

                            # Try to find company link
                            try:
                                parent = link.find_element(By.XPATH, './ancestor::div[contains(@class, "product") or contains(@class, "item")]')
                                company_link = parent.find_element(By.CSS_SELECTOR, "a[href*='Company/?mIdx=']")
                                company_url = company_link.get_attribute('href')
                                mIdx = company_url.split('mIdx=')[1].split('&')[0] if 'mIdx=' in company_url else 'unknown'
                            except:
                                mIdx = 'unknown'

                            product = {
                                'pIdx': pIdx,
                                'mIdx': mIdx,
                                'category_code': category_code,
                                'category_name': CATEGORIES[category_code],
                                'product_url': product_url,
                                'company_url': company_url if mIdx != 'unknown' else '',
                                'crawled_at': datetime.now().isoformat(),
                            }
                            products.append(product)
                    except Exception as e:
                        continue

                self.stats['successful_requests'] += 1
                return products

            except Exception as e:
                self.stats['failed_requests'] += 1

                if attempt < max_retries - 1:
                    # Exponential backoff
                    backoff_delay = self.backoff_factor ** attempt
                    print(f"  ⚠️ Retry {attempt + 1}/{max_retries} after {backoff_delay}s...")
                    time.sleep(backoff_delay)
                else:
                    print(f"  ❌ Failed after {max_retries} attempts: {e}")
                    return []

        return []

    def crawl_category(self, category_code, start_page=1, end_page=None):
        """Crawl all pages of a category with anti-ban features"""
        print(f"\n{'='*70}")
        print(f"CRAWLING: {CATEGORIES[category_code]}")
        print(f"Category: {category_code}")
        print(f"{'='*70}")

        # Load or create output file
        output_file = self.output_dir / category_code / f"{category_code}_products.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing data
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                all_products = json.load(f)
            print(f"📂 Loaded {len(all_products)} existing products")
        else:
            all_products = []

        # Determine page range
        if end_page is None:
            # Fetch total pages (simplified - you might want to detect this)
            end_page = 1000  # Set a reasonable upper limit

        print(f"Pages: {start_page} to {end_page}")

        page_num = start_page
        consecutive_empty_pages = 0
        max_empty_pages = 5  # Stop after 5 consecutive empty pages

        while page_num <= end_page:
            # Session refresh check
            if (page_num - start_page) % self.session_refresh_interval == 0 and page_num > start_page:
                self.refresh_session()

            print(f"  Page {page_num}: ", end='', flush=True)

            products = self.crawl_category_page(category_code, page_num)

            if len(products) == 0:
                consecutive_empty_pages += 1
                print(f"0 products (empty {consecutive_empty_pages}/{max_empty_pages})")

                if consecutive_empty_pages >= max_empty_pages:
                    print(f"\n⚠️ Reached {max_empty_pages} consecutive empty pages - stopping")
                    break
            else:
                consecutive_empty_pages = 0  # Reset counter
                print(f"{len(products)} products extracted")
                all_products.extend(products)

            # Save progress every 10 pages
            if page_num % 10 == 0:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_products, f, ensure_ascii=False, indent=2)
                print(f"  💾 Progress saved (page {page_num})")

            page_num += 1

        # Final save
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Category {category_code} complete: {len(all_products)} total products")
        print(f"   Output: {output_file}")

        return all_products

    def print_stats(self):
        """Print crawling statistics"""
        print("\n" + "="*70)
        print("CRAWLING STATISTICS")
        print("="*70)
        print(f"Total requests: {self.stats['total_requests']}")
        print(f"Successful: {self.stats['successful_requests']}")
        print(f"Failed: {self.stats['failed_requests']}")
        print(f"Success rate: {self.stats['successful_requests']/self.stats['total_requests']*100:.1f}%")
        print(f"Session refreshes: {self.stats['session_refreshes']}")
        print("="*70)

    def run(self, categories=None, start_page=1):
        """Run the crawler"""
        if categories is None:
            categories = list(CATEGORIES.keys())

        try:
            self.setup_driver()

            if not self.login():
                print("❌ Failed to login - aborting")
                return

            for category_code in categories:
                if category_code not in CATEGORIES:
                    print(f"⚠️ Unknown category: {category_code}")
                    continue

                self.crawl_category(category_code, start_page=start_page)

            self.print_stats()

        finally:
            if self.driver:
                self.driver.quit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Improved Freemold Crawler with Anti-Ban')
    parser.add_argument('--categories', nargs='+', choices=list(CATEGORIES.keys()),
                        help='Categories to crawl (default: all)')
    parser.add_argument('--start-page', type=int, default=1,
                        help='Starting page number (default: 1)')
    parser.add_argument('--visible', action='store_true',
                        help='Run in visible mode (not headless)')

    args = parser.parse_args()

    crawler = ImprovedFreemoldCrawler(
        headless=not args.visible,
        output_dir='data/freemold/crawled_products'
    )

    crawler.run(
        categories=args.categories,
        start_page=args.start_page
    )
