#!/bin/bash
# Clean and Backup Script - Prepare for Fresh Crawl

set -e  # Exit on error

echo "======================================================================"
echo "🧹 Clean & Backup - Fresh Start Preparation"
echo "======================================================================"

# Timestamp for backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="data/onehago/backup_${TIMESTAMP}"

echo ""
echo "📦 Step 1: Backing up existing data..."
echo "----------------------------------------------------------------------"

if [ -d "data/onehago/crawled" ]; then
    echo "   Creating backup: ${BACKUP_DIR}"
    mkdir -p "${BACKUP_DIR}"

    # Copy everything to backup
    cp -r data/onehago/crawled "${BACKUP_DIR}/"

    # Get size
    SIZE=$(du -sh "${BACKUP_DIR}/crawled" | cut -f1)
    echo "   ✅ Backup complete: ${SIZE}"
    echo "   Location: ${BACKUP_DIR}/crawled"
else
    echo "   ⚠️  No existing crawled directory found"
fi

echo ""
echo "🗑️  Step 2: Cleaning old data..."
echo "----------------------------------------------------------------------"

if [ -d "data/onehago/crawled" ]; then
    # Move to backup instead of delete
    echo "   Moving crawled → ${BACKUP_DIR}/crawled_original"
    mv data/onehago/crawled "${BACKUP_DIR}/crawled_original"
    echo "   ✅ Old data moved to backup"
else
    echo "   ✅ No old data to clean"
fi

echo ""
echo "📁 Step 3: Creating fresh folder structure..."
echo "----------------------------------------------------------------------"

# Create clean structure
mkdir -p data/onehago/crawled/images
mkdir -p data/onehago/crawled/details
mkdir -p data/onehago/crawled/logs
mkdir -p data/onehago/final

echo "   ✅ Created: data/onehago/crawled/"
echo "      ├── images/          (product images)"
echo "      ├── details/         (full product details JSON)"
echo "      ├── logs/            (crawl logs)"
echo "      └── product_urls.jsonl (Phase 1 output)"
echo ""
echo "   ✅ Created: data/onehago/final/"
echo "      └── (organized final data)"

echo ""
echo "📋 Step 4: Cleaning temp files..."
echo "----------------------------------------------------------------------"

# Clean temp logs
rm -f /tmp/onehago_*.log 2>/dev/null || true
rm -f /tmp/phase1_test.log 2>/dev/null || true

echo "   ✅ Cleaned /tmp/onehago_*.log"

echo ""
echo "======================================================================"
echo "✅ READY FOR FRESH CRAWL!"
echo "======================================================================"
echo ""
echo "📊 Summary:"
echo "   Backup location: ${BACKUP_DIR}"
echo "   Fresh structure: data/onehago/crawled/"
echo "   Final output: data/onehago/final/"
echo ""
echo "🚀 Next Steps:"
echo "   1. Test Phase 1: ./scripts/phase1_collect_product_urls.py --categories 96"
echo "   2. Test Phase 2: ./scripts/phase2_extract_details.py --test"
echo "   3. Run full crawl: ./scripts/run_full_crawl.sh"
echo ""
