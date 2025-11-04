#!/usr/bin/env python3
"""
Onehago Range Crawler - Processes specific product index range
Used by smart orchestrator to split large categories
"""

import json
import argparse
import time
import random
import requests
import sys
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import re

sys.stdout = open(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = open(sys.stderr.fileno(), 'w', buffering=1)

class OnehagoRangeCrawler:
    """Crawls a specific range of products within a category"""

    def __init__(self, category_id, start_idx, end_idx, split_id, total_splits,
                 delay_min=0.05, delay_max=0.15):
        self.category_id = category_id
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.split_id = split_id
        self.total_splits = total_splits
        self.delay_min = delay_min
        self.delay_max = delay_max

        # Output directories
        self.output_dir = Path('data/onehago/crawled')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.images_dir = self.output_dir / 'images'
        self.images_dir.mkdir(exist_ok=True)

        self.categories_dir = self.output_dir / 'categories'
        self.categories_dir.mkdir(exist_ok=True)

        # Load valid categories
        self.valid_categories = self.load_valid_categories()

        self.driver = None

        # Stats
        self.stats = {
            'products_processed': 0,
            'details_crawled': 0,
            'images_downloaded': 0,
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

    def setup_driver(self):
        """Setup Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')

        self.driver = webdriver.Chrome(options=chrome_options)

    def collect_product_list(self):
        """Collect ALL product IDs from category (shared work)"""
        cat_info = self.valid_categories.get(str(self.category_id), {})
        max_pages = cat_info.get('pages', 10)

        print(f"📂 Collecting product list for category {self.category_id} ({max_pages} pages)")

        all_products = []
        for page_num in range(1, max_pages + 1):
            try:
                url = f"https://www.onehago.com/mall/?cate_mode=list&cate={self.category_id}&CURRENT_PAGE={page_num}"
                self.driver.get(url)
                time.sleep(self.delay_min + (self.delay_max - self.delay_min) * random.random())

                product_elements = self.driver.find_elements(By.CSS_SELECTOR, ".product")

                if not product_elements:
                    break

                for product in product_elements:
                    try:
                        html = product.get_attribute('innerHTML')

                        # Extract product_id
                        match = re.search(r'prod_cd=(\d+)', html)
                        if match:
                            product_id = match.group(1)

                            # Extract basic info
                            name = "Unknown"
                            name_elem = product.find_elements(By.CSS_SELECTOR, ".prod_name")
                            if name_elem:
                                name = name_elem[0].text.strip()

                            all_products.append({
                                'product_id': product_id,
                                'name': name
                            })
                    except Exception as e:
                        continue

                print(f"  Page {page_num}/{max_pages}: {len(all_products)} products collected")

            except Exception as e:
                print(f"  ⚠️  Page {page_num} error: {e}")
                continue

        return all_products

    def crawl_product_detail(self, product_id):
        """Crawl single product detail page"""
        try:
            url = f"https://www.onehago.com/mall/?mode=view&prod_cd={product_id}"
            self.driver.get(url)
            time.sleep(self.delay_min + (self.delay_max - self.delay_min) * random.random())

            # Extract detailed info
            detail = {'product_id': product_id}

            # Name
            try:
                name_elem = self.driver.find_element(By.CSS_SELECTOR, ".prod_tit")
                detail['detailed_name'] = name_elem.text.strip()
            except:
                detail['detailed_name'] = "Unknown"

            # Specifications table
            specs = {}
            try:
                spec_rows = self.driver.find_elements(By.CSS_SELECTOR, ".spec_table tr")
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
            except:
                pass

            detail['specifications'] = specs

            # Manufacturer info
            try:
                mfr_elem = self.driver.find_element(By.CSS_SELECTOR, ".company_name")
                detail['manufacturer'] = mfr_elem.text.strip()
            except:
                detail['manufacturer'] = specs.get('제조사', '')

            # Contact info
            try:
                phone_elem = self.driver.find_element(By.CSS_SELECTOR, ".company_tel")
                detail['phone'] = phone_elem.text.strip()
            except:
                detail['phone'] = ''

            try:
                email_elem = self.driver.find_element(By.CSS_SELECTOR, ".company_email")
                detail['email'] = email_elem.text.strip()
            except:
                detail['email'] = ''

            # Download image
            try:
                img_elem = self.driver.find_element(By.CSS_SELECTOR, ".prod_img img")
                img_url = img_elem.get_attribute('src')

                if img_url and img_url.startswith('http'):
                    img_path = self.images_dir / f"{product_id}.jpg"

                    response = requests.get(img_url, timeout=10)
                    if response.status_code == 200:
                        with open(img_path, 'wb') as f:
                            f.write(response.content)
                        detail['image_path'] = f"images/{product_id}.jpg"
                        self.stats['images_downloaded'] += 1
            except:
                pass

            detail['detail_crawled'] = True
            self.stats['details_crawled'] += 1

            return detail

        except Exception as e:
            self.stats['errors'] += 1
            return None

    def run(self):
        """Main execution"""
        print("=" * 70)
        print(f"🔧 Range Crawler: Category {self.category_id}")
        print(f"📦 Part {self.split_id + 1}/{self.total_splits}")
        print(f"📊 Product range: {self.start_idx} - {self.end_idx}")
        print(f"⏱️  Delay: {self.delay_min}-{self.delay_max}s")
        print("=" * 70)

        # Setup browser
        self.setup_driver()

        # Step 1: Collect full product list
        all_products = self.collect_product_list()

        if not all_products:
            print("\n⚠️  No products found")
            self.driver.quit()
            return

        total_products = len(all_products)
        print(f"\n✅ Collected {total_products:,} total products")

        # Step 2: Process only our assigned range
        actual_end = min(self.end_idx, total_products)
        my_products = all_products[self.start_idx:actual_end]

        print(f"📋 Processing products {self.start_idx}-{actual_end} ({len(my_products)} products)")
        print()

        detailed_products = []

        for idx, prod_info in enumerate(my_products, 1):
            product_id = prod_info['product_id']

            print(f"  [{idx}/{len(my_products)}] Product {product_id}...", end=' ')

            detail = self.crawl_product_detail(product_id)

            if detail:
                detailed_products.append(detail)
                print("✅")
            else:
                print("❌")

            self.stats['products_processed'] += 1

        # Step 3: Save partial result
        if self.total_splits > 1:
            output_file = self.categories_dir / f'category_{self.category_id}_part{self.split_id}.json'
        else:
            output_file = self.categories_dir / f'category_{self.category_id}.json'

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_products, f, ensure_ascii=False, indent=2)

        # Cleanup
        self.driver.quit()

        # Summary
        duration = datetime.now() - self.stats['start_time']
        print("\n" + "=" * 70)
        print("✅ RANGE COMPLETE")
        print("=" * 70)
        print(f"Products processed: {self.stats['products_processed']}")
        print(f"Details crawled: {self.stats['details_crawled']}")
        print(f"Images downloaded: {self.stats['images_downloaded']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Duration: {duration}")
        print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description='Onehago Range Crawler')
    parser.add_argument('--category', type=int, required=True)
    parser.add_argument('--start-index', type=int, required=True)
    parser.add_argument('--end-index', type=int, required=True)
    parser.add_argument('--split-id', type=int, required=True)
    parser.add_argument('--total-splits', type=int, required=True)
    parser.add_argument('--min-delay', type=float, default=0.05)
    parser.add_argument('--max-delay', type=float, default=0.15)

    args = parser.parse_args()

    crawler = OnehagoRangeCrawler(
        category_id=args.category,
        start_idx=args.start_index,
        end_idx=args.end_index,
        split_id=args.split_id,
        total_splits=args.total_splits,
        delay_min=args.min_delay,
        delay_max=args.max_delay
    )

    crawler.run()

if __name__ == "__main__":
    main()
