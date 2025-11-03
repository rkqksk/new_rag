#!/bin/bash

# Continuous Crawler with Auto-restart
# This script runs the crawler continuously and restarts it every 30 minutes

LOG_FILE="/tmp/continuous_crawler.log"
CHECK_INTERVAL=1800  # 30 minutes in seconds

echo "========================================" | tee -a "$LOG_FILE"
echo "🚀 Continuous Crawler Started: $(date)" | tee -a "$LOG_FILE"
echo "Check interval: $CHECK_INTERVAL seconds (30 minutes)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

while true; do
    echo "" | tee -a "$LOG_FILE"
    echo "🔄 [$(date)] Starting new crawl cycle..." | tee -a "$LOG_FILE"
    
    # Run crawler with timeout
    timeout ${CHECK_INTERVAL} python3 scripts/crawl_onehago_complete.py --details 2>&1 | tee -a "$LOG_FILE"
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 124 ]; then
        echo "⏰ [$(date)] Crawler reached 30-minute timeout - restarting..." | tee -a "$LOG_FILE"
    elif [ $EXIT_CODE -eq 0 ]; then
        echo "✅ [$(date)] Crawler completed successfully - restarting..." | tee -a "$LOG_FILE"
    else
        echo "⚠️ [$(date)] Crawler exited with code $EXIT_CODE - restarting..." | tee -a "$LOG_FILE"
    fi
    
    # Brief pause before restart
    sleep 5
    
    # Check and display progress
    if [ -d "data/chungjinkorea/crawled_products_final" ]; then
        TOTAL_PRODUCTS=$(find data/chungjinkorea/crawled_products_final -name "*.json" | wc -l)
        echo "📊 [$(date)] Current progress: $TOTAL_PRODUCTS products crawled" | tee -a "$LOG_FILE"
    fi
done
