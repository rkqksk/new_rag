#!/bin/bash
# Monitor Production Crawl Progress

echo "========================================"
echo "📊 ONEHAGO PRODUCTION CRAWL MONITOR"
echo "========================================"
echo ""

# Phase 1 Progress
if [ -f "/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/phase1_progress.json" ]; then
    echo "📂 Phase 1: URL Collection"
    echo "----------------------------------------"
    cat /Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/phase1_progress.json | python3 -m json.tool 2>/dev/null || cat /Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/phase1_progress.json
    echo ""

    # Count URLs
    if [ -f "/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/all_product_urls.jsonl" ]; then
        url_count=$(wc -l < /Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/all_product_urls.jsonl)
        echo "📦 Total URLs collected: $url_count"
    fi
    echo ""
fi

# Phase 2 Progress
if [ -f "/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/phase2_progress.json" ]; then
    echo "📦 Phase 2: Data Extraction"
    echo "----------------------------------------"
    cat /Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/phase2_progress.json | python3 -m json.tool 2>/dev/null || cat /Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/phase2_progress.json
    echo ""
fi

# Latest log entries
echo "📋 Latest Log Entries (last 20 lines):"
echo "----------------------------------------"
latest_log=$(ls -t /Users/oypnus/Project/rag-enterprise/data/onehago/crawled/logs/phase*production*.log 2>/dev/null | head -1)
if [ -n "$latest_log" ]; then
    tail -20 "$latest_log"
else
    echo "No production logs found yet"
fi

echo ""
echo "========================================"
echo "ℹ️  Run this script again to check updated progress"
echo "========================================"
