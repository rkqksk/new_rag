#!/usr/bin/env python3
"""
남은 187개 제품의 이미지 크롤링
"""
import json
import requests
from pathlib import Path
import time

# 누락된 idx 로드
with open('/Users/oypnus/Project/rag-enterprise/missing_all_images.json', 'r') as f:
    missing_idx_list = json.load(f)

print(f"총 {len(missing_idx_list)}개 제품의 이미지를 크롤링합니다.\n")

base_dir = Path('/Users/oypnus/Project/rag-enterprise/data/crawled_products_final')

success_count = 0
error_count = 0
errors = []

for idx in missing_idx_list:
    idx_str = str(idx)
    
    # 제품 JSON 파일 찾기 (모든 카테고리 검색)
    json_file = None
    category = None
    material = None
    
    for category_dir in base_dir.iterdir():
        if not category_dir.is_dir() or category_dir.name == 'Cap':
            continue
        
        for material_dir in category_dir.iterdir():
            if not material_dir.is_dir():
                continue
            
            products_dir = material_dir / 'products'
            candidate = products_dir / f'idx_{idx_str}.json'
            
            if candidate.exists():
                json_file = candidate
                category = category_dir.name
                material = material_dir.name
                break
        
        if json_file:
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
    
    # 이미지 디렉토리 생성
    images_dir = json_file.parent.parent / 'images'
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
            img_info['local_path'] = f"data/crawled_products_final/{category}/{material}/images/{img_filename}"
            downloaded_images.append(img_info)
            
            time.sleep(0.5)
            
        except Exception as e:
            errors.append(f"idx_{idx_str}: {str(e)[:50]}")
    
    if downloaded_images:
        print(f"✅ idx_{idx_str} ({product_name}): {len(downloaded_images)}개 이미지")
        
        # JSON 업데이트
        product['downloaded_images'] = downloaded_images
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(product, f, ensure_ascii=False, indent=2)
        
        success_count += 1
    else:
        print(f"❌ idx_{idx_str} ({product_name}): 다운로드 실패")
        error_count += 1

print(f"\n{'='*80}")
print(f"✅ 성공: {success_count}/{len(missing_idx_list)}")
print(f"❌ 실패: {error_count}/{len(missing_idx_list)}")
print(f"{'='*80}")

if errors[:10]:
    print(f"\n에러 샘플:")
    for err in errors[:10]:
        print(f"  {err}")
