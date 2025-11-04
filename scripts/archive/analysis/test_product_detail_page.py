#!/usr/bin/env python3
"""
Test Product Detail Page Crawler

Tests accessing a single product detail page to understand:
1. What data is available
2. Image URLs and how to download them
3. Specifications format
4. Whether authentication is required
"""

import os
import json
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv('FREEMOLD_USERNAME')
PASSWORD = os.getenv('FREEMOLD_PASSWORD')

def setup_driver(headless=False):
    """Setup Chrome driver"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')

    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')

    # Load cookies if available
    driver = webdriver.Chrome(options=chrome_options)

    # Try to load cookies
    cookies_file = Path('cookies.json')
    if cookies_file.exists():
        driver.get('https://www.freemold.net')
        time.sleep(2)

        with open(cookies_file, 'r') as f:
            cookies = json.load(f)

        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                pass

        print("✅ Cookies loaded")

    return driver

def extract_product_details(driver, product_url):
    """Extract all details from a product page"""
    print(f"\n{'='*70}")
    print(f"Testing Product Detail Page")
    print(f"{'='*70}")
    print(f"URL: {product_url}")

    driver.get(product_url)
    time.sleep(3)

    # Check for access denied
    if "비회원은 해당페이지를 열람할 수 없습니다" in driver.page_source:
        print("❌ Access denied - authentication required")
        return None

    details = {
        'url': product_url,
        'images': [],
        'specifications': {},
        'description': '',
        'company_info': {},
        'html_structure': {}
    }

    # Extract images
    print("\n1. Images:")
    try:
        # Try common image selectors
        img_selectors = [
            "img[src*='product']",
            "img[src*='Product']",
            "img[src*='upload']",
            ".product-image img",
            "#product_image img",
            "img.product",
        ]

        for selector in img_selectors:
            images = driver.find_elements(By.CSS_SELECTOR, selector)
            if images:
                print(f"  Found {len(images)} images with selector: {selector}")
                for img in images:
                    src = img.get_attribute('src')
                    if src and 'product' in src.lower():
                        details['images'].append(src)
                        print(f"    - {src}")
                break

        if not details['images']:
            print("  ⚠️ No product images found with common selectors")
            # Try to find all images
            all_images = driver.find_elements(By.TAG_NAME, 'img')
            print(f"  Total images on page: {len(all_images)}")
            for img in all_images[:5]:  # Show first 5
                src = img.get_attribute('src')
                if src:
                    print(f"    - {src}")

    except Exception as e:
        print(f"  ❌ Error extracting images: {e}")

    # Extract specifications
    print("\n2. Specifications:")
    try:
        # Try common table/spec selectors
        spec_selectors = [
            "table.spec",
            "table.product-spec",
            ".specification table",
            "#spec table",
            "table",
        ]

        for selector in spec_selectors:
            tables = driver.find_elements(By.CSS_SELECTOR, selector)
            if tables:
                print(f"  Found {len(tables)} tables with selector: {selector}")
                for table in tables[:2]:  # Show first 2 tables
                    rows = table.find_elements(By.TAG_NAME, 'tr')
                    print(f"    Table with {len(rows)} rows:")
                    for row in rows[:5]:  # Show first 5 rows
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if len(cells) >= 2:
                            key = cells[0].text.strip()
                            value = cells[1].text.strip()
                            if key:
                                details['specifications'][key] = value
                                print(f"      {key}: {value}")
                break

    except Exception as e:
        print(f"  ❌ Error extracting specs: {e}")

    # Extract product description
    print("\n3. Description:")
    try:
        desc_selectors = [
            ".product-description",
            "#product_desc",
            ".description",
            "#description",
        ]

        for selector in desc_selectors:
            desc_elem = driver.find_elements(By.CSS_SELECTOR, selector)
            if desc_elem:
                description = desc_elem[0].text.strip()
                if description:
                    details['description'] = description
                    print(f"  {description[:200]}...")
                    break

    except Exception as e:
        print(f"  ❌ Error extracting description: {e}")

    # Analyze HTML structure
    print("\n4. Page Structure Analysis:")
    try:
        # Find main content area
        main_divs = driver.find_elements(By.CSS_SELECTOR, "div[id*='product'], div[class*='product']")
        print(f"  Product-related divs: {len(main_divs)}")

        # Count total elements
        all_imgs = len(driver.find_elements(By.TAG_NAME, 'img'))
        all_tables = len(driver.find_elements(By.TAG_NAME, 'table'))
        all_forms = len(driver.find_elements(By.TAG_NAME, 'form'))

        print(f"  Total images: {all_imgs}")
        print(f"  Total tables: {all_tables}")
        print(f"  Total forms: {all_forms}")

        details['html_structure'] = {
            'total_images': all_imgs,
            'total_tables': all_tables,
            'total_forms': all_forms,
        }

    except Exception as e:
        print(f"  ❌ Error analyzing structure: {e}")

    # Save page source for inspection
    output_dir = Path('data/freemold/detail_page_test')
    output_dir.mkdir(parents=True, exist_ok=True)

    html_file = output_dir / 'sample_product_page.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"\n✅ Page source saved to: {html_file}")

    # Save screenshot
    screenshot_file = output_dir / 'sample_product_page.png'
    driver.save_screenshot(str(screenshot_file))
    print(f"✅ Screenshot saved to: {screenshot_file}")

    return details

def main():
    # Test with sample product
    sample_url = "https://www.freemold.net/Front/Product/?tp=vi&pIdx=88939"

    driver = None
    try:
        driver = setup_driver(headless=False)  # Visible for debugging
        details = extract_product_details(driver, sample_url)

        if details:
            # Save extracted data
            output_file = Path('data/freemold/detail_page_test/extracted_data.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(details, f, ensure_ascii=False, indent=2)

            print(f"\n{'='*70}")
            print("EXTRACTION SUMMARY")
            print(f"{'='*70}")
            print(f"Images found: {len(details['images'])}")
            print(f"Specifications: {len(details['specifications'])} fields")
            print(f"Description: {'✅' if details['description'] else '❌'}")
            print(f"\n✅ Extracted data saved to: {output_file}")

    finally:
        if driver:
            input("\nPress Enter to close browser...")
            driver.quit()

if __name__ == '__main__':
    main()
