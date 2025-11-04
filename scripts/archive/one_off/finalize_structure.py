#!/usr/bin/env python3
"""
최종 폴더 구조 완성, 라벨 부여, 중복 정리

목표:
1. Category/Material/{products, images, print_area} 구조 완성
2. 각 제품에 category_label 부여 (bottle, jar, cappump)
3. 분류 안되는 제품 → 특별폴더/
4. 구식 폴더 삭제 및 정리
5. 전체 수량 집계

Usage:
    python scripts/finalize_structure.py --dry-run
    python scripts/finalize_structure.py
"""

import json
import shutil
from pathlib import Path
import argparse
from typing import Dict, Optional


class StructureFinalizer:
    """폴더 구조 최종화, 라벨 부여, 정리"""

    def __init__(self, base_dir: str = "data/crawled_products_final"):
        self.base_dir = Path(base_dir)
        self.categories = ["Bottle", "CapPump", "Jar"]
        self.materials = ["PE", "PET", "PETG", "PP", "Other"]
        self.subdirs = ["products", "images", "print_area"]

        # 라벨 매핑
        self.category_labels = {
            "Bottle": "bottle",
            "CapPump": "cappump",
            "Jar": "jar"
        }

        # 통계
        self.stats = {
            "total_products": 0,
            "labeled_products": 0,
            "special_folder_products": 0,
            "by_category": {},
            "by_material": {}
        }

    def detect_category(self, product_data: dict) -> Optional[str]:
        """제품명으로 카테고리 감지"""
        product_name = product_data.get("product_name", "").lower()

        # CapPump 키워드
        if any(kw in product_name for kw in ["펌프", "pump", "캡", "cap"]):
            return "CapPump"

        # Jar 키워드
        if any(kw in product_name for kw in ["크림", "jar", "cream"]):
            return "Jar"

        # Bottle 키워드
        if any(kw in product_name for kw in ["용기", "병", "브로우", "bottle", "ml"]):
            return "Bottle"

        return None

    def add_labels_to_products(self, dry_run: bool = False):
        """모든 제품 JSON에 category_label 추가"""

        print("=" * 80)
        print("1단계: 제품에 라벨 부여 (bottle, jar, cappump)")
        print("=" * 80)

        for category in self.categories:
            label = self.category_labels[category]

            for material in self.materials:
                products_dir = self.base_dir / category / material / "products"

                if not products_dir.exists():
                    continue

                product_files = list(products_dir.glob("idx_*.json"))

                if not product_files:
                    continue

                print(f"\n📂 {category}/{material}/ - {len(product_files)}개 제품")

                labeled_count = 0

                for json_file in product_files:
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            product_data = json.load(f)

                        # 라벨이 이미 있으면 스킵
                        if "category_label" in product_data:
                            continue

                        # 라벨 추가
                        product_data["category_label"] = label

                        if not dry_run:
                            with open(json_file, 'w', encoding='utf-8') as f:
                                json.dump(product_data, f, ensure_ascii=False, indent=2)

                        labeled_count += 1

                    except Exception as e:
                        print(f"  ❌ {json_file.name}: {e}")

                if labeled_count > 0:
                    print(f"  ✅ {labeled_count}개 제품에 '{label}' 라벨 추가")

    def create_subdirectories(self, dry_run: bool = False):
        """Category/Material/ 에 products, images, print_area 생성"""

        print("\n" + "=" * 80)
        print("2단계: 서브디렉토리 생성 (products, images, print_area)")
        print("=" * 80)

        created_count = 0

        for category in self.categories:
            for material in self.materials:
                material_dir = self.base_dir / category / material

                # products 폴더가 있는 경우만 처리
                if not (material_dir / "products").exists():
                    continue

                for subdir in self.subdirs:
                    subdir_path = material_dir / subdir

                    if not subdir_path.exists():
                        if not dry_run:
                            subdir_path.mkdir(parents=True, exist_ok=True)
                        print(f"  ✅ {category}/{material}/{subdir}/ 생성")
                        created_count += 1

        if created_count == 0:
            print("  ✓ 모든 서브디렉토리 이미 존재")

    def move_uncategorized_to_special(self, dry_run: bool = False):
        """분류 안된 제품들 → 특별폴더/Other/products/"""

        print("\n" + "=" * 80)
        print("3단계: 분류 안된 제품 → 특별폴더/")
        print("=" * 80)

        # 특별폴더 생성
        special_dir = self.base_dir / "특별폴더" / "Other"

        if not dry_run:
            for subdir in self.subdirs:
                (special_dir / subdir).mkdir(parents=True, exist_ok=True)

        print(f"📁 특별폴더/Other/ 생성")

        # 구식 플랫 폴더에서 분류 안된 제품 찾기
        uncategorized_count = 0

        old_materials = ["PE", "PET", "PETG", "PP", "Other"]

        for material in old_materials:
            old_products_dir = self.base_dir / material / "products"

            if not old_products_dir.exists():
                continue

            product_files = list(old_products_dir.glob("idx_*.json"))

            for json_file in product_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        product_data = json.load(f)

                    # 카테고리 감지
                    category = self.detect_category(product_data)

                    if category is None:
                        # 분류 안됨 → 특별폴더로
                        target_file = special_dir / "products" / json_file.name

                        # 이미 존재하는지 확인
                        already_exists = False
                        for cat in self.categories:
                            for mat in self.materials:
                                check_path = self.base_dir / cat / mat / "products" / json_file.name
                                if check_path.exists():
                                    already_exists = True
                                    break

                        if not already_exists and not target_file.exists():
                            if not dry_run:
                                shutil.copy2(json_file, target_file)

                                # 특별폴더 라벨 추가
                                with open(target_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                data["category_label"] = "special"
                                with open(target_file, 'w', encoding='utf-8') as f:
                                    json.dump(data, f, ensure_ascii=False, indent=2)

                            print(f"  ✅ {json_file.name}: {product_data.get('product_name', 'Unknown')} → 특별폴더/")
                            uncategorized_count += 1

                except Exception as e:
                    print(f"  ❌ {json_file.name}: {e}")

        if uncategorized_count == 0:
            print("  ✓ 분류 안된 제품 없음")
        else:
            print(f"\n  📊 총 {uncategorized_count}개 제품을 특별폴더로 이동")

        self.stats["special_folder_products"] = uncategorized_count

    def cleanup_old_folders(self, dry_run: bool = False):
        """구식 폴더 삭제"""

        print("\n" + "=" * 80)
        print("4단계: 구식 폴더 삭제")
        print("=" * 80)

        # 플랫 material 폴더들
        old_folders = ["PE", "PET", "PETG", "PP", "Other", "temp_crawl"]

        for folder_name in old_folders:
            folder_path = self.base_dir / folder_name

            if folder_path.exists() and folder_path.is_dir():
                try:
                    if not dry_run:
                        shutil.rmtree(folder_path)
                    print(f"  ✅ {folder_name}/ 삭제")
                except Exception as e:
                    print(f"  ❌ {folder_name}/ 삭제 실패: {e}")

        # Category 내 구식 폴더들
        for category in self.categories:
            category_dir = self.base_dir / category

            if not category_dir.exists():
                continue

            for item in category_dir.iterdir():
                if item.is_dir() and item.name not in self.materials:
                    try:
                        if not dry_run:
                            shutil.rmtree(item)
                        print(f"  ✅ {category}/{item.name}/ 삭제")
                    except Exception as e:
                        print(f"  ❌ {category}/{item.name}/ 삭제 실패: {e}")

    def generate_final_report(self):
        """최종 수량 집계 보고서"""

        print("\n" + "=" * 80)
        print("최종 수량 집계 (추가 크롤링 준비)")
        print("=" * 80)

        total = 0

        # Category별 집계
        for category in self.categories:
            category_total = 0
            label = self.category_labels[category]

            print(f"\n📦 {category} (라벨: {label})")

            for material in self.materials:
                products_dir = self.base_dir / category / material / "products"

                if products_dir.exists():
                    count = len(list(products_dir.glob("idx_*.json")))

                    if count > 0:
                        print(f"  {material}: {count}개")
                        category_total += count

            if category_total > 0:
                print(f"  소계: {category_total}개")
                total += category_total
                self.stats["by_category"][category] = category_total

        # 특별폴더 집계
        special_dir = self.base_dir / "특별폴더" / "Other" / "products"
        if special_dir.exists():
            special_count = len(list(special_dir.glob("idx_*.json")))
            if special_count > 0:
                print(f"\n📁 특별폴더 (라벨: special)")
                print(f"  Other: {special_count}개")
                total += special_count

        print("\n" + "=" * 80)
        print(f"✅ 전체: {total}개 제품")
        print("=" * 80)

        self.stats["total_products"] = total

        # 크롤링 범위 분석
        print("\n📊 크롤링 범위 분석:")

        all_indices = set()

        # 모든 제품의 인덱스 수집
        for category in self.categories:
            for material in self.materials:
                products_dir = self.base_dir / category / material / "products"
                if products_dir.exists():
                    for json_file in products_dir.glob("idx_*.json"):
                        idx = int(json_file.stem.replace("idx_", ""))
                        all_indices.add(idx)

        # 특별폴더도 포함
        special_dir = self.base_dir / "특별폴더" / "Other" / "products"
        if special_dir.exists():
            for json_file in special_dir.glob("idx_*.json"):
                idx = int(json_file.stem.replace("idx_", ""))
                all_indices.add(idx)

        if all_indices:
            min_idx = min(all_indices)
            max_idx = max(all_indices)

            print(f"  최소 인덱스: {min_idx}")
            print(f"  최대 인덱스: {max_idx}")
            print(f"  범위: idx {min_idx} ~ {max_idx}")
            print(f"  총 범위: {max_idx - min_idx + 1}개")
            print(f"  크롤링 완료: {len(all_indices)}개")
            print(f"  누락 가능: {max_idx - min_idx + 1 - len(all_indices)}개")

    def run(self, dry_run: bool = False):
        """전체 프로세스 실행"""

        print("\n" + "🔧" * 40)
        print("폴더 구조 최종화 + 라벨 부여 + 정리")
        print("🔧" * 40)
        print(f"Base: {self.base_dir}")
        print(f"Mode: {'DRY RUN (미리보기)' if dry_run else 'LIVE (실제 실행)'}")
        print("🔧" * 40)

        # 1. 라벨 부여
        self.add_labels_to_products(dry_run)

        # 2. 서브디렉토리 생성
        self.create_subdirectories(dry_run)

        # 3. 분류 안된 제품 → 특별폴더
        self.move_uncategorized_to_special(dry_run)

        # 4. 구식 폴더 삭제
        self.cleanup_old_folders(dry_run)

        # 5. 최종 보고서
        if not dry_run:
            self.generate_final_report()

        print("\n" + "=" * 80)
        if dry_run:
            print("✅ DRY RUN 완료 - 실제 변경 없음")
            print("실행: python scripts/finalize_structure.py")
        else:
            print("✅ 폴더 구조 최종화 완료!")
            print("✅ 추가 크롤링 준비 완료!")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="폴더 구조 최종화")
    parser.add_argument("--dry-run", action="store_true", help="미리보기")
    parser.add_argument("--base-dir", default="data/crawled_products_final")

    args = parser.parse_args()

    finalizer = StructureFinalizer(base_dir=args.base_dir)
    finalizer.run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
