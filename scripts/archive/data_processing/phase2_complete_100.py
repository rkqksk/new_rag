#!/usr/bin/env python3
"""
PHASE 2 (COMPLETE): Extract ALL Details for 100 Products
Extracts: product_name, specifications (코드, 용량, 사이즈, MOQ, 재질, 원산지),
company info (제조사, PHONE, FAX, 담당, E MAIL), and all images
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
        logging.FileHandler(f'/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/logs/phase2_complete_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths
BASE_PATH = Path('/Users/oypnus/Project/rag-enterprise/data/onehago')
INPUT_FILE = BASE_PATH / 'crawled' / 'test_phase1_correct_urls.jsonl'
OUTPUT_DIR = BASE_PATH / 'crawled' / 'test_phase2_complete_results'
IMAGES_DIR = OUTPUT_DIR / 'images'

# Ensure directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

class Phase2CompleteExtractor:
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
                'specifications': {},
                'company_info': {}
            }

            # 1. Product Name
            pack_tit = soup.find('div', class_='pack_tit')
            if pack_tit:
                product_name = pack_tit.get_text(strip=True)
                # Remove trailing numbers
                product_name = re.sub(r'\d+$', '', product_name).strip()
                details['product_name'] = product_name

            # 2. Specifications from pack_txt_li
            pack_txt_li = soup.find('div', class_='pack_txt_li')
            if pack_txt_li:
                text = pack_txt_li.get_text(strip=True)
                
                # Parse specifications
                spec_patterns = [
                    (r'코드([^용량사이즈MOQ재질원산지]+)', '코드'),
                    (r'용량([^사이즈MOQ재질원산지]+)', '용량'),
                    (r'사이즈([^MOQ재질원산지]+)', '사이즈'),
                    (r'MOQ([^재질원산지]+)', 'MOQ'),
                    (r'재질([^원산지]+)', '재질'),
                    (r'원산지(.+)', '원산지'),
                ]
                
                for pattern, key in spec_patterns:
                    match = re.search(pattern, text)
                    if match:
                        value = match.group(1).strip()
                        details['specifications'][key] = value

            # 3. Company info from pack_com_li
            pack_com_li = soup.find('div', class_='pack_com_li')
            if pack_com_li:
                text = pack_com_li.get_text(strip=True)
                
                # Extract company fields
                company_match = re.search(r'제조사([^P]+)PHONE', text)
                if company_match:
                    details['company_info']['제조사'] = company_match.group(1).strip()
                
                phone_match = re.search(r'PHONE([^F]+)FAX', text)
                if phone_match:
                    phone_value = phone_match.group(1).strip()
                    if phone_value and phone_value != '--':
                        details['phone'] = phone_value
                
                fax_match = re.search(r'FAX([^담]+)담당', text)
                if fax_match:
                    fax_value = fax_match.group(1).strip()
                    if fax_value and fax_value != '--':
                        details['fax'] = fax_value
                
                contact_match = re.search(r'담당([^E]+)E MAIL', text)
                if contact_match:
                    details['company_info']['담당'] = contact_match.group(1).strip()
                
                email_match = re.search(r'E MAIL([^\s]+)', text)
                if email_match:
                    details['email'] = email_match.group(1).strip()

            # 4. Image handling - get ALL images
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
    logger.info("🧪 PHASE 2 (COMPLETE): Extract ALL Details for 100 Products")
    logger.info("="*70)

    # Load product URLs from Phase 1
    products = []
    with open(INPUT_FILE, 'r') as f:
        for line in f:
            products.append(json.loads(line))

    logger.info(f"\n📊 Loaded {len(products)} products from Phase 1")

    # Extract details
    extractor = Phase2CompleteExtractor(max_workers=4)
    processed_products = []

    logger.info(f"🔍 Starting complete detail extraction...\n")

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

    # Detailed statistics
    product_name_count = sum(1 for p in processed_products if p.get('product_name'))
    specs_count = sum(1 for p in processed_products if p.get('specifications'))
    
    # Count specification fields
    spec_field_counts = {}
    for p in processed_products:
        if p.get('specifications'):
            for key in p['specifications'].keys():
                spec_field_counts[key] = spec_field_counts.get(key, 0) + 1
    
    images_count = sum(1 for p in processed_products if p.get('full_images'))
    total_images = sum(len(p.get('full_images', [])) for p in processed_products)
    phone_count = sum(1 for p in processed_products if p.get('phone'))
    email_count = sum(1 for p in processed_products if p.get('email'))
    manufacturer_count = sum(1 for p in processed_products if p.get('company_info', {}).get('제조사'))
    contact_count = sum(1 for p in processed_products if p.get('company_info', {}).get('담당'))

    logger.info(f"\n{'='*70}")
    logger.info(f"✅ PHASE 2 COMPLETE")
    logger.info(f"{'='*70}")
    logger.info(f"📊 Extraction Quality:")
    logger.info(f"  Total products: {len(processed_products)}")
    logger.info(f"  With product name: {product_name_count}/{len(processed_products)} ({product_name_count*100//len(processed_products)}%)")
    logger.info(f"  With specifications: {specs_count}/{len(processed_products)} ({specs_count*100//len(processed_products)}%)")
    
    logger.info(f"\n  Specification field coverage:")
    for field, count in sorted(spec_field_counts.items()):
        logger.info(f"    {field}: {count}/{len(processed_products)} ({count*100//len(processed_products)}%)")
    
    logger.info(f"\n  Company information:")
    logger.info(f"    제조사: {manufacturer_count}/{len(processed_products)} ({manufacturer_count*100//len(processed_products)}%)")
    logger.info(f"    담당: {contact_count}/{len(processed_products)} ({contact_count*100//len(processed_products)}%)")
    logger.info(f"    Phone: {phone_count}/{len(processed_products)} ({phone_count*100//len(processed_products)}%)")
    logger.info(f"    Email: {email_count}/{len(processed_products)} ({email_count*100//len(processed_products)}%)")
    
    logger.info(f"\n  Images:")
    logger.info(f"    Products with images: {images_count}/{len(processed_products)} ({images_count*100//len(processed_products)}%)")
    logger.info(f"    Total images downloaded: {total_images}")
    logger.info(f"    Average per product: {total_images/len(processed_products):.1f}")
    
    logger.info(f"\n  Output: {output_file}")
    logger.info(f"  Images: {IMAGES_DIR}")
    logger.info(f"{'='*70}")

    return product_name_count >= len(processed_products) * 0.95

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
