#!/usr/bin/env python3
"""
Comprehensive Onehago Product Crawler
- Extracts detailed product information
- Supports multiple categories
- Captures all specifications and images
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

# Setup paths and logging
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled')
CATEGORIES_FILE = BASE_PATH / 'valid_categories.json'
PRODUCT_URLS_FILE = BASE_PATH / 'product_urls.jsonl'
DETAILS_DIR = BASE_PATH / 'details'
IMAGES_DIR = BASE_PATH / 'images'

# Ensure directories exist
DETAILS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(BASE_PATH / 'logs' / f'detailed_crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class OnehagoDetailCrawler:
    def __init__(self, max_workers=4, delay_min=0.1, delay_max=0.3):
        self.max_workers = max_workers
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.session = requests.Session()

    def load_categories(self) -> List[Dict]:
        """Load categories from JSON file"""
        with open(CATEGORIES_FILE, 'r') as f:
            return json.load(f)

    def get_product_urls_by_category(self, category_id: str) -> List[Dict]:
        """Extract product URLs for a specific category"""
        urls = []
        with open(PRODUCT_URLS_FILE, 'r') as f:
            for line in f:
                product = json.loads(line)
                if str(product['category_id']) == str(category_id):
                    urls.append(product)
        return urls

    def download_image(self, url: str, product_id: str, index: int) -> Dict:
        """Download product image"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            ext = url.split('.')[-1].split('?')[0].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                ext = 'jpg'  # Default extension

            filename = f"{product_id}_{index}.{ext}"
            filepath = IMAGES_DIR / filename

            with open(filepath, 'wb') as f:
                f.write(response.content)

            return {
                'index': index,
                'url': url,
                'local_path': str(filepath),
                'size_bytes': len(response.content),
                'downloaded': True
            }
        except Exception as e:
            logger.warning(f"Image download failed: {url} - {e}")
            return None

    def extract_product_details(self, product_url: str) -> Dict[str, Any]:
        """Extract comprehensive product details"""
        try:
            response = self.session.get(product_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Detailed extraction logic
            details = {
                'source_url': product_url,
                'extracted_at': datetime.now().isoformat(),
                'specifications': {},
                'images': []
            }

            # Product specifications
            spec_table = soup.find('table', class_='spec_table')
            if spec_table:
                for row in spec_table.find_all('tr'):
                    cols = row.find_all(['th', 'td'])
                    if len(cols) == 2:
                        key = cols[0].get_text(strip=True)
                        value = cols[1].get_text(strip=True)
                        details['specifications'][key] = value

            # Company details
            company_section = soup.find('div', class_='company_info')
            if company_section:
                company_name = company_section.find(class_='company_name')
                company_tel = company_section.find(class_='company_tel')
                company_email = company_section.find(class_='company_email')

                if company_name:
                    details['company'] = company_name.get_text(strip=True)
                if company_tel:
                    details['phone'] = company_tel.get_text(strip=True)
                if company_email:
                    details['email'] = company_email.get_text(strip=True)

            # Product images
            img_elements = soup.find_all('img', class_='prod_img')
            with ThreadPoolExecutor(max_workers=3) as executor:
                image_futures = [
                    executor.submit(
                        self.download_image,
                        img.get('src'),
                        re.search(r'prod_cd=(\d+)', product_url).group(1),
                        idx
                    )
                    for idx, img in enumerate(img_elements)
                ]

                details['images'] = [
                    future.result() for future in as_completed(image_futures)
                    if future.result() is not None
                ]

            details['image_count'] = len(details['images'])

            return details

        except Exception as e:
            logger.error(f"Error extracting details from {product_url}: {e}")
            return {'error': str(e), 'source_url': product_url}

    def process_category(self, category_id: str):
        """Process all products in a category"""
        logger.info(f"Processing Category {category_id}")

        # Get product URLs for this category
        products = self.get_product_urls_by_category(category_id)

        logger.info(f"Found {len(products)} products in Category {category_id}")

        # Process products with thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_product = {
                executor.submit(self.extract_product_details, product['product_url']): product
                for product in products
            }

            for future in as_completed(future_to_product):
                original_product = future_to_product[future]
                try:
                    details = future.result()

                    # Merge original product info with extracted details
                    details.update({
                        'product_id': original_product['product_id'],
                        'product_name': original_product['product_name']
                    })

                    # Save details
                    output_file = DETAILS_DIR / f"{details['product_id']}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(details, f, ensure_ascii=False, indent=2)

                    logger.info(f"Saved details for Product {details['product_id']}")

                except Exception as e:
                    logger.error(f"Failed to process product: {e}")

    def run(self, categories=None):
        """Main execution method"""
        logger.info("🚀 Starting Onehago Detailed Crawler")

        # Load all categories if not specified
        all_categories = self.load_categories()

        if categories is None:
            categories = [cat['id'] for cat in all_categories]

        # Process specified categories
        for category_id in categories:
            self.process_category(str(category_id))

        logger.info("🏁 Crawling Complete!")

def main():
    crawler = OnehagoDetailCrawler(max_workers=4)
    crawler.run()  # Process all categories

if __name__ == "__main__":
    main()