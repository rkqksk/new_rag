#!/usr/bin/env python3
"""
Data Integrity & Quality Check
Final inspection of crawled products
"""

import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict


class DataIntegrityChecker:
    """Comprehensive data quality checker"""

    def __init__(self, base_dir: str = "data/crawled_products_final"):
        self.base_dir = Path(base_dir)
        self.categories = ["Bottle", "CapPump", "Jar", "특별폴더"]
        self.materials = ["PE", "PET", "PETG", "PP", "Other"]

        self.stats = {
            "total_products": 0,
            "by_category": defaultdict(int),
            "defects": {
                "missing_product_name": [],
                "missing_category_label": [],
                "missing_specifications": [],
                "empty_specifications": [],
                "missing_images": [],
                "no_downloaded_images": [],
                "missing_material_spec": [],
                "unknown_product": []
            },
            "quality": {
                "complete_products": 0,
                "products_with_images": 0,
                "products_with_specs": 0,
                "products_with_print_area": 0
            }
        }

    def check_product(self, json_path: Path) -> Dict:
        """Check individual product data"""

        issues = []

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            return {"issues": [f"JSON parse error: {e}"]}

        # 1. Product Name
        product_name = data.get("product_name", "")
        if not product_name:
            issues.append("missing_product_name")
        elif product_name == "Unknown Product":
            issues.append("unknown_product")

        # 2. Category Label
        if "category_label" not in data:
            issues.append("missing_category_label")

        # 3. Specifications
        specs = data.get("specifications", {})
        if not specs:
            issues.append("empty_specifications")
        else:
            # Check for material spec
            has_material = False
            for key in specs.keys():
                if any(kw in key for kw in ["재질", "Material", "원료"]):
                    has_material = True
                    break

            if not has_material:
                issues.append("missing_material_spec")

        # 4. Images
        images = data.get("images", [])
        downloaded_images = data.get("downloaded_images", [])

        if not images:
            issues.append("missing_images")

        if not downloaded_images:
            issues.append("no_downloaded_images")

        # Quality metrics
        is_complete = (
            product_name and
            product_name != "Unknown Product" and
            specs and
            images
        )

        return {
            "issues": issues,
            "is_complete": is_complete,
            "has_images": len(images) > 0,
            "has_specs": len(specs) > 0,
            "has_print_area": bool(data.get("print_area_url")),
            "product_name": product_name,
            "spec_count": len(specs),
            "image_count": len(images)
        }

    def scan_all_products(self):
        """Scan all products and collect statistics"""

        print("=" * 80)
        print("Data Integrity Check - Full Inspection")
        print("=" * 80)

        for category in self.categories:
            for material in self.materials:
                products_dir = self.base_dir / category / material / "products"

                if not products_dir.exists():
                    continue

                product_files = list(products_dir.glob("idx_*.json"))

                for json_file in product_files:
                    self.stats["total_products"] += 1
                    self.stats["by_category"][category] += 1

                    result = self.check_product(json_file)

                    # Track issues
                    for issue in result["issues"]:
                        self.stats["defects"][issue].append({
                            "idx": json_file.stem,
                            "path": f"{category}/{material}",
                            "product_name": result.get("product_name", "Unknown")
                        })

                    # Track quality
                    if result["is_complete"]:
                        self.stats["quality"]["complete_products"] += 1
                    if result["has_images"]:
                        self.stats["quality"]["products_with_images"] += 1
                    if result["has_specs"]:
                        self.stats["quality"]["products_with_specs"] += 1
                    if result["has_print_area"]:
                        self.stats["quality"]["products_with_print_area"] += 1

    def print_report(self):
        """Print comprehensive report"""

        print("\n" + "=" * 80)
        print("FINAL INSPECTION REPORT")
        print("=" * 80)

        # Overview
        print("\n📊 Overview:")
        print(f"  Total Products: {self.stats['total_products']}")

        print("\n  By Category:")
        for category, count in sorted(self.stats['by_category'].items()):
            pct = (count / self.stats['total_products'] * 100) if self.stats['total_products'] > 0 else 0
            print(f"    {category}: {count} ({pct:.1f}%)")

        # Quality Metrics
        print("\n" + "-" * 80)
        print("✅ Quality Metrics:")

        total = self.stats['total_products']

        complete = self.stats['quality']['complete_products']
        complete_pct = (complete / total * 100) if total > 0 else 0
        print(f"  Complete Products: {complete}/{total} ({complete_pct:.1f}%)")

        with_images = self.stats['quality']['products_with_images']
        images_pct = (with_images / total * 100) if total > 0 else 0
        print(f"  Products with Images: {with_images}/{total} ({images_pct:.1f}%)")

        with_specs = self.stats['quality']['products_with_specs']
        specs_pct = (with_specs / total * 100) if total > 0 else 0
        print(f"  Products with Specs: {with_specs}/{total} ({specs_pct:.1f}%)")

        with_print = self.stats['quality']['products_with_print_area']
        print_pct = (with_print / total * 100) if total > 0 else 0
        print(f"  Products with Print Area: {with_print}/{total} ({print_pct:.1f}%)")

        # Defects Summary
        print("\n" + "-" * 80)
        print("⚠️  Defects Summary:")

        total_defects = 0
        for defect_type, items in self.stats['defects'].items():
            if items:
                total_defects += len(items)
                print(f"  {defect_type}: {len(items)} cases")

        if total_defects == 0:
            print("  ✅ No defects found!")

        # Detailed Defects
        print("\n" + "=" * 80)
        print("🔍 Detailed Defects (Top 10 per type):")
        print("=" * 80)

        for defect_type, items in self.stats['defects'].items():
            if items:
                print(f"\n⚠️  {defect_type.upper()} ({len(items)} total):")
                for item in items[:10]:  # Show first 10
                    print(f"    {item['idx']} | {item['path']} | {item['product_name']}")

                if len(items) > 10:
                    print(f"    ... and {len(items) - 10} more")

        # Action Items
        print("\n" + "=" * 80)
        print("📋 ACTION ITEMS - What to Fill Up Later:")
        print("=" * 80)

        action_items = []

        # Priority 1: Critical issues
        if self.stats['defects']['unknown_product']:
            action_items.append({
                "priority": "HIGH",
                "issue": "Unknown Products",
                "count": len(self.stats['defects']['unknown_product']),
                "action": "These products need to be re-crawled or manually verified"
            })

        if self.stats['defects']['missing_product_name']:
            action_items.append({
                "priority": "HIGH",
                "issue": "Missing Product Names",
                "count": len(self.stats['defects']['missing_product_name']),
                "action": "Product names are essential - needs immediate attention"
            })

        # Priority 2: Important issues
        if self.stats['defects']['empty_specifications']:
            action_items.append({
                "priority": "MEDIUM",
                "issue": "Empty Specifications",
                "count": len(self.stats['defects']['empty_specifications']),
                "action": "Add product specifications (material, size, etc.)"
            })

        if self.stats['defects']['missing_material_spec']:
            action_items.append({
                "priority": "MEDIUM",
                "issue": "Missing Material in Specs",
                "count": len(self.stats['defects']['missing_material_spec']),
                "action": "Material classification is incomplete - affects search quality"
            })

        if self.stats['defects']['no_downloaded_images']:
            action_items.append({
                "priority": "MEDIUM",
                "issue": "Images Not Downloaded",
                "count": len(self.stats['defects']['no_downloaded_images']),
                "action": "Images exist but weren't downloaded - check download logic"
            })

        # Priority 3: Nice to have
        if self.stats['defects']['missing_category_label']:
            action_items.append({
                "priority": "LOW",
                "issue": "Missing Category Labels",
                "count": len(self.stats['defects']['missing_category_label']),
                "action": "Add category_label field for better filtering"
            })

        if action_items:
            for idx, item in enumerate(action_items, 1):
                print(f"\n{idx}. [{item['priority']}] {item['issue']}")
                print(f"   Count: {item['count']} products")
                print(f"   Action: {item['action']}")
        else:
            print("\n✅ No action items - data quality is excellent!")

        # Data Completeness Score
        print("\n" + "=" * 80)
        print("📈 Data Completeness Score:")
        print("=" * 80)

        completeness_score = (complete_pct + images_pct + specs_pct) / 3

        print(f"\n  Overall Score: {completeness_score:.1f}%")

        if completeness_score >= 90:
            grade = "A+ (Excellent)"
        elif completeness_score >= 80:
            grade = "A (Very Good)"
        elif completeness_score >= 70:
            grade = "B (Good)"
        elif completeness_score >= 60:
            grade = "C (Fair)"
        else:
            grade = "D (Needs Improvement)"

        print(f"  Grade: {grade}")

        print("\n" + "=" * 80)


def main():
    checker = DataIntegrityChecker()
    checker.scan_all_products()
    checker.print_report()


if __name__ == "__main__":
    main()
