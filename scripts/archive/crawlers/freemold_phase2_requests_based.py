#!/usr/bin/env python3
"""
🚀 FREEMOLD PHASE 2 - PRODUCTION EXTRACTION (Requests + BeautifulSoup)

Architecture: Based on onehago's proven phase2_production_text_only.py pattern
- Fast: requests library + concurrent.futures (10 workers)
- Reliable: BeautifulSoup HTML parsing with regex field extraction
- Quality: Table-based extraction for Freemold's specific HTML structure
- Resumable: Progress tracking with checkpoint files
- Output: Text-only (URLs only, no image downloads)
"""

import json
import logging
import requests
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import time

# ============================================
# CONFIGURATION
# ============================================

BASE_URL = "https://www.freemold.net"
PRODUCT_PAGE_TEMPLATE = "https://www.freemold.net/Front/Product/?tp=vi&pIdx={}"

DATA_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled")
DATA_DIR.mkdir(parents=True, exist_ok=True)

URLS_FILE = DATA_DIR / "product_urls_A003_complete.jsonl"
OUTPUT_DIR = DATA_DIR / "products_text_production"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PROGRESS_FILE = DATA_DIR / "freemold_phase2_requests_progress.json"

# Extraction config
WORKERS = 10
REQUEST_TIMEOUT = 8
REQUEST_DELAY = 0.5
BATCH_SIZE = 500

# Setup logging
log_file = DATA_DIR / f"freemold_phase2_requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# HTTP Session with connection pooling
session = requests.Session()
# Disable SSL verification for self-signed certificates
session.verify = False
# Suppress warnings about SSL verification
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10)
session.mount('https://', adapter)
session.mount('http://', adapter)

# ============================================
# EXTRACTION FUNCTIONS (Based on onehago pattern)
# ============================================

def extract_text_content(html, product_id):
    """
    Extract product text content from Freemold HTML
    Adapted from onehago's regex-based field extraction pattern
    """
    soup = BeautifulSoup(html, 'html.parser')

    details = {
        'product_name': None,
        'specifications': {},
        'company_info': {},
        'contact': {},
        'image_urls': []
    }

    try:
        # 1. Extract from tables (Freemold-specific structure)
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label_cell = cells[0]
                    value_cell = cells[1]

                    label_text = label_cell.get_text(strip=True).lower()
                    value_text = value_cell.get_text(strip=True)

                    if not value_text:
                        continue

                    # Product name extraction
                    if '제품명' in label_text or '상품명' in label_text:
                        if not details['product_name']:
                            details['product_name'] = value_text

                    # Specifications extraction
                    elif any(x in label_text for x in ['규격', '사양', '스펙']):
                        spec_key = label_text.replace(':', '').strip()
                        details['specifications'][spec_key] = value_text

                    # Company info extraction
                    elif any(x in label_text for x in ['제조사', '회사', '판매처']):
                        if not details['company_info'].get('제조사'):
                            details['company_info']['제조사'] = value_text

                    # ⭐ CRITICAL: Handle combined "제조사정보" cell (Freemold specific)
                    # This cell contains phone|fax|email separated by slashes and Korean labels
                    if '제조사정보' in label_text:
                        # Extract phone: "전화 : 031-391-1773"
                        phone_match = re.search(r'전화\s*[:：]\s*([\d\-\\/]+)', value_text)
                        if phone_match:
                            phone_num = phone_match.group(1).strip()
                            if phone_num and phone_num != '/':
                                details['contact']['phone'] = phone_num

                        # Extract fax: "팩스 : 031-394-1775"
                        fax_match = re.search(r'팩스\s*[:：]\s*([\d\-\\/]+)', value_text)
                        if fax_match:
                            fax_num = fax_match.group(1).strip()
                            if fax_num and fax_num != '/':
                                details['contact']['fax'] = fax_num

                        # Extract email: standard email regex
                        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', value_text)
                        if email_match:
                            email_addr = email_match.group(1).strip()
                            if email_addr:
                                details['contact']['email'] = email_addr

                    # Fallback: Extract separate contact fields if not in combined cell
                    elif '전화' in label_text:
                        phone_match = re.search(r'([\d\-\\/]+)', value_text)
                        if phone_match and not details['contact'].get('phone'):
                            phone_num = phone_match.group(1).strip()
                            if phone_num:
                                details['contact']['phone'] = phone_num

                    elif '팩스' in label_text:
                        fax_match = re.search(r'([\d\-\\/]+)', value_text)
                        if fax_match and not details['contact'].get('fax'):
                            fax_num = fax_match.group(1).strip()
                            if fax_num:
                                details['contact']['fax'] = fax_num

                    elif '이메일' in label_text or '메일' in label_text:
                        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', value_text)
                        if email_match and not details['contact'].get('email'):
                            email_addr = email_match.group(1).strip()
                            if email_addr:
                                details['contact']['email'] = email_addr

        logger.debug(f"✓ Text content extracted from product {product_id}")

    except Exception as e:
        logger.warning(f"⚠️  Error extracting text from {product_id}: {e}")

    return details

def extract_image_urls(html):
    """
    Extract product image URLs from Freemold HTML
    Using: "product" substring filter (user's hint)
    Only URLs containing "product" (case-insensitive) are product images
    """
    soup = BeautifulSoup(html, 'html.parser')
    image_urls = []

    try:
        img_tags = soup.find_all('img', limit=100)

        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if not src:
                continue

            # Convert relative URLs to absolute
            if not src.startswith('http'):
                src = urljoin(BASE_URL, src)

            # ⭐ FILTER: Only product images (contain "product" substring)
            # This filters out: /BannerImg/, /Icon/, /images/icon, etc.
            if 'product' not in src.lower():
                continue

            # Check valid image extension
            if not any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                continue

            # Avoid duplicates
            if src not in image_urls:
                image_urls.append(src)
                if len(image_urls) >= 10:  # Max 10 images per product
                    break

        logger.debug(f"✓ Extracted {len(image_urls)} product images (filtered by 'product')")

    except Exception as e:
        logger.warning(f"⚠️  Error extracting images: {e}")

    return image_urls

def fetch_and_extract(product_id, product_url, category, category_name):
    """
    Fetch product page and extract all text data
    Returns: dict with extraction results or None on error
    """
    try:
        # Fetch page
        response = session.get(product_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        # Extract text content
        text_content = extract_text_content(response.text, product_id)

        # Extract image URLs
        image_urls = extract_image_urls(response.text)

        # Build product record
        product = {
            'product_id': product_id,
            'category': category,
            'category_name': category_name,
            'url': product_url,
            'extracted_at': datetime.now().isoformat(),
            'name': text_content['product_name'],
            'specifications': text_content['specifications'] if text_content['specifications'] else None,
            'company_info': text_content['company_info'] if text_content['company_info'] else None,
            'contact': text_content['contact'] if text_content['contact'] else None,
            'image_urls': image_urls if image_urls else None,
            'extraction_success': True,
        }

        return product

    except Exception as e:
        logger.warning(f"⚠️  Error fetching product {product_id}: {e}")
        return {
            'product_id': product_id,
            'category': category,
            'category_name': category_name,
            'url': product_url,
            'extracted_at': datetime.now().isoformat(),
            'extraction_success': False,
            'error': str(e)
        }

# ============================================
# PROGRESS TRACKING
# ============================================

def load_progress():
    """Load extraction progress"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'total_urls': 0,
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'last_product_id': None,
        'start_time': datetime.now().isoformat()
    }

def save_progress(progress):
    """Save extraction progress"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

# ============================================
# MAIN EXTRACTION PIPELINE
# ============================================

def main():
    """Main extraction process"""

    logger.info("\n" + "=" * 80)
    logger.info("🚀 FREEMOLD PHASE 2 - PRODUCTION TEXT EXTRACTION")
    logger.info("=" * 80)
    logger.info(f"Architecture: Requests + BeautifulSoup (concurrent: {WORKERS} workers)")
    logger.info(f"Output: {OUTPUT_DIR}/")
    logger.info("=" * 80 + "\n")

    # Load progress
    progress = load_progress()

    # Read product URLs
    products = []
    with open(URLS_FILE, 'r') as f:
        for line in f:
            try:
                record = json.loads(line)
                products.append(record)
            except json.JSONDecodeError:
                logger.warning("⚠️  Skipping invalid JSON line")
                continue

    progress['total_urls'] = len(products)
    logger.info(f"📊 Total products to extract: {len(products)}")
    logger.info(f"⏱️  Estimated time: ~{len(products) * 0.5 / 60:.1f} minutes ({WORKERS} workers)")
    logger.info("")

    # Extract in batches using ThreadPoolExecutor
    batch_num = 1
    batch_products = []

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:

        # Submit all tasks
        future_to_product = {}
        for idx, product_info in enumerate(products, 1):
            product_id = product_info['product_id']
            product_url = PRODUCT_PAGE_TEMPLATE.format(product_id)
            category = product_info.get('category', 'unknown')
            category_name = product_info.get('category_name', 'Unknown')

            future = executor.submit(fetch_and_extract, product_id, product_url, category, category_name)
            future_to_product[future] = (idx, product_id)

            # Rate limiting
            time.sleep(REQUEST_DELAY / WORKERS)

        # Process results as they complete
        batch_file = OUTPUT_DIR / f"batch_{batch_num:05d}.jsonl"
        batch_file_handle = open(batch_file, 'w', encoding='utf-8')

        for future in as_completed(future_to_product):
            idx, product_id = future_to_product[future]

            try:
                result = future.result()
                batch_products.append(result)

                # Write to batch file
                batch_file_handle.write(json.dumps(result, ensure_ascii=False) + '\n')
                batch_file_handle.flush()

                # Update progress
                progress['processed'] += 1
                progress['last_product_id'] = product_id
                if result.get('extraction_success', False):
                    progress['successful'] += 1
                else:
                    progress['failed'] += 1

                # Log progress
                if progress['processed'] % 50 == 0:
                    rate = (progress['processed'] / (time.time() - datetime.fromisoformat(progress['start_time']).timestamp())) if progress['start_time'] else 0
                    logger.info(f"Progress: {progress['processed']}/{progress['total_urls']} | ✅ {progress['successful']} | ❌ {progress['failed']} | Rate: {rate:.1f} products/sec")
                    save_progress(progress)

                # Batch rotation
                if len(batch_products) >= BATCH_SIZE:
                    batch_file_handle.close()
                    logger.info(f"✅ Batch {batch_num} complete ({BATCH_SIZE} products)")
                    batch_num += 1
                    batch_products = []
                    batch_file = OUTPUT_DIR / f"batch_{batch_num:05d}.jsonl"
                    batch_file_handle = open(batch_file, 'w', encoding='utf-8')

            except Exception as e:
                logger.error(f"❌ Task failed for product {product_id}: {e}")
                progress['failed'] += 1

        # Close final batch file
        batch_file_handle.close()
        if batch_products:
            logger.info(f"✅ Batch {batch_num} complete ({len(batch_products)} products)")

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("✅ EXTRACTION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total processed: {progress['processed']}")
    logger.info(f"Successful: {progress['successful']} ({100*progress['successful']/progress['processed']:.1f}%)")
    logger.info(f"Failed: {progress['failed']} ({100*progress['failed']/progress['processed']:.1f}%)")
    logger.info(f"Output directory: {OUTPUT_DIR}/")
    logger.info(f"Progress file: {PROGRESS_FILE}")
    logger.info("=" * 80)

    save_progress(progress)
    session.close()

if __name__ == '__main__':
    main()
