#!/usr/bin/env python3
"""
FREEMOLD SELENIUM COMPREHENSIVE CRAWLER
Use browser automation to crawl ALL pages for all 7 categories
Discovers complete product dataset: ~47,000 per category × 7 = ~329,000 total
"""

import json
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://www.freemold.net"
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
print("🚀 FREEMOLD SELENIUM COMPREHENSIVE CRAWLER")
print("="*80)
print(f"Categories: {len(CATEGORIES)}")
print(f"Expected: ~47,000 items per category = ~329,000 total")
print("="*80 + "\n")

def setup_selenium_driver():
    """Setup Selenium with Chrome"""
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Chrome(options=options)
        print("✅ Selenium Chrome driver initialized")
        return driver
    except Exception as e:
        print(f"❌ Failed to initialize Selenium: {e}")
        return None

def discover_max_pages_selenium(driver, category_code, category_name):
    """Discover maximum pages using Selenium"""
    print(f"\n📊 Discovering max pages for {category_name}...")

    max_page = 1
    test_pages = [10, 50, 100, 500, 1000, 1500, 1592, 2000]

    for test_page in test_pages:
        try:
            url = f"{BASE}/Front/Product/?tp=ma&CatA={category_code}&page={test_page}"
            driver.get(url)
            time.sleep(1)

            # Check if page has products
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            products = soup.select('[data-idx]')

            if len(products) > 0:
                max_page = test_page
                print(f"  ✅ Page {test_page}: {len(products)} items found")
            else:
                print(f"  ⚠️  Page {test_page}: Empty (exceeds max)")
                break

        except Exception as e:
            print(f"  ❌ Page {test_page}: Error - {str(e)[:40]}")
            break

        time.sleep(0.5)

    print(f"  Result: Maximum page = {max_page}")
    return max_page

def crawl_category_all_pages_selenium(driver, category_code, category_name, max_pages):
    """Crawl all pages for a category using Selenium"""
    print(f"\n🔄 Crawling {category_name} ({category_code}): pages 1-{max_pages}")

    all_products = []
    seen_ids = set()

    for page in range(1, min(max_pages + 1, 2000)):  # Safety limit
        url = f"{BASE}/Front/Product/?tp=ma&CatA={category_code}&page={page}"

        if page % 100 == 1 or page == 1:
            print(f"  Progress: Pages {page}-{min(page+99, max_pages)}...", end=" ", flush=True)

        try:
            driver.get(url)
            time.sleep(0.5)

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Extract product links
            product_links = soup.select('a[href*="pIdx="]')

            for link in product_links:
                try:
                    href = link.get('href', '')
                    # Extract product ID
                    if 'pIdx=' in href:
                        pid = href.split('pIdx=')[-1].split('&')[0]
                        if pid and pid not in seen_ids and pid.isdigit():
                            all_products.append({
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
                print(f"({len(all_products)} unique products so far)")

        except Exception as e:
            if page % 100 == 0:
                print(f"\n  ❌ Page {page} error: {str(e)[:40]}")
            continue

        time.sleep(0.2)

    print(f"\n  ✅ Crawled {max_pages} pages: {len(all_products)} unique products")
    return all_products

# Main execution
driver = setup_selenium_driver()
if not driver:
    print("❌ Cannot proceed without Selenium driver")
    exit(1)

try:
    print("\n📋 PHASE 1: DISCOVER PAGE DEPTHS")
    print("-" * 80)

    category_pages = {}
    for cat_code, cat_name in CATEGORIES.items():
        max_pages = discover_max_pages_selenium(driver, cat_code, cat_name)
        category_pages[cat_code] = max_pages

    print("\n📋 PHASE 2: CRAWL ALL CATEGORIES")
    print("-" * 80)

    all_products = []
    for cat_code, cat_name in CATEGORIES.items():
        max_pages = category_pages.get(cat_code, 1)
        products = crawl_category_all_pages_selenium(driver, cat_code, cat_name, max_pages)
        all_products.extend(products)

    print("\n📋 PHASE 3: SAVE RESULTS")
    print("-" * 80)

    # Save products
    output_file = OUTPUT_DIR / "products_comprehensive_all_pages.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for product in all_products:
            f.write(json.dumps(product, ensure_ascii=False) + "\n")

    # Save summary
    summary = {
        "total_products_discovered": len(all_products),
        "categories": CATEGORIES,
        "page_counts": category_pages,
        "total_pages": sum(category_pages.values()),
        "file": str(output_file)
    }

    summary_file = OUTPUT_DIR / "comprehensive_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n📊 FINAL STATISTICS")
    print("=" * 80)
    print(f"✅ Total unique products discovered: {len(all_products)}")
    print(f"   Categories processed: {len(CATEGORIES)}")
    print(f"   Total pages crawled: {sum(category_pages.values())}")
    print(f"   File: {output_file}")
    print(f"\nCategory breakdown:")
    for cat_code, cat_name in CATEGORIES.items():
        pages = category_pages.get(cat_code, 0)
        print(f"   {cat_name}: {pages} pages")
    print("=" * 80)

finally:
    driver.quit()
    print("\n✅ Browser closed")
    print("🎉 Crawling complete!")
