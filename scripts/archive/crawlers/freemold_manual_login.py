#!/usr/bin/env python3
"""
🔐 FREEMOLD MANUAL LOGIN HELPER
================================
Opens Chrome browser for you to manually login to Freemold.net
Once logged in, the script will analyze the authenticated page structure
and discover the actual product URLs available after authentication.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import json
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

BASE_URL = "https://www.freemold.net"
OUTPUT_DIR = Path("/Users/oypnus/Project/rag-enterprise/data/freemold/authenticated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("="*80)
print("🔐 FREEMOLD.NET - MANUAL LOGIN HELPER")
print("="*80)
print("\n📋 INSTRUCTIONS:")
print("  1. A Chrome browser will open")
print("  2. Look for 'LOGIN' or '로그인' button on the page")
print("  3. Enter your Freemold credentials")
print("  4. Click login and complete any 2FA if needed")
print("  5. Once logged in successfully, press ENTER in this terminal")
print("  6. The script will analyze the authenticated page structure")
print("\n" + "="*80 + "\n")

try:
    # Setup Chrome with VISIBLE window
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # NOT headless - we want visible window!

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    # Navigate to homepage
    print("📱 Opening Freemold.net in Chrome...")
    driver.get(BASE_URL)

    # Wait for page to load
    time.sleep(3)

    print("\n✅ Chrome browser is now open with Freemold.net")
    print("📌 Please log in to your account manually")
    print("\n⏳ Waiting for your login (this will check every 5 seconds)...\n")

    # Monitor for successful login
    max_wait_seconds = 300  # 5 minutes
    start_time = time.time()
    logged_in = False

    while (time.time() - start_time) < max_wait_seconds:
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Signs of successful login:
            # 1. Logout link/button present
            logout_elem = soup.find(['a', 'button'], href=lambda x: x and 'logout' in str(x).lower() if x else False)

            # 2. User menu or mypage link
            user_menu = soup.find(['a', 'div'], class_=lambda x: x and 'mypage' in str(x).lower() if x else False)
            user_menu = user_menu or soup.find('a', href=lambda x: x and 'mypage' in str(x).lower() if x else False)

            # 3. Check for logout button in HTML
            logout_button = soup.find(['button', 'a'], string=lambda x: x and 'logout' in str(x).lower() if x else False)

            if logout_elem or user_menu or logout_button:
                print("\n✅ LOGIN DETECTED!")
                print("   Logout link found - confirming authentication...")
                logged_in = True
                break

            # Check URL change - if we're in a dashboard/mypage, we're logged in
            current_url = driver.current_url
            if 'mypage' in current_url.lower() or 'user' in current_url.lower():
                print(f"\n✅ URL CHANGE DETECTED: {current_url}")
                logged_in = True
                break

        except Exception as e:
            pass

        time.sleep(2)

    if logged_in:
        print("\n" + "="*80)
        print("🔍 ANALYZING AUTHENTICATED PAGE STRUCTURE")
        print("="*80)

        # Save current state
        current_url = driver.current_url
        print(f"\n🔗 Current URL: {current_url}")

        # Take screenshot
        screenshot_path = OUTPUT_DIR / f"freemold_logged_in_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"📸 Screenshot saved: {screenshot_path}")

        # Save HTML
        html_path = OUTPUT_DIR / f"freemold_logged_in_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"📄 HTML saved: {html_path}")

        # Now navigate to a product listing page
        print("\n📂 Navigating to product listing pages to analyze structure...")

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Find category links
        category_links = soup.find_all('a', href=lambda x: x and 'CatA=' in str(x) if x else False)
        print(f"\n📂 Categories found: {len(category_links)}")

        if category_links:
            for link in category_links[:3]:
                cat_href = link.get('href', '')
                cat_text = link.get_text(strip=True)
                print(f"   - {cat_text}: {cat_href}")

        # Navigate to first category
        if category_links:
            first_cat_href = category_links[0].get('href', '')
            first_cat_url = urljoin(BASE_URL, first_cat_href)

            print(f"\n🔍 Navigating to first category: {first_cat_url}")
            driver.get(first_cat_url)
            time.sleep(5)

            # Analyze the category page
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Look for product links with authenticated access
            print("\n🔗 Analyzing product links on category page...")

            # Try different patterns
            all_links = soup.find_all('a')
            product_links = []

            for link in all_links:
                href = link.get('href', '')
                if 'pIdx=' in href or 'tp=vi' in href or 'pid=' in href:
                    product_links.append(href)

            print(f"   - Product links found: {len(product_links)}")

            if product_links:
                print("\n   Sample product URLs:")
                for url in product_links[:5]:
                    print(f"     - {url}")

            # Check for elements with onclick containing product IDs
            onclick_products = []
            for elem in soup.find_all(True, {'onclick': True}):
                onclick = elem.get('onclick', '')
                if 'product' in onclick.lower() or 'view' in onclick.lower():
                    onclick_products.append(onclick)

            print(f"\n   - Elements with onclick handlers: {len(onclick_products)}")
            if onclick_products:
                print("   Sample onclick handlers:")
                for onclick in onclick_products[:3]:
                    print(f"     - {onclick[:80]}")

            # Save analysis results
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'authenticated_url': current_url,
                'category_url': first_cat_url,
                'categories_found': len(category_links),
                'product_links_found': len(product_links),
                'sample_product_links': product_links[:10],
                'onclick_handlers_found': len(onclick_products),
                'sample_onclick': onclick_products[:3]
            }

            analysis_path = OUTPUT_DIR / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(analysis_path, 'w') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)

            print(f"\n📊 Analysis saved: {analysis_path}")

        print("\n" + "="*80)
        print("✅ ANALYSIS COMPLETE")
        print("="*80)
        print(f"\nFiles saved in: {OUTPUT_DIR}")
        print("  1. Screenshot of logged-in state")
        print("  2. HTML of category page")
        print("  3. Analysis JSON with discovered URLs")
        print("\n📝 Next: Review the files to determine:")
        print("  - Are there more product URLs available when authenticated?")
        print("  - What is the correct URL pattern for authenticated products?")
        print("  - Do we need to update Phase 1 crawler to use authenticated access?")

        # Keep browser open for 30 more seconds for manual inspection
        print("\n⏳ Browser will stay open for 30 seconds...")
        print("You can manually inspect the page in Chrome")
        time.sleep(30)

    else:
        print("\n⚠️  Login was not detected within 5 minutes")
        print("Please try again or check your credentials")

    driver.quit()
    print("\n✅ Done!")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
