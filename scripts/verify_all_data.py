#!/usr/bin/env python3
"""
Comprehensive data verification script
Checks:
1. Product data completeness
2. Image file existence
3. Detail extraction status
4. Data quality per category
"""

import json
from pathlib import Path
from collections import defaultdict

class DataVerifier:
    def __init__(self):
        self.crawled_dir = Path('data/onehago/crawled')
        self.images_dir = self.crawled_dir / 'images'

        self.stats = {
            'total_products': 0,
            'products_with_urls': 0,
            'products_with_image_paths': 0,
            'images_actually_exist': 0,
            'products_with_details': 0,
            'products_with_specs': 0,
            'categories_complete': [],
            'categories_partial': [],
            'categories_empty': []
        }

        self.category_details = {}

    def verify_image_exists(self, image_path):
        """Check if image file actually exists"""
        if not image_path:
            return False

        # Try relative to crawled dir
        full_path = self.crawled_dir / image_path
        if full_path.exists():
            return True

        # Try direct path
        direct_path = Path(image_path)
        if direct_path.exists():
            return True

        return False

    def analyze_product(self, product):
        """Analyze single product completeness"""
        quality = {
            'has_id': bool(product.get('product_id')),
            'has_name': bool(product.get('product_name') or product.get('detailed_name')),
            'has_url': bool(product.get('detail_url') or product.get('product_url')),
            'has_image_url': bool(product.get('thumbnail_url') or product.get('full_image_url') or product.get('image_url')),
            'has_image_path': bool(product.get('image_path')),
            'image_exists': False,
            'has_details': bool(product.get('detail_crawled')),
            'has_specs': bool(product.get('specifications')),
            'has_manufacturer': bool(product.get('manufacturer')),
            'has_contact': bool(product.get('phone') or product.get('email'))
        }

        # Check if image actually exists
        if quality['has_image_path']:
            quality['image_exists'] = self.verify_image_exists(product.get('image_path'))

        return quality

    def verify_category_file(self, file_path):
        """Verify single category file"""
        try:
            with open(file_path) as f:
                products = json.load(f)

            if not products:
                return None

            cat_id = products[0].get('category_id', 'unknown')

            category_stats = {
                'category_id': cat_id,
                'file': file_path.name,
                'total_products': len(products),
                'with_urls': 0,
                'with_image_urls': 0,
                'with_image_paths': 0,
                'images_exist': 0,
                'with_details': 0,
                'with_specs': 0,
                'with_manufacturer': 0,
                'with_contact': 0,
                'quality_score': 0.0
            }

            for product in products:
                quality = self.analyze_product(product)

                if quality['has_url']:
                    category_stats['with_urls'] += 1
                if quality['has_image_url']:
                    category_stats['with_image_urls'] += 1
                if quality['has_image_path']:
                    category_stats['with_image_paths'] += 1
                if quality['image_exists']:
                    category_stats['images_exist'] += 1
                if quality['has_details']:
                    category_stats['with_details'] += 1
                if quality['has_specs']:
                    category_stats['with_specs'] += 1
                if quality['has_manufacturer']:
                    category_stats['with_manufacturer'] += 1
                if quality['has_contact']:
                    category_stats['with_contact'] += 1

            # Calculate quality score
            total = category_stats['total_products']
            if total > 0:
                scores = [
                    category_stats['with_urls'] / total,
                    category_stats['with_image_urls'] / total,
                    category_stats['images_exist'] / total,
                    category_stats['with_details'] / total,
                    category_stats['with_specs'] / total
                ]
                category_stats['quality_score'] = sum(scores) / len(scores) * 100

            return category_stats

        except Exception as e:
            print(f"  ❌ Error reading {file_path.name}: {e}")
            return None

    def run_verification(self):
        """Run comprehensive verification"""
        print("="*70)
        print("🔍 Comprehensive Data Verification")
        print("="*70)

        # Check images directory
        print(f"\n📁 Checking directories...")
        print(f"   Crawled dir: {self.crawled_dir}")
        print(f"   Images dir: {self.images_dir}")

        if self.images_dir.exists():
            image_files = list(self.images_dir.glob('*.jpg')) + list(self.images_dir.glob('*.png'))
            print(f"   ✅ Images directory exists: {len(image_files)} image files")
        else:
            print(f"   ❌ Images directory does not exist!")

        # Collect all category files
        all_files = []

        # Parent directory
        parent_files = list(self.crawled_dir.glob('category_*.json'))
        all_files.extend(parent_files)

        # Categories subdirectory
        cat_subdir = self.crawled_dir / 'categories'
        if cat_subdir.exists():
            subdir_files = list(cat_subdir.glob('category_*.json'))
            all_files.extend(subdir_files)

        print(f"\n📋 Found {len(all_files)} category files")
        print(f"   Parent directory: {len(parent_files)}")
        print(f"   Categories subdir: {len(subdir_files) if cat_subdir.exists() else 0}")

        # Verify each file
        print(f"\n{'='*70}")
        print(f"📊 Category-by-Category Analysis")
        print(f"{'='*70}")
        print(f"{'Cat':>4s} {'File':>30s} {'Prods':>6s} {'URLs':>5s} {'Imgs':>5s} {'Exist':>6s} {'Details':>7s} {'Quality':>7s}")
        print(f"{'-'*70}")

        for file_path in sorted(all_files):
            stats = self.verify_category_file(file_path)

            if stats:
                cat_id = stats['category_id']

                # Store for later analysis
                if cat_id not in self.category_details:
                    self.category_details[cat_id] = []
                self.category_details[cat_id].append(stats)

                # Print row
                url_pct = stats['with_urls'] / stats['total_products'] * 100 if stats['total_products'] > 0 else 0
                img_pct = stats['with_image_urls'] / stats['total_products'] * 100 if stats['total_products'] > 0 else 0
                exist_pct = stats['images_exist'] / stats['total_products'] * 100 if stats['total_products'] > 0 else 0
                detail_pct = stats['with_details'] / stats['total_products'] * 100 if stats['total_products'] > 0 else 0

                print(f"{cat_id:>4s} {stats['file']:>30s} {stats['total_products']:>6d} "
                      f"{url_pct:>4.0f}% {img_pct:>4.0f}% {exist_pct:>5.0f}% "
                      f"{detail_pct:>6.0f}% {stats['quality_score']:>6.1f}%")

        print(f"{'='*70}")

        # Consolidate duplicates
        print(f"\n🔄 Consolidating duplicate categories...")
        consolidated = {}

        for cat_id, file_stats in self.category_details.items():
            if len(file_stats) > 1:
                print(f"   ⚠️  Category {cat_id}: {len(file_stats)} files found")
                # Use the one with highest quality
                best = max(file_stats, key=lambda x: x['quality_score'])
                consolidated[cat_id] = best
            else:
                consolidated[cat_id] = file_stats[0]

        # Final summary
        print(f"\n{'='*70}")
        print(f"📊 Final Summary")
        print(f"{'='*70}")

        total_products = sum(s['total_products'] for s in consolidated.values())
        total_with_images_exist = sum(s['images_exist'] for s in consolidated.values())
        total_with_details = sum(s['with_details'] for s in consolidated.values())
        total_with_specs = sum(s['with_specs'] for s in consolidated.values())

        print(f"\n✅ Unique Categories: {len(consolidated)}")
        print(f"📦 Total Products: {total_products:,}")
        print(f"🖼️  Images Actually Exist: {total_with_images_exist:,} ({total_with_images_exist/total_products*100:.1f}%)")
        print(f"📝 Products with Details: {total_with_details:,} ({total_with_details/total_products*100:.1f}%)")
        print(f"📋 Products with Specs: {total_with_specs:,} ({total_with_specs/total_products*100:.1f}%)")

        # Classify categories by completeness
        print(f"\n🎯 Category Classification:")

        complete = []  # >90% quality
        partial = []   # 50-90% quality
        basic = []     # 10-50% quality
        empty = []     # <10% quality

        for cat_id, stats in sorted(consolidated.items(), key=lambda x: int(x[0])):
            score = stats['quality_score']
            if score >= 90:
                complete.append(cat_id)
            elif score >= 50:
                partial.append(cat_id)
            elif score >= 10:
                basic.append(cat_id)
            else:
                empty.append(cat_id)

        print(f"\n   ✅ Complete (≥90% quality): {len(complete)} categories")
        if complete:
            print(f"      {complete}")

        print(f"\n   ⚠️  Partial (50-90% quality): {len(partial)} categories")
        if partial:
            print(f"      {partial}")

        print(f"\n   ❌ Basic (10-50% quality): {len(basic)} categories")
        if basic:
            print(f"      {basic}")

        print(f"\n   💀 Empty (<10% quality): {len(empty)} categories")
        if empty:
            print(f"      {empty}")

        # Recommendations
        print(f"\n{'='*70}")
        print(f"💡 Recommendations")
        print(f"{'='*70}")

        if total_with_images_exist < total_products * 0.5:
            missing_images = total_products - total_with_images_exist
            print(f"\n1. 🖼️  CRITICAL: Download missing images")
            print(f"   - {missing_images:,} products need images downloaded")
            print(f"   - Only {total_with_images_exist/total_products*100:.1f}% have actual image files")

        if total_with_details < total_products * 0.5:
            missing_details = total_products - total_with_details
            print(f"\n2. 📝 Extract missing product details")
            print(f"   - {missing_details:,} products need detail extraction")
            print(f"   - Only {total_with_details/total_products*100:.1f}% have details")

        if len(consolidated) < 50:
            print(f"\n3. 📂 Crawl remaining categories")
            print(f"   - Only {len(consolidated)} categories collected")
            print(f"   - Many categories may still be missing")

        print(f"\n🎯 Next Steps:")
        if complete:
            print(f"   ✅ Use complete categories immediately: {complete}")
        if partial or basic:
            focus_cats = (partial + basic)[:10]
            print(f"   🔧 Focus on completing these categories first: {focus_cats}")

        return consolidated

if __name__ == "__main__":
    verifier = DataVerifier()
    verifier.run_verification()
