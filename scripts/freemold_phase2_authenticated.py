#!/usr/bin/env python3
"""
🚀 FREEMOLD.NET PHASE 2 - AUTHENTICATED TEXT EXTRACTION
=========================================================

Extracts product text data with proper authentication
- Uses session cookies from cookies.json
- Extracts: name, description, specs, manufacturer, contact, images, related products
- Parallel extraction with 8 workers
- Smart checkpointing every 500 products
- Resume capability

"""

import json
import time
import logging
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ============================================
# CONFIGURATION
# ============================================

BASE_URL = "https://www.freemold.net"

# Output directories
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Files
URLS_FILE = OUTPUT_DIR / "product_urls.jsonl"
OUTPUT_FILE = OUTPUT_DIR / "products_text_complete.jsonl"
PROGRESS_FILE = OUTPUT_DIR / "freemold_phase2_progress.json"
SUMMARY_FILE = OUTPUT_DIR / "freemold_extraction_summary.json"
COOKIES_FILE = Path("/Users/oypnus/Project/rag-enterprise/cookies.json")

# Setup logging
log_file = LOG_DIR / f"freemold_phase2_authenticated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# LOAD COOKIES
# ============================================

def load_cookies():
    """Load cookies from cookies.json"""
    if COOKIES_FILE.exists():
        with open(COOKIES_FILE, 'r') as f:
            cookies_list = json.load(f)
            cookies = {}
            for cookie in cookies_list:
                cookies[cookie['name']] = cookie['value']
            logger.info(f"✅ Loaded {len(cookies)} cookies: {', '.join(cookies.keys())}")
            return cookies
    logger.error("❌ cookies.json not found!")
    return {}

# ============================================
# PROGRESS TRACKING
# ============================================

def load_progress():
    """Load progress from checkpoint file"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'phase': 'extraction',
        'products_extracted': 0,
        'products_with_errors': 0,
        'last_product_id': None,
        'start_time': datetime.now().isoformat()
    }

def save_progress(progress):
    """Save progress to checkpoint file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

# ============================================
# PHASE 2: EXTRACT PRODUCT TEXT DATA (AUTHENTICATED)
# ============================================

def extract_product_text(product_url, product_id, category, category_name, cookies):
    """
    Extract text content from a single product detail page (with authentication)
    """

    product_data = {
        'product_id': product_id,
        'url': product_url,
        'category': category,
        'category_name': category_name,
        'crawled_at': datetime.now().isoformat(),
        'name': None,
        'description': None,
        'specs': {},
        'manufacturer': None,
        'supplier': None,
        'contact': None,
        'tags': [],
        'images': [],
        'related_products': []
    }

    try:
        # Use authenticated request with cookies
        response = requests.get(
            product_url,
            cookies=cookies,
            timeout=15,
            verify=False,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        response.encoding = 'utf-8'

        # Check if we got redirected to login page
        if '비회원은' in response.text or 'alert' in response.text.lower() and 'login' in response.text.lower():
            logger.warning(f"⚠️  Product {product_id}: Still getting login redirect, cookies may be expired")
            return product_data

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract product name - try multiple selectors
        name_elem = soup.find('h1') or soup.find(class_=lambda x: x and 'title' in x.lower() if x else False)
        if name_elem:
            product_data['name'] = name_elem.get_text(strip=True)[:500]

        # Extract all text content
        main_content = soup.find('div', class_=lambda x: x and any(k in x.lower() for k in ['content', 'detail', 'body', 'main']) if x else False)
        if not main_content:
            main_content = soup.find('div', {'id': lambda x: x and 'content' in x.lower() if x else False})

        if main_content:
            # Get all paragraphs and text
            for p in main_content.find_all(['p', 'div', 'span'], limit=20):
                text = p.get_text(strip=True)
                if text and len(text) > 10:
                    if not product_data['description']:
                        product_data['description'] = text[:2000]
                    elif len(product_data['description']) < 3000:
                        product_data['description'] += '\n' + text[:500]

        # Extract from table structure
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)

                    if '제품명' in label or 'product name' in label or '상품명' in label:
                        product_data['name'] = value[:500]
                    elif '규격' in label or 'specification' in label or '스펙' in label:
                        product_data['specs']['specification'] = value
                    elif '용량' in label or 'capacity' in label or '사이즈' in label or 'size' in label:
                        product_data['specs']['capacity'] = value
                    elif '재질' in label or 'material' in label:
                        product_data['specs']['material'] = value
                    elif '원산지' in label or 'origin' in label or '제조국' in label:
                        product_data['specs']['origin'] = value
                    elif '제조사' in label or '판매처' in label or '공급업체' in label or 'manufacturer' in label or 'supplier' in label:
                        if 'supplier' in label:
                            product_data['supplier'] = value
                        else:
                            product_data['manufacturer'] = value
                    elif '연락처' in label or 'contact' in label or '전화' in label or '이메일' in label or '핸드폰' in label:
                        product_data['contact'] = value
                    elif 'moq' in label or '최소' in label or '주문' in label:
                        product_data['specs']['moq'] = value
                    elif '색상' in label or 'color' in label or 'colour' in label:
                        product_data['specs']['color'] = value
                    elif '형태' in label or 'shape' in label or '형상' in label:
                        product_data['specs']['shape'] = value

        # Extract image URLs
        images = soup.find_all('img', src=lambda x: x and ('product' in x.lower() or 'image' in x.lower() or 'pic' in x.lower()) if x else False)
        for img in images[:10]:  # Limit to first 10 images
            img_url = img.get('src', '')
            if img_url and not img_url.startswith('data:'):
                if not img_url.startswith('http'):
                    img_url = urljoin(BASE_URL, img_url)
                product_data['images'].append(img_url)

        # Extract tags/keywords
        keywords = soup.find_all('meta', attrs={'name': 'keywords'})
        for keyword in keywords:
            content = keyword.get('content', '')
            if content:
                product_data['tags'] = [k.strip() for k in content.split(',')][:10]

        # Extract related products
        related = soup.find_all('a', href=lambda x: x and 'pIdx=' in x if x else False)
        for link in related[:5]:  # Limit to first 5
            href = link.get('href', '')
            if href and href != product_url:
                product_data['related_products'].append(href)

    except Exception as e:
        logger.warning(f"⚠️  Error extracting {product_id}: {str(e)[:100]}")

    return product_data

# ============================================
# MAIN EXTRACTION LOOP
# ============================================

def main():
    logger.info("=" * 80)
    logger.info("🚀 FREEMOLD PHASE 2 - AUTHENTICATED TEXT EXTRACTION")
    logger.info("=" * 80)

    # Load cookies
    cookies = load_cookies()
    if not cookies:
        logger.error("❌ No cookies found! Cannot authenticate.")
        return

    # Load progress
    progress = load_progress()
    start_index = progress['products_extracted']

    logger.info(f"\n📊 Starting extraction from product {start_index}")

    # Load product URLs
    products = []
    if URLS_FILE.exists():
        with open(URLS_FILE, 'r') as f:
            for i, line in enumerate(f):
                if i >= start_index:
                    data = json.loads(line)
                    products.append(data)
    else:
        logger.error(f"❌ {URLS_FILE} not found!")
        return

    logger.info(f"📦 Loaded {len(products)} products to extract")

    # Open output file for appending
    with open(OUTPUT_FILE, 'a') as out_f:
        extracted_count = 0
        error_count = 0

        # Use ThreadPoolExecutor for parallel extraction
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {}

            # Submit all tasks
            for product in products:
                future = executor.submit(
                    extract_product_text,
                    product['url'],
                    product['product_id'],
                    product['category'],
                    product['category_name'],
                    cookies
                )
                futures[future] = product

            # Process completed tasks
            for future in as_completed(futures):
                product = futures[future]
                try:
                    result = future.result()

                    # Write to output file
                    out_f.write(json.dumps(result, ensure_ascii=False) + '\n')
                    out_f.flush()

                    extracted_count += 1

                    if result['name']:
                        logger.info(f"✅ {product['product_id']}: {result['name'][:50]}")
                    else:
                        logger.warning(f"⚠️  {product['product_id']}: No name extracted")
                        error_count += 1

                    # Checkpoint every 500 products
                    if extracted_count % 500 == 0:
                        progress['products_extracted'] = start_index + extracted_count
                        progress['products_with_errors'] = error_count
                        progress['last_product_id'] = product['product_id']
                        save_progress(progress)
                        logger.info(f"📊 Progress: {extracted_count}/{len(products)} ({100*extracted_count//len(products)}%)")
                        logger.info(f"✅ Checkpoint: {extracted_count} products saved")

                except Exception as e:
                    logger.error(f"❌ Error processing {product['product_id']}: {e}")
                    error_count += 1

        # Final summary
        logger.info(f"\n" + "=" * 80)
        logger.info(f"✅ EXTRACTION COMPLETE")
        logger.info(f"=" * 80)
        logger.info(f"📊 Total extracted: {extracted_count}")
        logger.info(f"⚠️  Errors: {error_count}")
        logger.info(f"📁 Output: {OUTPUT_FILE}")

        # Save final summary
        summary = {
            'total_processed': len(products),
            'successfully_extracted': extracted_count,
            'errors': error_count,
            'start_time': progress['start_time'],
            'end_time': datetime.now().isoformat(),
            'success_rate': f"{100*extracted_count/len(products):.1f}%"
        }
        with open(SUMMARY_FILE, 'w') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # Update final progress
        progress['products_extracted'] = start_index + extracted_count
        progress['products_with_errors'] = error_count
        progress['phase'] = 'extraction_complete'
        save_progress(progress)

if __name__ == "__main__":
    main()
