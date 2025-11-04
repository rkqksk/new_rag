#!/bin/bash

# 8 Parallel Selenium Onehago Crawlers
# Distribute 3 categories × ~150 pages across 8 crawlers

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="/tmp"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Launching 8 Parallel Selenium Onehago Crawlers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Stop existing
echo "🛑 Stopping existing crawlers..."
ps aux | grep -E "onehago_selenium_parallel|onehago_parallel_crawler" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null
sleep 2
echo "✅ Cleanup complete"
echo ""

echo "📊 Distribution:"
echo "   Cat 2 (PACKAGING): Crawlers 0-2"
echo "   Cat 7 (BOTTLE): Crawlers 3-5"
echo "   Cat 21 (CONTAINER): Crawlers 6-7"
echo ""

# [crawler_id, category, start_page, end_page]
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

echo "🚀 Launching..."
echo ""

for config in "${CONFIGS[@]}"; do
    read -r id cat start end <<< "$config"
    LOG_FILE="${LOG_DIR}/onehago_selenium_${id}.log"

    echo "   Crawler $id: Cat $cat, Pages $start-$end → $LOG_FILE"

    cd "$PROJECT_DIR"
    nohup python3 scripts/onehago_selenium_parallel.py \
        --category $cat \
        --start-page $start \
        --end-page $end \
        --min-delay 0.5 \
        --max-delay 2.0 \
        > "$LOG_FILE" 2>&1 &

    sleep 2
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All 8 crawlers launched!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Monitor: watch -n 10 'tail -10 /tmp/onehago_selenium_*.log'"
echo "🔍 Processes: ps aux | grep onehago_selenium_parallel | grep -v grep"
echo "📈 Products: python3 -c \"import json; print(f'Total: {len(json.load(open(\"data/onehago/crawled/all_products.json\"))):,}')\""
echo ""
