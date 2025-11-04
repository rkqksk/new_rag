#!/usr/bin/env python3
"""
FREEMOLD REMOTE CHROME CRAWLER
Connects to existing Chrome instance at localhost:9222
Crawls ALL pages (1-1592) for category A001 using the persistent browser
"""

import json
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://www.freemold.net"
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("\n" + "="*80)
print("🚀 FREEMOLD REMOTE CHROME CRAWLER")
print("="*80)
print("Connecting to existing Chrome instance at localhost:9222...")
print("="*80 + "\n")

def connect_to_remote_chrome():
    """Connect to already-running Chrome instance"""
    try:
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "localhost:9222")
        driver = webdriver.Chrome(options=options)
        print("✅ Connected to remote Chrome instance!")
        return driver
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return None

# Connect to existing browser
driver = connect_to_remote_chrome()
if not driver:
    print("Cannot proceed without connection to Chrome")
    exit(1)

try:
    print("\n📋 PHASE 1: TEST PAGINATION ON A001")
    print("-" * 80)

    # Test page 1 first
    print("Testing page 1 (should show ~31 items)...")
    url = f"{BASE}/Front/Product/?tp=ma&CatA=A001&page=1"
    driver.get(url)
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    products_page1 = soup.select('[data-idx]')
    print(f"✅ Page 1: Found {len(products_page1)} product items")

    # Test page 10
    print("Testing page 10...")
    url = f"{BASE}/Front/Product/?tp=ma&CatA=A001&page=10"
    driver.get(url)
    time.sleep(1)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    products_page10 = soup.select('[data-idx]')
    print(f"✅ Page 10: Found {len(products_page10)} product items")

    # Test page 100
    print("Testing page 100...")
    url = f"{BASE}/Front/Product/?tp=ma&CatA=A001&page=100"
    driver.get(url)
    time.sleep(1)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    products_page100 = soup.select('[data-idx]')
    print(f"✅ Page 100: Found {len(products_page100)} product items")

    # Test page 1592 (your mentioned max)
    print("Testing page 1592 (max page)...")
    url = f"{BASE}/Front/Product/?tp=ma&CatA=A001&page=1592"
    driver.get(url)
    time.sleep(1)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    products_page1592 = soup.select('[data-idx]')
    print(f"✅ Page 1592: Found {len(products_page1592)} product items")

    print("\n📊 PHASE 2: ANALYZE PAGINATION PATTERN")
    print("-" * 80)

    if len(products_page1) > 0:
        items_per_page = len(products_page1)
        print(f"Items per page: ~{items_per_page}")
        print(f"Total pages: 1592")
        print(f"Estimated total: {items_per_page * 1592:,} products in A001 alone")
        print(f"× 7 categories = ~{items_per_page * 1592 * 7:,} total products")

    print("\n📋 PHASE 3: CRAWL ALL 1592 PAGES")
    print("-" * 80)
    print("Starting comprehensive crawl of all pages...")

    all_products = []
    seen_ids = set()
    errors = 0

    for page in range(1, 1593):  # 1 to 1592
        if page % 100 == 1 or page == 1:
            print(f"Progress: Pages {page}-{min(page+99, 1592)}...", end=" ", flush=True)

        try:
            url = f"{BASE}/Front/Product/?tp=ma&CatA=A001&page={page}"
            driver.get(url)
            time.sleep(0.3)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            product_links = soup.select('a[href*="pIdx="]')

            for link in product_links:
                try:
                    href = link.get('href', '')
                    if 'pIdx=' in href:
                        pid = href.split('pIdx=')[-1].split('&')[0]
                        if pid and pid not in seen_ids and pid.isdigit():
                            all_products.append({
                                'product_id': pid,
                                'category': 'A001',
                                'category_name': '프리몰드',
                                'url': urljoin(BASE, href),
                                'page': page
                            })
                            seen_ids.add(pid)
                except:
                    pass

            if page % 100 == 0:
                print(f"({len(all_products)} unique so far)")

        except Exception as e:
            errors += 1
            if page % 100 == 0:
                print(f"\n⚠️ Page {page} error")
            continue

        time.sleep(0.1)  # Rate limiting

    print(f"\n✅ Crawled all 1592 pages: {len(all_products)} unique products found!")
    print(f"Errors: {errors}")

    # Save results
    print("\n📋 PHASE 4: SAVE RESULTS")
    print("-" * 80)

    output_file = OUTPUT_DIR / "A001_all_pages_comprehensive.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for product in all_products:
            f.write(json.dumps(product, ensure_ascii=False) + "\n")

    summary = {
        "category": "A001",
        "category_name": "프리몰드",
        "total_pages": 1592,
        "products_discovered": len(all_products),
        "unique_product_ids": len(set(p['product_id'] for p in all_products)),
        "items_per_page": len(products_page1) if len(products_page1) > 0 else 0,
        "file": str(output_file)
    }

    summary_file = OUTPUT_DIR / "A001_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n📊 FINAL RESULTS FOR CATEGORY A001")
    print("=" * 80)
    print(f"✅ Total unique products discovered: {len(all_products)}")
    print(f"   Total pages crawled: 1592")
    print(f"   Unique IDs: {len(set(p['product_id'] for p in all_products))}")
    print(f"   File: {output_file}")
    print(f"\n💡 This means freemold has ~{len(all_products)} products just in A001!")
    print(f"   × 7 categories = ~{len(all_products) * 7:,} total products")
    print("=" * 80)

finally:
    driver.quit()
    print("\n✨ Crawling complete!")
