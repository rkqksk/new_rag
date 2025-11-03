#!/usr/bin/env python3
"""
Comprehensive Onehago Product Crawler
Extracts detailed product information with manual approval every 100 products
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
PRODUCT_URLS_FILE = BASE_PATH / 'crawled' / 'product_urls.jsonl'
DETAILS_DIR = BASE_PATH / 'crawled' / 'categories'
IMAGES_DIR = BASE_PATH / 'crawled' / 'images'
PROGRESS_FILE = BASE_PATH / 'crawled' / 'crawler_progress.json'
LOGS_DIR = BASE_PATH / 'crawled' / 'logs'

# Ensure directories exist
DETAILS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f'product_crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def user_confirmation(processed_count: int, auto_continue: bool = False) -> bool:
    """
    Ask user for confirmation to continue crawling
    Returns True to continue, False to stop
    """
    print("\n" + "=" * 70)
    print(f"✅ Processed {processed_count} products")

    # Auto-continue for initial test run
    if auto_continue:
        print("Auto-continuing for initial test run...")
        return True

    print("Do you want to continue crawling?")
    print("1. Continue")
    print("2. Stop")

    while True:
        try:
            choice = input("Enter your choice (1/2): ").strip()
            if choice == '1':
                return True
            elif choice == '2':
                return False
            else:
                print("Invalid input. Please enter 1 or 2.")
        except Exception as e:
            print(f"Error reading input: {e}")
            return False

class OnehagoProductCrawler:
    def __init__(self, max_workers=4, delay_min=0.1, delay_max=0.3, max_products=100, auto_continue=False):
        self.max_workers = max_workers
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.max_products = max_products
        self.auto_continue = auto_continue
        self.session = requests.Session()

        # Load and preprocess categories
        self.categories = self._load_categories()
        self.category_ids = {str(cat['id']): cat for cat in self.categories}

    def _load_categories(self) -> List[Dict]:
        """Load categories from JSON file"""
        logger.info(f"Loading categories from {CATEGORIES_FILE}")
        with open(CATEGORIES_FILE, 'r') as f:
            categories = json.load(f)
        logger.info(f"Loaded {len(categories)} categories")
        return categories

    def load_progress(self) -> Dict:
        """Load or create progress tracking"""
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        return {
            'processed_categories': [],
            'total_processed': 0,
            'last_processed_category': None
        }

    def save_progress(self, progress: Dict):
        """Save progress tracking"""
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=2)

    def get_product_urls_by_category(self, category_id: str) -> List[Dict]:
        """Extract product URLs for a specific category"""
        logger.info(f"Finding product URLs for Category {category_id}")
        urls = []
        with open(PRODUCT_URLS_FILE, 'r') as f:
            for line in f:
                product = json.loads(line)
                # Robust category matching
                if (str(product['category_id']) == str(category_id) or
                    int(product['category_id']) == int(category_id)):
                    urls.append(product)
        logger.info(f"Found {len(urls)} products in Category {category_id}")
        return urls

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
            detail_url = product_info.get('detail_url') or product_info.get('product_url')

            if not detail_url:
                logger.warning(f"No detail URL for product {product_info.get('product_id', 'Unknown')}")
                return {
                    **product_info,
                    'error': 'No detail URL found',
                    'detail_crawled': False,
                    'detail_crawled_at': datetime.now().isoformat()
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
                # Get all text and parse line by line
                info_text = box_info.get_text(separator='\n', strip=True)
                lines = [line.strip() for line in info_text.split('\n') if line.strip()]

                # Map common fields
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

            # Company info parsing
            company_div = soup.find('div', class_='company')
            if company_div:
                company_text = company_div.get_text(strip=True)
                details['manufacturer'] = company_text

                # Look for contact info in the page
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

            # Image handling - find ALL product images
            image_urls = []
            product_div = soup.find('div', class_='product')
            if product_div:
                imgs = product_div.find_all('img')
                for img in imgs:
                    src = img.get('src')
                    if src and '/productImages/' in src:
                        # Convert to absolute URL if needed
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

    def process_category(self, category_id: str) -> bool:
        """Process products in a category, return True if processing should continue"""
        logger.info(f"Processing Category {category_id}")

        # Get product URLs for this category
        all_products = self.get_product_urls_by_category(category_id)

        # Skip empty categories
        if len(all_products) == 0:
            logger.info(f"Skipping empty Category {category_id}")
            return True

        # Load progress
        progress = self.load_progress()

        # Limit to max_products if not reached
        products_to_process = all_products[:self.max_products]

        logger.info(f"Processing {len(products_to_process)} products in Category {category_id}")

        processed_products = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_product = {
                executor.submit(self.extract_product_details, product): product
                for product in products_to_process
            }

            for future in as_completed(future_to_product):
                try:
                    details = future.result()
                    processed_products.append(details)
                    logger.info(f"Processed Product {details.get('product_id', 'Unknown')}")
                except Exception as e:
                    logger.error(f"Failed to process product: {e}")

        # Save category results
        output_file = DETAILS_DIR / f"category_{category_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_products, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(processed_products)} products for Category {category_id}")

        # Update progress
        progress['processed_categories'].append(category_id)
        progress['total_processed'] += len(processed_products)
        progress['last_processed_category'] = category_id
        self.save_progress(progress)

        # Ask user for confirmation
        continue_processing = user_confirmation(progress['total_processed'], self.auto_continue)

        return continue_processing

    def run(self, categories=None):
        """Main execution method"""
        logger.info("🚀 Starting Onehago Product Crawler")

        if categories is None:
            # Sort by number of products (descending)
            categories = [
                cat['id'] for cat in sorted(self.categories,
                                            key=lambda x: int(x.get('products', 0)),
                                            reverse=True)
            ]

        # Process categories
        for category_id in categories:
            if not self.process_category(str(category_id)):
                logger.info("Stopping crawler as per user request")
                break

        logger.info("🏁 Crawling Complete!")

def main():
    # For first test run, use auto_continue=True to process all products without manual confirmation
    crawler = OnehagoProductCrawler(max_workers=4, auto_continue=True)
    crawler.run()  # Process all categories

if __name__ == "__main__":
    main()