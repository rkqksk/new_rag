#!/usr/bin/env python3
"""
Identify M.Bottle company by checking company profile pages with login
"""

import os
import time
import re
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

# Target companies in Direct Blow category
TARGET_COMPANIES = [
    {'mIdx': '481', 'product_count': 8},
    {'mIdx': '493', 'product_count': 5},
    {'mIdx': '1324', 'product_count': 2}
]

def setup_driver():
    """Setup Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def login(driver):
    """Login to freemold.net"""
    print("⏳ Logging in...")
    driver.get(LOGIN_URL)
    time.sleep(3)

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

    time.sleep(2)

    # Enter credentials
    username_input = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
    password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")

    username_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)
    password_input.submit()

    time.sleep(3)
    print("✅ Login successful")

def extract_company_name(driver, mIdx):
    """Extract company name from company profile page"""
    url = f"https://www.freemold.net/Front/Company/?mIdx={mIdx}"
    print(f"\n📍 Checking company {mIdx}: {url}")

    driver.get(url)
    time.sleep(3)

    # Check for alert (login required)
    try:
        alert = driver.switch_to.alert
        alert_text = alert.text
        print(f"  ⚠️ Alert detected: {alert_text}")
        alert.accept()
        return None, False
    except:
        pass  # No alert, proceed

    # Get page HTML
    html = driver.page_source

    # Save HTML for debugging
    with open(f'/tmp/company_{mIdx}.html', 'w', encoding='utf-8') as f:
        f.write(html)

    # Try multiple extraction methods
    company_name = None

    # Method 1: Look for company name in title
    try:
        title = driver.title
        if title and title != '프리몰드닷넷':
            company_name = title
            print(f"  ✅ From title: {company_name}")
    except:
        pass

    # Method 2: Search for specific patterns in HTML
    if not company_name:
        # Look for company name patterns
        patterns = [
            r'<h1[^>]*>([^<]+)</h1>',
            r'<h2[^>]*>([^<]+)</h2>',
            r'class="company[_-]?name"[^>]*>([^<]+)<',
            r'id="company[_-]?name"[^>]*>([^<]+)<',
            r'회사명[:\s]*([가-힣A-Za-z0-9\s\(\)\.]+)',
            r'업체명[:\s]*([가-힣A-Za-z0-9\s\(\)\.]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                candidate = match.group(1).strip()
                # Filter out common non-name text
                if candidate and len(candidate) < 50 and '로그인' not in candidate and '회원가입' not in candidate:
                    company_name = candidate
                    print(f"  ✅ From pattern '{pattern[:30]}...': {company_name}")
                    break

    # Method 3: Check for M.Bottle variations
    mbottle_found = False
    mbottle_patterns = ['엠보틀', 'M.Bottle', 'M-Bottle', 'MBOTTLE', 'MBottle', 'M Bottle']
    for pattern in mbottle_patterns:
        if pattern in html:
            mbottle_found = True
            print(f"  🎯 FOUND '{pattern}' in HTML!")
            if not company_name:
                company_name = pattern
            break

    if not company_name:
        print(f"  ⚠️ Could not extract company name from page")
        print(f"  📄 HTML saved to /tmp/company_{mIdx}.html")

    return company_name, mbottle_found

def main():
    print("=" * 70)
    print("M.BOTTLE COMPANY IDENTIFIER")
    print("=" * 70)
    print(f"Checking {len(TARGET_COMPANIES)} companies in Direct Blow category...")

    driver = setup_driver()

    try:
        # Login
        login(driver)

        # Check each company
        results = []
        for company in TARGET_COMPANIES:
            mIdx = company['mIdx']
            product_count = company['product_count']

            company_name, mbottle_found = extract_company_name(driver, mIdx)

            results.append({
                'mIdx': mIdx,
                'company_name': company_name or "Unknown",
                'product_count': product_count,
                'is_mbottle': mbottle_found
            })

        # Display results
        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)

        mbottle_company = None
        for result in results:
            marker = "🎯" if result['is_mbottle'] else "  "
            print(f"{marker} Company {result['mIdx']}: {result['company_name']}")
            print(f"   - Product count: {result['product_count']}")
            print(f"   - M.Bottle match: {'YES ✅' if result['is_mbottle'] else 'NO'}")
            print()

            if result['is_mbottle']:
                mbottle_company = result['mIdx']

        if mbottle_company:
            print(f"🎯 M.Bottle company identified: mIdx = {mbottle_company}")
        else:
            print("⚠️ Could not identify M.Bottle company automatically")
            print("📋 Check HTML files in /tmp/company_*.html manually")

        print("=" * 70)

        return mbottle_company

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
