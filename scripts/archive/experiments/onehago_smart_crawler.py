#!/usr/bin/env python3
"""
Smart Onehago Crawler with Product Range Splitting
Automatically splits large categories across multiple crawlers
"""

import json
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = open(sys.stderr.fileno(), 'w', buffering=1)

class SmartCrawlerOrchestrator:
    """Orchestrates crawlers with intelligent category splitting"""

    def __init__(self, max_crawlers=20):
        self.max_crawlers = max_crawlers
        self.output_dir = Path('data/onehago/crawled')
        self.progress_file = self.output_dir / 'crawl_progress.json'
        self.categories_dir = self.output_dir / 'categories'

        # Category sizes (approximate from website)
        self.category_sizes = {
            2: 20464,
            3: 1668,
            4: 2000,
            5: 922,
            7: 11600,
            8: 2480,
            12: 338,
            13: 710,
            16: 2000,
            17: 492,
            19: 202,
            25: 0,
            26: 2000,
            27: 2000,
            30: 800,
            31: 47,
            62: 50,
            72: 40
        }

        self.crawlers = {}
        self.work_queue = []
        self.completed_categories = set()
        self.category_parts = {}  # Track partial completions

    def load_progress(self):
        """Load existing progress"""
        if self.progress_file.exists():
            with open(self.progress_file) as f:
                progress = json.load(f)
                completed = [int(c) for c in progress.get('completed_categories', [])]
                self.completed_categories.update(completed)

        # Check for completed category files
        for cat_file in self.categories_dir.glob('category_*.json'):
            cat_id = int(cat_file.stem.split('_')[1])
            if cat_id in self.category_sizes:
                self.completed_categories.add(cat_id)

        print(f"✅ Already completed: {len(self.completed_categories)} categories")

    def create_work_queue(self):
        """Create work queue with smart category splitting"""
        pending = [c for c in self.category_sizes.keys()
                  if c not in self.completed_categories]

        print(f"\n📋 Pending categories: {len(pending)}")

        # Calculate split strategy
        for cat_id in pending:
            size = self.category_sizes[cat_id]

            # Split large categories
            if size > 5000:
                num_splits = min(8, max(2, size // 2500))
            elif size > 2000:
                num_splits = min(4, max(2, size // 2000))
            else:
                num_splits = 1

            products_per_split = size // num_splits if num_splits > 1 else size

            for split_idx in range(num_splits):
                start_idx = split_idx * products_per_split
                end_idx = start_idx + products_per_split if split_idx < num_splits - 1 else size

                self.work_queue.append({
                    'category': cat_id,
                    'split_id': split_idx,
                    'total_splits': num_splits,
                    'start_product': start_idx,
                    'end_product': end_idx,
                    'products': end_idx - start_idx
                })

        print(f"📦 Total work units: {len(self.work_queue)}")
        print(f"🚀 Using up to {min(self.max_crawlers, len(self.work_queue))} parallel crawlers")

    def start_crawler(self, crawler_id, work_unit):
        """Start a crawler for a work unit"""
        cat = work_unit['category']
        split = work_unit['split_id']
        total_splits = work_unit['total_splits']
        start = work_unit['start_product']
        end = work_unit['end_product']

        log_file = f'/tmp/onehago_smart_{crawler_id}.log'

        # Build command with product range
        cmd = [
            'python3', 'scripts/onehago_range_crawler.py',
            '--category', str(cat),
            '--start-index', str(start),
            '--end-index', str(end),
            '--split-id', str(split),
            '--total-splits', str(total_splits),
            '--min-delay', '0.05',
            '--max-delay', '0.15'
        ]

        process = subprocess.Popen(
            cmd,
            stdout=open(log_file, 'w'),
            stderr=subprocess.STDOUT
        )

        self.crawlers[crawler_id] = {
            'process': process,
            'work_unit': work_unit,
            'start_time': datetime.now(),
            'log_file': log_file
        }

        if total_splits > 1:
            print(f"🚀 Crawler {crawler_id:2d}: Cat {cat:3d} part {split+1}/{total_splits} "
                  f"(products {start:,}-{end:,}) PID {process.pid}")
        else:
            print(f"🚀 Crawler {crawler_id:2d}: Cat {cat:3d} "
                  f"({end:,} products) PID {process.pid}")

    def check_crawler_status(self, crawler_id):
        """Check crawler completion and merge partial results"""
        crawler = self.crawlers[crawler_id]
        process = crawler['process']

        retcode = process.poll()
        if retcode is not None:
            work = crawler['work_unit']
            cat = work['category']
            split = work['split_id']
            total_splits = work['total_splits']
            duration = datetime.now() - crawler['start_time']

            # Check for partial file
            part_file = self.categories_dir / f'category_{cat}_part{split}.json'

            if part_file.exists():
                print(f"✅ Crawler {crawler_id:2d}: Cat {cat} part {split+1}/{total_splits} "
                      f"complete ({duration})")

                # Track completion
                if cat not in self.category_parts:
                    self.category_parts[cat] = set()
                self.category_parts[cat].add(split)

                # Check if all parts complete
                if len(self.category_parts[cat]) == total_splits:
                    self.merge_category_parts(cat, total_splits)

                return True
            else:
                # Check log for empty or error
                with open(crawler['log_file']) as f:
                    log = f.read()
                    if 'No products' in log or 'empty' in log.lower():
                        print(f"⚠️  Crawler {crawler_id:2d}: Cat {cat} part {split+1} empty")
                        return True
                    else:
                        print(f"❌ Crawler {crawler_id:2d}: Cat {cat} part {split+1} failed")
                        # Re-queue with retry limit
                        return True

        return False

    def merge_category_parts(self, cat_id, total_parts):
        """Merge partial category files into one"""
        print(f"\n🔀 Merging {total_parts} parts for category {cat_id}...")

        all_products = []
        for part_id in range(total_parts):
            part_file = self.categories_dir / f'category_{cat_id}_part{part_id}.json'
            if part_file.exists():
                with open(part_file) as f:
                    products = json.load(f)
                    all_products.extend(products)
                    print(f"   Part {part_id+1}: {len(products)} products")

        # Save merged file
        merged_file = self.categories_dir / f'category_{cat_id}.json'
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)

        # Delete part files
        for part_id in range(total_parts):
            part_file = self.categories_dir / f'category_{cat_id}_part{part_id}.json'
            if part_file.exists():
                part_file.unlink()

        self.completed_categories.add(cat_id)
        print(f"✅ Category {cat_id} merged: {len(all_products):,} total products")

    def assign_next_work(self, crawler_id):
        """Assign next work unit"""
        if self.work_queue:
            work = self.work_queue.pop(0)
            self.start_crawler(crawler_id, work)
            return True
        return False

    def run(self):
        """Main loop"""
        print("=" * 70)
        print("🧠 Smart Onehago Crawler (Auto-Split Large Categories)")
        print("=" * 70)

        self.load_progress()
        self.create_work_queue()

        if not self.work_queue:
            print("\n✅ All work already complete!")
            return

        print(f"\n🚀 Starting crawlers...\n")

        # Start initial batch
        for cid in range(min(self.max_crawlers, len(self.work_queue))):
            if self.work_queue:
                work = self.work_queue.pop(0)
                self.start_crawler(cid, work)

        print(f"\n🔄 Monitoring...\n")

        last_status = time.time()

        while True:
            # Check statuses
            for cid in list(self.crawlers.keys()):
                if self.check_crawler_status(cid):
                    if not self.assign_next_work(cid):
                        del self.crawlers[cid]

            # Status update every 60 seconds
            if time.time() - last_status > 60:
                self.print_status()
                last_status = time.time()

            # Check completion
            if not self.crawlers and not self.work_queue:
                print("\n" + "=" * 70)
                print("🎉 ALL CRAWLING COMPLETE!")
                print(f"✅ Categories: {len(self.completed_categories)}")
                print("=" * 70)
                break

            time.sleep(5)

    def print_status(self):
        """Print status"""
        print(f"\n{'─' * 70}")
        print(f"📊 {datetime.now().strftime('%H:%M:%S')} | "
              f"Active: {len(self.crawlers)} | "
              f"Queue: {len(self.work_queue)} | "
              f"Done: {len(self.completed_categories)}")
        print(f"{'─' * 70}\n")

def main():
    orch = SmartCrawlerOrchestrator(max_crawlers=20)
    try:
        orch.run()
    except KeyboardInterrupt:
        print("\n⚠️  Stopping...")
        for cid, info in orch.crawlers.items():
            info['process'].terminate()

if __name__ == "__main__":
    main()
