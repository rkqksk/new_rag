#!/usr/bin/env python3
"""
Parallel crawler launcher for Onehago
Launches multiple crawler instances for different category ranges
"""
import json
import subprocess
import sys
from pathlib import Path
import time

def load_categories():
    """Load valid categories"""
    categories_file = Path(__file__).parent.parent / 'data' / 'onehago' / 'valid_categories.json'
    with open(categories_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_completed_categories():
    """Check which categories are already completed"""
    crawled_dir = Path(__file__).parent.parent / 'data' / 'onehago' / 'crawled'
    completed = set()

    if crawled_dir.exists():
        for f in crawled_dir.glob('category_*.json'):
            # Extract category ID from filename: category_2_Category_2.json
            parts = f.stem.split('_')
            if len(parts) >= 2 and parts[1].isdigit():
                completed.add(int(parts[1]))

    return completed

def launch_crawler(category_ids, crawler_id):
    """Launch a crawler for specific categories"""
    cmd = [
        'python3', '-c', f'''
import sys
sys.path.insert(0, "/Users/oypnus/Project/rag-enterprise")
from scripts.crawl_onehago_complete import OneHagoCrawler
import json

# Load all categories
with open("data/onehago/valid_categories.json", "r", encoding="utf-8") as f:
    all_categories = json.load(f)

# Filter to target categories
target_ids = {category_ids}
categories_to_crawl = [c for c in all_categories if c.get("id") in target_ids]

print(f"🚀 Crawler {crawler_id}: Starting with {{len(categories_to_crawl)}} categories")
print(f"   Category IDs: {category_ids}")
print()

# Create crawler with FASTER delays (0.5-2 seconds instead of 3-8)
crawler = OneHagoCrawler(delay_min=0.5, delay_max=2.0, headless=True)

# Crawl (list only, no details for now)
crawler.crawl_all_categories(categories_to_crawl, crawl_details=False)

print()
print(f"✅ Crawler {crawler_id}: Completed!")
'''
    ]

    log_file = Path(__file__).parent.parent / 'data' / 'onehago' / f'crawler_{crawler_id}.log'

    with open(log_file, 'w') as log:
        process = subprocess.Popen(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            cwd=Path(__file__).parent.parent
        )

    print(f"   Crawler {crawler_id}: PID {process.pid}, Log: {log_file.name}")
    return process

def main():
    """Main parallel crawler launcher"""
    print("=" * 80)
    print("🚀 Onehago Parallel Crawler Launcher")
    print("=" * 80)
    print()

    # Load categories
    all_categories = load_categories()
    completed = get_completed_categories()

    # Sort by size (descending)
    sorted_cats = sorted(
        all_categories,
        key=lambda x: x.get('products', 0) * x.get('pages', 0),
        reverse=True
    )

    # Get uncompleted categories
    uncompleted = [c for c in sorted_cats if c.get('id') not in completed]

    print(f"📊 Status:")
    print(f"   Total categories: {len(all_categories)}")
    print(f"   Completed: {len(completed)}")
    print(f"   Remaining: {len(uncompleted)}")
    print()

    if not uncompleted:
        print("✅ All categories already crawled!")
        return

    # Get number of parallel crawlers (default: 3)
    num_crawlers = int(sys.argv[1]) if len(sys.argv) > 1 else 3

    print(f"🔧 Configuration:")
    print(f"   Parallel crawlers: {num_crawlers}")
    print(f"   Mode: LIST ONLY (no details)")
    print()

    # Distribute categories across crawlers
    # Strategy: Give each crawler a mix of large and small categories
    category_groups = [[] for _ in range(num_crawlers)]

    for i, cat in enumerate(uncompleted):
        category_groups[i % num_crawlers].append(cat['id'])

    # Show distribution
    print("📋 Category Distribution:")
    for i, group in enumerate(category_groups, 1):
        if group:
            # Calculate total products for this group
            total_products = sum(
                c.get('products', 0) * c.get('pages', 0)
                for c in uncompleted
                if c.get('id') in group
            )
            print(f"   Crawler {i}: {len(group)} categories, ~{total_products:,} products")
            print(f"              IDs: {group[:5]}{'...' if len(group) > 5 else ''}")
    print()

    # Launch crawlers
    print("🚀 Launching Crawlers...")
    print()

    processes = []
    for i, group in enumerate(category_groups, 1):
        if group:
            proc = launch_crawler(group, i)
            processes.append(proc)
            time.sleep(2)  # Stagger launches

    print()
    print("=" * 80)
    print(f"✅ Launched {len(processes)} crawlers successfully!")
    print()
    print("📊 Monitor progress:")
    print(f"   tail -f data/onehago/crawler_*.log")
    print()
    print("🛑 Stop all crawlers:")
    print(f"   pkill -f crawl_parallel")
    print("=" * 80)

if __name__ == "__main__":
    main()
