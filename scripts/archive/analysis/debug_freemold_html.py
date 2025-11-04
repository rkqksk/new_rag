#!/usr/bin/env python3
"""
Debug script to fetch and analyze Freemold product page HTML structure
Focus: Contact extraction and image URLs
"""

import json
import re
from selenium import webdriver
from bs4 import BeautifulSoup
import time

def connect_to_chrome():
    """Connect to existing Chrome instance"""
    try:
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "localhost:9222")
        driver = webdriver.Chrome(options=options)
        print("✅ Connected to Chrome remote debugging")
        return driver
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return None

def analyze_product_page(product_id):
    """Fetch and analyze product page"""
    driver = connect_to_chrome()
    if not driver:
        return

    url = f"https://www.freemold.net/Front/Product/?tp=vi&pIdx={product_id}"
    print(f"\n🔍 Analyzing product {product_id}")
    print(f"URL: {url}")
    print("=" * 80)

    try:
        driver.get(url)
        time.sleep(3)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # ===== SECTION 1: Find ALL tables and their content =====
        print("\n1️⃣  ALL TABLE STRUCTURE:")
        print("-" * 80)
        tables = soup.find_all('table')
        print(f"Total tables: {len(tables)}")

        for table_idx, table in enumerate(tables):
            print(f"\n📊 Table {table_idx}:")
            rows = table.find_all('tr')
            print(f"   Rows: {len(rows)}")

            for row_idx, row in enumerate(rows[:10]):  # First 10 rows
                cells = row.find_all('td')
                if cells:
                    print(f"   Row {row_idx}: {len(cells)} cells")
                    for cell_idx, cell in enumerate(cells[:3]):  # First 3 cells
                        text = cell.get_text(strip=True)[:60]
                        print(f"      Cell {cell_idx}: {text}...")

        # ===== SECTION 2: Search for contact keywords =====
        print("\n2️⃣  CONTACT KEYWORD SEARCH:")
        print("-" * 80)

        contact_keywords = {
            '전화': 'phone',
            '팩스': 'fax',
            '이메일': 'email',
            '메일': 'email',
            '회사': 'company',
            '제조사': 'manufacturer',
            '회사명': 'company_name',
        }

        html_text = soup.get_text()
        for korean_key, english_key in contact_keywords.items():
            if korean_key in html_text:
                print(f"✅ Found '{korean_key}' ({english_key}) in page")
                # Find context
                idx = html_text.find(korean_key)
                context = html_text[max(0, idx-100):idx+100]
                print(f"   Context: {context}")
            else:
                print(f"❌ NOT found: '{korean_key}' ({english_key})")

        # ===== SECTION 3: Extract from specific table patterns =====
        print("\n3️⃣  TABLE-BASED EXTRACTION (Current Logic):")
        print("-" * 80)

        extracted_data = {
            'name': None,
            'specs': {},
            'contact': {},
            'manufacturer': None,
        }

        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label_cell = cells[0]
                    value_cell = cells[1]

                    label_text = label_cell.get_text(strip=True).lower()
                    value_text = value_cell.get_text(strip=True)

                    if not value_text:
                        continue

                    # Product name
                    if '제품명' in label_text or '상품명' in label_text:
                        extracted_data['name'] = value_text
                        print(f"✅ Name: {value_text}")

                    # Specs
                    elif '규격' in label_text or '사양' in label_text or '제품규격' in label_text:
                        extracted_data['specs']['규격/사양'] = value_text
                        print(f"✅ Specs: {value_text[:100]}")

                    # Contact - phone
                    elif '전화' in label_text:
                        phone_match = re.search(r'([\d\-\\/]+)', value_text)
                        if phone_match:
                            phone_num = phone_match.group(1).strip()
                            if phone_num:
                                extracted_data['contact']['phone'] = phone_num
                                print(f"✅ Phone: {phone_num}")

                    # Contact - fax
                    elif '팩스' in label_text:
                        fax_match = re.search(r'([\d\-\\/]+)', value_text)
                        if fax_match:
                            fax_num = fax_match.group(1).strip()
                            if fax_num:
                                extracted_data['contact']['fax'] = fax_num
                                print(f"✅ Fax: {fax_num}")

                    # Contact - email
                    elif '이메일' in label_text or '메일' in label_text:
                        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', value_text)
                        if email_match:
                            email_addr = email_match.group(1).strip()
                            if email_addr:
                                extracted_data['contact']['email'] = email_addr
                                print(f"✅ Email: {email_addr}")

                    # Manufacturer
                    elif '회사' in label_text or '제조사' in label_text or '회사명' in label_text:
                        if not extracted_data['manufacturer']:
                            extracted_data['manufacturer'] = value_text
                            print(f"✅ Manufacturer: {value_text}")

        # ===== SECTION 4: Image URLs =====
        print("\n4️⃣  IMAGE URL ANALYSIS:")
        print("-" * 80)

        img_tags = soup.find_all('img', limit=30)
        print(f"Total img tags: {len(img_tags)}")

        product_images = []
        navigation_images = []

        exclude_patterns = [
            '/BannerImg/', '/Icon/', '/images/icon', 'banner', 'logo',
            'navigation', 'menu', 'sprite', 'btn_', 'bg_',
            '/images/common', '/static/images', 'pixel', 'spacer', 'arrow'
        ]

        for img in img_tags:
            img_url = img.get('src') or img.get('data-src')
            if not img_url:
                continue

            # Make absolute URL
            if not img_url.startswith('http'):
                if img_url.startswith('/'):
                    img_url = 'https://www.freemold.net' + img_url
                else:
                    img_url = 'https://www.freemold.net/' + img_url

            # Check if valid image
            if not any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                continue

            # Check if product image or navigation
            is_excluded = any(pattern.lower() in img_url.lower() for pattern in exclude_patterns)

            if is_excluded:
                navigation_images.append(img_url)
                print(f"🚫 NAVIGATION: {img_url[:100]}")
            else:
                product_images.append(img_url)
                print(f"✅ PRODUCT: {img_url[:100]}")

        print(f"\nSummary: {len(product_images)} product images, {len(navigation_images)} navigation images")

        # ===== SECTION 5: Check for "product" substring in URLs =====
        print("\n5️⃣  CHECKING 'PRODUCT' SUBSTRING STRATEGY:")
        print("-" * 80)

        product_substring_images = []
        for img in img_tags:
            img_url = img.get('src') or img.get('data-src')
            if not img_url:
                continue

            if not img_url.startswith('http'):
                if img_url.startswith('/'):
                    img_url = 'https://www.freemold.net' + img_url
                else:
                    img_url = 'https://www.freemold.net/' + img_url

            # Check for "product" in URL
            if 'product' in img_url.lower():
                product_substring_images.append(img_url)
                print(f"✅ HAS 'product': {img_url}")

        print(f"\nTotal images with 'product' in URL: {len(product_substring_images)}")

        print("\n" + "=" * 80)
        print("📊 EXTRACTED DATA SUMMARY:")
        print(json.dumps(extracted_data, indent=2, ensure_ascii=False))

    finally:
        driver.quit()

if __name__ == '__main__':
    # Test with product ID 77866 (first product from Phase 1)
    analyze_product_page('77866')
