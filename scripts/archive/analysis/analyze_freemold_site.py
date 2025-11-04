#!/usr/bin/env python3
"""
Freemold.net Site Analyzer

Login and analyze site structure:
- Product categories
- Pagination
- Product information fields
- Total product count
"""

import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

def setup_driver():
    """Setup Chrome driver with options"""
    options = Options()
    # options.add_argument('--headless')  # Uncomment for headless mode
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
    print("LOGGING IN TO FREEMOLD.NET")
    print("=" * 70)

    try:
        # Navigate to login page
        driver.get(LOGIN_URL)
        time.sleep(2)

        print("📍 Current URL:", driver.current_url)
        print("📄 Page title:", driver.title)

        # Click login button (CSS selector: #divTopLoginArea > span:nth-child(1))
        print("\n🔍 Looking for login button...")

        # First, close any mask/overlay
        try:
            driver.execute_script("""
                var mask = document.getElementById('divMask');
                if (mask) mask.style.display = 'none';
            """)
            print("✅ Removed divMask overlay")
        except:
            pass

        time.sleep(1)

        # Use JavaScript to click (bypass overlay issues)
        try:
            driver.execute_script("""
                var loginBtn = document.querySelector('#divTopLoginArea > span:nth-child(1)');
                if (loginBtn) {
                    loginBtn.click();
                } else {
                    // Try calling loginLayer() directly
                    if (typeof loginLayer === 'function') {
                        loginLayer();
                    }
                }
            """)
            print("✅ Clicked login button via JavaScript")
        except Exception as e:
            print(f"⚠️ JavaScript click failed: {e}")
            # Fallback to regular click
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#divTopLoginArea > span:nth-child(1)"))
            )
            print("✅ Found login button:", login_button.text)
            driver.execute_script("arguments[0].click();", login_button)

        time.sleep(3)

        # Wait for login form
        print("\n🔍 Looking for login form...")

        # Find username input
        # Common input names: id, user_id, username, login_id
        possible_id_selectors = [
            "input[name='id']",
            "input[name='user_id']",
            "input[name='username']",
            "input[name='login_id']",
            "input[type='text']",
            "input#id",
            "input#user_id"
        ]

        username_input = None
        for selector in possible_id_selectors:
            try:
                username_input = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"✅ Found username input: {selector}")
                break
            except:
                continue

        if not username_input:
            print("❌ Could not find username input")
            print("📄 Page HTML:")
            print(driver.page_source[:1000])
            return False

        # Find password input
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        print("✅ Found password input")

        # Enter credentials
        username_input.clear()
        username_input.send_keys(USERNAME)
        print(f"✅ Entered username: {USERNAME}")

        password_input.clear()
        password_input.send_keys(PASSWORD)
        print("✅ Entered password: ********")

        # Find and click submit button
        possible_submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button.login",
            "a.login",
            "#btnLogin"
        ]

        submit_button = None
        for selector in possible_submit_selectors:
            try:
                submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"✅ Found submit button: {selector}")
                break
            except:
                continue

        if submit_button:
            submit_button.click()
            print("✅ Clicked submit button")
        else:
            # Try pressing Enter
            password_input.submit()
            print("✅ Submitted form (Enter key)")

        time.sleep(3)

        # Check if login successful
        if "logout" in driver.page_source.lower() or "로그아웃" in driver.page_source:
            print("\n✅ LOGIN SUCCESSFUL!")
            return True
        else:
            print("\n⚠️ Login may have failed - checking page content...")
            print("📄 Current URL:", driver.current_url)
            return True  # Continue anyway

    except Exception as e:
        print(f"\n❌ Login error: {e}")
        print("📄 Page HTML:")
        print(driver.page_source[:1000])
        return False

def navigate_to_product_page(driver):
    """Navigate to product listing page from #divA001 link"""
    print("\n" + "=" * 70)
    print("NAVIGATING TO PRODUCT PAGE")
    print("=" * 70)

    try:
        # Find link in #divA001
        divA001_link = driver.find_element(By.CSS_SELECTOR, "#divA001 a")
        product_url = divA001_link.get_attribute('href')

        print(f"📍 Found product link: {product_url}")

        # Navigate to product page
        driver.get(product_url)

        # Wait longer for JavaScript/AJAX to load
        print("⏳ Waiting for page to fully load (10 seconds)...")
        time.sleep(10)

        print(f"✅ Navigated to: {driver.current_url}")
        print(f"📄 Page title: {driver.title}")

        # Take screenshot for manual inspection
        screenshot_path = "data/freemold/product_page_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"📸 Screenshot saved: {screenshot_path}")

        return True

    except Exception as e:
        print(f"❌ Navigation error: {e}")
        return False

def analyze_site_structure(driver):
    """Analyze product categories and structure from #divA001"""
    print("\n" + "=" * 70)
    print("ANALYZING SITE STRUCTURE (#divA001)")
    print("=" * 70)

    analysis = {
        "categories": [],
        "total_products": 0,
        "pagination_info": {},
        "sample_products": [],
        "divA001_structure": {},
        "navigation": {}
    }

    try:
        # Look for #divA001 (main product area)
        print("\n🔍 Analyzing #divA001 area...")

        try:
            divA001 = driver.find_element(By.CSS_SELECTOR, "#divA001")
            print("✅ Found #divA001")

            # Get HTML structure
            divA001_html = divA001.get_attribute('outerHTML')
            divA001_text = divA001.text

            analysis["divA001_structure"]["html_length"] = len(divA001_html)
            analysis["divA001_structure"]["text_length"] = len(divA001_text)
            analysis["divA001_structure"]["html_sample"] = divA001_html[:1000]
            analysis["divA001_structure"]["text_sample"] = divA001_text[:500]

            print(f"📏 #divA001 HTML length: {len(divA001_html)} chars")
            print(f"📏 #divA001 text length: {len(divA001_text)} chars")

            # Look for product items within #divA001
            product_selectors = [
                "#divA001 .product-item",
                "#divA001 .product",
                "#divA001 .item",
                "#divA001 li",
                "#divA001 div[class*='product']",
                "#divA001 div[class*='item']",
                "#divA001 table tr",
                "#divA001 > div",
                "#divA001 > ul > li"
            ]

            products_found = False
            for selector in product_selectors:
                try:
                    products = driver.find_elements(By.CSS_SELECTOR, selector)
                    if products and len(products) > 5:  # At least 5 items
                        print(f"✅ Found {len(products)} items with: {selector}")

                        # Analyze first few products
                        for i, product in enumerate(products[:3]):
                            sample = {
                                "index": i,
                                "html": product.get_attribute('outerHTML')[:300],
                                "text": product.text[:200],
                                "class": product.get_attribute('class'),
                                "id": product.get_attribute('id')
                            }
                            analysis["sample_products"].append(sample)

                        analysis["divA001_structure"]["product_selector"] = selector
                        analysis["divA001_structure"]["product_count"] = len(products)
                        products_found = True
                        break
                except:
                    continue

            if not products_found:
                print("⚠️ Could not find product items in #divA001")
                analysis["divA001_structure"]["full_html_sample"] = divA001_html[:5000]

        except Exception as e:
            print(f"❌ Could not find #divA001: {e}")

        # Search entire page for product-like structures
        print("\n🔍 Searching entire page for products...")

        # Look for common product container patterns
        page_product_selectors = [
            "div[class*='product']",
            "div[class*='item']",
            "div[class*='goods']",
            "li[class*='product']",
            "article",
            ".product",
            ".item",
            "[data-product-id]",
            "[data-item-id]"
        ]

        page_products = []
        for selector in page_product_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) > 3:
                    print(f"✅ Found {len(elements)} items with: {selector}")

                    # Sample first 3
                    for i, elem in enumerate(elements[:3]):
                        sample = {
                            "selector": selector,
                            "index": i,
                            "html": elem.get_attribute('outerHTML')[:300],
                            "text": elem.text[:150],
                            "class": elem.get_attribute('class')
                        }
                        page_products.append(sample)

                    analysis["page_products"] = {
                        "selector": selector,
                        "count": len(elements),
                        "samples": page_products[:3]
                    }
                    break
            except:
                continue

        # Save page HTML for manual inspection
        print("\n💾 Saving full page HTML...")
        page_html_path = "data/freemold/product_page.html"
        with open(page_html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"✅ Page HTML saved: {page_html_path}")

        # Look for product categories
        print("\n🔍 Looking for product categories...")

        # Common category selectors (within and outside #divA001)
        category_selectors = [
            "#divA001 .category a",
            "#divA001 .menu a",
            ".category-list a",
            ".menu a",
            "#category a",
            "nav a",
            ".nav-item a",
            "#divA001 a[href*='category']",
            "#divA001 a[href*='search']"
        ]

        categories = []
        for selector in category_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    for elem in elements:
                        text = elem.text.strip()
                        href = elem.get_attribute('href')
                        if text and href:
                            categories.append({
                                "name": text,
                                "url": href
                            })
                    print(f"✅ Found {len(elements)} categories with selector: {selector}")
                    break
            except:
                continue

        analysis["categories"] = categories[:20]  # Top 20 categories
        print(f"\n📁 Categories found: {len(categories)}")
        for cat in categories[:10]:
            print(f"   - {cat['name']}: {cat['url']}")

        # Look for product listings
        print("\n🔍 Looking for product listings...")

        product_selectors = [
            ".product-item",
            ".product",
            ".item",
            ".goods-item",
            "li[class*='product']"
        ]

        products = []
        for selector in product_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✅ Found {len(elements)} products with selector: {selector}")

                    # Analyze first product
                    if elements:
                        first_product = elements[0]
                        product_html = first_product.get_attribute('outerHTML')

                        sample_product = {
                            "selector": selector,
                            "html_sample": product_html[:500],
                            "text": first_product.text[:200]
                        }
                        analysis["sample_products"].append(sample_product)
                    break
            except:
                continue

        # Look for pagination
        print("\n🔍 Looking for pagination...")

        pagination_selectors = [
            ".pagination",
            ".paging",
            ".page-numbers",
            "ul.pagination li"
        ]

        for selector in pagination_selectors:
            try:
                paging = driver.find_elements(By.CSS_SELECTOR, selector)
                if paging:
                    print(f"✅ Found pagination: {selector}")
                    analysis["pagination_info"]["selector"] = selector
                    analysis["pagination_info"]["count"] = len(paging)
                    break
            except:
                continue

        # Look for total product count
        print("\n🔍 Looking for total product count...")

        # Search for text like "Total: 53,000" or "전체: 53,000"
        page_text = driver.page_source
        import re

        count_patterns = [
            r'total[:\s]+([0-9,]+)',
            r'전체[:\s]+([0-9,]+)',
            r'총[:\s]+([0-9,]+)',
            r'([0-9,]+)\s*개'
        ]

        for pattern in count_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                analysis["total_products"] = matches[0]
                print(f"✅ Found product count: {matches[0]}")
                break

    except Exception as e:
        print(f"❌ Analysis error: {e}")

    return analysis

def save_analysis(analysis):
    """Save analysis to JSON"""
    output_file = "data/freemold/site_analysis.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Analysis saved to: {output_file}")

def main():
    """Main analysis workflow"""
    print("\n" + "=" * 70)
    print("FREEMOLD.NET SITE ANALYZER")
    print("=" * 70)
    print(f"Site: {LOGIN_URL}")
    print(f"Expected products: ~53,000")
    print("=" * 70)

    driver = None

    try:
        # Setup driver
        driver = setup_driver()

        # Login
        if not login(driver):
            print("\n❌ Login failed - cannot continue")
            return

        # Wait a bit after login
        time.sleep(3)

        # Navigate to product page
        if not navigate_to_product_page(driver):
            print("\n❌ Navigation failed - cannot continue")
            return

        # Analyze site structure on product page
        analysis = analyze_site_structure(driver)

        # Save analysis
        save_analysis(analysis)

        # Print summary
        print("\n" + "=" * 70)
        print("ANALYSIS SUMMARY")
        print("=" * 70)
        print(f"Categories found: {len(analysis['categories'])}")
        print(f"Total products: {analysis.get('total_products', 'Unknown')}")
        print(f"Pagination: {analysis['pagination_info']}")
        print(f"Sample products: {len(analysis['sample_products'])}")

        # Keep browser open for manual inspection
        print("\n💡 Browser will stay open for 30 seconds for manual inspection...")
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
