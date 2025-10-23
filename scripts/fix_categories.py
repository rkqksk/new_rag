#!/usr/bin/env python3
"""
잘못된 카테고리 수정
"""
import json
import shutil
from pathlib import Path

# 잘못 분류된 제품 로드
with open('/Users/oypnus/Project/rag-enterprise/misclassified_categories.json', 'r') as f:
    misclassified = json.load(f)

print(f"총 {len(misclassified)}개 제품의 카테고리를 수정합니다.\n")

base_dir = Path('/Users/oypnus/Project/rag-enterprise/data/crawled_products_final')

success = 0
errors = []

for item in misclassified:
    idx = item['idx']
    current_cat = item['current_category'].capitalize()
    expected_cat = item['expected_category'].capitalize()
    
    # 현재 경로에서 파일 찾기
    old_json_path = Path(item['path'])
    
    if not old_json_path.exists():
        errors.append(f"idx_{idx}: 파일 못찾음")
        continue
    
    # 제품 정보 읽기
    with open(old_json_path, 'r', encoding='utf-8') as f:
        product = json.load(f)
    
    # 카테고리 레이블 업데이트
    product['category_label'] = expected_cat.lower()
    
    # 재질 확인
    specs = product.get('specifications', {})
    material = specs.get('재질(원료)', 'Other')
    
    # 새 경로 생성
    new_dir = base_dir / expected_cat / material / 'products'
    new_dir.mkdir(parents=True, exist_ok=True)
    
    new_json_path = new_dir / f"idx_{idx}.json"
    
    # JSON 저장
    with open(new_json_path, 'w', encoding='utf-8') as f:
        json.dump(product, f, ensure_ascii=False, indent=2)
    
    # 이미지 파일 이동
    old_images_dir = old_json_path.parent.parent / 'images'
    new_images_dir = base_dir / expected_cat / material / 'images'
    new_images_dir.mkdir(parents=True, exist_ok=True)
    
    moved_images = 0
    for img_file in old_images_dir.glob(f"idx_{idx}_*.jpg"):
        new_img_path = new_images_dir / img_file.name
        shutil.move(str(img_file), str(new_img_path))
        moved_images += 1
    
    # 기존 JSON 삭제
    old_json_path.unlink()
    
    print(f"✅ idx_{idx}: {current_cat} → {expected_cat} (이미지 {moved_images}개)")
    success += 1

print(f"\n{'='*80}")
print(f"✅ 성공: {success}/{len(misclassified)}")
print(f"❌ 실패: {len(errors)}")
print(f"{'='*80}")

if errors:
    print(f"\n에러:")
    for err in errors[:10]:
        print(f"  {err}")
