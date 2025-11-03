#!/bin/bash

# Complete Onehago Crawler Launcher
# With details and images
# Separate files per category (no corruption)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="/tmp"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 Complete Onehago Crawler (Details + Images)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Stop existing
echo "🛑 Stopping existing crawlers..."
ps aux | grep -E "onehago.*parallel" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null
sleep 2
echo "✅ Cleanup complete"
echo ""

# Generate category distribution
echo "📊 Analyzing remaining work..."
cd "$PROJECT_DIR"

distribution=$(python3 << 'PYTHON_SCRIPT'
import json
from pathlib import Path

valid_file = Path('data/onehago/valid_categories.json')
valid_cats = json.load(open(valid_file))

# Check which categories already have complete data
categories_dir = Path('data/onehago/crawled/categories')
completed = set()
if categories_dir.exists():
    for cat_file in categories_dir.glob('category_*.json'):
        cat_id = cat_file.stem.replace('category_', '')
        completed.add(cat_id)

remaining = [cat for cat in valid_cats if cat['id'] not in completed]

print(f"Total categories: {len(valid_cats)}")
print(f"Completed: {len(completed)}")
print(f"Remaining: {len(remaining)}")
print()

# Sort by pages (descending)
remaining_sorted = sorted(remaining, key=lambda x: x['pages'], reverse=True)

# Distribute across 8 crawlers
num_crawlers = 8
crawlers = [[] for _ in range(num_crawlers)]
crawler_pages = [0] * num_crawlers

for cat in remaining_sorted:
    min_idx = crawler_pages.index(min(crawler_pages))
    crawlers[min_idx].append(cat['id'])
    crawler_pages[min_idx] += cat['pages']

for i in range(num_crawlers):
    if crawlers[i]:
        cat_list = ','.join(crawlers[i])
        print(f"{i}|{cat_list}|{crawler_pages[i]}")
PYTHON_SCRIPT
)

echo ""
echo "🚀 Launching crawlers..."
echo ""

# Launch each crawler
while IFS='|' read -r crawler_id categories pages; do
    if [ -n "$categories" ]; then
        LOG_FILE="${LOG_DIR}/onehago_complete_${crawler_id}.log"

        echo "   Crawler $crawler_id: ${pages} pages, categories: ${categories:0:60}..."

        nohup python3 scripts/onehago_complete_parallel.py \
            --categories "$categories" \
            --min-delay 0.3 \
            --max-delay 0.8 \
            > "$LOG_FILE" 2>&1 &

        sleep 2
    fi
done <<< "$distribution"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All crawlers launched!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Monitor: tail -f /tmp/onehago_complete_*.log"
echo "🔍 Processes: ps aux | grep onehago_complete_parallel | grep -v grep"
echo "📂 Categories: ls -lh data/onehago/crawled/categories/"
echo "🖼️  Images: ls data/onehago/crawled/images/ | wc -l"
echo ""
