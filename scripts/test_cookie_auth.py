#!/usr/bin/env python3
"""
Test cookie-based authentication for freemold.net

Instead of triggering the login modal, inject cookies directly
to establish an authenticated session.
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from dotenv import load_dotenv

load_dotenv()

def test_cookie_auth():
    """Test accessing product page with cookie-based authentication"""

    # Setup Chrome driver
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        print("Step 1: Navigate to freemold.net homepage...")
        driver.get('https://www.freemold.net')
        time.sleep(2)

        print("\nStep 2: Inject cookies from user's session...")
        # Get username from env (the user's memberID is rkqksk based on screenshot)
        username = os.getenv('FREEMOLD_USERNAME')

        # These cookies are from the user's screenshot
        # Note: We can't use exact cookie values from screenshot (security risk)
        # Instead, we'll do a proper login first to get valid cookies

        print("\nStep 3: Performing actual login to get valid cookies...")
        # Remove overlay
        driver.execute_script("""
            var mask = document.getElementById('divMask');
            if (mask) mask.style.display = 'none';
        """)

        # Wait for page to fully load
        time.sleep(3)

        # Try to click login button
        try:
            driver.execute_script("""
                var loginBtn = document.querySelector('#divTopLoginArea > span:nth-child(1)');
                if (loginBtn) {
                    console.log('Clicking login button...');
                    loginBtn.click();
                }
            """)
            time.sleep(2)
        except Exception as e:
            print(f"  Login button click failed: {e}")
            print("  Trying direct URL approach...")

            # Alternative: Try to access login page directly if it exists
            driver.get('https://www.freemold.net/Front/Member/?tp=lo')
            time.sleep(3)

        # Check if login form appeared
        try:
            username_input = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")

            print("  ✅ Login form found!")

            # Enter credentials
            username_input.clear()
            username_input.send_keys(os.getenv('FREEMOLD_USERNAME'))
            password_input.clear()
            password_input.send_keys(os.getenv('FREEMOLD_PASSWORD'))

            # Submit
            password_input.submit()
            time.sleep(5)

            # Check if login successful
            if "로그아웃" in driver.page_source or "Logout" in driver.page_source:
                print("  ✅ Login successful!")

                # Get cookies after successful login
                cookies = driver.get_cookies()
                print(f"\n  Cookies obtained: {len(cookies)} cookies")
                for cookie in cookies:
                    print(f"    - {cookie['name']}: {cookie['value'][:20]}..." if len(cookie['value']) > 20 else f"    - {cookie['name']}: {cookie['value']}")

                print("\nStep 4: Testing access to product detail page...")
                # Try accessing a sample product page
                test_url = "https://www.freemold.net/Front/Product/?tp=vi&pIdx=62964"
                driver.get(test_url)
                time.sleep(3)

                # Check for access denied alert
                try:
                    alert = driver.switch_to.alert
                    alert_text = alert.text
                    print(f"  ❌ Alert detected: {alert_text}")
                    alert.accept()
                    return False
                except:
                    print("  ✅ No access denied alert!")

                    # Check page content
                    page_text = driver.find_element(By.TAG_NAME, 'body').text
                    if "비회원은 해당페이지를 열람할 수 없습니다" in page_text:
                        print("  ❌ Access denied message in page content")
                        return False
                    else:
                        print("  ✅ Product page loaded successfully!")
                        print(f"  Page title: {driver.title}")

                        # Count images
                        images = driver.find_elements(By.TAG_NAME, 'img')
                        print(f"  Images found: {len(images)}")

                        # Save page source for inspection
                        with open('/tmp/freemold_product_page.html', 'w', encoding='utf-8') as f:
                            f.write(driver.page_source)
                        print("  Page saved to /tmp/freemold_product_page.html")

                        return True
            else:
                print("  ❌ Login failed - logout button not found")
                return False

        except Exception as e:
            print(f"  ❌ Login form not found: {e}")
            print("\nCurrent page URL:", driver.current_url)
            print("Page source preview:", driver.page_source[:500])
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        driver.quit()

if __name__ == '__main__':
    print("=" * 70)
    print("COOKIE-BASED AUTHENTICATION TEST")
    print("=" * 70)
    success = test_cookie_auth()
    print("\n" + "=" * 70)
    print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print("=" * 70)
