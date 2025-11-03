#!/usr/bin/env python3
"""
Onehago Page-Based Range Crawler
Crawls specific PAGE range (not product range) - Much more efficient!
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

class OnehagoPageCrawler:
    """Crawls specific page range within a category"""

    def __init__(self, category_id, start_page, end_page, split_id, total_splits,
                 delay_min=0.05, delay_max=0.15):
        self.category_id = category_id
        self.start_page = start_page
        self.end_page = end_page
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

        self.driver = None

        # Stats
        self.stats = {
            'pages_crawled': 0,
            'products_found': 0,
            'details_crawled': 0,
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
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')

        self.driver = webdriver.Chrome(options=chrome_options)

    def crawl_product_list_pages(self):
        """Crawl only assigned page range"""
        print(f"📂 Collecting pages {self.start_page}-{self.end_page} for category {self.category_id}")

        all_products = []

        for page_num in range(self.start_page, self.end_page + 1):
            try:
                url = f"https://www.onehago.com/mall/?cate_mode=list&cate={self.category_id}&CURRENT_PAGE={page_num}"
                self.driver.get(url)
                time.sleep(self.delay_min + (self.delay_max - self.delay_min) * random.random())

                product_elements = self.driver.find_elements(By.CSS_SELECTOR, ".product")

                if not product_elements:
                    print(f"  ⚠️  Page {page_num}: No products")
                    break

                page_count = 0
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
                            page_count += 1
                    except Exception as e:
                        continue

                print(f"  ✅ Page {page_num}: {page_count} products")
                self.stats['pages_crawled'] += 1
                self.stats['products_found'] += page_count

            except Exception as e:
                print(f"  ❌ Page {page_num} error: {str(e)[:100]}")
                self.stats['errors'] += 1
                continue

        return all_products

    def crawl_product_detail(self, product_id):
        """Crawl single product detail page"""
        try:
            url = f"https://www.onehago.com/mall/?mode=view&prod_cd={product_id}"
            self.driver.get(url)
            time.sleep(self.delay_min + (self.delay_max - self.delay_min) * random.random())

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

            # Manufacturer
            try:
                mfr_elem = self.driver.find_element(By.CSS_SELECTOR, ".company_name")
                detail['manufacturer'] = mfr_elem.text.strip()
            except:
                detail['manufacturer'] = specs.get('제조사', '')

            # Contact
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
        print(f"📄 Page-Based Crawler: Category {self.category_id}")
        print(f"📦 Part {self.split_id + 1}/{self.total_splits}")
        print(f"📊 Page range: {self.start_page} - {self.end_page}")
        print(f"⏱️  Delay: {self.delay_min}-{self.delay_max}s")
        print("=" * 70)
        print()

        # Setup browser
        self.setup_driver()

        # Step 1: Collect products from assigned pages only
        products = self.crawl_product_list_pages()

        if not products:
            print("\n⚠️  No products found")
            self.driver.quit()
            return

        print(f"\n✅ Collected {len(products):,} products from pages {self.start_page}-{self.end_page}")
        print(f"📋 Processing details...\n")

        # Step 2: Crawl details for all collected products
        detailed_products = []

        for idx, prod_info in enumerate(products, 1):
            product_id = prod_info['product_id']

            if idx % 10 == 0:
                print(f"  [{idx}/{len(products)}] ...", flush=True)

            detail = self.crawl_product_detail(product_id)

            if detail:
                detailed_products.append(detail)

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
        print("✅ PART COMPLETE")
        print("=" * 70)
        print(f"Pages crawled: {self.stats['pages_crawled']}")
        print(f"Products found: {self.stats['products_found']}")
        print(f"Details crawled: {self.stats['details_crawled']}")
        print(f"Images downloaded: {self.stats['images_downloaded']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Duration: {duration}")
        print(f"Saved to: {output_file.name}")
        print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description='Onehago Page-Based Crawler')
    parser.add_argument('--category', type=int, required=True)
    parser.add_argument('--start-page', type=int, required=True)
    parser.add_argument('--end-page', type=int, required=True)
    parser.add_argument('--split-id', type=int, required=True)
    parser.add_argument('--total-splits', type=int, required=True)
    parser.add_argument('--min-delay', type=float, default=0.05)
    parser.add_argument('--max-delay', type=float, default=0.15)

    args = parser.parse_args()

    crawler = OnehagoPageCrawler(
        category_id=args.category,
        start_page=args.start_page,
        end_page=args.end_page,
        split_id=args.split_id,
        total_splits=args.total_splits,
        delay_min=args.min_delay,
        delay_max=args.max_delay
    )

    crawler.run()

if __name__ == "__main__":
    main()
