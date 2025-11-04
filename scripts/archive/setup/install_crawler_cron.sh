#!/bin/bash

# Automated Crawler Cron Installation Script
# This script installs weekly automated crawls for all 4 sites

echo "══════════════════════════════════════════"
echo "🤖 Automated Crawler Cron Installation"
echo "══════════════════════════════════════════"
echo ""

# Get absolute project path
PROJECT_DIR="/Users/oypnus/Project/rag-enterprise"

echo "📁 Project Directory: $PROJECT_DIR"
echo ""

# Verify project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Error: Project directory not found at $PROJECT_DIR"
    exit 1
fi

# Create cron entries
echo "📝 Creating cron configuration..."
echo ""

# Temporary cron file
CRON_TEMP="/tmp/crawler_cron_temp.txt"

# Get existing crontab (if any)
crontab -l > "$CRON_TEMP" 2>/dev/null || touch "$CRON_TEMP"

# Remove old crawler entries (if any)
sed -i.bak '/# CRAWLER:/d' "$CRON_TEMP"
sed -i.bak '/crawl_chunjin_universal\.py/d' "$CRON_TEMP"
sed -i.bak '/crawl_jangup_full_81k\.py/d' "$CRON_TEMP"
sed -i.bak '/freemold_cat2_phase1_discovery\.py/d' "$CRON_TEMP"
sed -i.bak '/freemold_phase2_hybrid\.py/d' "$CRON_TEMP"
sed -i.bak '/phase1_production_full\.py/d' "$CRON_TEMP"
sed -i.bak '/onehago_orchestrator_continuous\.py/d' "$CRON_TEMP"

# Add new crawler cron jobs
cat >> "$CRON_TEMP" << 'CRON_EOF'

# ═══════════════════════════════════════════
# CRAWLER: Automated Weekly Web Crawlers
# ═══════════════════════════════════════════

# CRAWLER: Chunjinkorea - Every Sunday 4:00 AM
0 4 * * 0 cd /Users/oypnus/Project/rag-enterprise && python3 scripts/crawl_chunjin_universal.py >> /tmp/chunjin_weekly.log 2>&1

# CRAWLER: Jangup - Every Sunday 5:00 AM (after chunjinkorea)
0 5 * * 0 cd /Users/oypnus/Project/rag-enterprise && python3 scripts/crawl_jangup_full_81k.py >> /tmp/jangup_weekly.log 2>&1

# CRAWLER: Freemold Phase 1 - Every other Monday 3:00 AM
0 3 * * 1 [ $(expr $(date +\%W) \% 2) -eq 0 ] && cd /Users/oypnus/Project/rag-enterprise && python3 scripts/freemold_cat2_phase1_discovery.py >> /tmp/freemold_phase1_weekly.log 2>&1

# CRAWLER: Freemold Phase 2 - Every other Monday 4:00 AM (after Phase 1)
0 4 * * 1 [ $(expr $(date +\%W) \% 2) -eq 0 ] && cd /Users/oypnus/Project/rag-enterprise && python3 scripts/freemold_phase2_hybrid.py >> /tmp/freemold_phase2_weekly.log 2>&1

# CRAWLER: Onehago Phase 1 - Every Sunday 2:00 AM
0 2 * * 0 cd /Users/oypnus/Project/rag-enterprise && python3 scripts/phase1_production_full.py >> /tmp/onehago_phase1_weekly.log 2>&1

# CRAWLER: Onehago Phase 2 - Every Monday 2:00 AM (after Phase 1 completes Sunday)
0 2 * * 1 cd /Users/oypnus/Project/rag-enterprise && python3 scripts/onehago_orchestrator_continuous.py >> /tmp/onehago_phase2_weekly.log 2>&1

CRON_EOF

# Install new crontab
crontab "$CRON_TEMP"

if [ $? -eq 0 ]; then
    echo "✅ Cron jobs installed successfully!"
else
    echo "❌ Error installing cron jobs"
    exit 1
fi

# Cleanup
rm -f "$CRON_TEMP" "$CRON_TEMP.bak"

echo ""
echo "══════════════════════════════════════════"
echo "📅 WEEKLY CRAWL SCHEDULE"
echo "══════════════════════════════════════════"
echo ""
echo "Sunday:"
echo "  2:00 AM - Onehago Phase 1 starts (URL discovery)"
echo "  4:00 AM - Chunjinkorea crawler"
echo "  5:00 AM - Jangup crawler"
echo ""
echo "Monday:"
echo "  2:00 AM - Onehago Phase 2 starts (data extraction)"
echo "  3:00 AM - Freemold Phase 1 (bi-weekly, even weeks)"
echo "  4:00 AM - Freemold Phase 2 (bi-weekly, even weeks)"
echo ""
echo "══════════════════════════════════════════"
echo "📊 TOTAL WEEKLY PRODUCTS: 2,098,517"
echo "══════════════════════════════════════════"
echo ""
echo "✅ Automated crawling is now active!"
echo ""
echo "💡 Commands:"
echo "   View jobs:   crontab -l"
echo "   Remove jobs: crontab -r"
echo "   Edit jobs:   crontab -e"
echo ""
echo "📝 Log files location: /tmp/*_weekly.log"
echo ""
