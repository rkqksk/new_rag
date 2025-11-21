#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== CI/CD System Integrity Check ===${NC}"

FAILURES=0

# 1. Check for Duplicate CI/CD Workflows
echo -e "\n${YELLOW}[1] Checking for Duplicate Workflows...${NC}"
CI_FILES=$(find .github/workflows -maxdepth 1 -name "ci*.y*ml" | wc -l)
CD_FILES=$(find .github/workflows -maxdepth 1 -name "cd*.y*ml" | wc -l)

if [ "$CI_FILES" -gt 1 ]; then
    echo -e "${RED}❌ Duplicate CI workflows found ($CI_FILES files). Should be 1 (ci.yml).${NC}"
    find .github/workflows -name "ci*.y*ml"
    ((FAILURES++))
else
    echo -e "${GREEN}✅ CI workflow count correct.${NC}"
fi

if [ "$CD_FILES" -gt 1 ]; then
    echo -e "${RED}❌ Duplicate CD workflows found ($CD_FILES files). Should be 1 (cd.yml).${NC}"
    find .github/workflows -name "cd*.y*ml"
    ((FAILURES++))
else
    echo -e "${GREEN}✅ CD workflow count correct.${NC}"
fi

# 2. Check for Legacy Directories
echo -e "\n${YELLOW}[2] Checking for Legacy Directories...${NC}"
LEGACY_DIRS=("app" "backend" "frontend")
for dir in "${LEGACY_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${RED}❌ Legacy directory '$dir' exists. Should be archived/removed.${NC}"
        ((FAILURES++))
    else
        echo -e "${GREEN}✅ Legacy directory '$dir' not found.${NC}"
    fi
done

# 3. Verify Test Collection (Backend)
echo -e "\n${YELLOW}[3] Verifying Backend Test Collection...${NC}"
if python3 -m pytest tests/ --collect-only -q > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Pytest collection successful (Imports are valid).${NC}"
else
    echo -e "${RED}❌ Pytest collection failed. Check imports or dependencies.${NC}"
    # Run again to show error
    python3 -m pytest tests/ --collect-only
    ((FAILURES++))
fi

# 4. Verify Frontend Build (Dry Run)
echo -e "\n${YELLOW}[4] Verifying Frontend Config...${NC}"
if [ -f "package.json" ]; then
    echo -e "${GREEN}✅ package.json found.${NC}"
else
    echo -e "${RED}❌ package.json missing.${NC}"
    ((FAILURES++))
fi

# 5. Verify type-check script exists
echo -e "\n${YELLOW}[5] Verifying type-check scripts...${NC}"
if grep -q '"type-check"' package.json; then
    echo -e "${GREEN}✅ type-check script found in root package.json.${NC}"
else
    echo -e "${RED}❌ type-check script missing in root package.json.${NC}"
    ((FAILURES++))
fi

if [ -f "apps/web/package.json" ]; then
    if grep -q '"type-check"' apps/web/package.json; then
        echo -e "${GREEN}✅ type-check script found in apps/web/package.json.${NC}"
    else
        echo -e "${RED}❌ type-check script missing in apps/web/package.json.${NC}"
        ((FAILURES++))
    fi
fi

if [ -f "turbo.json" ]; then
    if grep -q '"type-check"' turbo.json; then
        echo -e "${GREEN}✅ type-check pipeline found in turbo.json.${NC}"
    else
        echo -e "${RED}❌ type-check pipeline missing in turbo.json.${NC}"
        ((FAILURES++))
    fi
fi

# Summary
echo -e "\n${GREEN}=== Summary ===${NC}"
if [ "$FAILURES" -eq 0 ]; then
    echo -e "${GREEN}🎉 System Integrity Verified! Ready for CI/CD.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  System Integrity Check Failed with $FAILURES issues.${NC}"
    echo -e "Run 'task.md' Phase 1 tasks to resolve."
    exit 1
fi
