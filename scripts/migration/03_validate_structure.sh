#!/bin/bash
# Migration Script 3: Comprehensive post-migration validation
# Ensures backend/ structure is correct and all imports work

set -e

echo "🔍 Phase 5: Post-Migration Validation"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Track test results
PASSED=0
FAILED=0
WARNINGS=0

# Helper function for test results
test_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((PASSED++))
}

test_fail() {
    echo -e "  ${RED}✗${NC} $1"
    ((FAILED++))
}

test_warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# Test 1: Directory Structure
echo ""
echo -e "${BLUE}Test 1: Directory Structure${NC}"
echo "----------------------------"

if [ -d "backend/api/v1" ]; then
    test_pass "backend/api/v1 exists"
else
    test_fail "backend/api/v1 missing"
fi

if [ -d "backend/api/v2" ]; then
    test_pass "backend/api/v2 exists"
else
    test_fail "backend/api/v2 missing"
fi

if [ -d "backend/middleware/advanced" ]; then
    test_pass "backend/middleware/advanced exists"
else
    test_fail "backend/middleware/advanced missing"
fi

if [ -d "backend/core" ]; then
    test_pass "backend/core exists"
else
    test_fail "backend/core missing"
fi

if [ -f "backend/main.py" ]; then
    test_pass "backend/main.py exists"
else
    test_fail "backend/main.py missing"
fi

# Test 2: File Counts
echo ""
echo -e "${BLUE}Test 2: File Counts${NC}"
echo "--------------------"

v1_count=$(find backend/api/v1 -name "*.py" 2>/dev/null | wc -l)
v2_count=$(find backend/api/v2 -name "*.py" 2>/dev/null | wc -l)
middleware_basic=$(find backend/middleware -maxdepth 1 -name "*.py" 2>/dev/null | wc -l)
middleware_advanced=$(find backend/middleware/advanced -name "*.py" 2>/dev/null | wc -l)
core_count=$(find backend/core -name "*.py" 2>/dev/null | wc -l)
services_count=$(find backend/services -name "*.py" 2>/dev/null | wc -l)

echo "  v1 APIs:              $v1_count files"
echo "  v2 APIs:              $v2_count files"
echo "  Middleware (basic):   $middleware_basic files"
echo "  Middleware (advanced): $middleware_advanced files"
echo "  Core modules:         $core_count files"
echo "  Services:             $services_count files"

if [ "$v1_count" -ge 10 ]; then
    test_pass "v1 APIs present ($v1_count files)"
else
    test_warn "v1 APIs count low ($v1_count files)"
fi

if [ "$v2_count" -ge 5 ]; then
    test_pass "v2 APIs present ($v2_count files)"
else
    test_warn "v2 APIs count low ($v2_count files)"
fi

# Test 3: Import Validation
echo ""
echo -e "${BLUE}Test 3: Import Validation${NC}"
echo "--------------------------"

# Check for old imports
app_imports=$(grep -r "from app\." backend/ 2>/dev/null | grep -v ".pyc" | grep -v "# from app" | wc -l || echo "0")
src_imports=$(grep -r "from src\." backend/ 2>/dev/null | grep -v ".pyc" | grep -v "# from src" | wc -l || echo "0")

if [ "$app_imports" -eq 0 ]; then
    test_pass "No app.* imports found"
else
    test_fail "Found $app_imports app.* imports"
    echo ""
    echo "First 5 occurrences:"
    grep -r "from app\." backend/ 2>/dev/null | grep -v ".pyc" | head -5
fi

if [ "$src_imports" -eq 0 ]; then
    test_pass "No src.* imports found"
else
    test_fail "Found $src_imports src.* imports"
    echo ""
    echo "First 5 occurrences:"
    grep -r "from src\." backend/ 2>/dev/null | grep -v ".pyc" | head -5
fi

# Test 4: Python Import Tests
echo ""
echo -e "${BLUE}Test 4: Python Import Tests${NC}"
echo "----------------------------"

python3 << 'PYEOF'
import sys
import importlib

# Critical modules to test
modules = [
    ("backend.core.config", "Core config"),
    ("backend.core.logging", "Core logging"),
    ("backend.core.exceptions", "Core exceptions"),
    ("backend.api.v1.search", "v1 Search API"),
    ("backend.middleware.request_logging", "Basic middleware"),
]

# Optional v2 modules (may not exist yet)
optional_modules = [
    ("backend.api.v2.auth", "v2 Auth API"),
    ("backend.api.v2.manufacturing", "v2 Manufacturing API"),
    ("backend.middleware.advanced.rate_limiting", "Advanced rate limiting"),
    ("backend.middleware.advanced.error_tracking", "Advanced error tracking"),
]

failed = []
passed = []
optional_failed = []

print("")
print("Required imports:")
for module, desc in modules:
    try:
        importlib.import_module(module)
        print(f"  ✓ {desc:30s} ({module})")
        passed.append(module)
    except Exception as e:
        print(f"  ✗ {desc:30s} ({module})")
        print(f"    Error: {str(e)[:60]}")
        failed.append((module, str(e)))

print("")
print("Optional v2 imports:")
for module, desc in optional_modules:
    try:
        importlib.import_module(module)
        print(f"  ✓ {desc:30s} ({module})")
        passed.append(module)
    except Exception as e:
        print(f"  ⚠ {desc:30s} ({module})")
        print(f"    Info: {str(e)[:60]}")
        optional_failed.append(module)

print("")
print(f"Summary: {len(passed)} passed, {len(failed)} failed, {len(optional_failed)} optional missing")

if failed:
    print("\n❌ Critical import failures detected")
    sys.exit(1)
else:
    print("\n✅ All critical imports successful")
    sys.exit(0)
PYEOF

import_result=$?

if [ $import_result -eq 0 ]; then
    test_pass "All critical modules import successfully"
else
    test_fail "Import errors detected"
fi

# Test 5: Syntax Validation
echo ""
echo -e "${BLUE}Test 5: Syntax Validation${NC}"
echo "--------------------------"

syntax_errors=0
checked=0

while IFS= read -r file; do
    ((checked++))
    if ! python3 -m py_compile "$file" 2>/dev/null; then
        echo -e "  ${RED}✗${NC} Syntax error: $file"
        ((syntax_errors++))
    fi
done < <(find backend/ -name "*.py" -type f)

if [ $syntax_errors -eq 0 ]; then
    test_pass "All $checked Python files have valid syntax"
else
    test_fail "$syntax_errors files have syntax errors (out of $checked)"
fi

# Test 6: Configuration Files
echo ""
echo -e "${BLUE}Test 6: Configuration Files${NC}"
echo "----------------------------"

# Check pytest.ini
if grep -q "source = backend" pytest.ini 2>/dev/null; then
    test_pass "pytest.ini updated to backend"
else
    test_warn "pytest.ini may need updating"
fi

# Check docker-compose.yml
if grep -q "backend.main:app" docker-compose.yml 2>/dev/null; then
    test_pass "docker-compose.yml updated to backend"
elif grep -q "app.main:app" docker-compose.yml 2>/dev/null; then
    test_warn "docker-compose.yml still references app.main"
fi

# Check Dockerfile
if [ -f "Dockerfile" ]; then
    if grep -q "backend.main:app" Dockerfile 2>/dev/null; then
        test_pass "Dockerfile updated to backend"
    elif grep -q "app.main:app" Dockerfile 2>/dev/null; then
        test_warn "Dockerfile still references app.main"
    fi
fi

# Test 7: Key Files Exist
echo ""
echo -e "${BLUE}Test 7: Key Files Exist${NC}"
echo "------------------------"

key_files=(
    "backend/main.py:Main entry point"
    "backend/core/config.py:Core configuration"
    "backend/api/v1/__init__.py:v1 API package"
    "backend/api/v2/__init__.py:v2 API package"
    "backend/middleware/__init__.py:Middleware package"
    "backend/middleware/advanced/__init__.py:Advanced middleware package"
)

for entry in "${key_files[@]}"; do
    IFS=: read -r file desc <<< "$entry"
    if [ -f "$file" ]; then
        test_pass "$desc"
    else
        test_fail "$desc missing ($file)"
    fi
done

# Test 8: API Version Structure
echo ""
echo -e "${BLUE}Test 8: API Version Structure${NC}"
echo "------------------------------"

v2_routes=(
    "backend/api/v2/auth.py:JWT Authentication"
    "backend/api/v2/manufacturing.py:Manufacturing API"
    "backend/api/v2/metrics.py:Metrics API"
    "backend/api/v2/saas.py:SaaS Platform"
)

v2_exists=0
for entry in "${v2_routes[@]}"; do
    IFS=: read -r file desc <<< "$entry"
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $desc"
        ((v2_exists++))
    else
        echo -e "  ${YELLOW}⚠${NC} $desc not found"
    fi
done

if [ $v2_exists -ge 2 ]; then
    test_pass "v2 API routes present ($v2_exists files)"
else
    test_warn "Limited v2 API routes ($v2_exists files)"
fi

# Final Summary
echo ""
echo "======================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ Validation PASSED${NC}"
else
    echo -e "${RED}❌ Validation FAILED${NC}"
fi
echo "======================================"
echo ""
echo "Results:"
echo -e "  ${GREEN}Passed:   $PASSED${NC}"
echo -e "  ${RED}Failed:   $FAILED${NC}"
echo -e "  ${YELLOW}Warnings: $WARNINGS${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}Migration validation successful!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Update docker-compose.yml manually if needed"
    echo "  2. Run: docker-compose build api"
    echo "  3. Run: docker-compose up -d"
    echo "  4. Run: pytest tests/test_api_quick.py -v"
    echo "  5. Test API: curl http://localhost:8001/health/ready"
    exit 0
else
    echo -e "${RED}Migration validation failed!${NC}"
    echo ""
    echo "Please review the failed tests above and fix issues."
    echo "You may need to manually update some files."
    exit 1
fi
