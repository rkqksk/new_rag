#!/usr/bin/env python3
"""
Analyze Company Profile Page Structure

Purpose: Understand company profile page layout to enable company-specific filtering
Target URL: https://www.freemold.net/Front/Company/?tp=pr&mIdx={COMPANY_ID}
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

# Test company IDs (from Direct Blow category)
TEST_COMPANIES = [
    {'mIdx': '446', 'name': 'User provided example'},
    {'mIdx': '481', 'name': 'Direct Blow company 1 (8 products)'},
    {'mIdx': '493', 'name': 'Direct Blow company 2 (5 products)'},
    {'mIdx': '1324', 'name': 'Direct Blow company 3 (2 products)'}
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

def analyze_company_profile(driver, mIdx, company_info):
    """Analyze company profile page structure"""
    # Both URL patterns (tp=pr and without tp parameter)
    urls = [
        f"https://www.freemold.net/Front/Company/?tp=pr&mIdx={mIdx}",
        f"https://www.freemold.net/Front/Company/?mIdx={mIdx}"
    ]

    print(f"\n{'='*70}")
    print(f"ANALYZING COMPANY: {company_info} (mIdx={mIdx})")
    print(f"{'='*70}")

    for url_type, url in enumerate(urls, 1):
        print(f"\n📍 Trying URL pattern {url_type}: {url}")

        driver.get(url)
        time.sleep(5)

        # Check for alerts
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            print(f"  ⚠️ Alert: {alert_text}")
            alert.accept()
            continue
        except:
            pass

        # Get page HTML
        html = driver.page_source

        # Save HTML for debugging
        output_file = f"data/freemold/company_profile_mIdx{mIdx}_type{url_type}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  💾 HTML saved: {output_file}")

        # Take screenshot
        screenshot_file = f"data/freemold/company_profile_mIdx{mIdx}_type{url_type}.png"
        driver.save_screenshot(screenshot_file)
        print(f"  📸 Screenshot: {screenshot_file}")

        # Extract company name (try multiple selectors)
        company_name = extract_company_name(driver, html)

        # Extract product links
        product_links = extract_product_links(html, mIdx)

        # Analysis result
        result = {
            'mIdx': mIdx,
            'url': url,
            'url_type': f'tp=pr' if url_type == 1 else 'no_tp_param',
            'company_name': company_name,
            'product_count': len(product_links),
            'product_links_sample': product_links[:5],  # First 5 products
            'html_file': output_file,
            'screenshot_file': screenshot_file
        }

        print(f"\n  📊 Analysis Results:")
        print(f"     Company Name: {company_name or 'NOT FOUND'}")
        print(f"     Products Found: {len(product_links)}")
        if product_links:
            print(f"     Sample Product IDs: {[p['pIdx'] for p in product_links[:5]]}")

        return result

    return None

def extract_company_name(driver, html):
    """Extract company name from page"""
    selectors = [
        'h1', 'h2', '.company-name', '#companyName',
        '.company_name', 'div.name', 'span.name',
        'div.title', 'span.title'
    ]

    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                text = element.text.strip()
                # Filter out navigation/menu text
                if text and len(text) < 100 and '로그인' not in text and '회원가입' not in text:
                    if '업체명' not in text and '제품' not in text:
                        return text
        except:
            pass

    # Try searching in HTML with regex
    import re
    patterns = [
        r'업체명[:\s]*([가-힣A-Za-z0-9\s\(\)\.]+)',
        r'회사명[:\s]*([가-힣A-Za-z0-9\s\(\)\.]+)',
        r'<title>([^<]+)</title>',
    ]

    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            candidate = match.group(1).strip()
            if candidate and '프리몰드' not in candidate:
                return candidate

    return None

def extract_product_links(html, mIdx):
    """Extract product links from company profile page"""
    import re

    # Find all pIdx values
    pIdx_matches = re.findall(r'pIdx=(\d+)', html)

    products = []
    seen = set()

    for pIdx in pIdx_matches:
        if pIdx not in seen:
            seen.add(pIdx)
            products.append({
                'pIdx': pIdx,
                'url': f'https://www.freemold.net/Front/Product/?tp=vi&pIdx={pIdx}',
                'mIdx': mIdx
            })

    return products

def main():
    print("=" * 70)
    print("FREEMOLD COMPANY PROFILE ANALYZER")
    print("=" * 70)
    print(f"Testing {len(TEST_COMPANIES)} company profiles...")
    print()

    driver = setup_driver()

    try:
        # Login
        login(driver)

        # Analyze each company
        results = []
        for company in TEST_COMPANIES:
            mIdx = company['mIdx']
            info = company['name']

            result = analyze_company_profile(driver, mIdx, info)
            if result:
                results.append(result)

        # Save results
        output_file = 'data/freemold/company_profile_analysis.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*70}")
        print(f"ANALYSIS COMPLETE")
        print(f"{'='*70}")
        print(f"✅ Results saved to: {output_file}")
        print(f"📁 HTML files: data/freemold/company_profile_mIdx*.html")
        print(f"📸 Screenshots: data/freemold/company_profile_mIdx*.png")
        print()

        # Summary
        print("📊 SUMMARY:")
        for result in results:
            print(f"\n  Company mIdx={result['mIdx']}:")
            print(f"    Name: {result['company_name'] or 'NOT FOUND'}")
            print(f"    Products: {result['product_count']}")
            print(f"    URL Type: {result['url_type']}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
