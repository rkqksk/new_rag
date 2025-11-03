#!/usr/bin/env python3
"""
FREEMOLD COMPREHENSIVE DISCOVERY INVESTIGATION
Investigate the discrepancy between expected (~80K) and actual (6.8K) product extraction
Similar investigation to plastics_kr that led to ID-based discovery approach

Strategy:
1. Phase 1: Test product IDs systematically to discover complete ID range
2. Phase 2: Analyze which IDs are valid/accessible
3. Phase 3: Determine why pagination method missed products
4. Phase 4: Calculate actual product count across all accessible IDs
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

BASE = "https://www.freemold.net"
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/investigation")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WAIT_TIMEOUT = 10

print("\n" + "="*80)
print("🔬 FREEMOLD DISCOVERY INVESTIGATION - FINDING THE MISSING ~73K PRODUCTS")
print("="*80)

def setup_driver():
    """Initialize Chrome WebDriver"""
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    try:
        driver = webdriver.Chrome(options=options)
        print("✅ Chrome driver initialized")
        return driver
    except Exception as e:
        print(f"✗ Failed to initialize driver: {e}")
        return None

def test_product_id_with_http(product_id):
    """Quick test if product ID exists using HTTP request"""
    url = f"{BASE}/Front/Product/?tp=vi&pIdx={product_id}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Check if product data exists
            product_name = soup.select_one(".product_name") or soup.select_one("[class*='title']")
            if product_name and len(product_name.text.strip()) > 0:
                return True, "accessible"
            else:
                return False, "no_content"
        else:
            return False, f"http_{response.status_code}"
    except Exception as e:
        return False, f"error_{str(e)[:20]}"

def test_product_id_with_selenium(driver, product_id):
    """Test if product ID accessible with Selenium (JavaScript rendering)"""
    url = f"{BASE}/Front/Product/?tp=vi&pIdx={product_id}"
    try:
        driver.get(url)
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(0.5)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_name = soup.select_one(".product_name") or soup.select_one("[class*='title']")

        if product_name and len(product_name.text.strip()) > 5:
            return True, "accessible"
        else:
            return False, "no_content"

    except TimeoutException:
        return False, "timeout"
    except Exception as e:
        return False, f"error_{str(e)[:20]}"

print("\n📊 PHASE 1: DETERMINE COMPLETE ID RANGE")
print("-" * 80)

# Load already discovered URLs to understand current range
current_urls_file = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/crawled/product_urls.jsonl")
discovered_ids = set()

if current_urls_file.exists():
    with open(current_urls_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                obj = json.loads(line)
                discovered_ids.add(int(obj['product_id']))
            except:
                pass

    print(f"✅ Loaded {len(discovered_ids)} product URLs from previous discovery")
    min_id = min(discovered_ids)
    max_id = max(discovered_ids)
    print(f"   Range: {min_id} - {max_id}")
    print(f"   Span: {max_id - min_id + 1} IDs")
    print(f"   Discovered: {len(discovered_ids)}")
    print(f"   Potential gap: {(max_id - min_id + 1) - len(discovered_ids)} IDs not in URL list")
else:
    print("⚠️  No previous discovery file found")

print("\n📊 PHASE 2: TEST EXTENDED ID RANGES")
print("-" * 80)

# Test ranges beyond discovered to find if more products exist
test_ranges = [
    (1, 100, "Very early IDs"),
    (100, 500, "Early IDs"),
    (500, 1500, "Before discovered min"),
    (min_id - 500, min_id, "Near min discovered"),
    (max_id, max_id + 500, "Beyond max discovered"),
    (max_id + 500, max_id + 1000, "Far beyond max"),
    (80000, 90000, "High ID range"),
    (90000, 99999, "Extreme high range"),
]

# Track results
test_results = {}
accessible_count = 0
total_tested = 0

print("\nTesting sample IDs from each range (every 50th ID)...")
print("")

for start, end, label in test_ranges:
    print(f"Testing {label} ({start}-{end})...", end=" ", flush=True)
    range_accessible = 0

    for test_id in range(start, min(end + 1, start + 500), 50):
        total_tested += 1
        exists, reason = test_product_id_with_http(test_id)

        if exists:
            range_accessible += 1
            accessible_count += 1
            if test_id not in discovered_ids:
                print(f"\n  🎯 FOUND NEW ID {test_id} (not in previous discovery)!")

        time.sleep(0.1)  # Rate limiting

    test_results[label] = range_accessible
    print(f"({range_accessible} accessible)")

print("\n📊 PHASE 3: ANALYSIS OF FINDINGS")
print("-" * 80)
print(f"Total IDs tested: {total_tested}")
print(f"Accessible IDs found: {accessible_count}")
print(f"Success rate: {accessible_count/total_tested*100:.1f}%")
print("")
print("Range breakdown:")
for label, count in test_results.items():
    print(f"  {label}: {count} accessible")

print("\n📊 PHASE 4: ESTIMATE TOTAL PRODUCTS")
print("-" * 80)

# Calculate potential for missing products
max_possible_id = max(discovered_ids) + 10000  # Test further out
estimated_gap_ids = max_possible_id - min(discovered_ids)
current_extraction_rate = len(discovered_ids) / (max_id - min_id + 1)

print(f"Current Discovery Stats:")
print(f"  Discovered URLs: {len(discovered_ids)}")
print(f"  ID range span: {max_id - min_id + 1}")
print(f"  Coverage: {len(discovered_ids) / (max_id - min_id + 1) * 100:.1f}%")
print(f"  Missing from range: {(max_id - min_id + 1) - len(discovered_ids)} IDs")
print("")
print(f"User's Expectation: ~80,000 products")
print(f"Current Extraction: 6,859 products")
print(f"Gap: ~73,000 products")
print("")
print(f"Potential Causes:")
print(f"  1. IDs span large range but many don't have accessible products")
print(f"  2. Pagination discovery method only found featured products")
print(f"  3. Need to test ALL IDs in range systematically")
print(f"  4. Some IDs may be inactive/deleted")

print("\n💡 RECOMMENDATION")
print("-" * 80)
print("Based on plastics_kr success pattern:")
print("  • Create ID-based full extraction crawler")
print("  • Test every ID from min to max in range")
print("  • Extract any accessible products (not just pagination)")
print("  • Should discover hidden products not in category listings")

print("\n" + "="*80)
print("🔬 INVESTIGATION COMPLETE")
print("="*80)

# Save results
results = {
    "discovered_ids_count": len(discovered_ids),
    "min_id": int(min_id),
    "max_id": int(max_id),
    "id_range_span": max_id - min_id + 1,
    "accessible_from_test": accessible_count,
    "test_results": test_results,
    "estimated_missing": 80000 - len(discovered_ids),
    "recommendation": "Create systematic ID-based crawler to test all IDs"
}

with open(OUTPUT_DIR / "discovery_investigation.json", 'w') as f:
    json.dump(results, f, indent=2)

print(f"✅ Results saved to {OUTPUT_DIR / 'discovery_investigation.json'}")
