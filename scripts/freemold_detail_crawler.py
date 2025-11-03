#!/usr/bin/env python3
"""
Freemold Product Detail Crawler

Crawls individual product detail pages to collect:
- Product images (high resolution)
- Detailed specifications
- Product descriptions
- Company information
"""

import os
import json
import time
import random
import requests
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

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

class FreemoldDetailCrawler:
    def __init__(self, headless=True, output_dir='data/freemold/product_details'):
        self.driver = None
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Anti-ban settings
        self.min_delay = 3.0
        self.max_delay = 6.0
        self.session_refresh_interval = 50

        self.stats = {
            'total_products': 0,
            'successful': 0,
            'failed': 0,
            'images_downloaded': 0,
        }

    def setup_driver(self):
        """Setup Chrome driver with anti-detection"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        user_agent = random.choice(USER_AGENTS)
        chrome_options.add_argument(f'user-agent={user_agent}')
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

        print(f"✅ Chrome driver initialized")

    def random_delay(self):
        """Random delay to mimic human"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

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
            time.sleep(0.5)
            password_input.clear()
            password_input.send_keys(PASSWORD)

            password_input.submit()
            time.sleep(5)

            # Verify login
            if "로그아웃" in self.driver.page_source:
                print("✅ Login successful")
                return True
            else:
                print("❌ Login failed")
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def download_image(self, img_url, save_dir, product_id):
        """Download product image"""
        try:
            # Create unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext = img_url.split('.')[-1].split('?')[0]
            filename = f"{product_id}_{timestamp}.{ext}"
            filepath = save_dir / filename

            # Download
            response = requests.get(img_url, timeout=10)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                self.stats['images_downloaded'] += 1
                return str(filepath)
            else:
                return None

        except Exception as e:
            print(f"    ⚠️ Failed to download image: {e}")
            return None

    def extract_product_detail(self, product_url, product_id, category_code):
        """Extract detailed information from product page"""
        try:
            self.stats['total_products'] += 1

            # Navigate to product page
            self.driver.get(product_url)
            time.sleep(3)

            # Check for errors
            if "error occurred on the server" in self.driver.page_source.lower():
                print(f"    ❌ Server error for product {product_id}")
                self.stats['failed'] += 1
                return None

            detail = {
                'product_id': product_id,
                'category_code': category_code,
                'url': product_url,
                'crawled_at': datetime.now().isoformat(),
                'images': [],
                'image_files': [],
                'specifications': {},
                'description': '',
                'raw_html_size': len(self.driver.page_source),
            }

            # Extract images from meta tags (usually high quality)
            try:
                og_image = self.driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']")
                img_url = og_image.get_attribute('content')
                if img_url:
                    detail['images'].append(img_url)
                    print(f"    📸 OG Image: {img_url}")
            except:
                pass

            # Extract images from page content
            try:
                # Look for product images in /data/Product/ directory
                import re
                html = self.driver.page_source
                product_images = re.findall(
                    r'https?://[^"\'<>]+/data/Product/[^"\'<>]+\.(?:jpg|jpeg|png|gif)',
                    html,
                    re.IGNORECASE
                )

                for img_url in set(product_images):
                    if img_url not in detail['images']:
                        detail['images'].append(img_url)
                        print(f"    📸 Image: {img_url}")

            except Exception as e:
                print(f"    ⚠️ Image extraction error: {e}")

            # Download images
            if detail['images']:
                image_dir = self.output_dir / category_code / 'images' / product_id
                image_dir.mkdir(parents=True, exist_ok=True)

                for img_url in detail['images']:
                    downloaded_path = self.download_image(img_url, image_dir, product_id)
                    if downloaded_path:
                        detail['image_files'].append(downloaded_path)

            # Extract specifications (will implement after seeing actual page structure)
            # For now, save raw HTML for analysis
            html_dir = self.output_dir / category_code / 'html'
            html_dir.mkdir(parents=True, exist_ok=True)
            html_file = html_dir / f"{product_id}.html"

            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)

            detail['html_file'] = str(html_file)

            self.stats['successful'] += 1
            return detail

        except Exception as e:
            print(f"    ❌ Extraction error: {e}")
            self.stats['failed'] += 1
            return None

    def crawl_products_from_list(self, products_file, category_code, limit=10):
        """Crawl product details from a product list file"""
        print(f"\n{'='*70}")
        print(f"CRAWLING PRODUCT DETAILS: {category_code}")
        print(f"{'='*70}")

        # Load product list
        with open(products_file, 'r', encoding='utf-8') as f:
            products = json.load(f)

        print(f"Total products in list: {len(products)}")
        print(f"Will crawl: {limit} products")

        results = []

        for idx, product in enumerate(products[:limit], 1):
            print(f"\n[{idx}/{limit}] Product {product['pIdx']}:")

            detail = self.extract_product_detail(
                product['product_url'],
                product['pIdx'],
                category_code
            )

            if detail:
                results.append(detail)

                # Save progress every 10 products
                if idx % 10 == 0:
                    self.save_results(results, category_code, temp=True)
                    print(f"  💾 Progress saved ({idx} products)")

            # Random delay
            self.random_delay()

            # Session refresh
            if idx % self.session_refresh_interval == 0 and idx < limit:
                print("\n🔄 Refreshing session...")
                self.driver.get('https://www.freemold.net')
                time.sleep(3)

        # Save final results
        self.save_results(results, category_code, temp=False)

        return results

    def save_results(self, results, category_code, temp=False):
        """Save crawled results to JSON"""
        suffix = '_temp' if temp else ''
        output_file = self.output_dir / category_code / f"{category_code}_details{suffix}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        if not temp:
            print(f"\n✅ Results saved to: {output_file}")

    def print_stats(self):
        """Print crawling statistics"""
        print("\n" + "="*70)
        print("CRAWLING STATISTICS")
        print("="*70)
        print(f"Total products attempted: {self.stats['total_products']}")
        print(f"Successful: {self.stats['successful']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"Success rate: {self.stats['successful']/max(self.stats['total_products'],1)*100:.1f}%")
        print(f"Images downloaded: {self.stats['images_downloaded']}")
        print("="*70)

    def run(self, category_code='B001', limit=10):
        """Run the detail crawler"""
        products_file = Path(f'data/freemold/crawled_products/{category_code}/{category_code}_products.json')

        if not products_file.exists():
            print(f"❌ Products file not found: {products_file}")
            return

        try:
            self.setup_driver()

            if not self.login():
                print("❌ Failed to login - aborting")
                return

            results = self.crawl_products_from_list(
                products_file,
                category_code,
                limit=limit
            )

            self.print_stats()

        finally:
            if self.driver:
                self.driver.quit()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Freemold Product Detail Crawler')
    parser.add_argument('--category', type=str, default='B001',
                        help='Category code (B001, B002, B003, B004)')
    parser.add_argument('--limit', type=int, default=10,
                        help='Number of products to crawl (default: 10)')
    parser.add_argument('--visible', action='store_true',
                        help='Run in visible mode (not headless)')

    args = parser.parse_args()

    crawler = FreemoldDetailCrawler(
        headless=not args.visible,
        output_dir='data/freemold/product_details'
    )

    crawler.run(
        category_code=args.category,
        limit=args.limit
    )
