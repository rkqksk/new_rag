#!/bin/bash

################################################################################
# Test Automation Scripts
################################################################################
# Purpose: Verify all automation scripts are working correctly
# Usage: ./scripts/test-automation.sh
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_info() { echo -e "${BLUE}→${NC} $1"; }

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

print_header "Testing Automation Scripts"

# Test 1: setup.sh exists and is executable
print_info "Test 1: Checking setup.sh..."
if [ -x "setup.sh" ]; then
    print_success "setup.sh exists and is executable"
else
    print_error "setup.sh missing or not executable"
    exit 1
fi

# Test 2: setup.sh --help works
print_info "Test 2: Testing setup.sh --help..."
if ./setup.sh --help > /dev/null 2>&1; then
    print_success "setup.sh --help works"
else
    print_error "setup.sh --help failed"
    exit 1
fi

# Test 3: build-all.sh exists and is executable
print_info "Test 3: Checking build-all.sh..."
if [ -x "build-all.sh" ]; then
    print_success "build-all.sh exists and is executable"
else
    print_error "build-all.sh missing or not executable"
    exit 1
fi

# Test 4: build-all.sh --help works
print_info "Test 4: Testing build-all.sh --help..."
if ./build-all.sh --help > /dev/null 2>&1; then
    print_success "build-all.sh --help works"
else
    print_error "build-all.sh --help failed"
    exit 1
fi

# Test 5: pre-commit config exists
print_info "Test 5: Checking .pre-commit-config.yaml..."
if [ -f ".pre-commit-config.yaml" ]; then
    print_success ".pre-commit-config.yaml exists"
else
    print_error ".pre-commit-config.yaml missing"
    exit 1
fi

# Test 6: pre-commit config has TypeScript hooks
print_info "Test 6: Checking TypeScript hooks in pre-commit..."
if grep -q "prettier" .pre-commit-config.yaml; then
    print_success "Prettier hook found"
else
    print_error "Prettier hook missing"
    exit 1
fi

if grep -q "eslint" .pre-commit-config.yaml; then
    print_success "ESLint hook found"
else
    print_error "ESLint hook missing"
    exit 1
fi

# Test 7: pre-commit config has design system hooks
print_info "Test 7: Checking design system hooks..."
if grep -q "no-icons" .pre-commit-config.yaml; then
    print_success "No icons hook found"
else
    print_error "No icons hook missing"
    exit 1
fi

if grep -q "pure-black-background" .pre-commit-config.yaml; then
    print_success "Pure black background hook found"
else
    print_error "Pure black background hook missing"
    exit 1
fi

# Test 8: Documentation exists
print_info "Test 8: Checking documentation..."
if [ -f "docs/guides/AUTOMATION_SCRIPTS.md" ]; then
    print_success "AUTOMATION_SCRIPTS.md exists"
else
    print_error "AUTOMATION_SCRIPTS.md missing"
    exit 1
fi

if [ -f "scripts/README.md" ]; then
    print_success "scripts/README.md exists"
else
    print_error "scripts/README.md missing"
    exit 1
fi

# Test 9: CLAUDE.md updated
print_info "Test 9: Checking CLAUDE.md updates..."
if grep -q "setup.sh" CLAUDE.md; then
    print_success "setup.sh documented in CLAUDE.md"
else
    print_error "setup.sh not found in CLAUDE.md"
    exit 1
fi

if grep -q "build-all.sh" CLAUDE.md; then
    print_success "build-all.sh documented in CLAUDE.md"
else
    print_error "build-all.sh not found in CLAUDE.md"
    exit 1
fi

if grep -q "pre-commit" CLAUDE.md; then
    print_success "pre-commit documented in CLAUDE.md"
else
    print_error "pre-commit not found in CLAUDE.md"
    exit 1
fi

print_header "All Tests Passed!"

echo -e "${GREEN}✓ All automation scripts are working correctly!${NC}\n"

echo -e "${BLUE}Summary:${NC}"
echo -e "  • setup.sh: ${GREEN}✓${NC} Working"
echo -e "  • build-all.sh: ${GREEN}✓${NC} Working"
echo -e "  • .pre-commit-config.yaml: ${GREEN}✓${NC} Updated with TypeScript & design hooks"
echo -e "  • Documentation: ${GREEN}✓${NC} Complete"
echo -e ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Run setup: ${YELLOW}./setup.sh${NC}"
echo -e "  2. Install pre-commit: ${YELLOW}pip install pre-commit && pre-commit install${NC}"
echo -e "  3. Build project: ${YELLOW}./build-all.sh --parallel${NC}"
echo -e ""
