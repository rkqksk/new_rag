#!/bin/bash
# Master Test Script: Run All 3 Phases for 100-Product Test

set -e  # Exit on error

echo "======================================================================="
echo "🧪 ONEHAGO CRAWLER - 100 PRODUCT TEST"
echo "======================================================================="
echo ""
echo "This test will:"
echo "  1️⃣  Phase 1: Collect 100 product URLs"
echo "  2️⃣  Phase 2: Extract details with JINA/BeautifulSoup"
echo "  3️⃣  Phase 3: Validate against category_24.json"
echo ""
echo "======================================================================="
echo ""

# Change to project directory
cd /Users/oypnus/Project/rag-enterprise

# Phase 1: Collect URLs
echo "🚀 Starting Phase 1: URL Collection"
echo "-----------------------------------------------------------------------"
python3 scripts/phase1_test_100.py
PHASE1_STATUS=$?

if [ $PHASE1_STATUS -ne 0 ]; then
    echo "❌ Phase 1 FAILED! Exiting..."
    exit 1
fi

echo ""
echo "✅ Phase 1 PASSED!"
echo ""
echo "Press ENTER to continue to Phase 2, or Ctrl+C to stop..."
read

# Phase 2: Extract Details
echo ""
echo "🚀 Starting Phase 2: Detail Extraction"
echo "-----------------------------------------------------------------------"
python3 scripts/phase2_test_100.py
PHASE2_STATUS=$?

if [ $PHASE2_STATUS -ne 0 ]; then
    echo "❌ Phase 2 FAILED! Exiting..."
    exit 1
fi

echo ""
echo "✅ Phase 2 PASSED!"
echo ""
echo "Press ENTER to continue to Phase 3, or Ctrl+C to stop..."
read

# Phase 3: Validate Quality
echo ""
echo "🚀 Starting Phase 3: Quality Validation"
echo "-----------------------------------------------------------------------"
python3 scripts/phase3_test_100.py
PHASE3_STATUS=$?

if [ $PHASE3_STATUS -ne 0 ]; then
    echo "❌ Phase 3 FAILED!"
    echo ""
    echo "Check validation report at:"
    echo "  data/onehago/crawled/test_validation_report.json"
    exit 1
fi

# All phases passed
echo ""
echo "======================================================================="
echo "🎉 ALL PHASES PASSED!"
echo "======================================================================="
echo ""
echo "📊 Results:"
echo "  Phase 1 URLs: data/onehago/crawled/test_phase1_urls.jsonl"
echo "  Phase 2 Details: data/onehago/crawled/test_phase2_results/"
echo "  Phase 3 Report: data/onehago/crawled/test_validation_report.json"
echo ""
echo "✅ Ready to scale to full 100K+ products!"
echo "======================================================================="

exit 0
