#!/usr/bin/env python3
"""
Onehago Auto Crawler with Work Queue
Automatically assigns next category when a crawler finishes
Keeps all 16 crawlers busy until all categories are complete
"""

import json
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Force unbuffered output
sys.stdout = open(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = open(sys.stderr.fileno(), 'w', buffering=1)

class CrawlerOrchestrator:
    """Manages 16 crawlers with automatic work queue"""

    def __init__(self, num_crawlers=16):
        self.num_crawlers = num_crawlers
        self.output_dir = Path('data/onehago/crawled')
        self.progress_file = self.output_dir / 'crawl_progress.json'
        self.categories_dir = self.output_dir / 'categories'

        # All categories to crawl
        self.all_categories = [
            2, 3, 4, 5, 7, 8, 12, 13, 16, 17, 19, 25, 26, 27, 30, 31, 62, 72
        ]

        # Track crawler processes
        self.crawlers = {}  # crawler_id -> {process, category, start_time}
        self.work_queue = []
        self.completed_categories = set()
        self.failed_categories = {}

    def load_progress(self):
        """Load existing progress"""
        if self.progress_file.exists():
            with open(self.progress_file) as f:
                progress = json.load(f)
                completed = [int(c) for c in progress.get('completed_categories', [])]
                self.completed_categories.update(completed)
                print(f"📂 Loaded progress: {len(completed)} categories already completed")

        # Also check for category JSON files
        for cat_file in self.categories_dir.glob('category_*.json'):
            cat_id = int(cat_file.stem.split('_')[1])
            if cat_id in self.all_categories:
                self.completed_categories.add(cat_id)

        print(f"✅ Total completed: {len(self.completed_categories)}/{len(self.all_categories)}")

    def initialize_work_queue(self):
        """Create work queue from pending categories"""
        self.work_queue = [
            cat for cat in self.all_categories
            if cat not in self.completed_categories
        ]
        print(f"📋 Work queue: {len(self.work_queue)} categories pending")
        print(f"   Categories: {self.work_queue}")

    def start_crawler(self, crawler_id, category):
        """Start a crawler process for a category"""
        log_file = f'/tmp/onehago_auto_{crawler_id}.log'

        cmd = [
            'python3', 'scripts/onehago_complete_parallel.py',
            '--categories', str(category),
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
            'category': category,
            'start_time': datetime.now(),
            'log_file': log_file
        }

        print(f"🚀 Crawler {crawler_id:2d} started: Category {category:3d} (PID {process.pid})")

    def check_crawler_status(self, crawler_id):
        """Check if crawler is still running and handle completion"""
        crawler = self.crawlers[crawler_id]
        process = crawler['process']

        # Check if process finished
        retcode = process.poll()
        if retcode is not None:
            # Process finished
            category = crawler['category']
            duration = datetime.now() - crawler['start_time']

            # Check if category file was created (success)
            cat_file = self.categories_dir / f'category_{category}.json'
            if cat_file.exists():
                print(f"✅ Crawler {crawler_id:2d} completed: Category {category:3d} ({duration})")
                self.completed_categories.add(category)
                return True  # Crawler available for new work
            else:
                # Check log for errors or empty category
                log_file = crawler['log_file']
                with open(log_file) as f:
                    log_content = f.read()
                    if 'No products found' in log_content or 'No products' in log_content:
                        print(f"⚠️  Crawler {crawler_id:2d} finished: Category {category:3d} (empty category)")
                        self.completed_categories.add(category)
                        return True
                    else:
                        print(f"❌ Crawler {crawler_id:2d} failed: Category {category:3d} ({duration})")
                        self.failed_categories[category] = self.failed_categories.get(category, 0) + 1

                        # Retry if failed less than 3 times
                        if self.failed_categories[category] < 3:
                            print(f"   Retry {self.failed_categories[category]}/3: Adding back to queue")
                            self.work_queue.append(category)
                        else:
                            print(f"   Giving up after 3 failures")
                            self.completed_categories.add(category)  # Mark as done to avoid infinite loop

                        return True  # Crawler available for new work

        return False  # Still running

    def assign_next_work(self, crawler_id):
        """Assign next category from queue to available crawler"""
        if self.work_queue:
            next_category = self.work_queue.pop(0)
            self.start_crawler(crawler_id, next_category)
            return True
        return False

    def run(self):
        """Main orchestration loop"""
        print("=" * 70)
        print("🤖 Onehago Auto Crawler Orchestrator")
        print(f"📊 Crawlers: {self.num_crawlers}")
        print(f"⏱️  Delay: 0.05-0.15s")
        print("=" * 70)
        print()

        # Load progress
        self.load_progress()

        # Initialize work queue
        self.initialize_work_queue()

        if not self.work_queue:
            print("✅ All categories already completed!")
            return

        print()
        print("🚀 Starting initial crawlers...")
        print()

        # Start initial batch of crawlers
        for crawler_id in range(min(self.num_crawlers, len(self.work_queue))):
            if self.work_queue:
                category = self.work_queue.pop(0)
                self.start_crawler(crawler_id, category)

        print()
        print("🔄 Monitoring and auto-assigning work...")
        print()

        # Main monitoring loop
        last_status_time = time.time()

        while True:
            # Check all crawler statuses
            for crawler_id in list(self.crawlers.keys()):
                if self.check_crawler_status(crawler_id):
                    # Crawler finished, assign next work
                    if not self.assign_next_work(crawler_id):
                        # No more work, remove crawler
                        del self.crawlers[crawler_id]

            # Print status every 30 seconds
            if time.time() - last_status_time > 30:
                self.print_status()
                last_status_time = time.time()

            # Check if all done
            if not self.crawlers and not self.work_queue:
                print()
                print("=" * 70)
                print("🎉 ALL CRAWLING COMPLETE!")
                print(f"✅ Categories completed: {len(self.completed_categories)}/{len(self.all_categories)}")
                if self.failed_categories:
                    print(f"⚠️  Failed categories: {list(self.failed_categories.keys())}")
                print("=" * 70)
                break

            # Sleep before next check
            time.sleep(5)

    def print_status(self):
        """Print current status"""
        print()
        print("─" * 70)
        print(f"📊 Status Update: {datetime.now().strftime('%H:%M:%S')}")
        print(f"   Active crawlers: {len(self.crawlers)}/{self.num_crawlers}")
        print(f"   Queue remaining: {len(self.work_queue)}")
        print(f"   Completed: {len(self.completed_categories)}/{len(self.all_categories)}")

        if self.crawlers:
            print(f"   Currently crawling:")
            for cid, info in sorted(self.crawlers.items()):
                duration = datetime.now() - info['start_time']
                minutes = int(duration.total_seconds() / 60)
                print(f"      Crawler {cid:2d}: Category {info['category']:3d} ({minutes}m)")

        print("─" * 70)

def main():
    orchestrator = CrawlerOrchestrator(num_crawlers=16)
    try:
        orchestrator.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("Stopping all crawlers...")
        for crawler_id, info in orchestrator.crawlers.items():
            info['process'].terminate()
        print("✅ All crawlers stopped")

if __name__ == "__main__":
    main()
