#!/usr/bin/env python3
"""
Process first 100 products from all_products.json
Extract details and organize by category
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
from collections import defaultdict

import logging
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago')
ALL_PRODUCTS_FILE = BASE_PATH / 'crawled' / 'all_products.json'
OUTPUT_DIR = BASE_PATH / 'crawled' / 'categories'
IMAGES_DIR = BASE_PATH / 'crawled' / 'images'
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
        logging.FileHandler(LOGS_DIR / f'process_100_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Product100Processor:
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

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
            detail_url = product_info.get('product_url') or product_info.get('url')

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
                        lambda url: self.download_image(url, str(details.get('product_id', details.get('id', 'unknown')))),
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

    def process_100_products(self):
        """Process first 100 products and organize by category"""
        logger.info("🚀 Processing first 100 products")

        # Load all products
        with open(ALL_PRODUCTS_FILE, 'r') as f:
            all_products = json.load(f)

        logger.info(f"Total products available: {len(all_products)}")

        # Take first 100
        products_to_process = all_products[:100]

        logger.info(f"Processing 100 products with detail extraction...")

        # Process with parallel extraction
        processed_products = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_product = {
                executor.submit(self.extract_product_details, product): product
                for product in products_to_process
            }

            for idx, future in enumerate(as_completed(future_to_product), 1):
                try:
                    details = future.result()
                    processed_products.append(details)

                    if idx % 10 == 0:
                        logger.info(f"Progress: {idx}/100 products processed")

                except Exception as e:
                    logger.error(f"Failed to process product: {e}")

        # Organize by category
        by_category = defaultdict(list)
        for product in processed_products:
            category_id = product.get('category_id') or product.get('category')
            if category_id:
                by_category[str(category_id)].append(product)

        # Save each category
        for category_id, products in by_category.items():
            output_file = OUTPUT_DIR / f"category_{category_id}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ Saved {len(products)} products to category_{category_id}.json")

        # Summary
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ Processing Complete!")
        logger.info(f"📊 Total products processed: {len(processed_products)}")
        logger.info(f"📁 Categories created: {len(by_category)}")
        logger.info(f"📂 Location: {OUTPUT_DIR}")
        logger.info(f"{'='*70}")

        # Quality metrics
        specs_count = sum(1 for p in processed_products if p.get('specifications'))
        images_count = sum(1 for p in processed_products if p.get('full_images'))

        logger.info(f"\n📊 Quality Metrics:")
        logger.info(f"  Products with specifications: {specs_count}/100 ({specs_count}%)")
        logger.info(f"  Products with images: {images_count}/100 ({images_count}%)")

def main():
    processor = Product100Processor(max_workers=4)
    processor.process_100_products()

if __name__ == "__main__":
    main()
