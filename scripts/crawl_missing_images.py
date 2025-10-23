#!/usr/bin/env python3
"""
누락된 이미지만 다시 크롤링
"""

import json
import requests
from pathlib import Path
import time
from urllib.parse import urljoin

# 누락된 idx 로드
missing_idx_file = Path('/Users/oypnus/Project/rag-enterprise/missing_image_idx.json')
with open(missing_idx_file, 'r') as f:
    missing_idx_list = json.load(f)

print(f"총 {len(missing_idx_list)}개 제품의 이미지를 크롤링합니다.\n")

base_dir = Path('/Users/oypnus/Project/rag-enterprise/data/crawled_products_final/Bottle')

success_count = 0
error_count = 0
errors = []

for idx in missing_idx_list:
    idx_str = str(idx)
    
    # 제품 JSON 파일 찾기
    json_file = None
    material = None
    
    for material_dir in base_dir.iterdir():
        if not material_dir.is_dir():
            continue
        
        products_dir = material_dir / 'products'
        candidate = products_dir / f'idx_{idx_str}.json'
        
        if candidate.exists():
            json_file = candidate
            material = material_dir.name
            break
    
    if not json_file:
        print(f"❌ idx_{idx_str}: JSON 파일 못찾음")
        error_count += 1
        continue
    
    # JSON 읽기
    with open(json_file, 'r', encoding='utf-8') as f:
        product = json.load(f)
    
    product_name = product.get('product_name', 'N/A')
    images_info = product.get('images', [])
    
    if not images_info:
        print(f"❌ idx_{idx_str} ({product_name}): 이미지 URL 정보 없음")
        error_count += 1
        continue
    
    # 이미지 다운로드
    images_dir = base_dir / material / 'images'
    images_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded_images = []
    
    for img_idx, img_info in enumerate(images_info, 1):
        img_url = img_info.get('url', '')
        img_type = img_info.get('type', 'unknown')
        
        if not img_url:
            continue
        
        try:
            response = requests.get(img_url, timeout=10)
            response.raise_for_status()
            
            # 파일명 생성
            img_filename = f"idx_{idx_str}_{img_type}_{img_idx}.jpg"
            img_path = images_dir / img_filename
            
            # 저장
            with open(img_path, 'wb') as f:
                f.write(response.content)
            
            # downloaded_images에 추가
            img_info['local_path'] = f"data/crawled_products_final/Bottle/{material}/images/{img_filename}"
            downloaded_images.append(img_info)
            
            print(f"✅ idx_{idx_str} ({product_name}): {img_filename}")
            
            time.sleep(0.5)  # 서버 부담 줄이기
            
        except Exception as e:
            print(f"❌ idx_{idx_str} ({product_name}): {str(e)[:50]}")
            errors.append(f"idx_{idx_str}: {str(e)}")
    
    # JSON 업데이트
    if downloaded_images:
        product['downloaded_images'] = downloaded_images
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(product, f, ensure_ascii=False, indent=2)
        
        success_count += 1
    else:
        error_count += 1

print(f"\n{'='*80}")
print(f"✅ 성공: {success_count}/{len(missing_idx_list)}")
print(f"❌ 실패: {error_count}/{len(missing_idx_list)}")
print(f"{'='*80}")

if errors:
    print(f"\n에러 상세 (최대 20개):")
    for err in errors[:20]:
        print(f"  {err}")
