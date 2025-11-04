#!/usr/bin/env python3
"""
🚀 FREEMOLD.NET PHASE 2 - TEXT-ONLY PRODUCT EXTRACTION
=======================================================

Extracts all text content from product detail pages
- Uses product URLs from Phase 1
- Text-only extraction (no images yet)
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

# Setup logging
log_file = LOG_DIR / f"freemold_phase2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
# PHASE 2: EXTRACT PRODUCT TEXT DATA
# ============================================

def extract_product_text(product_url, product_id, category, category_name):
    """
    Extract text content from a single product detail page
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
        'contact': None,
        'tags': [],
        'images': [],  # Just URLs, not downloaded
        'related_products': []
    }

    try:
        # Disable SSL verification for freemold.net (certificate issue)
        response = requests.get(product_url, timeout=15, verify=False)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract product name
        # Try multiple selectors
        name_elem = soup.find('h1') or soup.find(class_='product_title') or soup.find(class_='product-name')
        if name_elem:
            product_data['name'] = name_elem.get_text(strip=True)[:500]

        # Extract from table structure (common in freemold)
        # Look for specification tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)

                    if '제품명' in label or 'product name' in label:
                        product_data['name'] = value[:500]
                    elif '규격' in label or 'specification' in label:
                        product_data['specs']['specification'] = value
                    elif '용량' in label or 'capacity' in label:
                        product_data['specs']['capacity'] = value
                    elif '재질' in label or 'material' in label:
                        product_data['specs']['material'] = value
                    elif '원산지' in label or 'origin' in label:
                        product_data['specs']['origin'] = value
                    elif '제조사' in label or 'manufacturer' in label:
                        product_data['manufacturer'] = value
                    elif '연락처' in label or 'contact' in label or '전화' in label:
                        product_data['contact'] = value
                    elif 'moq' in label or '최소' in label:
                        product_data['specs']['moq'] = value

        # Extract description (main content area)
        desc_elem = soup.find(class_=lambda x: x and any(k in x.lower() for k in ['description', 'content', 'detail', 'info']) if x else False)
        if not desc_elem:
            desc_elem = soup.find('div', {'style': lambda x: x and 'width' in x if x else False})

        if desc_elem:
            # Remove scripts and styles
            for script in desc_elem(['script', 'style']):
                script.decompose()

            description = desc_elem.get_text(separator='\n', strip=True)
            # Clean up excessive whitespace
            description = '\n'.join(line.strip() for line in description.split('\n') if line.strip())
            product_data['description'] = description[:5000]  # Limit to 5000 chars

        # Extract images (just URLs, don't download)
        img_tags = soup.find_all('img')
        for img in img_tags:
            img_src = img.get('src', '')
            if img_src and ('/Images/' in img_src or '/data/' in img_src):
                full_img_url = urljoin(BASE_URL, img_src)
                if full_img_url not in product_data['images']:
                    product_data['images'].append(full_img_url)

        # Extract tags/keywords (if present)
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            keywords = meta_keywords.get('content', '')
            product_data['tags'] = [k.strip() for k in keywords.split(',')][:10]

        # Extract related/similar products (links only)
        related_links = soup.find_all('a', href=lambda x: x and 'tp=vi&pIdx=' in str(x))
        for link in related_links:
            href = link.get('href', '')
            if href != product_url:  # Don't include self-link
                match = re.search(r'pIdx=(\d+)', href)
                if match:
                    related_id = match.group(1)
                    if related_id not in product_data['related_products']:
                        product_data['related_products'].append(related_id)

        return product_data

    except requests.Timeout:
        logger.warning(f"⏱️  Timeout extracting {product_id}")
        return None
    except Exception as e:
        logger.warning(f"⚠️  Error extracting {product_id}: {e}")
        return None

def extract_all_products(max_workers=8):
    """
    Extract text from all product URLs
    """

    logger.info("=" * 80)
    logger.info("🚀 FREEMOLD PHASE 2: TEXT EXTRACTION")
    logger.info("=" * 80)

    # Load product URLs
    if not URLS_FILE.exists():
        logger.error("❌ No product URLs file found. Run Phase 1 first.")
        return []

    product_urls = []
    with open(URLS_FILE, 'r') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                product_urls.append(data)
            except:
                pass

    logger.info(f"📥 Loaded {len(product_urls)} product URLs")

    # Load existing extracted products (resume capability)
    progress = load_progress()
    extracted_products = []
    extracted_ids = set()

    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    extracted_products.append(data)
                    extracted_ids.add(data['product_id'])
                except:
                    pass
        logger.info(f"📥 Loaded {len(extracted_products)} existing extracted products")

    # Extract remaining products
    remaining_urls = [u for u in product_urls if u['product_id'] not in extracted_ids]
    logger.info(f"🔄 Remaining to extract: {len(remaining_urls)}")

    checkpoint_interval = 500

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(extract_product_text, u['url'], u['product_id'], u['category'], u['category_name']): u['product_id']
            for u in remaining_urls
        }

        completed = len(extracted_products)

        for future in as_completed(futures):
            pid = futures[future]
            completed += 1

            try:
                result = future.result()
                if result:
                    extracted_products.append(result)

                    # Progress logging
                    if completed % 100 == 0:
                        rate = completed / ((time.time() - time.time()) or 1)  # Very rough, fix if needed
                        logger.info(f"📊 Progress: {completed}/{len(product_urls)} ({100*completed/len(product_urls):.1f}%)")

                    # Checkpoint every 500 products
                    if completed % checkpoint_interval == 0:
                        with open(OUTPUT_FILE, 'w') as f:
                            for prod in extracted_products:
                                f.write(json.dumps(prod, ensure_ascii=False) + '\n')

                        progress['products_extracted'] = len(extracted_products)
                        progress['last_product_id'] = pid
                        save_progress(progress)

                        logger.info(f"✅ Checkpoint: {len(extracted_products)} products saved")
                else:
                    progress['products_with_errors'] += 1

            except Exception as e:
                logger.warning(f"Error processing {pid}: {e}")
                progress['products_with_errors'] += 1

    return extracted_products

# ============================================
# SAVE RESULTS
# ============================================

def save_results(products):
    """Save final results and summary"""

    logger.info("=" * 80)
    logger.info("💾 SAVING RESULTS")
    logger.info("=" * 80)

    # Final save
    with open(OUTPUT_FILE, 'w') as f:
        for prod in products:
            f.write(json.dumps(prod, ensure_ascii=False) + '\n')

    logger.info(f"✅ Saved {len(products)} products to {OUTPUT_FILE}")

    # Generate summary
    summary = {
        'total_products': len(products),
        'products_with_description': len([p for p in products if p.get('description')]),
        'products_with_specs': len([p for p in products if p.get('specs')]),
        'products_with_manufacturer': len([p for p in products if p.get('manufacturer')]),
        'total_images_collected': sum(len(p.get('images', [])) for p in products),
        'crawl_date': datetime.now().isoformat(),
        'output_file': str(OUTPUT_FILE),
        'sample_products': products[:3] if products else []
    }

    with open(SUMMARY_FILE, 'w') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    logger.info(f"📊 Saved summary to {SUMMARY_FILE}")

    return OUTPUT_FILE

# ============================================
# MAIN EXECUTION
# ============================================

def main():
    start_time = time.time()

    try:
        logger.info("\n" + "=" * 80)
        logger.info("🚀 FREEMOLD PHASE 2: TEXT-ONLY PRODUCT EXTRACTION")
        logger.info("=" * 80)

        # Extract all products
        products = extract_all_products(max_workers=8)

        if not products:
            logger.error("❌ No products extracted")
            return

        logger.info(f"\n✅ Extraction complete: {len(products)} products")

        # Save results
        output_file = save_results(products)

        elapsed = time.time() - start_time

        logger.info("\n" + "=" * 80)
        logger.info("📊 FINAL STATISTICS")
        logger.info("=" * 80)
        logger.info(f"  - Total products extracted: {len(products)}")
        logger.info(f"  - With descriptions: {len([p for p in products if p.get('description')])}")
        logger.info(f"  - With manufacturer info: {len([p for p in products if p.get('manufacturer')])}")
        logger.info(f"  - Total image URLs found: {sum(len(p.get('images', [])) for p in products)}")
        logger.info(f"  - Execution time: {elapsed/3600:.1f} hours")
        logger.info(f"  - Output file: {output_file}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
