#!/usr/bin/env python3
"""
FREEMOLD CATEGORY 2 (A003) - PHASE 2 TEXT & IMAGE EXTRACTION
Extract text content and images from all Category 2 product URLs

Workflow:
  Input: product_urls_a003_complete.jsonl (all discovered A003 URLs)
  Process: Visit each product page, extract text and images
  Output: products_text_a003_complete.jsonl (text + specs + images + contact)

Features:
  - Selenium browser automation (avoids blocking)
  - HTML parsing with BeautifulSoup
  - Text extraction & regex parsing
  - Image collection & validation
  - Contact info parsing (phone, fax, email)
  - Progress tracking & resumable extraction
  - Error recovery with logging
"""

import json
import time
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging

# Configuration
CATEGORY = "A003"
INPUT_URLS_FILE = Path(f"/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/product_urls_{CATEGORY}_complete.jsonl")
OUTPUT_FILE = Path(f"/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/products_text_{CATEGORY}_complete.jsonl")
PROGRESS_FILE = Path(f"/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/phase2_{CATEGORY}_progress.json")

BASE_URL = "https://www.freemold.net"
MAX_IMAGES = 10  # Collect up to 10 images per product
REQUEST_TIMEOUT = 15  # Seconds to wait for page load
RATE_LIMIT = 0.5  # Seconds between requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'/tmp/freemold_phase2_{CATEGORY}_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

print("\n" + "="*80)
print(f"🔄 FREEMOLD CATEGORY {CATEGORY} - PHASE 2 TEXT & IMAGE EXTRACTION")
print("="*80)
print(f"Input URLs: {INPUT_URLS_FILE}")
print(f"Output: {OUTPUT_FILE}")
print(f"Progress tracking: {PROGRESS_FILE}")
print("="*80 + "\n")

def connect_to_chrome():
    """Connect to existing Chrome instance or create new one"""
    try:
        # Try to connect to existing Chrome remote debugging session
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "localhost:9222")
        driver = webdriver.Chrome(options=options)
        logger.info("✅ Connected to existing Chrome instance (localhost:9222)")
        return driver
    except Exception as e:
        logger.warning(f"⚠️ Could not connect to remote Chrome: {e}")
        logger.info("Creating new Chrome instance...")
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        driver = webdriver.Chrome(options=options)
        logger.info("✅ Created new Chrome instance")
        return driver

def extract_text_content(html, product_id):
    """Extract main text content from product page HTML - FREEMOLD.NET SPECIFIC"""
    soup = BeautifulSoup(html, 'html.parser')

    content = {
        'name': None,
        'description': None,
        'specs': {},
        'manufacturer': None,
        'contact': {},
    }

    try:
        # ✅ FIXED: Find all table rows with class 'detailTitle' and 'detailContent'
        # Freemold.net uses table structure: <td class="detailTitle">제품명</td> <td class="detailContent">Product Name</td>

        # Find all tables
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    # First cell contains the label (detailTitle class)
                    label_cell = cells[0]
                    value_cell = cells[1]

                    label_text = label_cell.get_text(strip=True).lower()
                    value_text = value_cell.get_text(strip=True)

                    if not value_text:
                        continue

                    # Extract product name
                    if '제품명' in label_text or '상품명' in label_text:
                        if not content['name']:  # Use first occurrence
                            content['name'] = value_text

                    # Extract specifications
                    elif '규격' in label_text or '사양' in label_text or '제품규격' in label_text:
                        spec_key = '규격/사양'
                        content['specs'][spec_key] = value_text

                    # Extract company/manufacturer
                    elif '제조사정보' in label_text or '회사' in label_text or '제조사' in label_text or '회사명' in label_text:
                        # Special handling for "제조사정보" which contains phone, fax, email in one cell
                        if '제조사정보' in label_text:
                            # Extract contact info from "제조사정보" cell
                            # Format: "전화 : 031-391-1773 / 팩스 : 031-394-1775 / ..."

                            # Extract phone
                            phone_match = re.search(r'전화\s*[:：]\s*([\d\-\\/]+)', value_text)
                            if phone_match:
                                phone_num = phone_match.group(1).strip()
                                if phone_num and phone_num != '/':
                                    content['contact']['phone'] = phone_num

                            # Extract fax
                            fax_match = re.search(r'팩스\s*[:：]\s*([\d\-\\/]+)', value_text)
                            if fax_match:
                                fax_num = fax_match.group(1).strip()
                                if fax_num and fax_num != '/':
                                    content['contact']['fax'] = fax_num

                            # Extract email
                            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', value_text)
                            if email_match:
                                email_addr = email_match.group(1).strip()
                                if email_addr:
                                    content['contact']['email'] = email_addr
                        else:
                            # Regular manufacturer field
                            if not content['manufacturer']:
                                content['manufacturer'] = value_text

                    # Fallback: Extract contact - phone (in case it's a separate row)
                    elif '전화' in label_text and '전화' not in '제조사정보':
                        phone_match = re.search(r'([\d\-\\/]+)', value_text)
                        if phone_match:
                            phone_num = phone_match.group(1).strip()
                            if phone_num:
                                content['contact']['phone'] = phone_num

                    # Fallback: Extract contact - fax (in case it's a separate row)
                    elif '팩스' in label_text:
                        fax_match = re.search(r'([\d\-\\/]+)', value_text)
                        if fax_match:
                            fax_num = fax_match.group(1).strip()
                            if fax_num:
                                content['contact']['fax'] = fax_num

                    # Fallback: Extract contact - email (in case it's a separate row)
                    elif '이메일' in label_text or '메일' in label_text:
                        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', value_text)
                        if email_match:
                            email_addr = email_match.group(1).strip()
                            if email_addr:
                                content['contact']['email'] = email_addr

                    # Extract description
                    elif '설명' in label_text or '상세' in label_text:
                        if not content['description']:
                            desc_text = value_text[:500] if len(value_text) > 10 else None
                            if desc_text:
                                content['description'] = desc_text

        logger.debug(f"✓ Extracted text from product {product_id}")
        return content

    except Exception as e:
        logger.warning(f"⚠️ Error extracting text from product {product_id}: {e}")
        return content

def extract_images(html, base_url):
    """Extract image URLs from product page - PRODUCT IMAGES ONLY"""
    soup = BeautifulSoup(html, 'html.parser')
    images = []

    try:
        # ✅ FIXED: Use 'product' substring strategy as suggested by user
        # Product images contain "/data/Product/" in their URL path (case-insensitive)
        # This filters out navigation, banner, and icon images effectively

        # Find all img tags
        img_tags = soup.find_all('img', limit=100)  # Scan all images

        for img in img_tags:
            img_url = img.get('src') or img.get('data-src')
            if img_url:
                # Convert relative URLs to absolute
                if not img_url.startswith('http'):
                    img_url = urljoin(base_url, img_url)

                # Check valid URL and extension
                if not (img_url.startswith('http') and any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])):
                    continue

                # ✅ PRODUCT IMAGE FILTER: Check for "product" in URL (case-insensitive)
                # Real product images from Freemold always have "/data/Product/" in the path
                if 'product' not in img_url.lower():
                    logger.debug(f"Skipped non-product image: {img_url[:80]}...")
                    continue

                # Avoid duplicates
                if img_url in images:
                    continue

                # Add product image
                images.append(img_url)

                if len(images) >= MAX_IMAGES:
                    break

        logger.debug(f"✓ Extracted {len(images)} product images (filtered by 'product' in URL)")
        return images

    except Exception as e:
        logger.warning(f"⚠️ Error extracting images: {e}")
        return images

def extract_product_data(driver, product_url, product_id, category, category_name):
    """Visit product URL and extract all data"""
    try:
        logger.info(f"Extracting: {product_id} from {product_url}")

        # Load page
        driver.get(product_url)

        # Wait for page to load
        time.sleep(REQUEST_TIMEOUT)

        # Get page source
        html = driver.page_source

        # Extract text content
        text_content = extract_text_content(html, product_id)

        # Extract images
        images = extract_images(html, BASE_URL)

        # Build product record
        product = {
            'product_id': product_id,
            'category': category,
            'category_name': category_name,
            'url': product_url,
            'extracted_at': datetime.now().isoformat(),
            'name': text_content['name'],
            'description': text_content['description'],
            'specs': text_content['specs'] if text_content['specs'] else None,
            'manufacturer': text_content['manufacturer'],
            'contact': text_content['contact'] if text_content['contact'] else None,
            'images': images,
            'extraction_success': True,
        }

        return product

    except Exception as e:
        logger.error(f"❌ Error extracting product {product_id}: {e}")
        # Return minimal record on error
        return {
            'product_id': product_id,
            'category': category,
            'category_name': category_name,
            'url': product_url,
            'extracted_at': datetime.now().isoformat(),
            'extraction_success': False,
            'error': str(e),
        }

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
    }

def save_progress(progress):
    """Save extraction progress"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def main():
    """Main extraction process"""

    # Load existing progress
    progress = load_progress()

    # Read input URLs
    urls_to_process = []
    with open(INPUT_URLS_FILE, 'r') as f:
        for line in f:
            try:
                record = json.loads(line)
                urls_to_process.append(record)
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Skipping invalid JSON line")
                continue

    progress['total_urls'] = len(urls_to_process)
    logger.info(f"Total URLs to process: {len(urls_to_process)}")

    # Connect to Chrome
    driver = connect_to_chrome()

    try:
        # Open output file for appending
        with open(OUTPUT_FILE, 'a', encoding='utf-8') as outfile:

            for idx, url_record in enumerate(urls_to_process, 1):
                product_id = url_record['product_id']
                product_url = url_record['url']
                category = url_record.get('category', 'unknown')
                category_name = url_record.get('category_name', 'Unknown')

                logger.info(f"\n[{idx}/{len(urls_to_process)}] Processing {product_id}...")

                # Extract product data
                product = extract_product_data(driver, product_url, product_id, category, category_name)

                # Write to output
                outfile.write(json.dumps(product, ensure_ascii=False) + '\n')
                outfile.flush()

                # Update progress
                progress['processed'] += 1
                progress['last_product_id'] = product_id
                if product.get('extraction_success', False):
                    progress['successful'] += 1
                else:
                    progress['failed'] += 1

                # Log progress every 100 products
                if idx % 100 == 0:
                    logger.info(f"Progress: {idx}/{len(urls_to_process)} ({progress['successful']} successful, {progress['failed']} failed)")
                    save_progress(progress)

                # Rate limiting
                time.sleep(RATE_LIMIT)

        # Final summary
        logger.info("\n" + "="*80)
        logger.info(f"✅ EXTRACTION COMPLETE FOR CATEGORY {CATEGORY}")
        logger.info("="*80)
        logger.info(f"Total processed: {progress['processed']}")
        logger.info(f"Successful: {progress['successful']}")
        logger.info(f"Failed: {progress['failed']}")
        logger.info(f"Output file: {OUTPUT_FILE}")
        logger.info("="*80)

        save_progress(progress)

    finally:
        driver.quit()
        logger.info("✨ Browser closed, extraction finished")

if __name__ == '__main__':
    main()
