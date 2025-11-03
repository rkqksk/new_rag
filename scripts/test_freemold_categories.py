#!/usr/bin/env python3
"""
Freemold.net Category Page Structure Tester

Test the 4 bottle categories to understand:
- Product item selectors
- Pagination
- Product count
- Product detail link patterns
"""

import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Login credentials from environment
LOGIN_URL = os.getenv('FREEMOLD_BASE_URL', 'https://www.freemold.net')
USERNAME = os.getenv('FREEMOLD_USERNAME')
PASSWORD = os.getenv('FREEMOLD_PASSWORD')

if not USERNAME or not PASSWORD:
    raise ValueError("FREEMOLD_USERNAME and FREEMOLD_PASSWORD must be set in .env file")

# Categories to test
CATEGORIES = {
    "B001": "다이렉트 브로우 (Direct Blow)",
    "B002": "인젝션 브로우 (Injection Blow)",
    "B003": "헤비 브로우 (Heavy Blow)",
    "B004": "다층 브로우 (Multi-layer Blow)"
}

def setup_driver():
    """Setup Chrome driver"""
    options = Options()
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver

def login(driver):
    """Login to freemold.net"""
    print("\n" + "=" * 70)
    print("LOGGING IN")
    print("=" * 70)

    driver.get(LOGIN_URL)
    time.sleep(2)

    # Remove overlay
    driver.execute_script("""
        var mask = document.getElementById('divMask');
        if (mask) mask.style.display = 'none';
    """)

    # Click login button
    driver.execute_script("""
        var loginBtn = document.querySelector('#divTopLoginArea > span:nth-child(1)');
        if (loginBtn) loginBtn.click();
        else if (typeof loginLayer === 'function') loginLayer();
    """)

    time.sleep(3)

    # Enter credentials
    username_input = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
    password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")

    username_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)
    password_input.submit()

    time.sleep(3)
    print("✅ Login successful")

    return True

def analyze_category_page(driver, cat_b, cat_name):
    """Analyze a single category page"""
    print("\n" + "=" * 70)
    print(f"ANALYZING: {cat_name} (CatB={cat_b})")
    print("=" * 70)

    # Navigate to category
    url = f"https://www.freemold.net/Front/Product/?tp=ma&CatA=A001&CatB={cat_b}"
    print(f"📍 URL: {url}")

    driver.get(url)
    time.sleep(5)  # Wait for content to load

    analysis = {
        "category": cat_name,
        "catB": cat_b,
        "url": url,
        "product_items": [],
        "pagination": {},
        "total_count": 0
    }

    # Look for product items with various selectors
    product_selectors = [
        ".product-item",
        ".product",
        "li.product",
        "div.item",
        "[data-product-id]",
        "a[href*='pIdx']",  # Links to product detail pages
        ".goods-item",
        "div[class*='product']",
        "li[class*='product']"
    ]

    products_found = False
    for selector in product_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements and len(elements) > 0:
                print(f"✅ Found {len(elements)} items with selector: {selector}")

                # Sample first 3 products
                for i, elem in enumerate(elements[:3]):
                    try:
                        html = elem.get_attribute('outerHTML')[:500]
                        text = elem.text[:200]
                        href = elem.get_attribute('href') if elem.tag_name == 'a' else None

                        # Look for product links within the element
                        product_links = elem.find_elements(By.CSS_SELECTOR, "a[href*='pIdx']")
                        pIdx = None
                        if product_links:
                            href = product_links[0].get_attribute('href')
                            # Extract pIdx
                            if 'pIdx=' in href:
                                pIdx = href.split('pIdx=')[1].split('&')[0]

                        sample = {
                            "index": i,
                            "html_sample": html,
                            "text_sample": text,
                            "href": href,
                            "pIdx": pIdx
                        }
                        analysis["product_items"].append(sample)
                    except:
                        continue

                analysis["product_selector"] = selector
                analysis["product_count"] = len(elements)
                products_found = True
                break
        except:
            continue

    if not products_found:
        print("⚠️ No products found with standard selectors")

        # Try to find any links with pIdx
        try:
            all_pIdx_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='pIdx']")
            if all_pIdx_links:
                print(f"✅ Found {len(all_pIdx_links)} links with pIdx parameter")

                for i, link in enumerate(all_pIdx_links[:5]):
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    pIdx = href.split('pIdx=')[1].split('&')[0] if 'pIdx=' in href else None

                    analysis["product_items"].append({
                        "index": i,
                        "href": href,
                        "text": text,
                        "pIdx": pIdx
                    })

                analysis["product_selector"] = "a[href*='pIdx']"
                analysis["product_count"] = len(all_pIdx_links)
                products_found = True
        except:
            pass

    # Look for pagination
    pagination_selectors = [
        ".pagination",
        ".paging",
        "ul.pagination li",
        "a[href*='Page=']"
    ]

    for selector in pagination_selectors:
        try:
            paging_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if paging_elements:
                print(f"✅ Found pagination: {selector} ({len(paging_elements)} elements)")

                # Try to find page links
                page_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='Page=']")
                if page_links:
                    pages = []
                    for link in page_links[:10]:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        if 'Page=' in href:
                            page_num = href.split('Page=')[1].split('&')[0]
                            pages.append({"page": page_num, "url": href, "text": text})

                    analysis["pagination"] = {
                        "selector": selector,
                        "total_pages": len(pages),
                        "sample_pages": pages[:5]
                    }
                break
        except:
            continue

    # Look for total count
    import re
    page_text = driver.page_source
    count_patterns = [
        r'total[:\s]+([0-9,]+)',
        r'전체[:\s]+([0-9,]+)',
        r'총[:\s]+([0-9,]+)',
        r'([0-9,]+)\s*개'
    ]

    for pattern in count_patterns:
        matches = re.findall(pattern, page_text, re.IGNORECASE)
        if matches:
            analysis["total_count"] = matches[0]
            print(f"✅ Found product count: {matches[0]}")
            break

    # Take screenshot
    screenshot_path = f"data/freemold/category_{cat_b}_screenshot.png"
    driver.save_screenshot(screenshot_path)
    print(f"📸 Screenshot: {screenshot_path}")

    # Save page HTML
    html_path = f"data/freemold/category_{cat_b}_page.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"💾 HTML saved: {html_path}")

    return analysis

def main():
    """Test all 4 bottle categories"""
    print("\n" + "=" * 70)
    print("FREEMOLD CATEGORY STRUCTURE TESTER")
    print("=" * 70)
    print(f"Testing {len(CATEGORIES)} bottle categories")
    print("=" * 70)

    driver = None
    all_analysis = {}

    try:
        driver = setup_driver()

        # Login
        if not login(driver):
            print("❌ Login failed")
            return

        # Test each category
        for cat_b, cat_name in CATEGORIES.items():
            analysis = analyze_category_page(driver, cat_b, cat_name)
            all_analysis[cat_b] = analysis

            # Wait between requests
            time.sleep(2)

        # Save combined analysis
        output_file = "data/freemold/category_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_analysis, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 70)
        print("ANALYSIS SUMMARY")
        print("=" * 70)

        for cat_b, analysis in all_analysis.items():
            print(f"\n{analysis['category']} ({cat_b}):")
            print(f"  Products found: {analysis.get('product_count', 0)}")
            print(f"  Selector: {analysis.get('product_selector', 'N/A')}")
            print(f"  Pagination: {analysis.get('pagination', {})}")
            print(f"  Total count: {analysis.get('total_count', 'Unknown')}")

        print(f"\n✅ Complete analysis saved to: {output_file}")

        # Keep browser open for inspection
        print("\n💡 Browser will stay open for 30 seconds...")
        time.sleep(30)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()
            print("\n✅ Browser closed")

if __name__ == "__main__":
    main()
