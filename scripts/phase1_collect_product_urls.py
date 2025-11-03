#!/usr/bin/env python3
"""
Phase 1: Collect Product URLs from Onehago
Simple, fast URL harvesting without full content extraction

Strategy:
1. Iterate through categories and pages
2. Extract only: product_id, item_code, product_url, image_url, name
3. Save to JSONL for Phase 2 processing
"""

import json
import time
import random
import re
import argparse
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class ProductURLCollector:
    """Lightweight collector for product URLs only"""

    def __init__(self, delay_min=0.1, delay_max=0.3):
        self.delay_min = delay_min
        self.delay_max = delay_max

        # Output
        self.output_dir = Path('data/onehago/crawled')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.urls_file = self.output_dir / 'product_urls.jsonl'

        # Load category info
        self.categories = self.load_categories()

        self.driver = None

        # Stats
        self.stats = {
            'products_found': 0,
            'pages_processed': 0,
            'categories_complete': 0,
            'start_time': datetime.now()
        }

    def load_categories(self):
        """Load valid categories"""
        cat_file = Path('data/onehago/valid_categories.json')
        if cat_file.exists():
            with open(cat_file) as f:
                cats = json.load(f)
                return {cat['id']: cat for cat in cats}
        return {}

    def setup_driver(self):
        """Setup Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-images')  # Faster loading
        chrome_options.add_argument('user-agent=Mozilla/5.0')

        self.driver = webdriver.Chrome(options=chrome_options)

    def extract_product_info(self, product_element):
        """Extract product info from single .product element"""
        try:
            html = product_element.get_attribute('outerHTML')

            # Extract product_id (pid) from prodWish('XXXXX')
            pid_match = re.search(r'prodWish\([\'"](\d+)[\'"]\)', html)
            if not pid_match:
                return None

            product_id = pid_match.group(1)

            # Extract item code (no) from URL like pid=57529&no=504
            no_match = re.search(r'[&?]no=(\d+)', html)
            item_code = no_match.group(1) if no_match else None

            # Extract product name from urlset or overlay-info
            name_match = re.search(r'urlset\([\'"]?\d+[\'"]?,[\'"]?\d+[\'"]?,[\'"]?([^\'",]+)[\'"]?', html)
            if not name_match:
                name_match = re.search(r'item\s*:\s*([^<\n]+)', html)

            product_name = name_match.group(1).strip() if name_match else "Unknown"

            # Extract image URL
            img_match = re.search(r'<img[^>]+src=[\'"]([^\'"]+)[\'"]', html)
            image_url = img_match.group(1) if img_match else None

            # Fix relative URL
            if image_url and image_url.startswith('/'):
                image_url = f"https://www.onehago.com{image_url}"

            # Extract company name
            company_match = re.search(r'<strong class="com_name">([^<]+)</strong>', html)
            company = company_match.group(1).strip() if company_match else ""

            # Build product URL
            if item_code:
                product_url = f"https://www.onehago.com/mall/?cate_mode=view&pid={product_id}&no={item_code}"
            else:
                product_url = f"https://www.onehago.com/mall/?mode=view&prod_cd={product_id}"

            return {
                'product_id': product_id,
                'item_code': item_code,
                'product_url': product_url,
                'product_name': product_name,
                'company': company,
                'image_url': image_url,
                'extracted_at': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"    ⚠️  Extraction error: {e}")
            return None

    def collect_category(self, category_id):
        """Collect all products from a category"""
        cat_info = self.categories.get(str(category_id), {})
        max_pages = cat_info.get('pages', 10)
        cat_name = cat_info.get('name', f'Category {category_id}')

        print(f"\n{'='*70}")
        print(f"📂 Category {category_id}: {cat_name}")
        print(f"   Expected pages: {max_pages}")
        print(f"{'='*70}")

        category_products = []

        for page_num in range(1, max_pages + 1):
            try:
                url = f"https://www.onehago.com/mall/?cate_mode=list&cate={category_id}&CURRENT_PAGE={page_num}"
                self.driver.get(url)

                # Random delay
                time.sleep(self.delay_min + (self.delay_max - self.delay_min) * random.random())

                # Find all product elements
                product_elements = self.driver.find_elements(By.CSS_SELECTOR, ".box.product")

                if not product_elements:
                    print(f"  Page {page_num:3d}/{max_pages}: No products, stopping")
                    break

                page_products = 0
                for element in product_elements:
                    product_info = self.extract_product_info(element)
                    if product_info:
                        product_info['category_id'] = category_id
                        product_info['category_name'] = cat_name
                        product_info['page'] = page_num
                        category_products.append(product_info)
                        page_products += 1

                self.stats['pages_processed'] += 1
                print(f"  Page {page_num:3d}/{max_pages}: {page_products:3d} products  "
                      f"(Total: {len(category_products):4d})")

                # Early stop if no products found
                if page_products == 0:
                    break

            except Exception as e:
                print(f"  Page {page_num:3d}: Error - {e}")
                continue

        # Save category products
        if category_products:
            with open(self.urls_file, 'a', encoding='utf-8') as f:
                for product in category_products:
                    f.write(json.dumps(product, ensure_ascii=False) + '\n')

            self.stats['products_found'] += len(category_products)
            self.stats['categories_complete'] += 1

            print(f"\n✅ Category {category_id} complete: {len(category_products)} products")
        else:
            print(f"\n⚠️  Category {category_id}: No products found")

    def run(self, categories=None):
        """Main collection loop"""
        print("="*70)
        print("📋 Phase 1: Product URL Collection")
        print("="*70)

        self.setup_driver()

        try:
            # Determine which categories to process
            if categories:
                target_cats = categories
            else:
                target_cats = sorted([int(k) for k in self.categories.keys()])

            print(f"\n🎯 Target categories: {target_cats}")
            print(f"📁 Output file: {self.urls_file}")

            # Collect each category
            for cat_id in target_cats:
                self.collect_category(cat_id)

            # Final stats
            duration = datetime.now() - self.stats['start_time']
            print(f"\n{'='*70}")
            print(f"🎉 Phase 1 Complete!")
            print(f"{'='*70}")
            print(f"📊 Statistics:")
            print(f"   Categories processed: {self.stats['categories_complete']}")
            print(f"   Total products found: {self.stats['products_found']:,}")
            print(f"   Pages processed: {self.stats['pages_processed']:,}")
            print(f"   Duration: {duration}")
            print(f"   Output: {self.urls_file}")

        finally:
            if self.driver:
                self.driver.quit()

def main():
    parser = argparse.ArgumentParser(description='Phase 1: Collect product URLs')
    parser.add_argument('--categories', type=int, nargs='+',
                       help='Specific categories to process (default: all)')
    parser.add_argument('--min-delay', type=float, default=0.1,
                       help='Minimum delay between requests (default: 0.1)')
    parser.add_argument('--max-delay', type=float, default=0.3,
                       help='Maximum delay between requests (default: 0.3)')

    args = parser.parse_args()

    collector = ProductURLCollector(
        delay_min=args.min_delay,
        delay_max=args.max_delay
    )

    collector.run(categories=args.categories)

if __name__ == "__main__":
    main()
