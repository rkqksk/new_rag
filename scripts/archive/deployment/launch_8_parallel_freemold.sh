#!/bin/bash

# 8 Parallel Freemold Crawler Launcher
# Optimized for speed + stability

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="/tmp"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Launching 8 Parallel Freemold Crawlers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Stop any existing crawlers
echo "🛑 Stopping existing crawlers..."
ps aux | grep -E "crawl_freemold|python.*freemold" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null
sleep 2
echo "✅ Cleanup complete"
echo ""

# Calculate category distribution (153 categories ÷ 8 crawlers = ~19 each)
TOTAL_CATEGORIES=153
NUM_CRAWLERS=8
CATEGORIES_PER_CRAWLER=19

echo "📊 Configuration:"
echo "   Total categories: $TOTAL_CATEGORIES"
echo "   Parallel crawlers: $NUM_CRAWLERS"
echo "   Categories per crawler: ~$CATEGORIES_PER_CRAWLER"
echo ""

# Launch 8 parallel crawlers
echo "🚀 Launching crawlers..."
echo ""

for i in $(seq 0 7); do
    START_IDX=$((i * CATEGORIES_PER_CRAWLER))
    END_IDX=$(((i + 1) * CATEGORIES_PER_CRAWLER))

    if [ $i -eq 7 ]; then
        # Last crawler gets remaining categories
        END_IDX=$TOTAL_CATEGORIES
    fi

    LOG_FILE="${LOG_DIR}/freemold_crawler_${i}.log"

    echo "   Crawler $i: Categories $START_IDX-$END_IDX → $LOG_FILE"

    # Launch in background
    cd "$PROJECT_DIR"
    nohup python3 scripts/freemold_parallel_crawler.py \
        --start-idx $START_IDX \
        --end-idx $END_IDX \
        --min-delay 0.5 \
        --max-delay 2.0 \
        --headless \
        > "$LOG_FILE" 2>&1 &

    sleep 1
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All 8 crawlers launched!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Monitor progress:"
echo "   watch -n 10 'tail -20 /tmp/freemold_crawler_*.log'"
echo ""
echo "🔍 Check processes:"
echo "   ps aux | grep crawl_freemold | grep -v grep"
echo ""
echo "📈 View progress:"
echo "   python3 -c \"import json; data=json.load(open('data/freemold/universal/crawl_progress_universal.json')); print(f'Categories: {len(data)}/153, Products: {sum(len(v) for v in data.values()):,}')\""
echo ""
