#!/bin/bash

# 8 Parallel Onehago Crawler Launcher
# Strategy: Distribute 3 categories × ~150 pages across 8 crawlers
# - Category 2 (PACKAGING): 50 pages/crawler × 3 = crawlers 0-2
# - Category 7 (BOTTLE): 50 pages/crawler × 3 = crawlers 3-5
# - Category 21 (CONTAINER): 75 pages/crawler × 2 = crawlers 6-7

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="/tmp"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Launching 8 Parallel Onehago Crawlers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Stop any existing crawlers
echo "🛑 Stopping existing crawlers..."
ps aux | grep -E "onehago_parallel_crawler" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null
sleep 2
echo "✅ Cleanup complete"
echo ""

echo "📊 Distribution Strategy:"
echo "   Cat 2 (PACKAGING): Crawlers 0-2 (pages 1-150)"
echo "   Cat 7 (BOTTLE): Crawlers 3-5 (pages 1-150)"
echo "   Cat 21 (CONTAINER): Crawlers 6-7 (pages 1-150)"
echo ""

# Launch configuration: [crawler_id, category, start_page, end_page]
declare -a CONFIGS=(
    "0 2 1 50"
    "1 2 51 100"
    "2 2 101 150"
    "3 7 1 50"
    "4 7 51 100"
    "5 7 101 150"
    "6 21 1 75"
    "7 21 76 150"
)

echo "🚀 Launching crawlers..."
echo ""

for config in "${CONFIGS[@]}"; do
    read -r crawler_id category start_page end_page <<< "$config"

    LOG_FILE="${LOG_DIR}/onehago_crawler_${crawler_id}.log"

    echo "   Crawler $crawler_id: Cat $category, Pages $start_page-$end_page → $LOG_FILE"

    # Launch in background
    cd "$PROJECT_DIR"
    nohup python3 scripts/onehago_parallel_crawler.py \
        --category $category \
        --start-page $start_page \
        --end-page $end_page \
        --min-delay 0.5 \
        --max-delay 2.0 \
        > "$LOG_FILE" 2>&1 &

    sleep 1
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All 8 crawlers launched!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Monitor progress:"
echo "   watch -n 10 'tail -15 /tmp/onehago_crawler_*.log'"
echo ""
echo "🔍 Check processes:"
echo "   ps aux | grep onehago_parallel_crawler | grep -v grep"
echo ""
echo "📈 View total products:"
echo "   python3 -c \"import json; data=json.load(open('data/onehago/crawled/all_products.json')); print(f'Total products: {len(data):,}')\""
echo ""
