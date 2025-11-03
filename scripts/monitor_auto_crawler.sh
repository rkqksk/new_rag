#!/bin/bash
# Monitor Auto Crawler Progress

while true; do
    clear
    echo "╔════════════════════════════════════════════════════════════════════╗"
    echo "║       🤖 AUTO CRAWLER MONITOR (16x with Auto-Assignment)         ║"
    echo "╚════════════════════════════════════════════════════════════════════╝"
    echo ""

    # Show last status update from log
    tail -30 /tmp/auto_crawler.log | tail -20

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📁 Completed Category Files:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ls -lh data/onehago/crawled/categories/*.json 2>/dev/null | awk '{printf "   %-20s %6s %s %s %s\n", $9, $5, $6, $7, $8}'

    COMPLETED=$(ls data/onehago/crawled/categories/*.json 2>/dev/null | wc -l | tr -d ' ')
    echo ""
    echo "✅ Total files: $COMPLETED"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔄 Refresh: every 15 seconds (Ctrl+C to exit)"
    echo "📜 Full log: tail -f /tmp/auto_crawler.log"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    sleep 15
done
