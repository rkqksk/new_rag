#!/usr/bin/env python3
"""
FREEMOLD PHASE 2 - UNIVERSAL TEXT & IMAGE EXTRACTOR
Extract text content and images from all discovered product URLs
Scales to handle 47,000+ products per category

Workflow:
  Input: product_urls.jsonl (16,303+ URLs)
  Process: Visit each URL, extract text content and images
  Output: products_text_complete.jsonl (text + specs + images)

Features:
  - Selenium browser automation (avoiding blocking)
  - Text extraction from product pages
  - Image collection and validation
  - Specification parsing
  - Contact info extraction
  - Progress tracking and resumable extraction
  - Error recovery and logging
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
INPUT_URLS_FILE = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/product_urls.jsonl")
OUTPUT_FILE = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/products_text_complete.jsonl")
PROGRESS_FILE = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/phase2_extraction_progress.json")

BASE_URL = "https://www.freemold.net"
MAX_IMAGES = 10  # Collect up to 10 images per product
REQUEST_TIMEOUT = 15  # Seconds to wait for page load
RATE_LIMIT = 0.5  # Seconds between requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/freemold_phase2_extractor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

print("\n" + "="*80)
print("🔄 FREEMOLD PHASE 2 - UNIVERSAL TEXT & IMAGE EXTRACTOR")
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
    """Extract main text content from product page HTML"""
    soup = BeautifulSoup(html, 'html.parser')

    content = {
        'name': None,
        'description': None,
        'specs': {},
        'manufacturer': None,
        'contact': {},
    }

    try:
        # Extract product name
        name_elem = soup.find(['h1', 'h2', 'title'])
        if name_elem:
            content['name'] = name_elem.get_text(strip=True)

        # Extract specifications (look for specification blocks)
        spec_section = soup.find('div', {'class': re.compile(r'spec|detail|info', re.I)})
        if spec_section:
            # Extract all text from spec section
            spec_text = spec_section.get_text(strip=True)

            # Try to parse key-value pairs
            lines = spec_text.split('\n')
            for line in lines:
                if ':' in line:
                    key, val = line.split(':', 1)
                    key_clean = key.strip().lower().replace(' ', '_')
                    val_clean = val.strip()
                    if key_clean and val_clean:
                        content['specs'][key_clean] = val_clean

        # Extract contact information
        contact_section = soup.find('div', {'class': re.compile(r'contact|info', re.I)})
        if contact_section:
            contact_text = contact_section.get_text(strip=True)

            # Extract phone
            phone_match = re.search(r'전화\s*:?\s*([\d\-\/]+)', contact_text)
            if phone_match:
                content['contact']['phone'] = phone_match.group(1).strip()

            # Extract fax
            fax_match = re.search(r'팩스\s*:?\s*([\d\-\/]*)', contact_text)
            if fax_match:
                fax_val = fax_match.group(1).strip()
                if fax_val:
                    content['contact']['fax'] = fax_val

            # Extract email
            email_match = re.search(r'회사메일\s*:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', contact_text)
            if email_match:
                content['contact']['email'] = email_match.group(1).strip()

        # Extract manufacturer info (from page footer or company section)
        manufacturer_section = soup.find('div', {'class': re.compile(r'company|manufacturer|maker', re.I)})
        if manufacturer_section:
            content['manufacturer'] = manufacturer_section.get_text(strip=True)

        # Extract description (from main content area)
        desc_elem = soup.find(['p', 'div'], {'class': re.compile(r'description|content|main', re.I)})
        if desc_elem:
            desc_text = desc_elem.get_text(strip=True)
            if desc_text and len(desc_text) > 10:
                content['description'] = desc_text[:500]  # Limit to 500 chars

        logger.debug(f"✓ Extracted text from product {product_id}")
        return content

    except Exception as e:
        logger.warning(f"⚠️ Error extracting text from product {product_id}: {e}")
        return content

def extract_images(html, base_url):
    """Extract image URLs from product page"""
    soup = BeautifulSoup(html, 'html.parser')
    images = []

    try:
        # Find all img tags
        img_tags = soup.find_all('img', limit=MAX_IMAGES * 2)  # Get more than needed for filtering

        for img in img_tags:
            img_url = img.get('src') or img.get('data-src')
            if img_url:
                # Convert relative URLs to absolute
                if not img_url.startswith('http'):
                    img_url = urljoin(base_url, img_url)

                # Validate image URL
                if img_url.startswith('http') and any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    if img_url not in images:  # Avoid duplicates
                        images.append(img_url)

                    if len(images) >= MAX_IMAGES:
                        break

        logger.debug(f"Found {len(images)} images")
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
        logger.info("✅ EXTRACTION COMPLETE")
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
