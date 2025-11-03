#!/usr/bin/env python3
"""
Parallel Production Crawler - Maximum Speed
Runs Phase 1 (URL collection) and Phase 2 (Detail extraction) in parallel

Strategy:
- Phase 1: Collect URLs from all categories (parallel by category)
- Phase 2: Extract details + images (parallel by product batches)
- Auto-tune workers based on CPU cores
"""

import json
import subprocess
import time
import argparse
from pathlib import Path
from datetime import datetime
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, as_completed

class ParallelCrawler:
    def __init__(self, max_workers=None, phase1_only=False, phase2_only=False):
        # Auto-tune workers
        cpu_count = mp.cpu_count()
        self.max_workers = max_workers or min(cpu_count * 2, 20)  # 2x CPU cores, max 20

        self.phase1_only = phase1_only
        self.phase2_only = phase2_only

        self.output_dir = Path('data/onehago/crawled')
        self.urls_file = self.output_dir / 'product_urls.jsonl'

        # Load categories
        self.categories = self.load_categories()

        self.stats = {
            'phase1_complete': 0,
            'phase1_failed': 0,
            'phase2_complete': 0,
            'phase2_failed': 0,
            'start_time': datetime.now()
        }

    def load_categories(self):
        """Load valid categories"""
        cat_file = Path('data/onehago/valid_categories.json')
        if cat_file.exists():
            with open(cat_file) as f:
                cats = json.load(f)
                return {cat['id']: cat for cat in cats}
        return {}

    def run_phase1_category(self, category_id):
        """Run Phase 1 for single category"""
        try:
            cmd = [
                '.direnv/python-3.11/bin/python3',
                'scripts/phase1_collect_product_urls.py',
                '--categories', str(category_id),
                '--min-delay', '0.05',
                '--max-delay', '0.15'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                # Parse output to get product count
                output = result.stdout
                if 'products found' in output:
                    return {'category': category_id, 'success': True, 'output': output}

            return {'category': category_id, 'success': False, 'error': result.stderr}

        except Exception as e:
            return {'category': category_id, 'success': False, 'error': str(e)}

    def run_phase1_parallel(self):
        """Run Phase 1 for all categories in parallel"""
        print("="*70)
        print("📋 Phase 1: Parallel URL Collection")
        print("="*70)

        categories = sorted([int(k) for k in self.categories.keys()])
        total = len(categories)

        print(f"\n🎯 Collecting URLs from {total} categories")
        print(f"⚡ Using {self.max_workers} parallel workers\n")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all categories
            futures = {
                executor.submit(self.run_phase1_category, cat_id): cat_id
                for cat_id in categories
            }

            # Process results as they complete
            for idx, future in enumerate(as_completed(futures), 1):
                cat_id = futures[future]
                try:
                    result = future.result()
                    if result['success']:
                        self.stats['phase1_complete'] += 1
                        print(f"[{idx}/{total}] ✅ Category {cat_id:3d} complete")
                    else:
                        self.stats['phase1_failed'] += 1
                        print(f"[{idx}/{total}] ❌ Category {cat_id:3d} failed: {result.get('error', 'Unknown')[:50]}")
                except Exception as e:
                    self.stats['phase1_failed'] += 1
                    print(f"[{idx}/{total}] ❌ Category {cat_id:3d} error: {str(e)[:50]}")

        # Count total products collected
        total_products = 0
        if self.urls_file.exists():
            with open(self.urls_file) as f:
                total_products = sum(1 for _ in f)

        print(f"\n{'='*70}")
        print(f"📊 Phase 1 Summary:")
        print(f"   Categories successful: {self.stats['phase1_complete']}/{total}")
        print(f"   Categories failed: {self.stats['phase1_failed']}")
        print(f"   Total products collected: {total_products:,}")
        print(f"{'='*70}\n")

        return total_products

    def run_phase2_batch(self, start_idx, batch_size):
        """Run Phase 2 for a batch of products"""
        try:
            cmd = [
                '.direnv/python-3.11/bin/python3',
                'scripts/phase2_extract_details.py',
                '--max-products', str(batch_size),
                '--min-delay', '0.1',
                '--max-delay', '0.3'
            ]

            # Create temp file with batch products
            # (In production, modify phase2 to accept start_idx parameter)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

            if result.returncode == 0:
                return {'start': start_idx, 'success': True}

            return {'start': start_idx, 'success': False, 'error': result.stderr}

        except Exception as e:
            return {'start': start_idx, 'success': False, 'error': str(e)}

    def run_phase2_parallel(self, total_products):
        """Run Phase 2 with parallel workers"""
        print("="*70)
        print("📝 Phase 2: Parallel Detail Extraction + Image Download")
        print("="*70)

        if total_products == 0:
            print("❌ No products to process. Run Phase 1 first.")
            return

        # For now, run single process (Phase 2 needs refactoring for true parallelization)
        # TODO: Split Phase 2 to support parallel processing by product batches
        print(f"\n⚡ Processing {total_products:,} products...")
        print(f"   (Sequential for now - parallel Phase 2 requires refactoring)\n")

        cmd = [
            '.direnv/python-3.11/bin/python3',
            'scripts/phase2_extract_details.py',
            '--min-delay', '0.1',
            '--max-delay', '0.3'
        ]

        try:
            result = subprocess.run(cmd, text=True)
            if result.returncode == 0:
                self.stats['phase2_complete'] = total_products
            else:
                self.stats['phase2_failed'] = total_products

        except Exception as e:
            print(f"❌ Phase 2 error: {e}")
            self.stats['phase2_failed'] = total_products

    def run(self):
        """Main parallel crawl orchestration"""
        print("\n" + "="*70)
        print("🚀 PARALLEL PRODUCTION CRAWLER")
        print("="*70)
        print(f"   Workers: {self.max_workers}")
        print(f"   CPU cores: {mp.cpu_count()}")
        print(f"   Categories: {len(self.categories)}")
        print("="*70)

        start_time = datetime.now()

        # Phase 1: Parallel URL collection
        if not self.phase2_only:
            total_products = self.run_phase1_parallel()
        else:
            # Count existing products
            total_products = 0
            if self.urls_file.exists():
                with open(self.urls_file) as f:
                    total_products = sum(1 for _ in f)
            print(f"⏭️  Skipping Phase 1, found {total_products:,} existing products")

        # Phase 2: Detail extraction (currently sequential)
        if not self.phase1_only and total_products > 0:
            self.run_phase2_parallel(total_products)
        else:
            print(f"\n⏭️  Skipping Phase 2 (use --no-phase1-only to run)")

        # Final summary
        duration = datetime.now() - start_time
        print(f"\n{'='*70}")
        print(f"🎉 CRAWL COMPLETE!")
        print(f"{'='*70}")
        print(f"📊 Final Statistics:")
        print(f"   Phase 1 categories: {self.stats['phase1_complete']} success, {self.stats['phase1_failed']} failed")
        print(f"   Phase 2 products: {self.stats['phase2_complete']} success, {self.stats['phase2_failed']} failed")
        print(f"   Total duration: {duration}")
        print(f"   Output: {self.output_dir}")
        print(f"{'='*70}\n")

def main():
    parser = argparse.ArgumentParser(description='Parallel production crawler')
    parser.add_argument('--workers', type=int,
                       help='Max parallel workers (default: auto = 2x CPU cores)')
    parser.add_argument('--phase1-only', action='store_true',
                       help='Run only Phase 1 (URL collection)')
    parser.add_argument('--phase2-only', action='store_true',
                       help='Run only Phase 2 (detail extraction)')

    args = parser.parse_args()

    crawler = ParallelCrawler(
        max_workers=args.workers,
        phase1_only=args.phase1_only,
        phase2_only=args.phase2_only
    )

    crawler.run()

if __name__ == "__main__":
    main()
