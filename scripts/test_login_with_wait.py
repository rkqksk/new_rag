#!/usr/bin/env python3
"""
Test login with longer waits and more debugging
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

def test_login_with_debugging():
    """Test login with extensive debugging and longer waits"""

    chrome_options = Options()
    # Don't use headless so we can see what's happening
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        print("Step 1: Navigate to homepage...")
        driver.get('https://www.freemold.net')
        time.sleep(5)  # Longer wait for all JS to load

        print("\nStep 2: Check if already logged in...")
        if "로그아웃" in driver.page_source:
            print("  ✅ Already logged in!")
            cookies = driver.get_cookies()
            print(f"  Cookies: {len(cookies)}")
            for cookie in cookies:
                print(f"    {cookie['name']}: {cookie['value'][:30]}...")
            return True

        print("\nStep 3: Remove overlay mask...")
        driver.execute_script("""
            var mask = document.getElementById('divMask');
            if (mask) {
                console.log('Removing mask');
                mask.style.display = 'none';
            }
        """)

        print("\nStep 4: Check if loginLayer function exists...")
        function_exists = driver.execute_script("""
            return typeof loginLayer === 'function';
        """)
        print(f"  loginLayer function exists: {function_exists}")

        if not function_exists:
            print("\nStep 5: Wait longer for JavaScript to load...")
            time.sleep(10)
            function_exists = driver.execute_script("""
                return typeof loginLayer === 'function';
            """)
            print(f"  loginLayer function exists after wait: {function_exists}")

        print("\nStep 6: Try to trigger login modal...")
        # Try multiple methods
        methods = [
            ("Direct function call", "if (typeof loginLayer === 'function') { loginLayer(); return true; } return false;"),
            ("Click login span", """
                var span = document.querySelector('#divTopLoginArea > span:nth-child(1)');
                if (span) { span.click(); return true; } return false;
            """),
            ("Trigger onclick event", """
                var span = document.querySelector('#divTopLoginArea > span:nth-child(1)');
                if (span && span.onclick) { span.onclick(); return true; } return false;
            """),
        ]

        for method_name, js_code in methods:
            print(f"\n  Trying: {method_name}")
            result = driver.execute_script(js_code)
            print(f"    Result: {result}")
            time.sleep(3)

            # Check if login form appeared
            try:
                wait = WebDriverWait(driver, 5)
                username_input = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
                )
                print("    ✅ Login form appeared!")

                # Enter credentials
                password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")

                username_input.clear()
                username_input.send_keys(USERNAME)
                password_input.clear()
                password_input.send_keys(PASSWORD)

                print("    Submitting login...")
                password_input.submit()
                time.sleep(5)

                # Check success
                if "로그아웃" in driver.page_source:
                    print("    ✅ Login successful!")

                    # Get cookies
                    cookies = driver.get_cookies()
                    print(f"\n  Session cookies: {len(cookies)}")
                    for cookie in cookies:
                        print(f"    {cookie['name']}: {cookie['value'][:30]}...")

                    # Test product page
                    print("\n  Testing product page access...")
                    test_url = "https://www.freemold.net/Front/Product/?tp=vi&pIdx=62964"
                    driver.get(test_url)
                    time.sleep(3)

                    # Check for alert
                    try:
                        alert = driver.switch_to.alert
                        print(f"    ❌ Alert: {alert.text}")
                        alert.accept()
                        return False
                    except:
                        print("    ✅ No access denied alert!")
                        print(f"    Page title: {driver.title}")

                        # Save page
                        with open('/tmp/freemold_product_success.html', 'w', encoding='utf-8') as f:
                            f.write(driver.page_source)
                        print("    Saved to /tmp/freemold_product_success.html")

                        # Save cookies to file for future use
                        import json
                        with open('/tmp/freemold_cookies.json', 'w') as f:
                            json.dump(cookies, f, indent=2)
                        print("    Cookies saved to /tmp/freemold_cookies.json")

                        return True

            except Exception as e:
                print(f"    ❌ Login form did not appear: {e}")
                continue

        print("\n❌ All login methods failed")

        # Debug: Save current page
        print("\nSaving current page state for inspection...")
        with open('/tmp/freemold_failed_login.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("Saved to /tmp/freemold_failed_login.html")

        return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        print("\nBrowser will stay open for 30 seconds for manual inspection...")
        print("You can manually click the login button to see if it works")
        time.sleep(30)
        driver.quit()

if __name__ == '__main__':
    print("=" * 70)
    print("LOGIN TEST WITH DEBUGGING")
    print("=" * 70)
    success = test_login_with_debugging()
    print("\n" + "=" * 70)
    print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print("=" * 70)
