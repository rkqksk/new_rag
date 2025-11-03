#!/usr/bin/env python3
"""
JINA-based Onehago Product Scraper
Extracts detailed product information using Jina
"""

import json
import os
import sys
import time
import requests
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# JINA imports
from jina import Executor, requests as jina_requests

# Setup paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled')
PRODUCT_URLS_PATH = BASE_PATH / 'product_urls.jsonl'
DETAILS_PATH = BASE_PATH / 'details'
DETAILS_PATH.mkdir(parents=True, exist_ok=True)
LOGS_PATH = BASE_PATH / 'logs'
LOGS_PATH.mkdir(parents=True, exist_ok=True)

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOGS_PATH / f'jina_crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class OnehagoProductScraper(Executor):
    @jina_requests(on='/extract')
    def extract_product_details(self, docs, **kwargs):
        """Extract detailed product information using Jina"""
        result_docs = []

        for doc in docs:
            try:
                # Get product info from the JSON doc
                url = doc.get('url', '')
                product_id = doc.get('product_id', '')

                # Fetch product page
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                # Use BeautifulSoup for parsing
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract detailed information
                details = {
                    'product_id': product_id,
                    'source_url': url,
                    'extracted_at': datetime.now().isoformat(),
                }

                # Specifications table
                try:
                    spec_table = soup.find('table', class_='spec_table')
                    if spec_table:
                        specs = {}
                        for row in spec_table.find_all('tr'):
                            cols = row.find_all(['th', 'td'])
                            if len(cols) == 2:
                                key = cols[0].get_text(strip=True)
                                value = cols[1].get_text(strip=True)
                                specs[key] = value
                        details['specifications'] = specs
                except Exception as spec_err:
                    logger.warning(f"Spec extraction error for {url}: {spec_err}")
                    details['specifications'] = {}

                # Images
                try:
                    images = []
                    img_elements = soup.find_all('img', class_='prod_img')
                    for idx, img in enumerate(img_elements):
                        img_url = img.get('src')
                        if img_url:
                            # Download image
                            img_response = requests.get(img_url, timeout=10)
                            if img_response.status_code == 200:
                                local_path = f"images/{product_id}_{idx}.jpg"
                                full_local_path = BASE_PATH / local_path
                                full_local_path.parent.mkdir(parents=True, exist_ok=True)

                                with open(full_local_path, 'wb') as f:
                                    f.write(img_response.content)

                                images.append({
                                    'index': idx,
                                    'url': img_url,
                                    'local_path': local_path,
                                    'size_bytes': len(img_response.content),
                                    'downloaded': True
                                })
                    details['images'] = images
                    details['image_count'] = len(images)
                except Exception as img_err:
                    logger.warning(f"Image extraction error for {url}: {img_err}")
                    details['images'] = []
                    details['image_count'] = 0

                # Add additional context from original document
                for key, value in doc.items():
                    if key not in ['url', 'product_id']:
                        details[key] = value

                # Append to results
                result_docs.append(details)

            except Exception as e:
                logger.error(f"Error extracting {url}: {e}")
                result_docs.append({'error': str(e), 'product_id': product_id, 'source_url': url})

        return result_docs

def load_product_urls(limit=100):
    """Load first 100 product URLs from JSONL"""
    products = []
    with open(PRODUCT_URLS_PATH, 'r') as f:
        for idx, line in enumerate(f, 1):
            if idx > limit:
                break
            product = json.loads(line)
            product['url'] = product.pop('product_url')  # Rename for consistency
            products.append(product)
    return products

def process_products(products: List[Dict[str, Any]]):
    """Process products using Jina"""
    logger.info(f"Processing {len(products)} products...")

    # Initialize Jina Executor
    scraper = OnehagoProductScraper()

    # Process documents
    processed_docs = scraper.extract_product_details(products)

    # Save results
    for doc in processed_docs:
        if 'product_id' in doc and 'error' not in doc:
            product_id = doc['product_id']
            details_file = DETAILS_PATH / f"{product_id}.json"
            try:
                with open(details_file, 'w', encoding='utf-8') as f:
                    json.dump(doc, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved details for product {product_id}")
            except Exception as e:
                logger.error(f"Error saving details for {product_id}: {e}")

def main():
    logger.info("🚀 Starting Onehago JINA Product Crawler")

    # Load first 100 products
    products = load_product_urls(limit=100)

    logger.info(f"Loaded {len(products)} products")

    # Process products
    process_products(products)

    logger.info("🏁 Crawling Complete!")

if __name__ == "__main__":
    main()