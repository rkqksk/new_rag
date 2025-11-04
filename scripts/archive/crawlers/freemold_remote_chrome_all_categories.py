#!/usr/bin/env python3
"""
FREEMOLD REMOTE CHROME CRAWLER - ALL CATEGORIES
Connects to existing Chrome instance at localhost:9222
Crawls ALL pages for ALL 7 categories to discover complete product dataset
Expected: ~47,000 products per category × 7 = ~329,000 total
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

# All 7 categories
CATEGORIES = {
    "A001": "프리몰드",
    "A003": "패키징/포장재",
    "A004": "후가공/임가공",
    "A006": "원료",
    "A007": "인증/임상기관",
    "A008": "금형/기계/시공",
    "A009": "디자인/마케팅"
}

print("\n" + "="*80)
print("🚀 FREEMOLD REMOTE CHROME CRAWLER - ALL CATEGORIES")
print("="*80)
print(f"Categories: {len(CATEGORIES)}")
print(f"Expected: ~47,000 items per category = ~{len(CATEGORIES) * 47000:,} total")
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

all_products_by_category = {}

try:
    print("\n📋 COMPREHENSIVE CRAWL: ALL 7 CATEGORIES")
    print("-" * 80)

    for category_code, category_name in CATEGORIES.items():
        print(f"\n🔄 Crawling {category_name} ({category_code}): pages 1-1592")
        print("-" * 80)

        category_products = []
        seen_ids = set()
        errors = 0

        # Crawl all 1592 pages for this category
        for page in range(1, 1593):  # 1 to 1592
            if page % 100 == 1 or page == 1:
                print(f"  Progress: Pages {page}-{min(page+99, 1592)}...", end=" ", flush=True)

            try:
                url = f"{BASE}/Front/Product/?tp=ma&CatA={category_code}&page={page}"
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
                                category_products.append({
                                    'product_id': pid,
                                    'category': category_code,
                                    'category_name': category_name,
                                    'url': urljoin(BASE, href),
                                    'page': page
                                })
                                seen_ids.add(pid)
                    except:
                        pass

                if page % 100 == 0:
                    print(f"({len(category_products)} unique so far)")

            except Exception as e:
                errors += 1
                if page % 100 == 0:
                    print(f"\n  ⚠️ Page {page} error")
                continue

            time.sleep(0.1)  # Rate limiting

        print(f"\n  ✅ Crawled 1592 pages: {len(category_products)} unique products found!")
        print(f"     Errors: {errors}")

        all_products_by_category[category_code] = category_products

    print("\n📋 PHASE 4: SAVE RESULTS")
    print("-" * 80)

    # Combine all products
    all_products = []
    for category_code, products in all_products_by_category.items():
        all_products.extend(products)

    # Save combined results
    output_file = OUTPUT_DIR / "all_products_all_categories_comprehensive.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for product in all_products:
            f.write(json.dumps(product, ensure_ascii=False) + "\n")

    # Save summary by category
    summary = {
        "total_products": len(all_products),
        "total_categories": len(CATEGORIES),
        "categories": CATEGORIES,
        "products_by_category": {
            category_code: len(all_products_by_category.get(category_code, []))
            for category_code in CATEGORIES.keys()
        },
        "file": str(output_file)
    }

    summary_file = OUTPUT_DIR / "all_categories_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n📊 FINAL STATISTICS")
    print("==" * 40)
    print(f"✅ Total unique products discovered: {len(all_products):,}")
    print(f"   Categories processed: {len(CATEGORIES)}")
    print(f"   Total pages crawled: {1592 * len(CATEGORIES):,}")
    print(f"   File: {output_file}")
    print(f"\n📈 Products by Category:")

    for category_code in CATEGORIES.keys():
        count = len(all_products_by_category.get(category_code, []))
        category_name = CATEGORIES[category_code]
        print(f"   {category_name}: {count:,} products")

    print("=" * 80)

finally:
    driver.quit()
    print("\n✨ Crawling complete!")
