#!/usr/bin/env python3
"""
Debug script to analyze onehago product page HTML structure
Focus: Contact extraction patterns and image URL filtering strategy
"""

import json
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

def analyze_product_page(product_id):
    """Fetch and analyze onehago product page structure"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Construct onehago URL (example based on common patterns)
        url = f"https://www.1hagoshop.com/product/detail.html?product_no={product_id}"

        print(f"\n🔍 Analyzing onehago product {product_id}")
        print(f"URL: {url}")
        print("=" * 80)

        try:
            # Navigate to product page
            page.goto(url, timeout=15000)
            page.wait_for_load_state('networkidle')

            # Get page source
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # ===== SECTION 1: Find ALL tables and their structure =====
            print("\n1️⃣  ALL TABLE STRUCTURE:")
            print("-" * 80)
            tables = soup.find_all('table')
            print(f"Total tables: {len(tables)}")

            for table_idx, table in enumerate(tables[:5]):  # First 5 tables
                print(f"\n📊 Table {table_idx}:")
                rows = table.find_all('tr')
                print(f"   Rows: {len(rows)}")

                for row_idx, row in enumerate(rows[:10]):  # First 10 rows
                    cells = row.find_all(['td', 'th'])
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
                '연락처': 'phone',
                '핸드폰': 'phone',
                '팩스': 'fax',
                '이메일': 'email',
                '메일': 'email',
                '회사': 'company',
                '제조사': 'manufacturer',
                '판매처': 'seller',
                '담당자': 'contact_person',
            }

            html_text = soup.get_text()
            found_keywords = []
            for korean_key, english_key in contact_keywords.items():
                if korean_key in html_text:
                    found_keywords.append((korean_key, english_key))
                    print(f"✅ Found '{korean_key}' ({english_key})")

                    # Find context
                    idx = html_text.find(korean_key)
                    context = html_text[max(0, idx-100):idx+150]
                    print(f"   Context: ...{context}...")
                else:
                    print(f"❌ NOT found: '{korean_key}' ({english_key})")

            # ===== SECTION 3: Extract from table patterns =====
            print("\n3️⃣  TABLE-BASED EXTRACTION (test logic):")
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
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label_cell = cells[0]
                        value_cell = cells[1]

                        label_text = label_cell.get_text(strip=True).lower()
                        value_text = value_cell.get_text(strip=True)

                        if not value_text:
                            continue

                        # Product name
                        if '상품명' in label_text or '제품명' in label_text or '상품' in label_text:
                            if not extracted_data['name']:
                                extracted_data['name'] = value_text
                                print(f"✅ Name: {value_text[:80]}")

                        # Specs
                        elif '규격' in label_text or '사양' in label_text or '스펙' in label_text:
                            extracted_data['specs'][label_text] = value_text
                            print(f"✅ Specs ({label_text}): {value_text[:80]}")

                        # Contact - phone
                        elif '전화' in label_text or '연락처' in label_text:
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
                        elif '이메일' in label_text or '메일' in label_text or '이메일' in label_text:
                            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', value_text)
                            if email_match:
                                email_addr = email_match.group(1).strip()
                                if email_addr:
                                    extracted_data['contact']['email'] = email_addr
                                    print(f"✅ Email: {email_addr}")

                        # Manufacturer
                        elif '제조사' in label_text or '판매처' in label_text or '회사' in label_text:
                            if not extracted_data['manufacturer']:
                                extracted_data['manufacturer'] = value_text
                                print(f"✅ Manufacturer: {value_text[:80]}")

            # ===== SECTION 4: Image URLs =====
            print("\n4️⃣  IMAGE URL ANALYSIS:")
            print("-" * 80)

            img_tags = soup.find_all('img', limit=50)
            print(f"Total img tags found: {len(img_tags)}")

            product_images = []
            all_images = []

            for img in img_tags:
                img_url = img.get('src') or img.get('data-src')
                if not img_url:
                    continue

                # Make absolute URL if needed
                if not img_url.startswith('http'):
                    if img_url.startswith('/'):
                        img_url = 'https://www.1hagoshop.com' + img_url
                    else:
                        img_url = 'https://www.1hagoshop.com/' + img_url

                all_images.append(img_url)

                # Check if valid image extension
                if not any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    continue

                # Check for "product" substring (strategy from Freemold)
                if 'product' in img_url.lower():
                    product_images.append(img_url)
                    print(f"✅ PRODUCT: {img_url[:120]}")

            print(f"\n📊 Summary:")
            print(f"   Total images found: {len(all_images)}")
            print(f"   Product images (with 'product' in URL): {len(product_images)}")

            # ===== SECTION 5: Detailed img tag analysis =====
            print("\n5️⃣  DETAILED IMAGE ANALYSIS:")
            print("-" * 80)

            for idx, img in enumerate(img_tags[:15]):  # First 15 images
                src = img.get('src') or img.get('data-src') or 'NO_SRC'
                alt = img.get('alt') or 'NO_ALT'
                classes = img.get('class') or []
                id_attr = img.get('id') or 'NO_ID'

                print(f"\n📸 Image {idx}:")
                print(f"   SRC: {src[:100]}")
                print(f"   ALT: {alt[:60]}")
                print(f"   CLASS: {classes}")
                print(f"   ID: {id_attr}")

            # ===== SECTION 6: Check for "product" substring patterns =====
            print("\n6️⃣  CHECKING 'PRODUCT' SUBSTRING STRATEGY:")
            print("-" * 80)

            product_substring_images = []
            other_images = []

            for img_url in all_images:
                if 'product' in img_url.lower():
                    product_substring_images.append(img_url)
                else:
                    other_images.append(img_url)

            print(f"\nImages with 'product' in URL: {len(product_substring_images)}")
            for img_url in product_substring_images[:10]:
                print(f"  ✅ {img_url[:100]}")

            print(f"\nImages WITHOUT 'product' in URL: {len(other_images)}")
            for img_url in other_images[:10]:
                print(f"  ❌ {img_url[:100]}")

            # ===== FINAL SUMMARY =====
            print("\n" + "=" * 80)
            print("📊 EXTRACTED DATA SUMMARY:")
            print(json.dumps(extracted_data, indent=2, ensure_ascii=False))

            print("\n" + "=" * 80)
            print("🎯 RECOMMENDATIONS FOR onehago EXTRACTION:")
            print("-" * 80)
            print(f"✅ Found keywords: {[k[0] for k in found_keywords]}")
            print(f"✅ Strategy for contact: {'Table-based extraction' if extracted_data['contact'] else 'Need alternative strategy'}")
            print(f"✅ Strategy for images: Use 'product' substring filtering")

        except Exception as e:
            print(f"\n❌ Error analyzing page: {e}")

        finally:
            browser.close()

if __name__ == '__main__':
    # Test with a sample product ID from onehago
    # These are typical onehago product IDs based on their URL structure
    sample_product_ids = [
        "100000000",  # Sample ID
        "100000001",  # Sample ID
    ]

    print("\n" + "=" * 80)
    print("🔍 ONEHAGO HTML STRUCTURE ANALYSIS")
    print("=" * 80)
    print("Analyzing onehago product pages to identify contact and image extraction patterns")
    print("=" * 80)

    # Try first sample product
    analyze_product_page(sample_product_ids[0])
