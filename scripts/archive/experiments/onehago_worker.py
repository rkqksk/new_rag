#!/usr/bin/env python3
"""
Onehago Phase 2 Worker - Processes a specific chunk of URLs
Each worker handles 1,000 URLs independently
"""
import json
import requests
import sys
import time
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 onehago_worker.py <worker_id>")
        print("Example: python3 onehago_worker.py 90  # Processes URLs 90000-90999")
        sys.exit(1)

    worker_id = int(sys.argv[1])
    chunk_size = 1000
    start_line = worker_id * chunk_size
    end_line = start_line + chunk_size

    # Configuration
    INPUT_FILE = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/all_product_urls.jsonl')
    OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only')
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE = OUTPUT_DIR / f'worker_{worker_id:04d}_output.jsonl'

    # Setup session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    print(f"🚀 WORKER {worker_id} STARTING", flush=True)
    print(f"📊 Processing lines {start_line:,} to {end_line-1:,}", flush=True)
    print(f"📁 Output: {OUTPUT_FILE.name}", flush=True)
    print(f"⏱️  Started at {datetime.now().strftime('%H:%M:%S')}", flush=True)
    print("", flush=True)

    # Stream file and process chunk
    products_processed = 0
    products_success = 0
    products_failed = 0
    start_time = datetime.now()

    with open(INPUT_FILE, 'r') as infile, open(OUTPUT_FILE, 'w') as outfile:
        for line_num, line in enumerate(infile):
            # Skip until we reach our chunk
            if line_num < start_line:
                continue

            # Stop after our chunk
            if line_num >= end_line:
                break

            # Process this product
            try:
                product = json.loads(line)

                # Extract product details
                response = session.get(product['product_url'], timeout=30)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract product name
                pack_tit = soup.find('div', class_='pack_tit')
                product_name = pack_tit.get_text(strip=True) if pack_tit else ""

                # Extract all product specifications from dt/dd pairs
                pack_info = soup.find('div', class_='pack_info')

                # Initialize nested dictionaries and individual fields
                specifications = {}
                company_info = {}
                phone = ""
                fax = ""
                email = ""

                if pack_info:
                    # Extract all dt/dd pairs
                    dt_elements = pack_info.find_all('dt')
                    for dt in dt_elements:
                        label = dt.get_text(strip=True)
                        dd = dt.find_next_sibling('dd')
                        value = dd.get_text(strip=True) if dd else ""

                        # Map Korean labels to nested structures
                        if '코드' in label:
                            specifications['코드'] = value
                        elif '용량' in label:
                            specifications['용량'] = value
                        elif '사이즈' in label:
                            specifications['사이즈'] = value
                        elif 'MOQ' in label or '수량' in label:
                            specifications['MOQ'] = value
                        elif '재질' in label:
                            specifications['재질'] = value
                        elif '원산지' in label:
                            specifications['원산지'] = value
                        elif '제조사' in label:
                            company_info['제조사'] = value
                        elif '담당' in label:
                            company_info['담당'] = value
                        elif 'PHONE' in label or '전화' in label:
                            phone = value
                        elif 'FAX' in label:
                            fax = value
                        elif 'E MAIL' in label or 'EMAIL' in label or '이메일' in label:
                            email = value

                # Extract all image URLs from the page
                image_urls = []
                # Find all img tags in the page
                img_tags = soup.find_all('img')
                for img in img_tags:
                    src = img.get('src', '')
                    # Filter for product images (usually in productImages directory)
                    if src and 'productImages' in src:
                        # Make absolute URL if relative
                        if src.startswith('http'):
                            image_urls.append(src)
                        else:
                            image_urls.append(f"https://www.onehago.com{src}")

                # Remove duplicates while preserving order
                seen = set()
                unique_images = []
                for url in image_urls:
                    if url not in seen:
                        seen.add(url)
                        unique_images.append(url)

                # Write result with nested structure matching batch file
                result = {
                    **product,
                    'detail_crawled': True,
                    'detail_crawled_at': datetime.now().isoformat(),
                    'specifications': specifications,
                    'company_info': company_info,
                    'image_urls': unique_images,
                    'product_name': product_name,
                    'phone': phone,
                    'fax': fax,
                    'email': email,
                    'image_count': len(unique_images)
                }
                outfile.write(json.dumps(result, ensure_ascii=False) + '\n')
                outfile.flush()  # Ensure data is written immediately

                products_success += 1

            except Exception as e:
                result = {
                    **product,
                    'detail_crawled': False,
                    'error': str(e),
                    'worker_id': worker_id
                }
                outfile.write(json.dumps(result, ensure_ascii=False) + '\n')
                outfile.flush()

                products_failed += 1

            products_processed += 1

            # Progress logging every 100 products
            if products_processed % 100 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = products_processed / elapsed * 60 if elapsed > 0 else 0
                print(f"Worker {worker_id}: {products_processed:,}/1000 ({products_processed/10:.1f}%) | "
                      f"Rate: {rate:.0f}/min | Success: {products_success:,}", flush=True)

            # Rate limiting
            time.sleep(0.1)

    # Summary
    elapsed = datetime.now() - start_time
    print("", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"✅ WORKER {worker_id} COMPLETE", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"📊 Processed: {products_processed:,} products", flush=True)
    print(f"✅ Success: {products_success:,} ({products_success/products_processed*100:.1f}%)", flush=True)
    print(f"❌ Failed: {products_failed:,} ({products_failed/products_processed*100:.1f}%)", flush=True)
    print(f"⏱️  Time: {elapsed}", flush=True)
    print(f"📈 Rate: {products_processed / elapsed.total_seconds() * 60:.0f} products/min", flush=True)
    print(f"📁 Output: {OUTPUT_FILE}", flush=True)
    print(f"{'='*60}", flush=True)

    # Exit with success if we got >95% success rate
    success_rate = products_success / products_processed if products_processed > 0 else 0
    sys.exit(0 if success_rate > 0.95 else 1)

if __name__ == "__main__":
    main()
