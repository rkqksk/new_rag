#!/usr/bin/env python3
"""
Phase 2: Extract Product Details + Download Images
Uses product URLs from Phase 1 to extract full details and images

Strategy:
1. Read product URLs from Phase 1 output
2. Visit each product page with Selenium
3. Extract full specifications, manufacturer, contact info
4. Download product images (all available images)
5. Save detailed JSON + images
"""

import json
import time
import random
import re
import argparse
import requests
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ProductDetailExtractor:
    """Extract full product details and download images"""

    def __init__(self, delay_min=0.2, delay_max=0.5, max_products=None):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.max_products = max_products

        # Directories
        self.output_dir = Path('data/onehago/crawled')
        self.images_dir = self.output_dir / 'images'
        self.details_dir = self.output_dir / 'details'
        self.logs_dir = self.output_dir / 'logs'

        # Ensure directories exist
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.details_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Input file
        self.urls_file = self.output_dir / 'product_urls.jsonl'

        self.driver = None

        # Stats
        self.stats = {
            'products_processed': 0,
            'details_extracted': 0,
            'images_downloaded': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

    def setup_driver(self):
        """Setup Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('user-agent=Mozilla/5.0')

        self.driver = webdriver.Chrome(options=chrome_options)

    def download_image(self, image_url, product_id, image_index=0):
        """Download single image"""
        try:
            # Fix relative URLs
            if image_url.startswith('/'):
                image_url = f"https://www.onehago.com{image_url}"

            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                # Determine extension
                ext = Path(image_url).suffix or '.jpg'

                # Save with product_id + index
                filename = f"{product_id}_{image_index}{ext}"
                filepath = self.images_dir / filename

                filepath.write_bytes(response.content)

                return {
                    'index': image_index,
                    'url': image_url,
                    'local_path': str(filepath.relative_to(self.output_dir)),
                    'size_bytes': len(response.content),
                    'downloaded': True
                }
            else:
                return {'url': image_url, 'error': f'HTTP {response.status_code}', 'downloaded': False}

        except Exception as e:
            return {'url': image_url, 'error': str(e), 'downloaded': False}

    def extract_product_detail(self, product_info):
        """Extract full details from product page"""
        try:
            product_url = product_info['product_url']
            product_id = product_info['product_id']

            print(f"   📄 {product_id}: {product_info.get('product_name', 'Unknown')[:40]}...")

            self.driver.get(product_url)
            time.sleep(self.delay_min + (self.delay_max - self.delay_min) * random.random())

            detail = {
                'product_id': product_id,
                'source_url': product_url,
                'extracted_at': datetime.now().isoformat()
            }

            # Copy basic info from Phase 1
            detail['product_name'] = product_info.get('product_name', '')
            detail['company'] = product_info.get('company', '')
            detail['category_id'] = product_info.get('category_id', '')

            # Extract detailed product name/title
            try:
                # Try multiple selectors
                title_selectors = [
                    ".prod_tit",
                    ".product_title",
                    "h1.title",
                    ".prod_name",
                    ".product-name",
                    "div[class*='title'] strong"
                ]

                for selector in title_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].text.strip():
                        detail['detailed_name'] = elements[0].text.strip()
                        break
            except:
                pass

            # Extract specifications table
            specs = {}
            try:
                # Find table rows
                spec_rows = self.driver.find_elements(By.CSS_SELECTOR, "table tr")

                for row in spec_rows:
                    try:
                        ths = row.find_elements(By.TAG_NAME, "th")
                        tds = row.find_elements(By.TAG_NAME, "td")

                        for th, td in zip(ths, tds):
                            key = th.text.strip()
                            value = td.text.strip()
                            if key and value:
                                specs[key] = value
                    except:
                        continue

                detail['specifications'] = specs
            except:
                detail['specifications'] = {}

            # Extract manufacturer/company info
            try:
                company_selectors = [".company_name", ".manufacturer", ".maker", ".com_name"]
                for selector in company_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].text.strip():
                        detail['manufacturer'] = elements[0].text.strip()
                        break
            except:
                detail['manufacturer'] = detail.get('company', '')

            # Extract contact info
            try:
                phone_elements = self.driver.find_elements(By.CSS_SELECTOR, ".company_tel, .phone, .tel")
                if phone_elements:
                    detail['phone'] = phone_elements[0].text.strip()
            except:
                detail['phone'] = specs.get('PHONE', specs.get('TEL', ''))

            try:
                email_elements = self.driver.find_elements(By.CSS_SELECTOR, ".email, .company_email")
                if email_elements:
                    detail['email'] = email_elements[0].text.strip()
            except:
                detail['email'] = specs.get('E MAIL', specs.get('EMAIL', ''))

            # Extract ALL images on page
            images_data = []
            try:
                img_elements = self.driver.find_elements(By.TAG_NAME, "img")

                # Filter product images (exclude UI icons, logos, etc)
                product_images = []
                for img in img_elements:
                    src = img.get_attribute('src')
                    if src and any(x in src.lower() for x in ['product', 'upload', 'thumb', '/image']):
                        if src not in [p for p in product_images]:  # Deduplicate
                            product_images.append(src)

                # Download images
                for idx, img_url in enumerate(product_images[:5]):  # Max 5 images per product
                    img_data = self.download_image(img_url, product_id, idx)
                    images_data.append(img_data)
                    if img_data.get('downloaded'):
                        self.stats['images_downloaded'] += 1

                detail['images'] = images_data
                detail['image_count'] = len([img for img in images_data if img.get('downloaded')])

            except Exception as e:
                print(f"      ⚠️  Image extraction error: {e}")
                detail['images'] = []

            # Save detail JSON
            detail_file = self.details_dir / f"{product_id}.json"
            with open(detail_file, 'w', encoding='utf-8') as f:
                json.dump(detail, f, ensure_ascii=False, indent=2)

            self.stats['details_extracted'] += 1
            print(f"      ✅ Details extracted, {detail.get('image_count', 0)} images downloaded")

            return detail

        except Exception as e:
            print(f"      ❌ Error: {e}")
            self.stats['errors'] += 1
            return None

    def process_products(self, limit=None):
        """Process products from Phase 1 output"""
        if not self.urls_file.exists():
            print(f"❌ Phase 1 output not found: {self.urls_file}")
            print(f"   Run Phase 1 first: python3 scripts/phase1_collect_product_urls.py")
            return

        # Read products
        products = []
        with open(self.urls_file, 'r', encoding='utf-8') as f:
            for line in f:
                products.append(json.loads(line))

        if limit:
            products = products[:limit]

        total = len(products)
        print(f"\n📋 Processing {total} products from Phase 1")

        # Process each product
        for idx, product_info in enumerate(products, 1):
            print(f"\n[{idx}/{total}] Processing product {product_info['product_id']}...")

            self.extract_product_detail(product_info)
            self.stats['products_processed'] += 1

            # Progress update every 10 products
            if idx % 10 == 0:
                self.print_progress(idx, total)

    def print_progress(self, current, total):
        """Print progress statistics"""
        elapsed = datetime.now() - self.stats['start_time']
        rate = current / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0

        print(f"\n{'─'*70}")
        print(f"📊 Progress: {current}/{total} ({current/total*100:.1f}%)")
        print(f"   Details extracted: {self.stats['details_extracted']}")
        print(f"   Images downloaded: {self.stats['images_downloaded']}")
        print(f"   Errors: {self.stats['errors']}")
        print(f"   Rate: {rate:.1f} products/sec")
        print(f"   Elapsed: {elapsed}")
        print(f"{'─'*70}")

    def run(self, test_mode=False):
        """Main extraction loop"""
        print("="*70)
        print("📝 Phase 2: Product Detail Extraction + Image Download")
        print("="*70)

        self.setup_driver()

        try:
            if test_mode:
                print("\n🧪 TEST MODE: Processing first 5 products only")
                self.process_products(limit=5)
            else:
                self.process_products(limit=self.max_products)

            # Final stats
            duration = datetime.now() - self.stats['start_time']
            print(f"\n{'='*70}")
            print(f"🎉 Phase 2 Complete!")
            print(f"{'='*70}")
            print(f"📊 Final Statistics:")
            print(f"   Products processed: {self.stats['products_processed']:,}")
            print(f"   Details extracted: {self.stats['details_extracted']:,}")
            print(f"   Images downloaded: {self.stats['images_downloaded']:,}")
            print(f"   Errors: {self.stats['errors']}")
            print(f"   Duration: {duration}")
            print(f"   Output: {self.details_dir}")
            print(f"   Images: {self.images_dir}")

        finally:
            if self.driver:
                self.driver.quit()

def main():
    parser = argparse.ArgumentParser(description='Phase 2: Extract product details + download images')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: process only first 5 products')
    parser.add_argument('--max-products', type=int,
                       help='Maximum number of products to process')
    parser.add_argument('--min-delay', type=float, default=0.2,
                       help='Minimum delay between requests (default: 0.2)')
    parser.add_argument('--max-delay', type=float, default=0.5,
                       help='Maximum delay between requests (default: 0.5)')

    args = parser.parse_args()

    extractor = ProductDetailExtractor(
        delay_min=args.min_delay,
        delay_max=args.max_delay,
        max_products=args.max_products
    )

    extractor.run(test_mode=args.test)

if __name__ == "__main__":
    main()
