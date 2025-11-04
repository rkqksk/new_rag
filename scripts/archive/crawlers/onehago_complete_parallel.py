#!/usr/bin/env python3
"""
Onehago Complete Parallel Crawler with Details & Images

Properly fixed:
- Separate JSON files per category (no shared file corruption)
- Full detail page crawling (specs, manufacturer, contact)
- Image downloading (all product photos)
- Progress tracking per category

Usage:
    python3 onehago_complete_parallel.py --categories 2,7,39
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

# Force unbuffered output
sys.stdout = open(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = open(sys.stderr.fileno(), 'w', buffering=1)

class OnehagoCompleteCrawler:
    """Complete crawler with details and images"""

    def __init__(self, category_ids, delay_min=0.3, delay_max=0.8):
        self.category_ids = category_ids
        self.delay_min = delay_min
        self.delay_max = delay_max

        # Output directories
        self.output_dir = Path('data/onehago/crawled')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.images_dir = self.output_dir / 'images'
        self.images_dir.mkdir(exist_ok=True)

        self.categories_dir = self.output_dir / 'categories'
        self.categories_dir.mkdir(exist_ok=True)

        self.progress_file = self.output_dir / 'crawl_progress.json'

        # Load valid categories metadata
        self.valid_categories = self.load_valid_categories()

        self.driver = None

        # Statistics
        self.stats = {
            'categories_crawled': 0,
            'pages_crawled': 0,
            'products_found': 0,
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

    def is_category_completed(self, category_id):
        """Check if category already completed"""
        category_file = self.categories_dir / f'category_{category_id}.json'
        return category_file.exists()

    def mark_category_completed(self, category_id):
        """Update progress file"""
        progress = {'completed_categories': [], 'last_updated': None}

        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)

        if 'completed_categories' not in progress:
            progress['completed_categories'] = []

        if str(category_id) not in progress['completed_categories']:
            progress['completed_categories'].append(str(category_id))

        progress['last_category'] = str(category_id)
        progress['last_updated'] = datetime.now().isoformat()

        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)

    def setup_driver(self):
        """Initialize Selenium"""
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def download_image(self, img_url, product_id):
        """Download product image"""
        try:
            if not img_url or not img_url.startswith('http'):
                return None

            response = requests.get(img_url, timeout=10)
            if response.status_code == 200:
                # Get extension from URL
                ext = 'jpg'
                if '.png' in img_url.lower():
                    ext = 'png'
                elif '.jpeg' in img_url.lower() or '.jpg' in img_url.lower():
                    ext = 'jpg'

                img_path = self.images_dir / f"{product_id}.{ext}"
                with open(img_path, 'wb') as f:
                    f.write(response.content)

                return str(img_path.relative_to(self.output_dir))
        except Exception as e:
            print(f"      ⚠️  Image download failed: {e}")
        return None

    def crawl_product_detail(self, product):
        """Crawl product detail page"""
        try:
            detail_url = product.get('detail_url')
            if not detail_url:
                return product

            self.driver.get(detail_url)
            time.sleep(1)

            # Detailed product name
            try:
                name_elem = self.driver.find_element(By.CSS_SELECTOR, "h2, .product-name, .product_name")
                if name_elem:
                    product['detailed_name'] = name_elem.text.strip()
            except:
                pass

            # High-quality image
            try:
                img_elem = self.driver.find_element(By.CSS_SELECTOR, "img[src*='productImages']")
                if img_elem:
                    full_img_url = img_elem.get_attribute("src")
                    if full_img_url:
                        product['full_image_url'] = full_img_url
                        img_path = self.download_image(full_img_url, product['product_id'])
                        if img_path:
                            product['image_path'] = img_path
                            self.stats['images_downloaded'] += 1
            except:
                pass

            # Product specifications (dl/dt/dd structure)
            try:
                spec_data = {}
                dl_elements = self.driver.find_elements(By.CSS_SELECTOR, "dl")

                for dl in dl_elements:
                    try:
                        dt_elem = dl.find_element(By.CSS_SELECTOR, "dt")
                        dd_elem = dl.find_element(By.CSS_SELECTOR, "dd")

                        if dt_elem and dd_elem:
                            key = dt_elem.text.strip()
                            value = dd_elem.text.strip()

                            if key and value and len(key) < 50:
                                spec_data[key] = value
                    except:
                        pass

                if spec_data:
                    product['specifications'] = spec_data
            except:
                pass

            # Manufacturer
            try:
                company_dt = self.driver.find_element(By.XPATH, "//dt[contains(text(), '제조사')]")
                if company_dt:
                    company_dd = company_dt.find_element(By.XPATH, "following-sibling::dd[1]")
                    if company_dd:
                        product['manufacturer'] = company_dd.text.strip().split('\n')[0].strip()
            except:
                pass

            # Contact info
            try:
                phone_dt = self.driver.find_element(By.XPATH, "//dt[contains(text(), 'PHONE')]")
                if phone_dt:
                    phone_dd = phone_dt.find_element(By.XPATH, "following-sibling::dd[1]")
                    if phone_dd:
                        product['phone'] = phone_dd.text.strip()
            except:
                pass

            try:
                email_dt = self.driver.find_element(By.XPATH, "//dt[contains(text(), 'MAIL') or contains(text(), 'EMAIL')]")
                if email_dt:
                    email_dd = email_dt.find_element(By.XPATH, "following-sibling::dd[1]")
                    if email_dd:
                        product['email'] = email_dd.text.strip()
            except:
                pass

            # Additional images (gallery)
            try:
                gallery_imgs = self.driver.find_elements(By.CSS_SELECTOR, ".product-images img, .gallery img")
                additional_images = []
                for idx, img in enumerate(gallery_imgs[:5]):  # Max 5 additional images
                    img_url = img.get_attribute("src")
                    if img_url and img_url.startswith('http'):
                        img_path = self.download_image(img_url, f"{product['product_id']}_extra_{idx}")
                        if img_path:
                            additional_images.append(img_path)

                if additional_images:
                    product['additional_images'] = additional_images
            except:
                pass

            product['detail_crawled'] = True
            product['detail_crawled_at'] = datetime.now().isoformat()
            self.stats['details_crawled'] += 1

        except Exception as e:
            print(f"      ❌ Detail crawl failed: {e}")
            product['detail_error'] = str(e)

        return product

    def crawl_category_list(self, category_id):
        """Crawl category product list"""
        cat_info = self.valid_categories.get(str(category_id), {})
        max_pages = cat_info.get('pages', 10)

        print(f"\n📂 Category {category_id}: {max_pages} pages")

        products = []
        for page_num in range(1, max_pages + 1):
            try:
                url = f"https://www.onehago.com/mall/?cate_mode=list&cate={category_id}&CURRENT_PAGE={page_num}"
                self.driver.get(url)
                time.sleep(self.delay_min + (self.delay_max - self.delay_min) * random.random())

                # Extract products
                product_elements = self.driver.find_elements(By.CSS_SELECTOR, ".product")

                if not product_elements:
                    print(f"  ⚠️  Page {page_num}: No products")
                    break

                seen_ids = set()
                page_products = []

                for product in product_elements:
                    try:
                        html = product.get_attribute('innerHTML')

                        # Extract product_id
                        product_id = None
                        if "prodWish('" in html:
                            start = html.find("prodWish('") + 10
                            end = html.find("')", start)
                            product_id = html[start:end]

                        if not product_id or product_id in seen_ids:
                            continue

                        seen_ids.add(product_id)

                        # Extract basic info
                        product_name = ''
                        try:
                            img = product.find_element(By.TAG_NAME, "img")
                            img_alt = img.get_attribute("alt") or ""
                            img_title = img.get_attribute("title") or ""
                            if img_alt and "새창열기" not in img_alt and len(img_alt) > 3:
                                product_name = img_alt.strip()
                            elif img_title and len(img_title) > 3:
                                product_name = img_title.strip()
                        except:
                            pass

                        # Extract company_no
                        company_no = None
                        try:
                            links = product.find_elements(By.CSS_SELECTOR, "a[href*='cate_mode=view']")
                            for link in links:
                                href = link.get_attribute("href")
                                if href and "&no=" in href:
                                    no_start = href.find("&no=") + 4
                                    no_end = href.find("&", no_start)
                                    company_no = href[no_start:no_end] if no_end != -1 else href[no_start:]
                                    break
                        except:
                            pass

                        # Thumbnail image
                        img_url = None
                        try:
                            img = product.find_element(By.TAG_NAME, "img")
                            img_url = img.get_attribute("src")
                        except:
                            pass

                        page_products.append({
                            'product_id': product_id,
                            'product_name': product_name,
                            'company_no': company_no,
                            'category_id': str(category_id),
                            'category_name': f'Category_{category_id}',
                            'thumbnail_url': img_url,
                            'detail_url': f"https://onehago.com/mall/?cate_mode=view&pid={product_id}&no={company_no}" if company_no and product_id else None,
                            'found_on_page': page_num,
                            'crawled_at': datetime.now().isoformat()
                        })

                    except Exception as e:
                        continue

                products.extend(page_products)
                self.stats['pages_crawled'] += 1
                self.stats['products_found'] += len(page_products)

                print(f"  ✅ Page {page_num}: {len(page_products)} products")

            except Exception as e:
                print(f"  ❌ Page {page_num} error: {e}")
                self.stats['errors'] += 1

        return products

    def crawl_category(self, category_id):
        """Crawl complete category with details"""
        if self.is_category_completed(category_id):
            print(f"⏭️  Category {category_id}: Already completed")
            return

        print(f"\n{'='*70}")
        print(f"📂 CATEGORY {category_id}")
        print(f"{'='*70}")

        # Step 1: Crawl product list
        products = self.crawl_category_list(category_id)

        if not products:
            print(f"  ⚠️  No products found")
            return

        # Step 2: Crawl details for each product
        print(f"\n📋 Crawling details for {len(products)} products...")
        for idx, product in enumerate(products, 1):
            try:
                print(f"  [{idx}/{len(products)}] {product['product_name'][:50]}...")
                self.crawl_product_detail(product)

                # Delay between detail requests
                time.sleep(self.delay_min + (self.delay_max - self.delay_min) * random.random())
            except Exception as e:
                print(f"      ❌ Error: {e}")
                self.stats['errors'] += 1

        # Step 3: Save to separate category file
        category_file = self.categories_dir / f'category_{category_id}.json'
        with open(category_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

        self.mark_category_completed(category_id)
        self.stats['categories_crawled'] += 1

        print(f"\n✅ Category {category_id} complete: {len(products)} products saved")
        print(f"   Details: {sum(1 for p in products if p.get('detail_crawled'))} products")
        print(f"   Images: {sum(1 for p in products if p.get('image_path'))} downloaded")

    def crawl_all(self):
        """Crawl all assigned categories"""
        print("=" * 70)
        print(f"🤖 Onehago Complete Crawler (Details + Images)")
        print(f"📂 Categories: {self.category_ids}")
        print(f"⏱️  Delay: {self.delay_min}s - {self.delay_max}s")
        print("=" * 70)

        self.setup_driver()

        for category_id in self.category_ids:
            try:
                self.crawl_category(category_id)
            except Exception as e:
                print(f"\n❌ Category {category_id} failed: {e}")
                self.stats['errors'] += 1

        # Cleanup
        if self.driver:
            self.driver.quit()

        # Final stats
        self.stats['end_time'] = datetime.now()
        duration = self.stats['end_time'] - self.stats['start_time']

        print("\n" + "=" * 70)
        print("CRAWLER SUMMARY")
        print("=" * 70)
        print(f"Categories: {self.stats['categories_crawled']}/{len(self.category_ids)}")
        print(f"Pages: {self.stats['pages_crawled']}")
        print(f"Products found: {self.stats['products_found']}")
        print(f"Details crawled: {self.stats['details_crawled']}")
        print(f"Images downloaded: {self.stats['images_downloaded']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Duration: {duration}")
        print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description='Onehago Complete Parallel Crawler')
    parser.add_argument('--categories', type=str, required=True, help='Comma-separated category IDs')
    parser.add_argument('--min-delay', type=float, default=0.3)
    parser.add_argument('--max-delay', type=float, default=0.8)

    args = parser.parse_args()

    category_ids = [int(c.strip()) for c in args.categories.split(',')]

    crawler = OnehagoCompleteCrawler(
        category_ids=category_ids,
        delay_min=args.min_delay,
        delay_max=args.max_delay
    )

    crawler.crawl_all()

if __name__ == "__main__":
    main()
