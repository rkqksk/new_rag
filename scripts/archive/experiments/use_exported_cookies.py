#!/usr/bin/env python3
"""
Use exported cookies from browser to establish authenticated session

INSTRUCTIONS FOR USER:
1. Log in to freemold.net in your browser
2. Open DevTools (F12) → Application → Cookies → www.freemold.net
3. Copy all cookie values and save them to cookies.json in this format:
   [
     {"name": "ASPSESSIONIDCCGCCRSD", "value": "YOUR_VALUE", "domain": ".freemold.net"},
     {"name": "User", "value": "YOUR_VALUE", "domain": ".freemold.net"},
     ... (copy all cookies)
   ]
4. Run this script: python3 use_exported_cookies.py cookies.json
"""

import os
import sys
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def use_exported_cookies(cookie_file):
    """Load cookies from file and test product page access"""

    if not os.path.exists(cookie_file):
        print(f"❌ Cookie file not found: {cookie_file}")
        print("\nPlease create cookies.json with your browser cookies.")
        print("See script header for instructions.")
        return False

    # Load cookies
    with open(cookie_file, 'r') as f:
        cookies = json.load(f)

    print(f"Loaded {len(cookies)} cookies from {cookie_file}")

    # Setup browser
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        print("\nStep 1: Navigate to freemold.net...")
        driver.get('https://www.freemold.net')
        time.sleep(2)

        print("Step 2: Inject cookies...")
        for cookie in cookies:
            # Selenium requires specific cookie format
            cookie_dict = {
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': cookie.get('domain', '.freemold.net'),
            }
            # Optional fields
            if 'path' in cookie:
                cookie_dict['path'] = cookie['path']
            if 'secure' in cookie:
                cookie_dict['secure'] = cookie['secure']

            try:
                driver.add_cookie(cookie_dict)
                print(f"  ✅ Added: {cookie['name']}")
            except Exception as e:
                print(f"  ❌ Failed to add {cookie['name']}: {e}")

        print("\nStep 3: Refresh page to apply cookies...")
        driver.get('https://www.freemold.net')
        time.sleep(2)

        # Check if logged in
        if "로그아웃" in driver.page_source or "Logout" in driver.page_source:
            print("✅ Login successful!")
        else:
            print("⚠️ Cannot verify login status")

        print("\nStep 4: Test product page access...")
        test_url = "https://www.freemold.net/Front/Product/?tp=vi&pIdx=62964"
        driver.get(test_url)
        time.sleep(3)

        # Check for access denied alert
        try:
            alert = driver.switch_to.alert
            print(f"❌ Access denied: {alert.text}")
            alert.accept()
            return False
        except:
            print("✅ No access denied alert!")

        # Check page content
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        if "비회원은 해당페이지를 열람할 수 없습니다" in page_text:
            print("❌ Access denied message in page")
            return False

        print("✅ Product page accessible!")
        print(f"Page title: {driver.title}")

        # Count images
        images = driver.find_elements(By.TAG_NAME, 'img')
        print(f"Images found: {len(images)}")

        # Save page for inspection
        output_file = '/tmp/freemold_product_with_cookies.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"Page saved to: {output_file}")

        # Extract product info as test
        print("\nProduct Information:")
        # Look for product code
        try:
            # This is just example - actual selectors would need to be determined
            print("  (Would extract product details here)")
        except:
            pass

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        driver.quit()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        cookie_file = 'cookies.json'
        print(f"Usage: python3 {sys.argv[0]} [cookies.json]")
        print(f"Using default: {cookie_file}")
    else:
        cookie_file = sys.argv[1]

    print("=" * 70)
    print("COOKIE-BASED AUTHENTICATION TEST")
    print("=" * 70)
    print()

    success = use_exported_cookies(cookie_file)

    print("\n" + "=" * 70)
    print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print("=" * 70)

    if not success and not os.path.exists(cookie_file):
        print("\n💡 To create cookies.json:")
        print("1. Log in to freemold.net in your browser")
        print("2. Open DevTools (F12) → Application → Cookies")
        print("3. Export all cookies for www.freemold.net")
        print("4. Save as cookies.json in this format:")
        print("""
[
  {
    "name": "ASPSESSIONIDCCGCCRSD",
    "value": "YOUR_SESSION_VALUE",
    "domain": ".freemold.net",
    "path": "/"
  },
  {
    "name": "User",
    "value": "YOUR_USER_VALUE",
    "domain": ".freemold.net",
    "path": "/"
  }
]
        """)
