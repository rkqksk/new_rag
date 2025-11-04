#!/usr/bin/env python3
"""
Quick test of worker extraction to verify structure matches batch_00232.jsonl
"""
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Test with a product from batch_00232.jsonl
test_product = {
    "product_id": "37498",
    "company_no": "649",
    "product_url": "https://www.onehago.com/mall/?cate_mode=view&pid=37498&no=649",
    "category_id": 40,
    "page": 20,
    "discovered_at": "2025-10-31T21:20:54.869541"
}

print("🧪 Testing Worker Extraction Structure")
print("=" * 60)
print(f"Test URL: {test_product['product_url']}")
print()

# Setup session
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
})

try:
    # Fetch product page
    response = session.get(test_product['product_url'], timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract product name
    pack_tit = soup.find('div', class_='pack_tit')
    product_name = pack_tit.get_text(strip=True) if pack_tit else ""

    # Extract specifications from dt/dd pairs
    pack_info = soup.find('div', class_='pack_info')

    specifications = {}
    company_info = {}
    phone = ""
    fax = ""
    email = ""

    if pack_info:
        dt_elements = pack_info.find_all('dt')
        for dt in dt_elements:
            label = dt.get_text(strip=True)
            dd = dt.find_next_sibling('dd')
            value = dd.get_text(strip=True) if dd else ""

            if '코드' in label:
                specifications['코드'] = value
            elif '용량' in label:
                specifications['용량'] = value
            elif '사이즈' in label:
                specifications['사이즈'] = value
            elif 'MOQ' in label or '수량' in label:
                specifications['MOQ'] = value
            elif '재질' in label:
                specifications['재질'] = value
            elif '원산지' in label:
                specifications['원산지'] = value
            elif '제조사' in label:
                company_info['제조사'] = value
            elif '담당' in label:
                company_info['담당'] = value
            elif 'PHONE' in label or '전화' in label:
                phone = value
            elif 'FAX' in label:
                fax = value
            elif 'E MAIL' in label or 'EMAIL' in label or '이메일' in label:
                email = value

    # Extract all image URLs
    image_urls = []
    img_tags = soup.find_all('img')
    for img in img_tags:
        src = img.get('src', '')
        if src and 'productImages' in src:
            if src.startswith('http'):
                image_urls.append(src)
            else:
                image_urls.append(f"https://www.onehago.com{src}")

    # Remove duplicates while preserving order
    seen = set()
    unique_images = []
    for url in image_urls:
        if url not in seen:
            seen.add(url)
            unique_images.append(url)

    # Build result matching batch file structure
    result = {
        **test_product,
        'detail_crawled': True,
        'detail_crawled_at': datetime.now().isoformat(),
        'specifications': specifications,
        'company_info': company_info,
        'image_urls': unique_images,
        'product_name': product_name,
        'phone': phone,
        'fax': fax,
        'email': email,
        'image_count': len(unique_images)
    }

    print("✅ Extraction Result:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()
    print(f"📊 Summary:")
    print(f"   Product name: {product_name}")
    print(f"   Specifications: {len(specifications)} fields")
    print(f"   Company info: {len(company_info)} fields")
    print(f"   Images: {len(unique_images)} URLs")
    print()
    print("🎯 Structure check:")
    print(f"   ✅ Has 'specifications' dict: {isinstance(result.get('specifications'), dict)}")
    print(f"   ✅ Has 'company_info' dict: {isinstance(result.get('company_info'), dict)}")
    print(f"   ✅ Has 'image_urls' list: {isinstance(result.get('image_urls'), list)}")
    print(f"   ✅ Has 'image_count': {'image_count' in result}")
    print(f"   ✅ Has 'detail_crawled_at': {'detail_crawled_at' in result}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
