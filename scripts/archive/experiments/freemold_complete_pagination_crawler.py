#!/usr/bin/env python3
"""
FREEMOLD COMPREHENSIVE PAGINATION CRAWLER
Crawl ALL pages (1 to max) for all 7 categories
User discovered: A001 has 1,592 pages with ~47,000 items
This crawler will discover ALL products across ALL categories
"""

import json
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from urllib.parse import urljoin

BASE = "https://www.freemold.net"
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = {
    "A001": "프리몰드 (Premold)",
    "A003": "패키징/포장재",
    "A004": "후가공/임가공",
    "A006": "원료",
    "A007": "인증/임상기관",
    "A008": "금형/기계/시공",
    "A009": "디자인/마케팅"
}

print("\n" + "="*80)
print("🚀 FREEMOLD COMPLETE PAGINATION CRAWLER")
print("="*80)
print(f"Target: ALL pages across {len(CATEGORIES)} categories")
print(f"Expected: ~47,000 items per category = ~329,000 total")
print("="*80 + "\n")

def discover_max_pages(category_code, category_name):
    """Discover maximum page number for a category"""
    print(f"\n📊 Discovering max pages for {category_name} ({category_code})...")

    # Try common high page numbers to find the limit
    test_pages = [10, 50, 100, 500, 1000, 1500, 1592, 2000, 3000, 5000]
    max_page = 1

    for page in test_pages:
        url = f"{BASE}/Front/Product/?tp=ma&CatA={category_code}&page={page}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Check if page has products
                products = soup.select('[data-idx]')
                if len(products) > 0:
                    max_page = max(max_page, page)
                    print(f"  ✅ Page {page}: {len(products)} items found")
                else:
                    print(f"  ⚠️  Page {page}: Empty (exceeds max)")
                    break
        except Exception as e:
            print(f"  ❌ Page {page}: Error - {str(e)[:40]}")
            break
        time.sleep(0.3)

    return max_page

def crawl_category_all_pages(category_code, category_name, max_pages):
    """Crawl ALL pages for a single category"""
    print(f"\n🔄 Crawling {category_name} ({category_code}): pages 1-{max_pages}")

    all_products = []
    seen_ids = set()

    for page in range(1, max_pages + 1):
        url = f"{BASE}/Front/Product/?tp=ma&CatA={category_code}&page={page}"

        if page % 100 == 1 or page == 1:
            print(f"  Progress: Pages {page}-{min(page+99, max_pages)}...", end=" ", flush=True)

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract product info from page
                # Look for product containers (adjust selector based on actual HTML)
                product_links = soup.select('a[href*="pIdx="]')

                for link in product_links:
                    try:
                        href = link.get('href', '')
                        # Extract product ID from URL parameter
                        if 'pIdx=' in href:
                            pid = href.split('pIdx=')[-1].split('&')[0]
                            if pid and pid not in seen_ids:
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
            print(f"\n  ❌ Page {page} error: {str(e)[:40]}")
            continue

        time.sleep(0.2)  # Rate limiting

    print(f"\n  ✅ Crawled {max_pages} pages: {len(all_products)} unique products")
    return all_products

# Main execution
print("\n📋 PHASE 1: DISCOVER PAGE DEPTHS FOR ALL CATEGORIES")
print("-" * 80)

category_page_counts = {}
for cat_code, cat_name in CATEGORIES.items():
    try:
        max_pages = discover_max_pages(cat_code, cat_name)
        category_page_counts[cat_code] = max_pages
        print(f"  Result: {cat_name} = {max_pages} pages")
    except Exception as e:
        print(f"  Error discovering {cat_name}: {e}")
        category_page_counts[cat_code] = 1

print("\n📋 PHASE 2: CRAWL ALL PAGES FOR ALL CATEGORIES")
print("-" * 80)

all_discovered = []
for cat_code, cat_name in CATEGORIES.items():
    max_pages = category_page_counts.get(cat_code, 1)
    products = crawl_category_all_pages(cat_code, cat_name, max_pages)
    all_discovered.extend(products)

print("\n📊 PHASE 3: SAVE COMPLETE DISCOVERY")
print("-" * 80)

# Save complete list
output_file = OUTPUT_DIR / "product_urls_complete_all_pages.jsonl"
with open(output_file, 'w', encoding='utf-8') as f:
    for product in all_discovered:
        f.write(json.dumps(product, ensure_ascii=False) + "\n")

print(f"✅ Saved {len(all_discovered)} unique product URLs")
print(f"   File: {output_file}")

# Save summary
summary = {
    "total_products_discovered": len(all_discovered),
    "categories": CATEGORIES,
    "page_counts": category_page_counts,
    "estimated_total": sum(category_page_counts.values()) * 30,  # ~30 items per page
    "file": str(output_file)
}

summary_file = OUTPUT_DIR / "discovery_summary_complete.json"
with open(summary_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\n📊 FINAL STATISTICS")
print("=" * 80)
print(f"Total unique products discovered: {len(all_discovered)}")
print(f"Categories processed: {len(CATEGORIES)}")
print(f"Estimated total pages: {sum(category_page_counts.values())}")
print(f"Estimated items per category: ~47,000 (if similar to A001)")
print(f"Estimated total items: ~{sum(category_page_counts.values()) * 30:,}")
print("=" * 80)
print("\n✨ Phase 1 complete! Ready for extraction phase.")
