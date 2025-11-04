#!/bin/bash

# 3 Parallel Onehago Crawler Launcher (Conservative)
# Strategy: 1 crawler per category to avoid resource contention
# - Category 2 (PACKAGING): Crawler 0 (pages 1-150)
# - Category 7 (BOTTLE): Crawler 1 (pages 1-150)
# - Category 21 (CONTAINER): Crawler 2 (pages 1-150)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="/tmp"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Launching 3 Parallel Onehago Crawlers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Stop any existing crawlers
echo "🛑 Stopping existing crawlers..."
ps aux | grep -E "onehago_parallel_crawler" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null
sleep 2
echo "✅ Cleanup complete"
echo ""

echo "📊 Distribution Strategy:"
echo "   Crawler 0: Cat 2 (PACKAGING) - all 150 pages"
echo "   Crawler 1: Cat 7 (BOTTLE) - all 150 pages"
echo "   Crawler 2: Cat 21 (CONTAINER) - all 150 pages"
echo ""

# Launch configuration: [crawler_id, category, start_page, end_page]
declare -a CONFIGS=(
    "0 2 1 150"
    "1 7 1 150"
    "2 21 1 150"
)

echo "🚀 Launching crawlers..."
echo ""

for config in "${CONFIGS[@]}"; do
    read -r crawler_id category start_page end_page <<< "$config"

    LOG_FILE="${LOG_DIR}/onehago_crawler_${crawler_id}.log"

    echo "   Crawler $crawler_id: Cat $category ($([ $category -eq 2 ] && echo "PACKAGING" || [ $category -eq 7 ] && echo "BOTTLE" || echo "CONTAINER")), Pages $start_page-$end_page → $LOG_FILE"

    # Launch in background with longer startup delay to avoid resource contention
    cd "$PROJECT_DIR"
    nohup python3 scripts/onehago_parallel_crawler.py \
        --category $category \
        --start-page $start_page \
        --end-page $end_page \
        --min-delay 1.0 \
        --max-delay 3.0 \
        > "$LOG_FILE" 2>&1 &

    # Longer delay between launches to avoid browser initialization conflicts
    sleep 5
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All 3 crawlers launched!"
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
