#!/bin/bash
# Migration Script 2: Update all imports from app.* and src.* to backend.*
# Comprehensive import replacement with validation

set -e

echo "🔄 Phase 3C: Updating imports in backend/"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Track statistics
FILES_UPDATED=0
TOTAL_FILES=0
BACKUP_DIR=".migration_backup_$(date +%Y%m%d_%H%M%S)"

# Create backup
echo ""
echo -e "${BLUE}Creating backup in $BACKUP_DIR...${NC}"
mkdir -p "$BACKUP_DIR"
cp -r backend/ "$BACKUP_DIR/"
echo -e "  ${GREEN}✓${NC} Backup created"

# Function to update imports in a file
update_imports() {
    local file="$1"
    local changed=0

    # Skip __pycache__ and non-Python files
    if [[ "$file" == *"__pycache__"* ]] || [[ "$file" != *.py ]]; then
        return
    fi

    ((TOTAL_FILES++))

    # Create temporary file
    temp_file="${file}.tmp"
    cp "$file" "$temp_file"

    # Update app.* imports to backend.*
    # Handle both "from app." and "import app."
    sed -i 's/from app\.\([a-zA-Z0-9_\.]*\) import/from backend.\1 import/g' "$temp_file"
    sed -i 's/import app\.\([a-zA-Z0-9_\.]*\)/import backend.\1/g' "$temp_file"

    # Update src.api.routes.* to backend.api.v2.*
    sed -i 's/from src\.api\.routes\.\([a-zA-Z0-9_]*\) import/from backend.api.v2.\1 import/g' "$temp_file"
    sed -i 's/import src\.api\.routes\.\([a-zA-Z0-9_]*\)/import backend.api.v2.\1/g' "$temp_file"

    # Update src.api.v1.* to backend.api.v2.*
    sed -i 's/from src\.api\.v1\.\([a-zA-Z0-9_]*\) import/from backend.api.v2.\1 import/g' "$temp_file"
    sed -i 's/import src\.api\.v1\.\([a-zA-Z0-9_]*\)/import backend.api.v2.\1/g' "$temp_file"

    # Update src.middleware.* to backend.middleware.advanced.*
    sed -i 's/from src\.middleware\.\([a-zA-Z0-9_]*\) import/from backend.middleware.advanced.\1 import/g' "$temp_file"
    sed -i 's/import src\.middleware\.\([a-zA-Z0-9_]*\)/import backend.middleware.advanced.\1/g' "$temp_file"

    # Update remaining src.* imports to backend.*
    sed -i 's/from src\.\([a-zA-Z0-9_\.]*\) import/from backend.\1 import/g' "$temp_file"
    sed -i 's/import src\.\([a-zA-Z0-9_\.]*\)/import backend.\1/g' "$temp_file"

    # Check if file changed
    if ! diff -q "$file" "$temp_file" > /dev/null 2>&1; then
        mv "$temp_file" "$file"
        echo -e "  ${GREEN}✓${NC} $file"
        ((FILES_UPDATED++))
        changed=1
    else
        rm "$temp_file"
    fi

    return $changed
}

# Export function for find
export -f update_imports
export GREEN RED YELLOW NC
export FILES_UPDATED TOTAL_FILES

# Step 1: Update all Python files in backend/
echo ""
echo "Step 1: Updating imports in backend/ Python files..."
echo ""

find backend/ -type f -name "*.py" | while read -r file; do
    update_imports "$file" || true
done

# Step 2: Update pytest.ini
echo ""
echo "Step 2: Updating pytest.ini..."
if [ -f "pytest.ini" ]; then
    sed -i 's/source = app/source = backend/g' pytest.ini
    echo -e "  ${GREEN}✓${NC} pytest.ini updated"
fi

# Step 3: Update alembic/env.py
echo ""
echo "Step 3: Updating alembic/env.py..."
if [ -f "alembic/env.py" ]; then
    sed -i 's/from app\./from backend./g' alembic/env.py
    sed -i 's/import app\./import backend./g' alembic/env.py
    echo -e "  ${GREEN}✓${NC} alembic/env.py updated"
fi

# Step 4: Update tests/
echo ""
echo "Step 4: Updating tests/ directory..."
if [ -d "tests" ]; then
    find tests/ -type f -name "*.py" | while read -r file; do
        update_imports "$file" || true
    done
    echo -e "  ${GREEN}✓${NC} tests/ updated"
fi

# Step 5: Update scripts/
echo ""
echo "Step 5: Updating scripts/ directory..."
if [ -d "scripts" ]; then
    # Update Python scripts
    find scripts/ -type f -name "*.py" | while read -r file; do
        update_imports "$file" || true
    done

    # Update shell scripts
    find scripts/ -type f -name "*.sh" | while read -r file; do
        if grep -q "app\.main\|app\." "$file" 2>/dev/null; then
            sed -i 's/app\.main/backend.main/g' "$file"
            sed -i 's/--app app:/--app backend:/g' "$file"
            echo -e "  ${GREEN}✓${NC} $file"
        fi
    done
fi

# Step 6: Validation
echo ""
echo "Step 6: Validating import updates..."
echo ""

# Check for remaining app.* imports in backend/
app_imports=$(grep -r "from app\." backend/ 2>/dev/null | grep -v ".pyc" | wc -l || echo "0")
if [ "$app_imports" -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} No app.* imports found in backend/"
else
    echo -e "  ${RED}✗${NC} Found $app_imports app.* imports in backend/"
    echo ""
    echo "Remaining app.* imports:"
    grep -r "from app\." backend/ 2>/dev/null | grep -v ".pyc" | head -10
fi

# Check for remaining src.* imports in backend/
src_imports=$(grep -r "from src\." backend/ 2>/dev/null | grep -v ".pyc" | wc -l || echo "0")
if [ "$src_imports" -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} No src.* imports found in backend/"
else
    echo -e "  ${RED}✗${NC} Found $src_imports src.* imports in backend/"
    echo ""
    echo "Remaining src.* imports:"
    grep -r "from src\." backend/ 2>/dev/null | grep -v ".pyc" | head -10
fi

# Step 7: Test import syntax
echo ""
echo "Step 7: Testing Python import syntax..."
python3 << 'PYEOF'
import sys
import ast

def check_syntax(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        return True, None
    except SyntaxError as e:
        return False, str(e)

# Check a few critical files
critical_files = [
    'backend/main.py',
    'backend/core/config.py',
    'backend/api/v1/search.py',
]

errors = []
for file_path in critical_files:
    try:
        valid, error = check_syntax(file_path)
        if valid:
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path}: {error}")
            errors.append(file_path)
    except FileNotFoundError:
        print(f"  ⚠ {file_path} not found")

if errors:
    print(f"\n❌ Syntax errors found in {len(errors)} files")
    sys.exit(1)
else:
    print("\n✅ All critical files have valid syntax")
PYEOF

syntax_check=$?

# Summary
echo ""
echo "=========================================="
if [ "$app_imports" -eq 0 ] && [ "$src_imports" -eq 0 ] && [ "$syntax_check" -eq 0 ]; then
    echo -e "${GREEN}✅ Import Update Complete${NC}"
else
    echo -e "${YELLOW}⚠ Import Update Complete with Warnings${NC}"
fi
echo "=========================================="
echo ""
echo "Statistics:"
echo "  Total files processed: $TOTAL_FILES"
echo "  Files updated:        $FILES_UPDATED"
echo ""
echo "Validation:"
if [ "$app_imports" -eq 0 ]; then
    echo -e "  app.* imports:   ${GREEN}0${NC}"
else
    echo -e "  app.* imports:   ${RED}$app_imports${NC}"
fi
if [ "$src_imports" -eq 0 ]; then
    echo -e "  src.* imports:   ${GREEN}0${NC}"
else
    echo -e "  src.* imports:   ${RED}$src_imports${NC}"
fi
echo ""
echo "Backup saved at: $BACKUP_DIR"
echo ""

if [ "$app_imports" -gt 0 ] || [ "$src_imports" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Manual review required for remaining imports${NC}"
    echo ""
    echo "To rollback:"
    echo "  rm -rf backend/"
    echo "  cp -r $BACKUP_DIR/backend ."
    echo ""
fi

echo "Next step: Run 03_validate_structure.sh"
