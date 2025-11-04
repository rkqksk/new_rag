#!/bin/bash
# Monitor Phase 2 Text Extraction Progress

echo "========================================"
echo "📊 PHASE 2 TEXT EXTRACTION MONITOR"
echo "========================================"
echo ""

# Check progress file
if [ -f "/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only/phase2_progress.json" ]; then
    echo "📂 Phase 2: Text Extraction Progress"
    echo "----------------------------------------"
    cat /Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only/phase2_progress.json | python3 -m json.tool 2>/dev/null || cat /Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only/phase2_progress.json
    echo ""

    # Calculate percentage
    cat /Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only/phase2_progress.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
processed = data.get('products_processed', 0)
total = 2011553
percentage = (processed / total * 100) if total > 0 else 0
print(f'📊 Progress: {processed:,}/{total:,} ({percentage:.1f}%)')
print(f'✅ Success: {data.get(\"products_success\", 0):,}')
print(f'❌ Failed: {data.get(\"products_failed\", 0):,}')
" 2>/dev/null
    echo ""

    # Count batch files
    batch_count=$(ls -1 /Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only/batch_*.jsonl 2>/dev/null | wc -l)
    echo "📦 Batch files created: $batch_count"
else
    echo "⚠️  No progress file found yet (crawler still initializing)"
fi

echo ""
echo "📋 Latest Log Entries (last 15 lines):"
echo "----------------------------------------"
latest_log=$(ls -t /Users/oypnus/Project/rag-enterprise/data/onehago/crawled/logs/phase2_production_text_*.log 2>/dev/null | head -1)
if [ -n "$latest_log" ]; then
    tail -15 "$latest_log"
else
    echo "No production logs found yet"
fi

echo ""
echo "========================================"
echo "ℹ️  Run this script again to check updated progress"
echo "========================================"
