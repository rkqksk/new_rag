#!/usr/bin/env python3
"""
Page-Based Crawler Orchestrator
Splits categories by PAGES not products - Much more efficient!
"""

import json
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = open(sys.stderr.fileno(), 'w', buffering=1)

class PageOrchestrator:
    """Orchestrates page-based crawlers"""

    def __init__(self, max_crawlers=20):
        self.max_crawlers = max_crawlers
        self.output_dir = Path('data/onehago/crawled')
        self.categories_dir = self.output_dir / 'categories'

        # Category page counts (from valid_categories.json)
        self.category_pages = {
            2: 103,   # MASSIVE
            3: 9,
            4: 10,
            5: 6,
            7: 58,    # LARGE
            8: 13,
            12: 2,
            13: 4,
            16: 10,
            17: 3,
            19: 2,
            25: 10,
            26: 10,
            27: 10,
            30: 4,
            31: 1,
            62: 1,
            72: 1
        }

        self.crawlers = {}
        self.work_queue = []
        self.completed_categories = set()
        self.category_parts = {}

    def load_progress(self):
        """Check what's already done"""
        for cat_file in self.categories_dir.glob('category_*.json'):
            if '_part' not in cat_file.name:
                cat_id = int(cat_file.stem.split('_')[1])
                if cat_id in self.category_pages:
                    self.completed_categories.add(cat_id)

        print(f"✅ Already completed: {len(self.completed_categories)} categories")

    def create_work_queue(self):
        """Create work units based on page splits"""
        pending = [c for c in self.category_pages.keys()
                  if c not in self.completed_categories]

        print(f"📋 Pending categories: {len(pending)}")
        print()

        for cat_id in sorted(pending, key=lambda x: self.category_pages[x], reverse=True):
            pages = self.category_pages[cat_id]

            # Determine split strategy based on page count
            if pages >= 50:
                # Split into ~13 pages per crawler
                num_splits = max(2, pages // 13)
            elif pages >= 20:
                # Split into ~10 pages per crawler
                num_splits = max(2, pages // 10)
            elif pages >= 10:
                # Split into ~5 pages per crawler
                num_splits = 2
            else:
                # Small categories - no split
                num_splits = 1

            pages_per_split = pages // num_splits if num_splits > 1 else pages

            print(f"Category {cat_id:3d}: {pages:3d} pages → {num_splits} crawlers ({pages_per_split:2d} pages each)")

            for split_idx in range(num_splits):
                start_page = split_idx * pages_per_split + 1
                end_page = start_page + pages_per_split - 1 if split_idx < num_splits - 1 else pages

                self.work_queue.append({
                    'category': cat_id,
                    'start_page': start_page,
                    'end_page': end_page,
                    'split_id': split_idx,
                    'total_splits': num_splits
                })

        print()
        print(f"📦 Total work units: {len(self.work_queue)}")
        print(f"🚀 Will use up to {min(self.max_crawlers, len(self.work_queue))} parallel crawlers")

    def start_crawler(self, crawler_id, work):
        """Start a page-based crawler"""
        cat = work['category']
        start_page = work['start_page']
        end_page = work['end_page']
        split_id = work['split_id']
        total_splits = work['total_splits']

        log_file = f'/tmp/onehago_page_{crawler_id}.log'

        cmd = [
            'python3', 'scripts/onehago_page_crawler.py',
            '--category', str(cat),
            '--start-page', str(start_page),
            '--end-page', str(end_page),
            '--split-id', str(split_id),
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
            'work': work,
            'start_time': datetime.now(),
            'log_file': log_file
        }

        if total_splits > 1:
            print(f"🚀 Crawler {crawler_id:2d}: Cat {cat:3d} part {split_id+1}/{total_splits} "
                  f"(pages {start_page}-{end_page}) PID {process.pid}")
        else:
            print(f"🚀 Crawler {crawler_id:2d}: Cat {cat:3d} "
                  f"(pages {start_page}-{end_page}) PID {process.pid}")

    def check_crawler_status(self, crawler_id):
        """Check if crawler finished"""
        crawler = self.crawlers[crawler_id]
        process = crawler['process']

        retcode = process.poll()
        if retcode is not None:
            work = crawler['work']
            cat = work['category']
            split_id = work['split_id']
            total_splits = work['total_splits']
            duration = datetime.now() - crawler['start_time']

            # Check for output file
            if total_splits > 1:
                part_file = self.categories_dir / f'category_{cat}_part{split_id}.json'
            else:
                part_file = self.categories_dir / f'category_{cat}.json'

            if part_file.exists():
                print(f"✅ Crawler {crawler_id:2d}: Cat {cat} part {split_id+1}/{total_splits} complete ({duration})")

                # Track completion
                if cat not in self.category_parts:
                    self.category_parts[cat] = set()
                self.category_parts[cat].add(split_id)

                # Check if all parts done
                if len(self.category_parts[cat]) == total_splits:
                    self.merge_category_parts(cat, total_splits)

                return True
            else:
                # Check for empty/error
                with open(crawler['log_file']) as f:
                    log = f.read()
                    if 'No products' in log:
                        print(f"⚠️  Crawler {crawler_id:2d}: Cat {cat} part {split_id+1} empty")
                        return True
                    else:
                        print(f"❌ Crawler {crawler_id:2d}: Cat {cat} part {split_id+1} failed")
                        return True

        return False

    def merge_category_parts(self, cat_id, total_parts):
        """Merge partial files"""
        print(f"\n🔀 Merging {total_parts} parts for category {cat_id}...")

        all_products = []
        for part_id in range(total_parts):
            part_file = self.categories_dir / f'category_{cat_id}_part{part_id}.json'
            if part_file.exists():
                with open(part_file) as f:
                    products = json.load(f)
                    all_products.extend(products)
                    print(f"   Part {part_id+1}: {len(products)} products")

        # Save merged
        merged_file = self.categories_dir / f'category_{cat_id}.json'
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)

        # Delete parts
        for part_id in range(total_parts):
            part_file = self.categories_dir / f'category_{cat_id}_part{part_id}.json'
            if part_file.exists():
                part_file.unlink()

        self.completed_categories.add(cat_id)
        print(f"✅ Category {cat_id} merged: {len(all_products):,} total products\n")

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
        print("📄 Page-Based Crawler Orchestrator")
        print("=" * 70)
        print()

        self.load_progress()
        self.create_work_queue()

        if not self.work_queue:
            print("\n✅ All work complete!")
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
                print(f"\n{'─' * 70}")
                print(f"📊 {datetime.now().strftime('%H:%M:%S')} | "
                      f"Active: {len(self.crawlers)} | "
                      f"Queue: {len(self.work_queue)} | "
                      f"Done: {len(self.completed_categories)}")
                print(f"{'─' * 70}\n")
                last_status = time.time()

            # Check completion
            if not self.crawlers and not self.work_queue:
                print("\n" + "=" * 70)
                print("🎉 ALL CRAWLING COMPLETE!")
                print(f"✅ Categories: {len(self.completed_categories)}")
                print("=" * 70)
                break

            time.sleep(5)

def main():
    orch = PageOrchestrator(max_crawlers=20)
    try:
        orch.run()
    except KeyboardInterrupt:
        print("\n⚠️  Stopping...")
        for cid, info in orch.crawlers.items():
            info['process'].terminate()

if __name__ == "__main__":
    main()
