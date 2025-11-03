#!/usr/bin/env python3
"""
Onehago 100-Product Test Crawler
Combines URL collection + detail extraction for testing
"""

import json
import os
import sys
import time
import re
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

import logging
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago')
CATEGORIES_FILE = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/valid_categories.json')
OUTPUT_DIR = BASE_PATH / 'crawled' / 'test_100'
IMAGES_DIR = OUTPUT_DIR / 'images'
PROGRESS_FILE = OUTPUT_DIR / 'progress.json'
LOGS_DIR = BASE_PATH / 'crawled' / 'logs'

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f'test_100_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Onehago100TestCrawler:
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        # Load categories
        with open(CATEGORIES_FILE, 'r') as f:
            self.categories = json.load(f)

        # Sort by product count (largest first)
        self.categories = sorted(self.categories, key=lambda x: int(x.get('products', 0)), reverse=True)

        logger.info(f"Loaded {len(self.categories)} categories")

    def get_category_products(self, category_id: int, max_products: int = 100) -> List[Dict]:
        """Collect product URLs from a category"""
        products = []
        page = 1

        logger.info(f"Collecting products from Category {category_id}")

        while len(products) < max_products:
            try:
                url = f"https://www.onehago.com/mall/?mode=list&category={category_id}&page={page}"
                response = self.session.get(url, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Find product items
                product_items = soup.find_all('div', class_='item')

                if not product_items:
                    logger.info(f"No more products found on page {page}")
                    break

                for item in product_items:
                    if len(products) >= max_products:
                        break

                    # Extract product link
                    link = item.find('a', href=True)
                    if not link:
                        continue

                    href = link['href']

                    # Extract product ID from URL
                    match = re.search(r'prod_cd=(\d+)', href)
                    if not match:
                        continue

                    product_id = match.group(1)

                    # Get product name
                    name_elem = item.find('div', class_='name')
                    product_name = name_elem.get_text(strip=True) if name_elem else ''

                    # Get company
                    company_elem = item.find('div', class_='company')
                    company = company_elem.get_text(strip=True) if company_elem else ''

                    # Get image
                    img = item.find('img')
                    image_url = img.get('src', '') if img else ''

                    products.append({
                        'product_id': product_id,
                        'product_url': f"https://www.onehago.com{href}" if href.startswith('/') else href,
                        'product_name': product_name,
                        'company': company,
                        'image_url': image_url,
                        'category_id': category_id,
                        'page': page,
                        'collected_at': datetime.now().isoformat()
                    })

                logger.info(f"Collected {len(products)} products so far from Category {category_id}")

                page += 1
                time.sleep(0.2)  # Short delay between pages

            except Exception as e:
                logger.error(f"Error collecting from Category {category_id}, page {page}: {e}")
                break

        return products

    def download_image(self, url: str, product_id: str) -> Dict:
        """Download product image"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            ext = url.split('.')[-1].split('?')[0].lower()
            ext = ext if ext in ['jpg', 'jpeg', 'png', 'gif'] else 'jpg'

            filename = f"{product_id}.{ext}"
            filepath = IMAGES_DIR / filename

            with open(filepath, 'wb') as f:
                f.write(response.content)

            return {
                'url': url,
                'local_path': str(filepath.relative_to(BASE_PATH)),
                'size_bytes': len(response.content)
            }
        except Exception as e:
            logger.warning(f"Image download failed: {url} - {e}")
            return None

    def extract_product_details(self, product_info: Dict) -> Dict[str, Any]:
        """Extract comprehensive product details"""
        try:
            detail_url = product_info.get('product_url')

            if not detail_url:
                return {
                    **product_info,
                    'error': 'No detail URL',
                    'detail_crawled': False
                }

            response = self.session.get(detail_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            details = {
                **product_info,
                'detail_crawled': True,
                'detail_crawled_at': datetime.now().isoformat(),
                'specifications': {}
            }

            # Specifications from box-info div
            box_info = soup.find('div', class_='box-info')
            if box_info:
                info_text = box_info.get_text(separator='\n', strip=True)
                lines = [line.strip() for line in info_text.split('\n') if line.strip()]

                field_map = {
                    0: '제조사',
                    1: '코드',
                    2: '사이즈',
                    3: 'Neck',
                    4: 'Neck Size',
                    5: '재질'
                }

                for idx, line in enumerate(lines):
                    if idx in field_map:
                        details['specifications'][field_map[idx]] = line
                    else:
                        details['specifications'][f'field_{idx}'] = line

            # Company info
            company_div = soup.find('div', class_='company')
            if company_div:
                company_text = company_div.get_text(strip=True)
                details['manufacturer'] = company_text

                page_text = soup.get_text()

                phone_match = re.search(r'(?:PHONE|전화|TEL)[:\s]*(\d{2,4}-\d{3,4}-\d{4})', page_text, re.IGNORECASE)
                fax_match = re.search(r'FAX[:\s]*(\d{2,4}-\d{3,4}-\d{4})', page_text, re.IGNORECASE)
                email_match = re.search(r'(?:E\s*MAIL|이메일)[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', page_text, re.IGNORECASE)

                if phone_match:
                    details['phone'] = phone_match.group(1)
                if fax_match:
                    details['fax'] = fax_match.group(1)
                if email_match:
                    details['email'] = email_match.group(1)

            # Image handling
            image_urls = []
            product_div = soup.find('div', class_='product')
            if product_div:
                imgs = product_div.find_all('img')
                for img in imgs:
                    src = img.get('src')
                    if src and '/productImages/' in src:
                        if src.startswith('/'):
                            src = f"https://www.onehago.com{src}"
                        image_urls.append(src)

            with ThreadPoolExecutor(max_workers=3) as executor:
                details['full_images'] = [
                    img for img in executor.map(
                        lambda url: self.download_image(url, details['product_id']),
                        image_urls
                    ) if img is not None
                ]

            return details

        except Exception as e:
            logger.error(f"Error extracting details from {detail_url}: {e}")
            return {
                **product_info,
                'error': str(e),
                'detail_crawled': False,
                'detail_crawled_at': datetime.now().isoformat()
            }

    def run_test(self, target_count: int = 100):
        """Run test to collect and process N products"""
        logger.info(f"🚀 Starting 100-Product Test (target: {target_count} products)")

        all_products = []

        # Collect products from categories until we reach target
        for category in self.categories:
            if len(all_products) >= target_count:
                break

            category_id = category['id']
            needed = target_count - len(all_products)

            products = self.get_category_products(category_id, max_products=needed)

            if products:
                logger.info(f"✅ Collected {len(products)} products from Category {category_id}")
                all_products.extend(products)

        logger.info(f"\n{'='*70}")
        logger.info(f"📦 Total collected: {len(all_products)} products")
        logger.info(f"{'='*70}\n")

        if len(all_products) == 0:
            logger.error("❌ No products collected!")
            return

        # Process products with detail extraction
        logger.info(f"🔍 Starting detail extraction for {len(all_products)} products...")

        processed_products = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_product = {
                executor.submit(self.extract_product_details, product): product
                for product in all_products
            }

            for idx, future in enumerate(as_completed(future_to_product), 1):
                try:
                    details = future.result()
                    processed_products.append(details)

                    if idx % 10 == 0:
                        logger.info(f"Progress: {idx}/{len(all_products)} products processed")

                except Exception as e:
                    logger.error(f"Failed to process product: {e}")

        # Save results
        output_file = OUTPUT_DIR / 'products_100.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_products, f, ensure_ascii=False, indent=2)

        logger.info(f"\n{'='*70}")
        logger.info(f"✅ Test Complete!")
        logger.info(f"📁 Saved {len(processed_products)} products to {output_file}")
        logger.info(f"🖼️  Downloaded images to {IMAGES_DIR}")
        logger.info(f"{'='*70}")

        # Summary statistics
        specs_count = sum(1 for p in processed_products if p.get('specifications'))
        images_count = sum(1 for p in processed_products if p.get('full_images'))

        logger.info(f"\n📊 Quality Metrics:")
        logger.info(f"  Products with specifications: {specs_count}/{len(processed_products)} ({specs_count*100//len(processed_products)}%)")
        logger.info(f"  Products with images: {images_count}/{len(processed_products)} ({images_count*100//len(processed_products)}%)")

def main():
    crawler = Onehago100TestCrawler(max_workers=4)
    crawler.run_test(target_count=100)

if __name__ == "__main__":
    main()
