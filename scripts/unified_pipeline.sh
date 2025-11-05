#!/bin/bash
#
# Unified Crawl-to-RAG Pipeline
#
# Complete workflow: Crawling → Preprocessing → Validation → Embedding → RAG
#
# Usage:
#   ./scripts/unified_pipeline.sh onehago
#   ./scripts/unified_pipeline.sh chungjinkorea
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Data type
DATA_TYPE="${1:-onehago}"

# Validate data type
if [[ ! "$DATA_TYPE" =~ ^(onehago|chungjinkorea)$ ]]; then
    echo -e "${RED}❌ Invalid data type: $DATA_TYPE${NC}"
    echo -e "Usage: $0 {onehago|chungjinkorea}"
    exit 1
fi

# Paths
CRAWLED_DIR="data/crawled/$DATA_TYPE/crawled/production"
INPUT_FILE="$CRAWLED_DIR/packaging_unique_for_images.jsonl"
ENHANCED_FILE="$CRAWLED_DIR/packaging_enhanced.jsonl"
STATS_FILE="$CRAWLED_DIR/preprocessing_stats.json"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python3"

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE} UNIFIED CRAWL-TO-RAG PIPELINE: ${DATA_TYPE}${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${RED}❌ Virtual environment not found: $VENV_PYTHON${NC}"
    exit 1
fi

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo -e "${RED}❌ Input file not found: $INPUT_FILE${NC}"
    echo -e "${YELLOW}Please run web crawler first or check the path${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Input file found: $INPUT_FILE${NC}"
FILE_SIZE=$(du -h "$INPUT_FILE" | cut -f1)
PRODUCT_COUNT=$(wc -l < "$INPUT_FILE" | tr -d ' ')
echo -e "   Size: $FILE_SIZE"
echo -e "   Products: $PRODUCT_COUNT"
echo ""

# ============================================================================
# STEP 1: Preprocessing
# ============================================================================
echo -e "${BLUE}[1/3] PREPROCESSING${NC}"
echo -e "────────────────────────────────────────────────────────────────────────────────"

if [ -f "$ENHANCED_FILE" ]; then
    echo -e "${YELLOW}⚠️  Enhanced file already exists: $ENHANCED_FILE${NC}"
    read -p "Do you want to reprocess? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}✅ Skipping preprocessing (using existing file)${NC}"
    else
        echo -e "${YELLOW}Removing existing file...${NC}"
        rm -f "$ENHANCED_FILE" "$STATS_FILE"
        echo -e "${GREEN}Running preprocessing...${NC}"
        $VENV_PYTHON .claude/skills/rag-pipeline/scripts/preprocess.py \
            --input "$INPUT_FILE" \
            --output "$ENHANCED_FILE" \
            --data-type "$DATA_TYPE" \
            --stats-file "$STATS_FILE"
    fi
else
    echo -e "${GREEN}Running preprocessing...${NC}"
    $VENV_PYTHON .claude/skills/rag-pipeline/scripts/preprocess.py \
        --input "$INPUT_FILE" \
        --output "$ENHANCED_FILE" \
        --data-type "$DATA_TYPE" \
        --stats-file "$STATS_FILE"
fi

echo ""

# ============================================================================
# STEP 2: Validation
# ============================================================================
echo -e "${BLUE}[2/3] VALIDATION${NC}"
echo -e "────────────────────────────────────────────────────────────────────────────────"

if [ -f "$STATS_FILE" ]; then
    echo -e "${GREEN}✅ Preprocessing statistics:${NC}"
    $VENV_PYTHON -c "
import json
with open('$STATS_FILE', 'r') as f:
    stats = json.load(f)
    print(f'   Total products: {stats[\"total_products\"]}')
    print(f'   Steps applied: {len(stats[\"steps_applied\"])}')
    for key, value in stats['statistics'].items():
        pct = value / stats['total_products'] * 100 if stats['total_products'] > 0 else 0
        print(f'   {key}: {value} ({pct:.1f}%)')
"
else
    echo -e "${YELLOW}⚠️  Statistics file not found${NC}"
fi

echo ""

# ============================================================================
# STEP 3: Embedding
# ============================================================================
echo -e "${BLUE}[3/3] EMBEDDING${NC}"
echo -e "────────────────────────────────────────────────────────────────────────────────"

# Check Qdrant connection
echo -e "${GREEN}Checking Qdrant connection...${NC}"
if curl -s -f http://localhost:6333/collections > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Qdrant is running${NC}"
else
    echo -e "${RED}❌ Qdrant is not running${NC}"
    echo -e "${YELLOW}Please start Qdrant: docker-compose up -d qdrant${NC}"
    exit 1
fi

# Check collection
COLLECTION_NAME="${DATA_TYPE}_v2"
echo -e "${GREEN}Target collection: $COLLECTION_NAME${NC}"

# Ask for confirmation
echo ""
echo -e "${YELLOW}This will embed $PRODUCT_COUNT products to Qdrant collection: $COLLECTION_NAME${NC}"
echo -e "${YELLOW}Estimated time: $(( PRODUCT_COUNT / 100 * 2 ))-$(( PRODUCT_COUNT / 100 * 3 )) minutes${NC}"
echo ""
read -p "Continue with embedding? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Running enhanced embedding...${NC}"

    # Create symlink for embedding script to find enhanced file
    mkdir -p "$PROJECT_ROOT/data/crawled/$DATA_TYPE/crawled/production"

    # Run embedding
    $VENV_PYTHON scripts/embed_onehago_enhanced.py

    echo -e "${GREEN}✅ Embedding complete${NC}"
else
    echo -e "${YELLOW}Skipping embedding${NC}"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE} PIPELINE COMPLETE${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""
echo -e "${GREEN}✅ Preprocessing: $ENHANCED_FILE${NC}"
echo -e "${GREEN}✅ Statistics: $STATS_FILE${NC}"

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}✅ Embedding: $COLLECTION_NAME (Qdrant)${NC}"
fi

echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Test search quality:"
echo -e "     ${YELLOW}curl -X POST http://localhost:8001/chat/query -d '{\"query\":\"50ml bottle\"}'${NC}"
echo ""
echo -e "  2. Update frontend to use $COLLECTION_NAME:"
echo -e "     ${YELLOW}Update dashboard.html collection selection${NC}"
echo ""
echo -e "  3. Monitor Qdrant:"
echo -e "     ${YELLOW}open http://localhost:6333/dashboard${NC}"
echo ""
