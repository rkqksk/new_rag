#!/usr/bin/env bash
# v10.0.0 Validation Script
# Comprehensive validation of the v10 structure

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0
WARN=0

# Output file
REPORT="/home/rkqksk/projects/new_rag/V10_VALIDATION_REPORT.md"

echo "🔍 v10.0.0 Validation Script"
echo "============================"
echo ""

# Initialize report
cat > "$REPORT" << 'EOF'
# v10.0.0 Validation Report

**Generated**: $(date +"%Y-%m-%d %H:%M:%S")
**Status**: 🟡 IN PROGRESS

---

## Validation Results

EOF

# Helper functions
pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    echo "- ✅ **PASS**: $1" >> "$REPORT"
    ((PASS++))
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    echo "- ❌ **FAIL**: $1" >> "$REPORT"
    ((FAIL++))
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
    echo "- ⚠️  **WARN**: $1" >> "$REPORT"
    ((WARN++))
}

info() {
    echo -e "${BLUE}ℹ️  INFO${NC}: $1"
}

section() {
    echo ""
    echo -e "${BLUE}═══ $1 ═══${NC}"
    echo "" >> "$REPORT"
    echo "### $1" >> "$REPORT"
    echo "" >> "$REPORT"
}

cd /home/rkqksk/projects/new_rag

#============================================================================
# 1. Structure Validation
#============================================================================
section "1. Directory Structure"

# Check required top-level directories
required_dirs=("apps" "packages" "infrastructure" "services" "docs" ".claude" "workflows")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        pass "Directory exists: $dir"
    else
        fail "Missing directory: $dir"
    fi
done

# Check apps
apps=("api" "web" "pwa" "mobile")
for app in "${apps[@]}"; do
    if [ -d "apps/$app" ]; then
        pass "App exists: apps/$app"
        if [ -f "apps/$app/package.json" ] || [ -f "apps/$app/requirements.txt" ]; then
            pass "App has dependencies: apps/$app"
        else
            warn "App missing dependencies file: apps/$app"
        fi
    else
        fail "Missing app: apps/$app"
    fi
done

# Check packages
packages=("core" "ui" "config" "utils" "mobile-ui")
for pkg in "${packages[@]}"; do
    if [ -d "packages/$pkg" ]; then
        pass "Package exists: packages/$pkg"
        if [ -f "packages/$pkg/package.json" ]; then
            pass "Package has package.json: packages/$pkg"
        else
            fail "Package missing package.json: packages/$pkg"
        fi
    else
        fail "Missing package: packages/$pkg"
    fi
done

#============================================================================
# 2. Configuration Validation
#============================================================================
section "2. Configuration Files"

config_files=(
    "package.json"
    "pnpm-workspace.yaml"
    "turbo.json"
    ".gitignore"
    "tsconfig.json:optional"
)

for file in "${config_files[@]}"; do
    required=true
    if [[ $file == *":optional" ]]; then
        file="${file%:optional}"
        required=false
    fi

    if [ -f "$file" ]; then
        pass "Config file exists: $file"
    else
        if $required; then
            fail "Missing required config: $file"
        else
            warn "Missing optional config: $file"
        fi
    fi
done

#============================================================================
# 3. Dependencies
#============================================================================
section "3. Dependencies"

# Check if node_modules exists
if [ -d "node_modules" ]; then
    pass "Node dependencies installed"
else
    fail "Node dependencies not installed (run: pnpm install)"
fi

# Check pnpm
if command -v pnpm &> /dev/null; then
    pnpm_version=$(pnpm --version)
    pass "pnpm installed: v$pnpm_version"
else
    fail "pnpm not installed"
fi

# Check Node.js
if command -v node &> /dev/null; then
    node_version=$(node --version)
    pass "Node.js installed: $node_version"
else
    fail "Node.js not installed"
fi

# Check Python
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    pass "Python installed: $python_version"
else
    warn "Python not found (needed for apps/api)"
fi

#============================================================================
# 4. Build Test
#============================================================================
section "4. Build Process"

info "Testing package builds..."

# Test core package build
if [ -f "packages/core/package.json" ]; then
    if grep -q '"build"' packages/core/package.json; then
        if cd packages/core && pnpm build > /dev/null 2>&1; then
            pass "packages/core builds successfully"
            cd ../..
        else
            fail "packages/core build failed"
            cd ../..
        fi
    else
        warn "packages/core has no build script"
    fi
fi

#============================================================================
# 5. Documentation
#============================================================================
section "5. Documentation"

docs=(
    "README.md"
    "CHANGELOG.md"
    "CLAUDE.md"
    "QUICK_START.md"
    "PROGRESS.md"
    "V10_COMPREHENSIVE_REVIEW.md"
    "V10_EXECUTION_PLAN.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        pass "Documentation exists: $doc"
    else
        warn "Missing documentation: $doc"
    fi
done

#============================================================================
# 6. Archive
#============================================================================
section "6. Archive Validation"

if [ -d ".archive" ]; then
    pass ".archive directory exists"

    archived=("app-v9" "backend-v9" "src-v9")
    for archive in "${archived[@]}"; do
        if [ -d ".archive/$archive" ]; then
            pass "Archived: .archive/$archive"
        else
            warn "Missing archive: .archive/$archive"
        fi
    done
else
    fail ".archive directory missing"
fi

#============================================================================
# 7. Infrastructure
#============================================================================
section "7. Infrastructure"

infra_dirs=("k8s" "terraform" "observability")
for dir in "${infra_dirs[@]}"; do
    if [ -d "infrastructure/$dir" ]; then
        pass "Infrastructure component: infrastructure/$dir"
    else
        warn "Missing infrastructure: infrastructure/$dir"
    fi
done

#============================================================================
# 8. Git Status
#============================================================================
section "8. Git Status"

if git rev-parse --git-dir > /dev/null 2>&1; then
    pass "Git repository initialized"

    current_branch=$(git branch --show-current)
    info "Current branch: $current_branch"
    echo "- Current branch: \`$current_branch\`" >> "$REPORT"

    if [ -n "$(git status --porcelain)" ]; then
        warn "Working directory has uncommitted changes"
    else
        pass "Working directory clean"
    fi
else
    fail "Not a git repository"
fi

#============================================================================
# Summary
#============================================================================
echo "" >> "$REPORT"
echo "---" >> "$REPORT"
echo "" >> "$REPORT"
echo "## Summary" >> "$REPORT"
echo "" >> "$REPORT"
echo "- ✅ **Passed**: $PASS" >> "$REPORT"
echo "- ❌ **Failed**: $FAIL" >> "$REPORT"
echo "- ⚠️  **Warnings**: $WARN" >> "$REPORT"
echo "" >> "$REPORT"

TOTAL=$((PASS + FAIL + WARN))
if [ $TOTAL -gt 0 ]; then
    PASS_RATE=$((PASS * 100 / TOTAL))
    echo "**Pass Rate**: $PASS_RATE% ($PASS/$TOTAL)" >> "$REPORT"
fi

echo "" >> "$REPORT"

if [ $FAIL -eq 0 ]; then
    echo "**Status**: ✅ **VALIDATION PASSED**" >> "$REPORT"
    echo ""
    echo -e "${GREEN}════════════════════════════════${NC}"
    echo -e "${GREEN}✅ VALIDATION PASSED${NC}"
    echo -e "${GREEN}════════════════════════════════${NC}"
    echo ""
    echo "Passed: $PASS | Failed: $FAIL | Warnings: $WARN"
    exit 0
else
    echo "**Status**: ❌ **VALIDATION FAILED**" >> "$REPORT"
    echo ""
    echo -e "${RED}════════════════════════════════${NC}"
    echo -e "${RED}❌ VALIDATION FAILED${NC}"
    echo -e "${RED}════════════════════════════════${NC}"
    echo ""
    echo "Passed: $PASS | Failed: $FAIL | Warnings: $WARN"
    echo ""
    echo -e "${YELLOW}Please fix the failed checks and run again.${NC}"
    exit 1
fi

echo ""
echo "📄 Full report: $REPORT"