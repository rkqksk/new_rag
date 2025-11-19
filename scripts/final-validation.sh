#!/usr/bin/env bash
# Final validation script for v10.0.0 release

set -e

echo "🎯 Final Validation - v10.0.0"
echo "=============================="
echo ""

# Create validation report
REPORT_FILE="reports/validation/final-validation-$(date +%Y%m%d-%H%M%S).md"
mkdir -p reports/validation

# Initialize report
cat > $REPORT_FILE <<EOF
# Final Validation Report - v10.0.0

**Generated**: $(date -Iseconds)
**Version**: v10.0.0 "Unified Maximum"
**Status**: In Progress

---

EOF

TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Helper function to add check result
add_check() {
    local name=$1
    local status=$2
    local details=$3

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [ "$status" = "pass" ]; then
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        echo "✅ $name" | tee -a $REPORT_FILE
    else
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        echo "❌ $name" | tee -a $REPORT_FILE
    fi

    if [ -n "$details" ]; then
        echo "   $details" | tee -a $REPORT_FILE
    fi
}

echo "## 1. Environment Validation" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE

# Check Node.js
if node --version > /dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    add_check "Node.js installed" "pass" "Version: $NODE_VERSION"
else
    add_check "Node.js installed" "fail" "Node.js not found"
fi

# Check Python
if python3 --version > /dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version)
    add_check "Python installed" "pass" "Version: $PYTHON_VERSION"
else
    add_check "Python installed" "fail" "Python not found"
fi

# Check pnpm
if pnpm --version > /dev/null 2>&1; then
    PNPM_VERSION=$(pnpm --version)
    add_check "pnpm installed" "pass" "Version: $PNPM_VERSION"
else
    add_check "pnpm installed" "fail" "pnpm not found"
fi

# Check Docker
if docker --version > /dev/null 2>&1; then
    DOCKER_VERSION=$(docker --version)
    add_check "Docker installed" "pass" "Version: $DOCKER_VERSION"
else
    add_check "Docker installed" "fail" "Docker not found"
fi

echo "" | tee -a $REPORT_FILE
echo "## 2. Dependency Validation" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE

# Check node_modules
if [ -d "node_modules" ]; then
    add_check "Node dependencies installed" "pass" "$(du -sh node_modules | cut -f1)"
else
    add_check "Node dependencies installed" "fail" "Run: pnpm install"
fi

# Check Python virtual environment
if [ -d ".venv" ]; then
    add_check "Python venv exists" "pass" ""
else
    add_check "Python venv exists" "fail" "Run: python3 -m venv .venv"
fi

echo "" | tee -a $REPORT_FILE
echo "## 3. Build Validation" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE

# Check if builds exist
if [ -d "apps/web/.next" ]; then
    add_check "Web app build exists" "pass" ""
else
    add_check "Web app build exists" "fail" "Run: pnpm build"
fi

echo "" | tee -a $REPORT_FILE
echo "## 4. Test Validation" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE

# Run tests if pytest is available
if command -v pytest > /dev/null 2>&1; then
    echo "   Running backend tests..."
    if pytest tests/ -v --tb=short -x 2>&1 | tee -a reports/validation/pytest-output.txt; then
        add_check "Backend tests" "pass" "All tests passed"
    else
        add_check "Backend tests" "fail" "Some tests failed - check reports/validation/pytest-output.txt"
    fi
else
    add_check "Backend tests" "fail" "pytest not found"
fi

# Run E2E tests if Playwright is available
if [ -f "playwright.config.ts" ]; then
    echo "   Checking E2E test configuration..."
    add_check "E2E tests configured" "pass" "Playwright config found"
else
    add_check "E2E tests configured" "fail" "playwright.config.ts not found"
fi

echo "" | tee -a $REPORT_FILE
echo "## 5. Security Validation" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE

# Check for security files
if [ -f "SECURITY.md" ]; then
    add_check "Security policy exists" "pass" "SECURITY.md present"
else
    add_check "Security policy exists" "fail" "Create SECURITY.md"
fi

# Check .env is gitignored
if grep -q "^\.env$" .gitignore 2>/dev/null; then
    add_check ".env in .gitignore" "pass" ""
else
    add_check ".env in .gitignore" "fail" "Add .env to .gitignore"
fi

# Check for hardcoded secrets (basic check)
if grep -r "password.*=.*['\"]" --include="*.py" --include="*.js" apps/ 2>/dev/null | grep -v "password: str" | grep -v "# " > /dev/null; then
    add_check "No hardcoded passwords" "fail" "Potential hardcoded passwords found"
else
    add_check "No hardcoded passwords" "pass" ""
fi

echo "" | tee -a $REPORT_FILE
echo "## 6. Documentation Validation" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE

# Check essential documentation
for doc in "README.md" "CLAUDE.md" "PROGRESS.md"; do
    if [ -f "$doc" ]; then
        add_check "$doc exists" "pass" "$(wc -l < $doc) lines"
    else
        add_check "$doc exists" "fail" ""
    fi
done

# Check docs directory
if [ -d "docs" ]; then
    DOC_COUNT=$(find docs -name "*.md" | wc -l)
    add_check "Documentation directory" "pass" "$DOC_COUNT markdown files"
else
    add_check "Documentation directory" "fail" "docs/ not found"
fi

echo "" | tee -a $REPORT_FILE
echo "## 7. Git Validation" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE

# Check git status
if [ -d ".git" ]; then
    add_check "Git repository" "pass" ""

    # Check for uncommitted changes
    if [ -z "$(git status --porcelain)" ]; then
        add_check "Working directory clean" "pass" "No uncommitted changes"
    else
        add_check "Working directory clean" "fail" "$(git status --porcelain | wc -l) uncommitted changes"
    fi

    # Check current branch
    CURRENT_BRANCH=$(git branch --show-current)
    add_check "Git branch" "pass" "Currently on: $CURRENT_BRANCH"
else
    add_check "Git repository" "fail" "Not a git repository"
fi

echo "" | tee -a $REPORT_FILE
echo "## 8. CI/CD Validation" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE

# Check GitHub Actions
if [ -d ".github/workflows" ]; then
    WORKFLOW_COUNT=$(find .github/workflows -name "*.yml" -o -name "*.yaml" | wc -l)
    add_check "GitHub Actions workflows" "pass" "$WORKFLOW_COUNT workflows configured"
else
    add_check "GitHub Actions workflows" "fail" ".github/workflows not found"
fi

# Check Docker files
if [ -f "docker-compose.yml" ]; then
    add_check "Docker Compose config" "pass" ""
else
    add_check "Docker Compose config" "fail" "docker-compose.yml not found"
fi

echo "" | tee -a $REPORT_FILE
echo "## 9. Performance Validation" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE

# Check if performance reports exist
if [ -d "reports/performance" ]; then
    PERF_REPORTS=$(find reports/performance -name "*.json" | wc -l)
    if [ $PERF_REPORTS -gt 0 ]; then
        add_check "Performance benchmarks" "pass" "$PERF_REPORTS reports available"
    else
        add_check "Performance benchmarks" "fail" "Run: ./scripts/benchmark.sh"
    fi
else
    add_check "Performance benchmarks" "fail" "No performance reports"
fi

echo "" | tee -a $REPORT_FILE
echo "## 10. Deployment Validation" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE

# Check Kubernetes configs
if [ -d "infrastructure/k8s" ]; then
    K8S_CONFIGS=$(find infrastructure/k8s -name "*.yaml" | wc -l)
    add_check "Kubernetes configs" "pass" "$K8S_CONFIGS manifests"
else
    add_check "Kubernetes configs" "fail" "infrastructure/k8s not found"
fi

# Check deployment scripts
if [ -f "scripts/deploy-production.sh" ]; then
    add_check "Production deploy script" "pass" ""
else
    add_check "Production deploy script" "fail" "scripts/deploy-production.sh not found"
fi

# Generate final summary
echo "" | tee -a $REPORT_FILE
echo "---" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE
echo "## Summary" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE
echo "- **Total Checks**: $TOTAL_CHECKS" | tee -a $REPORT_FILE
echo "- **Passed**: $PASSED_CHECKS" | tee -a $REPORT_FILE
echo "- **Failed**: $FAILED_CHECKS" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE

# Calculate score
SCORE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
echo "**Score**: $SCORE/100" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE

if [ $FAILED_CHECKS -eq 0 ]; then
    echo "## 🎉 Result: PASSED" | tee -a $REPORT_FILE
    echo "" | tee -a $REPORT_FILE
    echo "All validation checks passed! Ready for v10.0.0 release." | tee -a $REPORT_FILE
    EXIT_CODE=0
else
    echo "## ⚠️ Result: ISSUES FOUND" | tee -a $REPORT_FILE
    echo "" | tee -a $REPORT_FILE
    echo "Please address the failed checks before proceeding with release." | tee -a $REPORT_FILE
    EXIT_CODE=1
fi

echo "" | tee -a $REPORT_FILE
echo "---" | tee -a $REPORT_FILE
echo "*Report saved to: $REPORT_FILE*" | tee -a $REPORT_FILE

echo ""
echo "📄 Full report: $REPORT_FILE"

exit $EXIT_CODE
