#!/usr/bin/env python3
"""
Freemold Product Detail Crawler - Manual Login Version

Uses Chrome Remote Debugging to connect to an already-logged-in browser.

Usage:
  1. Start Chrome with remote debugging:
     /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
       --remote-debugging-port=9222 \
       --user-data-dir="/tmp/chrome_debug"

  2. Manually log in to freemold.net in that Chrome window

  3. Run this script:
     python3 scripts/freemold_manual_detail_crawler.py --category B001 --limit 10
"""

import json
import time
import random
import requests
import argparse
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class ManualFreemoldCrawler:
    def __init__(self, debug_port=9222, output_dir='data/freemold/product_details_manual', delay=3):
        self.debug_port = debug_port
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.delay = delay

        self.stats = {
            'total_products': 0,
            'successful': 0,
            'failed': 0,
            'images_downloaded': 0,
        }

    def connect_to_chrome(self):
        """Connect to an already-running Chrome instance"""
        print(f"\n🔗 Connecting to Chrome on port {self.debug_port}...")

        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", f"localhost:{self.debug_port}")

        try:
            driver = webdriver.Chrome(options=chrome_options)
            print("✅ Connected to Chrome successfully")
            return driver
        except Exception as e:
            print(f"❌ Failed to connect to Chrome: {e}")
            print(f"\n💡 Make sure Chrome is running with:")
            print(f"   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\")
            print(f"     --remote-debugging-port={self.debug_port} \\")
            print(f'     --user-data-dir="/tmp/chrome_debug"')
            return None

    def verify_login(self, driver):
        """Verify that the browser is logged in"""
        print("\n🔐 Verifying login status...")

        try:
            driver.get('https://www.freemold.net')
            time.sleep(2)

            if "로그아웃" in driver.page_source:
                print("✅ Session is logged in!")
                return True
            else:
                print("❌ Not logged in. Please log in manually in the Chrome window.")
                return False

        except Exception as e:
            print(f"❌ Error checking login: {e}")
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

    def extract_product_detail(self, driver, product_url, product_id, category_code):
        """Extract detailed information from product page"""
        try:
            self.stats['total_products'] += 1

            print(f"  Navigating to product page...")
            driver.get(product_url)
            time.sleep(2)

            # Check for errors
            content = driver.page_source
            if "error occurred on the server" in content.lower():
                print(f"    ❌ Server error")
                self.stats['failed'] += 1
                return None

            if "비회원은 해당페이지를 열람할 수 없습니다" in content:
                print(f"    ❌ Access denied - need login")
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
                og_image = driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']")
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
                        print(f"    💾 Downloaded: {downloaded_path}")

            # Save HTML
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

            driver.save_screenshot(str(screenshot_file))
            detail['screenshot_file'] = str(screenshot_file)

            print(f"    ✅ Saved HTML and screenshot")

            self.stats['successful'] += 1
            return detail

        except Exception as e:
            print(f"    ❌ Extraction error: {e}")
            self.stats['failed'] += 1
            return None

    def crawl_products(self, products_file, category_code, limit=10):
        """Crawl product details from a product list file"""
        print(f"\n{'='*70}")
        print(f"CRAWLING PRODUCT DETAILS: {category_code} (Manual Mode)")
        print(f"{'='*70}")

        # Load product list
        with open(products_file, 'r', encoding='utf-8') as f:
            products = json.load(f)

        print(f"Total products in list: {len(products)}")
        print(f"Will crawl: {limit} products")

        # Connect to Chrome
        driver = self.connect_to_chrome()
        if not driver:
            return []

        # Verify login
        if not self.verify_login(driver):
            print("\n⚠️ Please log in to freemold.net in the Chrome window,")
            print("   then press Enter to continue...")
            input()

            if not self.verify_login(driver):
                print("❌ Still not logged in. Aborting.")
                driver.quit()
                return []

        # Crawl products
        results = []

        try:
            for idx, product in enumerate(products[:limit], 1):
                print(f"\n[{idx}/{limit}] Product {product['pIdx']}:")

                detail = self.extract_product_detail(
                    driver,
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
                delay = random.uniform(self.delay, self.delay + 2)
                time.sleep(delay)

            # Save final results
            self.save_results(results, category_code, temp=False)

        finally:
            # Don't quit the driver - keep Chrome open for manual use
            print("\n💡 Chrome window left open for reuse")

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
        if self.stats['total_products'] > 0:
            print(f"Success rate: {self.stats['successful']/self.stats['total_products']*100:.1f}%")
        print(f"Images downloaded: {self.stats['images_downloaded']}")
        print("="*70)

    def run(self, category_code='B001', limit=10):
        """Run the crawler"""
        products_file = Path(f'data/freemold/crawled_products/{category_code}/{category_code}_products.json')

        if not products_file.exists():
            print(f"❌ Products file not found: {products_file}")
            return

        results = self.crawl_products(products_file, category_code, limit=limit)
        self.print_stats()

        return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Freemold Manual Crawler - Connects to logged-in Chrome',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:

  1. Start Chrome with remote debugging:
     /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\
       --remote-debugging-port=9222 \\
       --user-data-dir="/tmp/chrome_debug"

  2. Log in to freemold.net in that Chrome window

  3. Run this script:
     python3 scripts/freemold_manual_detail_crawler.py --category B001 --limit 10
        """
    )

    parser.add_argument('--category', type=str, default='B001',
                        help='Category code (B001, B002, B003, B004)')
    parser.add_argument('--limit', type=int, default=10,
                        help='Number of products to crawl (default: 10)')
    parser.add_argument('--debug-port', type=int, default=9222,
                        help='Chrome remote debugging port (default: 9222)')
    parser.add_argument('--delay', type=float, default=3.0,
                        help='Delay between requests in seconds (default: 3)')

    args = parser.parse_args()

    crawler = ManualFreemoldCrawler(
        debug_port=args.debug_port,
        output_dir='data/freemold/product_details_manual',
        delay=args.delay
    )

    crawler.run(
        category_code=args.category,
        limit=args.limit
    )
