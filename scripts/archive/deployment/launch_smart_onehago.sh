#!/bin/bash

# Smart Onehago Crawler Launcher
# Distributes CATEGORIES (not page ranges) across 8 crawlers
# Skips already-completed categories

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="/tmp"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 Smart Onehago Crawler - Category Distribution"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Stop existing
echo "🛑 Stopping existing crawlers..."
ps aux | grep -E "onehago_selenium_parallel|onehago_smart_parallel" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null
sleep 2
echo "✅ Cleanup complete"
echo ""

# Generate category distribution using Python
echo "📊 Analyzing remaining work..."
cd "$PROJECT_DIR"

python3 << 'PYTHON_SCRIPT'
import json
from pathlib import Path

# Load valid categories
valid_file = Path('data/onehago/valid_categories.json')
valid_cats = json.load(open(valid_file))

# Load progress
progress_file = Path('data/onehago/crawled/crawl_progress.json')
completed = set()
if progress_file.exists():
    progress = json.load(open(progress_file))
    completed = set(progress.get('completed_categories', []))

# Filter remaining
remaining = [cat for cat in valid_cats if cat['id'] not in completed]

print(f"Total categories: {len(valid_cats)}")
print(f"Completed: {len(completed)}")
print(f"Remaining: {len(remaining)}")
print()

# Sort by pages (descending) for smart distribution
remaining_sorted = sorted(remaining, key=lambda x: x['pages'], reverse=True)

# Distribute across 8 crawlers
num_crawlers = 8
crawlers = [[] for _ in range(num_crawlers)]
crawler_pages = [0] * num_crawlers

# Greedy assignment: assign each category to crawler with least pages
for cat in remaining_sorted:
    # Find crawler with minimum pages
    min_idx = crawler_pages.index(min(crawler_pages))
    crawlers[min_idx].append(cat['id'])
    crawler_pages[min_idx] += cat['pages']

# Output assignments
print("Category distribution:")
for i in range(num_crawlers):
    if crawlers[i]:
        cat_list = ','.join(crawlers[i])
        print(f"{i}|{cat_list}|{crawler_pages[i]}")
    else:
        print(f"{i}||0")
PYTHON_SCRIPT

# Read Python output and launch crawlers
distribution=$(python3 << 'PYTHON_SCRIPT'
import json
from pathlib import Path

valid_file = Path('data/onehago/valid_categories.json')
valid_cats = json.load(open(valid_file))

progress_file = Path('data/onehago/crawled/crawl_progress.json')
completed = set()
if progress_file.exists():
    progress = json.load(open(progress_file))
    completed = set(progress.get('completed_categories', []))

remaining = [cat for cat in valid_cats if cat['id'] not in completed]
remaining_sorted = sorted(remaining, key=lambda x: x['pages'], reverse=True)

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
        LOG_FILE="${LOG_DIR}/onehago_smart_${crawler_id}.log"

        echo "   Crawler $crawler_id: ${pages} pages, cats: ${categories:0:60}..."

        nohup python3 scripts/onehago_smart_parallel.py \
            --categories "$categories" \
            --min-delay 0.1 \
            --max-delay 0.3 \
            > "$LOG_FILE" 2>&1 &

        sleep 1
    fi
done <<< "$distribution"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All crawlers launched!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Monitor: watch -n 5 'tail -8 /tmp/onehago_smart_*.log'"
echo "🔍 Processes: ps aux | grep onehago_smart_parallel | grep -v grep"
echo "📈 Progress: python3 -c \"import json; p=json.load(open('data/onehago/crawled/crawl_progress.json')); print(f'Completed: {len(p[\\\"completed_categories\\\"])}/153')\""
echo ""
