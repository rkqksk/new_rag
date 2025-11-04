#!/bin/bash
# Monitor onehago crawler progress

LOG_FILE="/tmp/onehago_full_crawl.log"
PID_FILE="/tmp/onehago_crawler.pid"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Onehago Crawler Status Monitor"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if crawler is running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ Crawler is RUNNING (PID: $PID)"
    else
        echo "❌ Crawler is NOT running (PID file exists but process not found)"
    fi
else
    echo "⚠️  No PID file found - crawler may not have started"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Progress Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "$LOG_FILE" ]; then
    # Count completed categories
    CATEGORIES_DONE=$(grep -c "Category already completed\|marking category .* as completed" "$LOG_FILE" 2>/dev/null || echo "0")

    # Get current category being processed
    CURRENT_CATEGORY=$(grep -E "^\[.*\]$|^📦 Category:" "$LOG_FILE" | tail -2 | head -1)

    # Get current page being processed
    CURRENT_PAGE=$(grep "📄 Page" "$LOG_FILE" | tail -1)

    # Count total products found
    PRODUCTS_FOUND=$(grep "✅ Found .* products on this page" "$LOG_FILE" | wc -l)

    # Get latest status
    LATEST_STATUS=$(tail -5 "$LOG_FILE")

    echo "📂 Categories completed: $CATEGORIES_DONE / 153"
    echo ""
    echo "🔄 Current work:"
    echo "$CURRENT_CATEGORY"
    echo "$CURRENT_PAGE"
    echo ""
    echo "📦 Pages processed: $PRODUCTS_FOUND"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 Latest activity:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$LATEST_STATUS"
else
    echo "❌ Log file not found at: $LOG_FILE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Commands:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Watch live:  tail -f $LOG_FILE"
echo "  Stop:        kill \$(cat $PID_FILE)"
echo "  Check again: bash $0"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
