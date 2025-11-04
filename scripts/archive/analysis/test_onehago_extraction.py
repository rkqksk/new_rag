#!/usr/bin/env python3
"""
Test script to diagnose Onehago product extraction
Tests actual HTML structure and CSS selectors
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re

def setup_driver():
    """Setup Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')
    return webdriver.Chrome(options=chrome_options)

def test_category_page(driver, category_id=22, page=1):
    """Test product extraction from category page"""
    print(f"\n{'='*70}")
    print(f"🔍 Testing Category {category_id}, Page {page}")
    print(f"{'='*70}\n")

    url = f"https://www.onehago.com/mall/?cate_mode=list&cate={category_id}&CURRENT_PAGE={page}"
    print(f"URL: {url}")

    driver.get(url)
    time.sleep(2)  # Wait for page load

    # Get page source
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    print(f"\n📄 Page Title: {driver.title}")
    print(f"📏 Page Size: {len(page_source):,} characters")

    # Test various selectors
    print(f"\n🎯 Testing CSS Selectors:")
    print(f"{'-'*70}")

    selectors = [
        ".product",
        ".prod_item",
        ".product-item",
        "div[class*='product']",
        "li[class*='product']",
        ".list_item",
        ".item",
        "a[href*='prod_cd']"
    ]

    for selector in selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        print(f"  {selector:30s} → {len(elements):3d} elements")

    # Find all links with prod_cd
    print(f"\n🔗 Product Links (prod_cd):")
    print(f"{'-'*70}")

    prod_links = re.findall(r'href="[^"]*prod_cd=(\d+)[^"]*"', page_source)
    unique_prod_ids = list(set(prod_links))
    print(f"  Found {len(prod_links)} total links, {len(unique_prod_ids)} unique product IDs")

    if unique_prod_ids[:5]:
        print(f"  Sample IDs: {unique_prod_ids[:5]}")

    # Search for common product container patterns
    print(f"\n📦 Common Container Classes:")
    print(f"{'-'*70}")

    container_patterns = [
        r'class="([^"]*product[^"]*)"',
        r'class="([^"]*item[^"]*)"',
        r'class="([^"]*list[^"]*)"',
        r'class="([^"]*goods[^"]*)"'
    ]

    for pattern in container_patterns:
        matches = re.findall(pattern, page_source, re.IGNORECASE)
        unique_classes = list(set(matches))[:3]
        if unique_classes:
            print(f"  Pattern '{pattern}': {unique_classes}")

    # Try to extract with BeautifulSoup
    print(f"\n🥣 BeautifulSoup Analysis:")
    print(f"{'-'*70}")

    # Find all divs/lis with product-related classes
    potential_containers = soup.find_all(['div', 'li', 'article'], class_=re.compile(r'(product|item|goods|list)', re.I))
    print(f"  Found {len(potential_containers)} potential product containers")

    if potential_containers:
        first = potential_containers[0]
        print(f"\n  First container classes: {first.get('class', [])}")
        print(f"  First container HTML (first 200 chars):")
        print(f"  {str(first)[:200]}...")

    # Check for images
    print(f"\n🖼️  Images Analysis:")
    print(f"{'-'*70}")

    img_elements = driver.find_elements(By.TAG_NAME, "img")
    print(f"  Total images: {len(img_elements)}")

    product_images = [img for img in img_elements if 'product' in img.get_attribute('src').lower() or 'prod' in img.get_attribute('src').lower()]
    print(f"  Product-related images: {len(product_images)}")

    if product_images:
        print(f"  Sample image src: {product_images[0].get_attribute('src')[:80]}...")

    return len(unique_prod_ids) > 0

def test_product_detail(driver, product_id="46893"):
    """Test product detail extraction"""
    print(f"\n{'='*70}")
    print(f"🔍 Testing Product Detail Page: {product_id}")
    print(f"{'='*70}\n")

    url = f"https://www.onehago.com/mall/?mode=view&prod_cd={product_id}"
    print(f"URL: {url}")

    driver.get(url)
    time.sleep(2)

    page_source = driver.page_source

    print(f"\n📄 Page Title: {driver.title}")
    print(f"📏 Page Size: {len(page_source):,} characters")

    # Test selectors for product details
    print(f"\n🎯 Testing Detail Selectors:")
    print(f"{'-'*70}")

    detail_selectors = {
        "Product Title": [".prod_tit", ".product_title", "h1.title", ".prod_name"],
        "Product Images": [".prod_img img", ".product_image img", ".detail_img img"],
        "Specifications": [".spec_table", ".specification", ".product_spec"],
        "Manufacturer": [".company_name", ".manufacturer", ".maker"],
        "Price": [".price", ".prod_price", ".sale_price"]
    }

    for field, selectors in detail_selectors.items():
        print(f"\n  {field}:")
        for selector in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"    ✅ {selector:30s} → {len(elements)} found")
                if field == "Product Title" and elements[0].text:
                    print(f"       Text: {elements[0].text[:50]}...")
            else:
                print(f"    ❌ {selector:30s} → Not found")

    # Find all images
    print(f"\n🖼️  Product Images:")
    print(f"{'-'*70}")

    img_elements = driver.find_elements(By.TAG_NAME, "img")
    product_images = [img for img in img_elements if 'product' in img.get_attribute('src').lower() or 'upload' in img.get_attribute('src').lower()]

    print(f"  Total images: {len(img_elements)}")
    print(f"  Product images: {len(product_images)}")

    if product_images:
        print(f"\n  Sample images:")
        for idx, img in enumerate(product_images[:3]):
            src = img.get_attribute('src')
            print(f"    [{idx+1}] {src}")

def main():
    """Main test function"""
    print("\n🚀 Onehago Extraction Diagnostic Tool")
    print("="*70)

    driver = setup_driver()

    try:
        # Test 1: Category page (small category)
        success = test_category_page(driver, category_id=22, page=1)

        if not success:
            print(f"\n⚠️  WARNING: No products found on category page!")
            print(f"   Trying alternative category...")
            test_category_page(driver, category_id=13, page=1)

        # Test 2: Product detail page
        print(f"\n")
        test_product_detail(driver, product_id="46893")

        print(f"\n{'='*70}")
        print(f"✅ Diagnostic Complete!")
        print(f"{'='*70}\n")

        print(f"📋 Next Steps:")
        print(f"  1. Review the CSS selectors that found products")
        print(f"  2. Update crawler code with correct selectors")
        print(f"  3. Test extraction with new selectors")
        print(f"  4. Create Phase 1 URL collection script")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
