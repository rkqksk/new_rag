#!/usr/bin/env python3
"""
Freemold Product Detail Crawler using Playwright

Playwright advantages over Selenium:
- Better anti-bot detection avoidance
- Native async support
- More reliable login automation
- Better handling of dynamic content
"""

import os
import json
import time
import asyncio
import requests
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv('FREEMOLD_USERNAME')
PASSWORD = os.getenv('FREEMOLD_PASSWORD')

class PlaywrightFreemoldCrawler:
    def __init__(self, headless=False, output_dir='data/freemold/product_details_pw'):
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.stats = {
            'total_products': 0,
            'successful': 0,
            'failed': 0,
            'images_downloaded': 0,
        }

    def login(self, page):
        """Login to freemold.net using Playwright"""
        print("\n" + "="*70)
        print("LOGGING IN WITH PLAYWRIGHT")
        print("="*70)

        try:
            # Navigate to homepage
            page.goto('https://www.freemold.net', timeout=30000)
            page.wait_for_load_state('networkidle')

            # Remove overlay if exists
            page.evaluate("""
                var mask = document.getElementById('divMask');
                if (mask) mask.style.display = 'none';
            """)

            # Trigger login modal
            print("  Triggering login modal...")
            page.evaluate("""
                var loginBtn = document.querySelector('#divTopLoginArea > span:nth-child(1)');
                if (loginBtn) {
                    loginBtn.click();
                } else if (typeof loginLayer === 'function') {
                    loginLayer();
                }
            """)

            time.sleep(2)

            # Wait for login form
            print("  Waiting for login form...")
            page.wait_for_selector("input[type='text']", timeout=10000)

            # Fill credentials
            print(f"  Entering username: {USERNAME[:3]}***")
            page.fill("input[type='text']", USERNAME)
            time.sleep(0.5)

            print("  Entering password...")
            page.fill("input[type='password']", PASSWORD)
            time.sleep(0.5)

            # Submit form
            print("  Submitting login form...")
            page.press("input[type='password']", "Enter")

            # Wait for navigation
            page.wait_for_load_state('networkidle', timeout=10000)
            time.sleep(3)

            # Verify login
            content = page.content()
            if "로그아웃" in content:
                print("✅ Login successful!")
                return True
            else:
                print("❌ Login failed - logout button not found")
                # Save page for debugging
                debug_file = self.output_dir / 'login_failed.html'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  Debug HTML saved to: {debug_file}")
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            # Save screenshot for debugging
            try:
                screenshot_file = self.output_dir / 'login_error.png'
                page.screenshot(path=str(screenshot_file))
                print(f"  Screenshot saved to: {screenshot_file}")
            except:
                pass
            return False

    def download_image(self, img_url, save_dir, product_id):
        """Download product image"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext = img_url.split('.')[-1].split('?')[0]
            filename = f"{product_id}_{timestamp}.{ext}"
            filepath = save_dir / filename

            response = requests.get(img_url, timeout=10)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                self.stats['images_downloaded'] += 1
                return str(filepath)
            return None

        except Exception as e:
            print(f"    ⚠️ Image download failed: {e}")
            return None

    def extract_product_detail(self, page, product_url, product_id, category_code):
        """Extract detailed information from product page"""
        try:
            self.stats['total_products'] += 1

            print(f"  Navigating to product page...")
            page.goto(product_url, timeout=30000)
            page.wait_for_load_state('networkidle')
            time.sleep(2)

            # Check for errors
            content = page.content()
            if "error occurred on the server" in content.lower():
                print(f"    ❌ Server error")
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
            }

            # Extract images from meta tags
            try:
                og_image = page.query_selector("meta[property='og:image']")
                if og_image:
                    img_url = og_image.get_attribute('content')
                    if img_url:
                        detail['images'].append(img_url)
                        print(f"    📸 OG Image: {img_url}")
            except:
                pass

            # Extract all product images
            import re
            product_images = re.findall(
                r'https?://[^"\'<>]+/data/Product/[^"\'<>]+\.(?:jpg|jpeg|png|gif)',
                content,
                re.IGNORECASE
            )

            for img_url in set(product_images):
                if img_url not in detail['images']:
                    detail['images'].append(img_url)
                    print(f"    📸 Image: {img_url}")

            # Download images
            if detail['images']:
                image_dir = self.output_dir / category_code / 'images' / product_id
                image_dir.mkdir(parents=True, exist_ok=True)

                for img_url in detail['images']:
                    downloaded_path = self.download_image(img_url, image_dir, product_id)
                    if downloaded_path:
                        detail['image_files'].append(downloaded_path)

            # Save HTML for later analysis
            html_dir = self.output_dir / category_code / 'html'
            html_dir.mkdir(parents=True, exist_ok=True)
            html_file = html_dir / f"{product_id}.html"

            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(content)

            detail['html_file'] = str(html_file)

            # Save screenshot
            screenshot_dir = self.output_dir / category_code / 'screenshots'
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            screenshot_file = screenshot_dir / f"{product_id}.png"

            page.screenshot(path=str(screenshot_file), full_page=True)
            detail['screenshot_file'] = str(screenshot_file)

            self.stats['successful'] += 1
            return detail

        except Exception as e:
            print(f"    ❌ Extraction error: {e}")
            self.stats['failed'] += 1
            return None

    def crawl_products(self, products_file, category_code, limit=5):
        """Crawl product details from a product list file"""
        print(f"\n{'='*70}")
        print(f"CRAWLING PRODUCT DETAILS: {category_code}")
        print(f"{'='*70}")

        # Load product list
        with open(products_file, 'r', encoding='utf-8') as f:
            products = json.load(f)

        print(f"Total products in list: {len(products)}")
        print(f"Will crawl: {limit} products")

        with sync_playwright() as p:
            # Launch browser
            print("\n🌐 Launching Playwright browser...")
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                ]
            )

            # Create context with realistic settings
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='ko-KR',
            )

            # Remove webdriver property
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """)

            page = context.new_page()

            try:
                # Login
                if not self.login(page):
                    print("❌ Failed to login - aborting")
                    return []

                # Crawl products
                results = []

                for idx, product in enumerate(products[:limit], 1):
                    print(f"\n[{idx}/{limit}] Product {product['pIdx']}:")

                    detail = self.extract_product_detail(
                        page,
                        product['product_url'],
                        product['pIdx'],
                        category_code
                    )

                    if detail:
                        results.append(detail)

                        # Save progress every 5 products
                        if idx % 5 == 0:
                            self.save_results(results, category_code, temp=True)
                            print(f"  💾 Progress saved ({idx} products)")

                    # Random delay (3-6 seconds)
                    import random
                    delay = random.uniform(3, 6)
                    time.sleep(delay)

                # Save final results
                self.save_results(results, category_code, temp=False)

                return results

            finally:
                browser.close()

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
        if self.stats['total_products'] > 0:
            print(f"Success rate: {self.stats['successful']/self.stats['total_products']*100:.1f}%")
        print(f"Images downloaded: {self.stats['images_downloaded']}")
        print("="*70)

    def run(self, category_code='B001', limit=5):
        """Run the crawler"""
        products_file = Path(f'data/freemold/crawled_products/{category_code}/{category_code}_products.json')

        if not products_file.exists():
            print(f"❌ Products file not found: {products_file}")
            return

        results = self.crawl_products(products_file, category_code, limit=limit)
        self.print_stats()

        return results

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Freemold Playwright Crawler')
    parser.add_argument('--category', type=str, default='B001',
                        help='Category code (B001, B002, B003, B004)')
    parser.add_argument('--limit', type=int, default=5,
                        help='Number of products to crawl (default: 5)')
    parser.add_argument('--headless', action='store_true',
                        help='Run in headless mode')

    args = parser.parse_args()

    crawler = PlaywrightFreemoldCrawler(
        headless=args.headless,
        output_dir='data/freemold/product_details_pw'
    )

    crawler.run(
        category_code=args.category,
        limit=args.limit
    )
