#!/usr/bin/env python3
"""
Test login with proper wait for AJAX-loaded login form
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv('FREEMOLD_USERNAME')
PASSWORD = os.getenv('FREEMOLD_PASSWORD')

def test_login_with_ajax():
    """Test login with proper AJAX wait"""

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        print("Step 1: Navigate to homepage and wait for full load...")
        driver.get('https://www.freemold.net')
        time.sleep(5)  # Wait for all JavaScript to load

        print("\nStep 2: Check if divLayerPop exists...")
        layer_pop_exists = driver.execute_script("""
            return document.getElementById('divLayerPop') !== null;
        """)
        print(f"  divLayerPop exists: {layer_pop_exists}")

        print("\nStep 3: Trigger loginLayer() and wait for AJAX...")
        driver.execute_script("""
            loginLayer();
        """)

        # Wait for the modal to become visible
        print("  Waiting for modal to appear...")
        wait = WebDriverWait(driver, 10)
        layer_pop = wait.until(
            EC.visibility_of_element_located((By.ID, "divLayerPop"))
        )
        print("  ✅ Modal appeared!")

        # Wait for AJAX content to load (login form inputs)
        print("  Waiting for login form to load via AJAX...")
        time.sleep(3)  # Give AJAX time to complete

        # Try multiple selectors for login inputs
        selectors = [
            ("name='loginId'", By.NAME, "loginId"),
            ("id='loginId'", By.ID, "loginId"),
            ("input[type='text']", By.CSS_SELECTOR, "input[type='text']"),
        ]

        username_input = None
        for desc, by_type, selector in selectors:
            try:
                username_input = driver.find_element(by_type, selector)
                print(f"  ✅ Found username input via {desc}")
                break
            except:
                continue

        if not username_input:
            print("  ❌ Could not find username input")
            # Save modal HTML for inspection
            modal_html = driver.execute_script("""
                return document.getElementById('divLayerPop').innerHTML;
            """)
            with open('/tmp/freemold_modal_content.html', 'w', encoding='utf-8') as f:
                f.write(modal_html)
            print("  Modal content saved to /tmp/freemold_modal_content.html")
            return False

        # Find password input
        password_selectors = [
            ("name='loginPw'", By.NAME, "loginPw"),
            ("id='loginPw'", By.ID, "loginPw"),
            ("input[type='password']", By.CSS_SELECTOR, "input[type='password']"),
        ]

        password_input = None
        for desc, by_type, selector in password_selectors:
            try:
                password_input = driver.find_element(by_type, selector)
                print(f"  ✅ Found password input via {desc}")
                break
            except:
                continue

        if not password_input:
            print("  ❌ Could not find password input")
            return False

        print("\nStep 4: Enter credentials...")
        username_input.clear()
        username_input.send_keys(USERNAME)
        password_input.clear()
        password_input.send_keys(PASSWORD)
        print("  ✅ Credentials entered")

        print("\nStep 5: Submit login...")
        # Look for login button
        try:
            login_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit'], input[value*='로그인'], button:contains('로그인')")
            login_button.click()
        except:
            # Fallback: submit via password field
            password_input.submit()

        print("  Waiting for login to complete...")
        time.sleep(5)

        print("\nStep 6: Verify login success...")
        if "로그아웃" in driver.page_source or "Logout" in driver.page_source:
            print("  ✅ Login successful!")

            # Get cookies
            cookies = driver.get_cookies()
            print(f"\n  Session cookies: {len(cookies)}")
            for cookie in cookies:
                print(f"    {cookie['name']}: {cookie['value'][:30]}...")

            # Save cookies for future use
            import json
            with open('/tmp/freemold_cookies.json', 'w') as f:
                json.dump(cookies, f, indent=2)
            print("\n  ✅ Cookies saved to /tmp/freemold_cookies.json")

            print("\nStep 7: Test product page access...")
            test_url = "https://www.freemold.net/Front/Product/?tp=vi&pIdx=62964"
            driver.get(test_url)
            time.sleep(3)

            # Check for alert
            try:
                alert = driver.switch_to.alert
                print(f"  ❌ Access denied: {alert.text}")
                alert.accept()
                return False
            except:
                print("  ✅ No access denied alert!")

            # Check page content
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            if "비회원은 해당페이지를 열람할 수 없습니다" in page_text:
                print("  ❌ Access denied message in page")
                return False

            print("  ✅ Product page accessible!")
            print(f"  Page title: {driver.title}")

            # Count images
            images = driver.find_elements(By.TAG_NAME, 'img')
            print(f"  Images found: {len(images)}")

            # Save page
            with open('/tmp/freemold_product_success.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("  Page saved to /tmp/freemold_product_success.html")

            return True
        else:
            print("  ❌ Login failed - logout button not found")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

        # Save current state
        try:
            with open('/tmp/freemold_error_state.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("Error state saved to /tmp/freemold_error_state.html")
        except:
            pass

        return False

    finally:
        driver.quit()

if __name__ == '__main__':
    print("=" * 70)
    print("LOGIN TEST WITH AJAX WAIT")
    print("=" * 70)
    success = test_login_with_ajax()
    print("\n" + "=" * 70)
    print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print("=" * 70)
