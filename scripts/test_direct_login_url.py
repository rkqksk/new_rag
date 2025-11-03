#!/usr/bin/env python3
"""
Test accessing login page directly via URL instead of modal
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

def test_direct_login():
    """Test accessing login page directly"""

    chrome_options = Options()
    # Don't use headless for debugging
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Try various possible login URLs
        login_urls = [
            'https://www.freemold.net/Front/Member/?tp=lo',  # Login page
            'https://www.freemold.net/Front/Member/Login.asp',  # ASP login
            'https://www.freemold.net/Member/Login.asp',
            'https://www.freemold.net/login.asp',
        ]

        for url in login_urls:
            print(f"\nTrying URL: {url}")
            driver.get(url)
            time.sleep(3)

            print(f"  Current URL: {driver.current_url}")
            print(f"  Page title: {driver.title}")

            # Look for login form
            try:
                # Try different input selectors
                username_input = None
                password_input = None

                # Try by type
                try:
                    username_input = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
                    password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                    print("  ✅ Found login form by type!")
                except:
                    pass

                # Try by name
                if not username_input:
                    try:
                        username_input = driver.find_element(By.NAME, "memberID")
                        password_input = driver.find_element(By.NAME, "memberPW")
                        print("  ✅ Found login form by name!")
                    except:
                        pass

                # Try by id
                if not username_input:
                    try:
                        username_input = driver.find_element(By.ID, "memberID")
                        password_input = driver.find_element(By.ID, "memberPW")
                        print("  ✅ Found login form by ID!")
                    except:
                        pass

                if username_input and password_input:
                    print(f"\n  Username input: {username_input.get_attribute('name')} / {username_input.get_attribute('id')}")
                    print(f"  Password input: {password_input.get_attribute('name')} / {password_input.get_attribute('id')}")

                    # Enter credentials
                    username_input.clear()
                    username_input.send_keys(USERNAME)
                    password_input.clear()
                    password_input.send_keys(PASSWORD)

                    print("\n  Submitting login form...")
                    password_input.submit()
                    time.sleep(5)

                    # Check if login successful
                    print(f"  After login URL: {driver.current_url}")
                    if "로그아웃" in driver.page_source or "Logout" in driver.page_source:
                        print("  ✅ Login successful!")

                        # Get cookies
                        cookies = driver.get_cookies()
                        print(f"\n  Cookies: {len(cookies)}")
                        for cookie in cookies:
                            print(f"    {cookie['name']}: {cookie['value'][:30]}...")

                        # Test product page access
                        print("\n  Testing product page access...")
                        test_url = "https://www.freemold.net/Front/Product/?tp=vi&pIdx=62964"
                        driver.get(test_url)
                        time.sleep(3)

                        # Check for alert
                        try:
                            alert = driver.switch_to.alert
                            print(f"  ❌ Alert: {alert.text}")
                            alert.accept()
                        except:
                            print("  ✅ No access denied alert!")
                            print(f"  Product page title: {driver.title}")

                            # Save page
                            with open('/tmp/freemold_product_success.html', 'w', encoding='utf-8') as f:
                                f.write(driver.page_source)
                            print("  Saved to /tmp/freemold_product_success.html")

                        return True
                    else:
                        print("  ❌ Login failed - no logout button")

            except Exception as e:
                print(f"  ❌ No login form: {e}")

        print("\n❌ All login URLs failed")
        return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        print("\nClosing browser in 10 seconds...")
        time.sleep(10)
        driver.quit()

if __name__ == '__main__':
    test_direct_login()
