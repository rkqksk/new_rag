#!/bin/bash
# Fix all test import paths for v10 migration
# Generated: 2025-11-19
# Purpose: Update test imports from old patterns to v10 structure

set -e  # Exit on error

echo "========================================================================="
echo "Test Import Path Migration for apps/api (v10)"
echo "========================================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to project root
cd "$(dirname "$0")/.."

echo "Working directory: $(pwd)"
echo ""

# Backup function
backup_file() {
    local file=$1
    if [ -f "$file" ]; then
        cp "$file" "$file.backup-$(date +%Y%m%d-%H%M%S)"
        echo -e "${GREEN}✓${NC} Backed up: $file"
    fi
}

# Verification function
verify_file_exists() {
    local file=$1
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ Error: File not found: $file${NC}"
        return 1
    fi
    return 0
}

echo "Step 1: Pre-migration verification"
echo "-------------------------------------------------------------------"

# Check current state
OLD_APP_MAIN=$(grep -c "from app\.main import" tests/conftest.py 2>/dev/null || echo "0")
OLD_API_API=$(grep -r "from apps\.api\.api\." tests/ 2>/dev/null | wc -l || echo "0")

echo "Found import issues:"
echo "  - 'from app.main' patterns: $OLD_APP_MAIN"
echo "  - 'from apps.api.api.*' patterns: $OLD_API_API"
echo ""

if [ "$OLD_APP_MAIN" = "0" ] && [ "$OLD_API_API" = "0" ]; then
    echo -e "${GREEN}✓ No import issues found. Migration may have already been completed.${NC}"
    exit 0
fi

# Create backups directory
BACKUP_DIR=".backups/test-imports-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}✓${NC} Created backup directory: $BACKUP_DIR"
echo ""

# Files to update
FILES_TO_UPDATE=(
    "tests/conftest.py"
    "tests/integration/test_api_integration.py"
    "tests/integration/test_app_initialization.py"
    "tests/integration/test_e2e_pipeline.py"
    "tests/integration/test_e2e_simple.py"
    "tests/integration/test_nexa_integration.py"
    "tests/integration/test_product_loading.py"
)

echo "Step 2: Creating backups"
echo "-------------------------------------------------------------------"

for file in "${FILES_TO_UPDATE[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/$(basename $file)"
        echo -e "${GREEN}✓${NC} Backed up: $file"
    else
        echo -e "${YELLOW}⚠${NC} Skipped (not found): $file"
    fi
done
echo ""

echo "Step 3: Applying import path updates"
echo "-------------------------------------------------------------------"

# Fix 1: conftest.py - app.main → apps.api.main
echo "Fix 1/3: Updating tests/conftest.py (app.main → apps.api.main)"
if verify_file_exists "tests/conftest.py"; then
    sed -i.bak 's/from app\.main import app/from apps.api.main import app/' tests/conftest.py
    rm -f tests/conftest.py.bak
    echo -e "${GREEN}✓${NC} Updated: tests/conftest.py"
else
    echo -e "${RED}✗${NC} Failed: tests/conftest.py not found"
fi
echo ""

# Fix 2: apps.api.api.main → apps.api.main
echo "Fix 2/3: Updating apps.api.api.main imports"
for file in tests/integration/test_api_integration.py \
            tests/integration/test_app_initialization.py \
            tests/integration/test_e2e_pipeline.py \
            tests/integration/test_e2e_simple.py; do
    if [ -f "$file" ]; then
        sed -i.bak 's/from apps\.api\.api\.main import/from apps.api.main import/g' "$file"
        rm -f "$file.bak"
        echo -e "${GREEN}✓${NC} Updated: $file"
    else
        echo -e "${YELLOW}⚠${NC} Skipped: $file (not found)"
    fi
done
echo ""

# Fix 3: apps.api.api.v1 → apps.api.v1
echo "Fix 3/3: Updating apps.api.api.v1 imports"
for file in tests/integration/test_nexa_integration.py \
            tests/integration/test_product_loading.py; do
    if [ -f "$file" ]; then
        sed -i.bak 's/from apps\.api\.api\.v1\./from apps.api.v1./g' "$file"
        rm -f "$file.bak"
        echo -e "${GREEN}✓${NC} Updated: $file"
    else
        echo -e "${YELLOW}⚠${NC} Skipped: $file (not found)"
    fi
done
echo ""

echo "Step 4: Post-migration verification"
echo "-------------------------------------------------------------------"

# Verify old patterns are gone
NEW_APP_MAIN=$(grep -c "from app\.main import" tests/conftest.py 2>/dev/null || echo "0")
NEW_API_API=$(grep -r "from apps\.api\.api\." tests/ 2>/dev/null | wc -l || echo "0")

echo "Remaining import issues:"
echo "  - 'from app.main' patterns: $NEW_APP_MAIN (should be 0)"
echo "  - 'from apps.api.api.*' patterns: $NEW_API_API (should be 0)"
echo ""

# Verify new patterns exist
CORRECT_MAIN=$(grep -c "from apps\.api\.main import" tests/conftest.py 2>/dev/null || echo "0")
CORRECT_V1=$(grep -r "from apps\.api\.v1\." tests/integration/test_nexa_integration.py tests/integration/test_product_loading.py 2>/dev/null | wc -l || echo "0")

echo "Correct import patterns:"
echo "  - 'from apps.api.main' in conftest.py: $CORRECT_MAIN (should be 1)"
echo "  - 'from apps.api.v1.*' in test files: $CORRECT_V1 (should be >= 2)"
echo ""

# Final status
if [ "$NEW_APP_MAIN" = "0" ] && [ "$NEW_API_API" = "0" ] && [ "$CORRECT_MAIN" = "1" ]; then
    echo -e "${GREEN}========================================================================="
    echo -e "✓ Migration completed successfully!"
    echo -e "=========================================================================${NC}"
    echo ""
    echo "Backups saved in: $BACKUP_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Run: pytest tests/conftest.py -v"
    echo "  2. Run: pytest tests/integration/test_api_integration.py -v"
    echo "  3. Run full suite: pytest tests/ -v"
    echo ""
    echo "If issues occur, restore from backups:"
    echo "  cp $BACKUP_DIR/* tests/"
    echo ""
else
    echo -e "${YELLOW}========================================================================="
    echo -e "⚠ Migration completed with warnings"
    echo -e "=========================================================================${NC}"
    echo ""
    echo "Please manually review the following:"
    if [ "$NEW_APP_MAIN" != "0" ]; then
        echo -e "${YELLOW}  - 'from app.main' still found in tests/conftest.py${NC}"
    fi
    if [ "$NEW_API_API" != "0" ]; then
        echo -e "${YELLOW}  - 'from apps.api.api.*' patterns still exist${NC}"
    fi
    if [ "$CORRECT_MAIN" != "1" ]; then
        echo -e "${YELLOW}  - Expected 'from apps.api.main' not found in conftest.py${NC}"
    fi
    echo ""
    echo "Backups available in: $BACKUP_DIR"
fi

echo ""
echo "Migration log saved to: TEST_IMPORT_ANALYSIS.md"
echo ""
