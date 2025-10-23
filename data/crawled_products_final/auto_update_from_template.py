# 수집 데이터 자동 통합 스크립트
# 사용법: python3 auto_update_from_template.py <템플릿파일.xlsx>

import pandas as pd
import json
from pathlib import Path
import sys

if len(sys.argv) < 2:
    print("사용법: python3 auto_update_from_template.py <템플릿파일.xlsx>")
    sys.exit(1)

template_file = sys.argv[1]
base_dir = Path('data/crawled_products_final')

# Load template
df = pd.read_excel(template_file, sheet_name=0)

updated_count = 0

for _, row in df.iterrows():
    json_file = base_dir / row['_json_file']
    
    if not json_file.exists():
        print(f"⚠️ 파일 없음: {json_file}")
        continue
    
    # Load product
    with open(json_file, 'r', encoding='utf-8') as f:
        product = json.load(f)
    
    # Update pricing
    if 'pricing' not in product:
        product['pricing'] = {}
    
    if pd.notna(row.get('정상가')) and row.get('정상가') != '':
        product['pricing']['regular_price'] = float(row['정상가'])
    
    if pd.notna(row.get('할인가')) and row.get('할인가') != '':
        product['pricing']['discount_price'] = float(row['할인가'])
    
    if pd.notna(row.get('공급가')) and row.get('공급가') != '':
        product['pricing']['supply_price'] = float(row['공급가'])
    
    if pd.notna(row.get('판매가')) and row.get('판매가') != '':
        product['pricing']['selling_price'] = float(row['판매가'])
    
    # Update coating
    if pd.notna(row.get('코팅가격')) and row.get('코팅가격') != '':
        if 'coating_options' not in product['pricing']:
            product['pricing']['coating_options'] = []
        product['pricing']['coating_options'] = [{
            'type': 'matte_coating',
            'name': '무광코팅',
            'price': float(row['코팅가격']),
            'note': '2코팅, 그라데이션 등 별도 코팅은 문의 바랍니다'
        }]
    
    # Update specs
    if pd.notna(row.get('업체명')) and row.get('업체명') != '':
        if 'product_list_info' not in product:
            product['product_list_info'] = {}
        product['product_list_info']['vendor'] = str(row['업체명'])
    
    if pd.notna(row.get('SPEC')) and row.get('SPEC') != '':
        if 'product_list_info' not in product:
            product['product_list_info'] = {}
        product['product_list_info']['spec'] = str(row['SPEC'])
    
    if pd.notna(row.get('사양')) and row.get('사양') != '':
        if 'product_list_info' not in product:
            product['product_list_info'] = {}
        product['product_list_info']['detail'] = str(row['사양'])
    
    if pd.notna(row.get('포장')) and row.get('포장') != '':
        if 'product_list_info' not in product:
            product['product_list_info'] = {}
        product['product_list_info']['package'] = str(row['포장'])
    
    # Save
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(product, f, ensure_ascii=False, indent=2)
    
    updated_count += 1
    print(f"✅ 업데이트: {row['제품명']}")

print(f"\n총 {updated_count}개 제품 업데이트 완료!")