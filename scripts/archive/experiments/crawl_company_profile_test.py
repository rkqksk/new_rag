#!/usr/bin/env python3
"""
Company Profile Based Crawler - Test Version

Target: https://www.freemold.net/Front/Company/?tp=pr&mIdx=446
Purpose: Test if we can access and crawl company profile pages with proper session handling
"""

import os
import time
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Login credentials from environment
LOGIN_URL = os.getenv('FREEMOLD_BASE_URL', 'https://www.freemold.net')
USERNAME = os.getenv('FREEMOLD_USERNAME')
PASSWORD = os.getenv('FREEMOLD_PASSWORD')

if not USERNAME or not PASSWORD:
    raise ValueError("FREEMOLD_USERNAME and FREEMOLD_PASSWORD must be set in .env file")

# Test company
TEST_COMPANY = {'mIdx': '446', 'name': 'Test Company'}

def setup_driver():
    """Setup Chrome driver with proper options"""
    chrome_options = Options()
    # Don't use headless mode for debugging
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')

    # Keep browser open for debugging
    chrome_options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def login_and_maintain_session(driver):
    """Login with proper session handling"""
    print("\n" + "="*70)
    print("STEP 1: LOGGING IN")
    print("="*70)

    driver.get(LOGIN_URL)
    time.sleep(3)

    # Remove overlay
    driver.execute_script("""
        var mask = document.getElementById('divMask');
        if (mask) mask.style.display = 'none';
    """)

    # Click login button using JavaScript
    driver.execute_script("""
        var loginBtn = document.querySelector('#divTopLoginArea > span:nth-child(1)');
        if (loginBtn) {
            loginBtn.click();
        } else if (typeof loginLayer === 'function') {
            loginLayer();
        }
    """)

    time.sleep(3)

    # Enter credentials
    try:
        wait = WebDriverWait(driver, 10)
        username_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
        )
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")

        username_input.clear()
        username_input.send_keys(USERNAME)
        password_input.clear()
        password_input.send_keys(PASSWORD)

        # Submit login
        password_input.submit()
        time.sleep(5)

        # Verify login success
        if "로그아웃" in driver.page_source or "Logout" in driver.page_source:
            print("✅ Login successful - session established")
            return True
        else:
            print("⚠️ Login may have failed - checking current page")
            print(f"Current URL: {driver.current_url}")
            return False

    except Exception as e:
        print(f"❌ Login failed with error: {e}")
        return False

def access_company_profile(driver, mIdx):
    """Try to access company profile page"""
    print("\n" + "="*70)
    print(f"STEP 2: ACCESSING COMPANY PROFILE (mIdx={mIdx})")
    print("="*70)

    # Try different URL patterns
    url_patterns = [
        f"https://www.freemold.net/Front/Company/?tp=pr&mIdx={mIdx}",
        f"https://www.freemold.net/Front/Company/?mIdx={mIdx}",
        f"https://www.freemold.net/Front/Company/Index.aspx?tp=pr&mIdx={mIdx}",
    ]

    for idx, url in enumerate(url_patterns, 1):
        print(f"\n📍 Attempt {idx}: {url}")

        driver.get(url)
        time.sleep(5)

        # Check for alert
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            print(f"  ⚠️ Alert detected: {alert_text}")
            alert.accept()
            time.sleep(2)
            continue
        except:
            pass

        # Check if page loaded successfully
        current_url = driver.current_url
        page_source = driver.page_source

        print(f"  📍 Current URL: {current_url}")
        print(f"  📄 Page length: {len(page_source)} characters")

        # Check for success indicators
        if "업체정보" in page_source or "회사명" in page_source or "업체명" in page_source:
            print(f"  ✅ SUCCESS! Company profile page loaded")

            # Save the HTML
            output_dir = Path('data/freemold/company_test')
            output_dir.mkdir(parents=True, exist_ok=True)

            html_file = output_dir / f'company_{mIdx}_success.html'
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"  💾 HTML saved: {html_file}")

            # Take screenshot
            screenshot_file = output_dir / f'company_{mIdx}_success.png'
            driver.save_screenshot(str(screenshot_file))
            print(f"  📸 Screenshot: {screenshot_file}")

            # Extract data
            data = extract_company_data(driver, page_source, mIdx)
            return data
        else:
            print(f"  ❌ Company profile page not loaded properly")

            # Save failed attempt
            output_dir = Path('data/freemold/company_test')
            output_dir.mkdir(parents=True, exist_ok=True)

            html_file = output_dir / f'company_{mIdx}_attempt_{idx}.html'
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"  💾 Failed HTML saved: {html_file}")

    print("\n❌ All attempts failed to load company profile page")
    return None

def extract_company_data(driver, html, mIdx):
    """Extract company information and product list"""
    print("\n" + "="*70)
    print("STEP 3: EXTRACTING DATA")
    print("="*70)

    data = {
        'mIdx': mIdx,
        'company_name': None,
        'products': []
    }

    # Extract company name
    name_selectors = [
        'h1', 'h2', '.company-name', '#companyName',
        'div.title', 'span.title'
    ]

    for selector in name_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                text = elem.text.strip()
                if text and len(text) < 100:
                    data['company_name'] = text
                    print(f"  ✅ Company name found: {text}")
                    break
            if data['company_name']:
                break
        except:
            pass

    # Extract product links
    pIdx_pattern = r'pIdx=(\d+)'
    pIdx_matches = re.findall(pIdx_pattern, html)

    seen_pIdx = set()
    for pIdx in pIdx_matches:
        if pIdx not in seen_pIdx:
            seen_pIdx.add(pIdx)
            data['products'].append({
                'pIdx': pIdx,
                'mIdx': mIdx,
                'product_url': f'https://www.freemold.net/Front/Product/?tp=vi&pIdx={pIdx}'
            })

    print(f"  ✅ Found {len(data['products'])} unique products")

    # Save extracted data
    output_dir = Path('data/freemold/company_test')
    json_file = output_dir / f'company_{mIdx}_data.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  💾 Data saved: {json_file}")

    return data

def main():
    print("=" * 70)
    print("FREEMOLD COMPANY PROFILE CRAWLER - TEST")
    print("=" * 70)
    print(f"Target: Company mIdx={TEST_COMPANY['mIdx']}")
    print(f"URL: https://www.freemold.net/Front/Company/?tp=pr&mIdx={TEST_COMPANY['mIdx']}")
    print()

    driver = setup_driver()

    try:
        # Step 1: Login
        if not login_and_maintain_session(driver):
            print("\n❌ Login failed - aborting")
            return

        # Step 2: Access company profile
        company_data = access_company_profile(driver, TEST_COMPANY['mIdx'])

        if company_data:
            print("\n" + "="*70)
            print("SUCCESS SUMMARY")
            print("="*70)
            print(f"  Company mIdx: {company_data['mIdx']}")
            print(f"  Company Name: {company_data['company_name']}")
            print(f"  Products Found: {len(company_data['products'])}")
            if company_data['products']:
                print(f"  Sample Product IDs: {[p['pIdx'] for p in company_data['products'][:5]]}")
            print("\n✅ Company profile crawling is POSSIBLE!")
        else:
            print("\n" + "="*70)
            print("FAILURE SUMMARY")
            print("="*70)
            print("❌ Could not access company profile page")
            print("📋 Possible reasons:")
            print("   1. Account doesn't have permission to view company profiles")
            print("   2. Session not properly maintained after login")
            print("   3. Company profile requires different URL pattern")
            print("   4. Need to navigate through different pages first")

        print("\n💡 Browser will stay open for manual inspection...")
        print("   Press Ctrl+C to close")

        # Keep browser open for manual inspection
        input("\nPress Enter to close browser...")

    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔄 Closing browser...")
        driver.quit()
        print("✅ Done")

if __name__ == "__main__":
    main()
