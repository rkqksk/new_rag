#!/bin/bash

# Crawler Monitor - Shows real-time status every 30 minutes

LOG_FILE="/tmp/crawler_monitor.log"

echo "========================================" | tee -a "$LOG_FILE"
echo "📊 Crawler Monitor Started: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

while true; do
    echo "" | tee -a "$LOG_FILE"
    echo "📈 [$(date)] Crawler Status Report" | tee -a "$LOG_FILE"
    echo "----------------------------------------" | tee -a "$LOG_FILE"
    
    # Count products by category
    if [ -d "data/chungjinkorea/crawled_products_final" ]; then
        for category in Bottle Jar Cap Pump; do
            if [ -d "data/chungjinkorea/crawled_products_final/$category" ]; then
                COUNT=$(find "data/chungjinkorea/crawled_products_final/$category" -name "*.json" | wc -l)
                echo "  $category: $COUNT products" | tee -a "$LOG_FILE"
            fi
        done
        
        TOTAL=$(find data/chungjinkorea/crawled_products_final -name "*.json" | wc -l)
        echo "  TOTAL: $TOTAL products" | tee -a "$LOG_FILE"
    fi
    
    # Check crawler process
    if pgrep -f "continuous_crawler.sh" > /dev/null; then
        echo "  Status: ✅ Crawler is RUNNING" | tee -a "$LOG_FILE"
    else
        echo "  Status: ❌ Crawler is NOT RUNNING" | tee -a "$LOG_FILE"
    fi
    
    echo "----------------------------------------" | tee -a "$LOG_FILE"
    
    # Wait 30 minutes
    sleep 1800
done
