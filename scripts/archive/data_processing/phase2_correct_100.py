#!/usr/bin/env python3
"""
PHASE 2 (CORRECT): Extract Details for 100 Products
Uses correct URL format: ?cate_mode=view&pid=X&no=Y
"""

import json
import requests
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(f'/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/logs/phase2_correct_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago')
INPUT_FILE = BASE_PATH / 'crawled' / 'test_phase1_correct_urls.jsonl'
OUTPUT_DIR = BASE_PATH / 'crawled' / 'test_phase2_correct_results'
IMAGES_DIR = OUTPUT_DIR / 'images'

# Ensure directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

class Phase2Extractor:
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def download_image(self, url: str, product_id: str, img_idx: int) -> Dict:
        """Download product image"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            ext = url.split('.')[-1].split('?')[0].lower()
            ext = ext if ext in ['jpg', 'jpeg', 'png', 'gif'] else 'jpg'

            filename = f"{product_id}_{img_idx}.{ext}"
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
            product_id = product_info.get('product_id')

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

            # Extract phone, fax, email
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

            # Image handling - get ALL images
            image_urls = []
            for img in soup.find_all('img'):
                src = img.get('src')
                if src and '/productImages/' in src:
                    if src.startswith('/'):
                        src = f"https://www.onehago.com{src}"
                    image_urls.append(src)

            # Download images in parallel
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_url = {
                    executor.submit(self.download_image, url, product_id, idx): url
                    for idx, url in enumerate(image_urls, 1)
                }

                details['full_images'] = []
                for future in as_completed(future_to_url):
                    img_data = future.result()
                    if img_data:
                        details['full_images'].append(img_data)

            return details

        except Exception as e:
            logger.error(f"Error extracting details from {detail_url}: {e}")
            return {
                **product_info,
                'error': str(e),
                'detail_crawled': False,
                'detail_crawled_at': datetime.now().isoformat()
            }

def main():
    logger.info("="*70)
    logger.info("🧪 PHASE 2 (CORRECT): Extract Details for 100 Products")
    logger.info("="*70)

    # Load product URLs from Phase 1
    products = []
    with open(INPUT_FILE, 'r') as f:
        for line in f:
            products.append(json.loads(line))

    logger.info(f"\n📊 Loaded {len(products)} products from Phase 1")

    # Extract details
    extractor = Phase2Extractor(max_workers=4)
    processed_products = []

    logger.info(f"🔍 Starting detail extraction...\n")

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_product = {
            executor.submit(extractor.extract_product_details, product): product
            for product in products
        }

        for idx, future in enumerate(as_completed(future_to_product), 1):
            try:
                details = future.result()
                processed_products.append(details)

                if idx % 10 == 0:
                    logger.info(f"  Progress: {idx}/{len(products)} products processed")

            except Exception as e:
                logger.error(f"Failed to process product: {e}")

    # Save results
    output_file = OUTPUT_DIR / 'products_detailed.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_products, f, ensure_ascii=False, indent=2)

    # Summary
    specs_count = sum(1 for p in processed_products if p.get('specifications'))
    images_count = sum(1 for p in processed_products if p.get('full_images'))
    phone_count = sum(1 for p in processed_products if p.get('phone'))
    total_images = sum(len(p.get('full_images', [])) for p in processed_products)

    logger.info(f"\n{'='*70}")
    logger.info(f"✅ PHASE 2 COMPLETE")
    logger.info(f"{'='*70}")
    logger.info(f"📊 Quality Metrics:")
    logger.info(f"  Total products: {len(processed_products)}")
    logger.info(f"  With specifications: {specs_count}/{len(processed_products)} ({specs_count*100//len(processed_products)}%)")
    logger.info(f"  With images: {images_count}/{len(processed_products)} ({images_count*100//len(processed_products)}%)")
    logger.info(f"  Total images downloaded: {total_images}")
    logger.info(f"  With phone: {phone_count}/{len(processed_products)} ({phone_count*100//len(processed_products)}%)")
    logger.info(f"  Output: {output_file}")
    logger.info(f"  Images: {IMAGES_DIR}")
    logger.info(f"{'='*70}")

    return specs_count >= len(processed_products) * 0.95  # 95% success rate

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
