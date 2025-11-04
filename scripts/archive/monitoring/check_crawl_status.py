#!/usr/bin/env python3
"""
Check Freemold Crawler Status

Quick status checker for the running crawler.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

def check_status():
    """Check crawler status"""
    print("=" * 70)
    print("FREEMOLD CRAWLER STATUS")
    print("=" * 70)
    print()

    # Check if process is running
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'freemold_crawler.py'],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            print("🔄 Status: RUNNING")
            print(f"   PID: {result.stdout.strip()}")
        else:
            print("✅ Status: COMPLETED (or not started)")
    except:
        print("⚠️  Status: UNKNOWN")

    print()

    # Check progress file
    progress_file = Path('data/freemold/crawl_progress.json')
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            progress = json.load(f)

        print("📊 Progress:")
        print()

        total_pages = {'B001': 857, 'B002': 168, 'B003': 177, 'B004': 40}

        for cat, pages in total_pages.items():
            if cat in progress:
                last_page = progress[cat]['last_page']
                updated = progress[cat]['updated_at']
                percent = (last_page / pages) * 100
                bar_length = 40
                filled = int(bar_length * last_page / pages)
                bar = '█' * filled + '░' * (bar_length - filled)

                print(f"  {cat}: [{bar}] {last_page:3}/{pages} ({percent:5.1f}%)")
                print(f"        Last update: {updated[:19]}")
            else:
                print(f"  {cat}: Not started")

        # Calculate overall progress
        completed = sum(progress.get(cat, {'last_page': 0})['last_page'] for cat in total_pages.keys())
        total = sum(total_pages.values())
        overall_percent = (completed / total) * 100

        print()
        print(f"📈 Overall: {completed}/{total} pages ({overall_percent:.1f}%)")

        # Estimate remaining time
        if overall_percent > 0:
            # Get time difference from first category start
            first_cat = next(iter(progress.values()))
            start_time = datetime.fromisoformat(first_cat['updated_at'])
            current_time = datetime.now()
            elapsed = (current_time - start_time).total_seconds()

            pages_per_second = completed / elapsed if elapsed > 0 else 0
            remaining_pages = total - completed
            remaining_seconds = remaining_pages / pages_per_second if pages_per_second > 0 else 0

            remaining_minutes = int(remaining_seconds / 60)
            print(f"⏱️  Estimated time remaining: ~{remaining_minutes} minutes")
    else:
        print("📊 No progress file found - crawler may not have started")

    print()

    # Check output files
    output_dir = Path('data/freemold/crawled_products')
    if output_dir.exists():
        print("📁 Output Files:")
        for cat_dir in sorted(output_dir.iterdir()):
            if cat_dir.is_dir():
                json_file = cat_dir / f'{cat_dir.name}_products.json'
                if json_file.exists():
                    with open(json_file, 'r') as f:
                        products = json.load(f)
                        print(f"   {cat_dir.name}: {len(products):,} products")

    print()
    print("=" * 70)

if __name__ == "__main__":
    check_status()
