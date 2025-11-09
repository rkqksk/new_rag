#!/bin/bash
# ============================================================================
# Git Secret Cleanup Script
# ============================================================================
# Purpose: Remove accidentally committed secrets from git history
# Usage: ./scripts/security/cleanup-git-secrets.sh [method]
# Methods: bfg | filter-repo | analyze
#
# ⚠️  WARNING: This rewrites git history. Coordinate with team before running!
# ============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}=================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

confirm() {
    read -p "$(echo -e ${YELLOW}$1${NC}) [y/N]: " -r
    [[ $REPLY =~ ^[Yy]$ ]]
}

# ============================================================================
# Analysis Functions
# ============================================================================

analyze_secrets() {
    print_header "Analyzing Repository for Secrets"

    echo "Searching for potential secrets in git history..."

    # Search patterns
    local patterns=(
        "sk-proj-[A-Za-z0-9_-]{20,}"  # OpenAI project keys
        "sk-[A-Za-z0-9_-]{20,}"        # OpenAI legacy keys
        "sk_live_[A-Za-z0-9]{24,}"     # Stripe live keys
        "sk_test_[A-Za-z0-9]{24,}"     # Stripe test keys
        "ghp_[A-Za-z0-9]{36}"          # GitHub PATs
        "glpat-[A-Za-z0-9_-]{20,}"     # GitLab PATs
        "AKIA[A-Z0-9]{16}"             # AWS access keys
        "AIza[A-Za-z0-9_-]{35}"        # Google API keys
    )

    local found_secrets=0

    for pattern in "${patterns[@]}"; do
        echo "Checking for pattern: $pattern"

        if git log --all --full-history -p | grep -E "$pattern" | grep -v "your-api-key" > /dev/null 2>&1; then
            print_warning "Found potential secrets matching: $pattern"
            found_secrets=$((found_secrets + 1))

            # Show affected files
            echo "Affected files:"
            git log --all --full-history --name-only -p | grep -E "$pattern" -B 5 | grep "^diff --git" | awk '{print $3}' | sed 's/^a\///' | sort -u
            echo ""
        fi
    done

    # Check for committed .env files
    echo "Checking for committed .env files..."
    if git log --all --full-history --name-only -- .env .env.local .env.* | grep -v ".env.example" > /dev/null 2>&1; then
        print_warning "Found .env files in git history"
        git log --all --full-history --name-only -- .env .env.local .env.* | grep -v ".env.example"
        found_secrets=$((found_secrets + 1))
    fi

    echo ""
    if [ $found_secrets -eq 0 ]; then
        print_success "No secrets found in git history!"
    else
        print_warning "Found $found_secrets potential security issues"
        print_warning "Run with 'bfg' or 'filter-repo' method to clean"
    fi
}

# ============================================================================
# BFG Repo-Cleaner Method
# ============================================================================

cleanup_with_bfg() {
    print_header "Cleaning Secrets with BFG Repo-Cleaner"

    # Check if BFG is installed
    if ! command -v bfg &> /dev/null; then
        print_error "BFG Repo-Cleaner is not installed"
        echo ""
        echo "Install with:"
        echo "  macOS:   brew install bfg"
        echo "  Linux:   Download from https://rtyley.github.io/bfg-repo-cleaner/"
        echo "  Windows: Download .jar from https://rtyley.github.io/bfg-repo-cleaner/"
        exit 1
    fi

    print_warning "This will rewrite git history!"
    print_warning "All team members will need to re-clone the repository"

    if ! confirm "Continue with BFG cleanup?"; then
        echo "Cleanup cancelled"
        exit 0
    fi

    # Create backup
    local backup_dir="$PROJECT_ROOT/../rag-enterprise-backup-$(date +%Y%m%d-%H%M%S)"
    print_warning "Creating backup at: $backup_dir"
    cp -r "$PROJECT_ROOT" "$backup_dir"
    print_success "Backup created"

    cd "$PROJECT_ROOT"

    # Remove .env files from history
    echo "Removing .env files from history..."
    bfg --delete-files .env --delete-files '.env.*' --no-blob-protection .

    # Remove files matching secret patterns
    echo "Removing secret files..."
    bfg --delete-files '*.key' --delete-files '*.pem' --no-blob-protection .
    bfg --delete-files 'credentials.json' --delete-files 'secrets.yaml' --no-blob-protection .

    # Clean up
    echo "Cleaning repository..."
    git reflog expire --expire=now --all
    git gc --prune=now --aggressive

    print_success "BFG cleanup complete!"
    print_warning "Next steps:"
    echo "  1. Review changes: git log --oneline -20"
    echo "  2. Force push: git push --force"
    echo "  3. Notify team to re-clone repository"
    echo "  4. Rotate all exposed secrets"
}

# ============================================================================
# git-filter-repo Method
# ============================================================================

cleanup_with_filter_repo() {
    print_header "Cleaning Secrets with git-filter-repo"

    # Check if git-filter-repo is installed
    if ! command -v git-filter-repo &> /dev/null; then
        print_error "git-filter-repo is not installed"
        echo ""
        echo "Install with:"
        echo "  pip install git-filter-repo"
        exit 1
    fi

    print_warning "This will rewrite git history!"
    print_warning "All team members will need to re-clone the repository"

    if ! confirm "Continue with git-filter-repo cleanup?"; then
        echo "Cleanup cancelled"
        exit 0
    fi

    # Create backup
    local backup_dir="$PROJECT_ROOT/../rag-enterprise-backup-$(date +%Y%m%d-%H%M%S)"
    print_warning "Creating backup at: $backup_dir"
    cp -r "$PROJECT_ROOT" "$backup_dir"
    print_success "Backup created"

    cd "$PROJECT_ROOT"

    # Analyze repository first
    echo "Analyzing repository..."
    git filter-repo --analyze

    echo "Analysis complete. Check .git/filter-repo/analysis/ for details"

    if ! confirm "Proceed with removing .env files?"; then
        echo "Cleanup cancelled"
        exit 0
    fi

    # Remove .env files
    echo "Removing .env files from history..."
    git filter-repo --invert-paths --path .env --path '.env.local' --path '.env.*.local' --force

    print_success "git-filter-repo cleanup complete!"
    print_warning "Next steps:"
    echo "  1. Review changes: git log --oneline -20"
    echo "  2. Re-add remote: git remote add origin <your-repo-url>"
    echo "  3. Force push: git push --force --all"
    echo "  4. Force push tags: git push --force --tags"
    echo "  5. Notify team to re-clone repository"
    echo "  6. Rotate all exposed secrets"
}

# ============================================================================
# Quick Check Function
# ============================================================================

quick_check() {
    print_header "Quick Security Check"

    echo "1. Checking .gitignore configuration..."
    if git check-ignore -v .env > /dev/null 2>&1; then
        print_success ".env is properly ignored"
    else
        print_error ".env is NOT ignored!"
    fi

    echo ""
    echo "2. Checking for tracked .env files..."
    if git ls-files | grep -E "\.env$|\.env\." | grep -v ".env.example" > /dev/null 2>&1; then
        print_error "Found tracked .env files:"
        git ls-files | grep -E "\.env$|\.env\." | grep -v ".env.example"
    else
        print_success "No .env files are tracked"
    fi

    echo ""
    echo "3. Checking for common secret patterns in current branch..."
    if git log --oneline -20 -p | grep -E "(sk-proj-|sk_live_|AKIA)" | grep -v "your-api-key" > /dev/null 2>&1; then
        print_warning "Found potential secrets in recent commits"
    else
        print_success "No obvious secrets in recent commits"
    fi

    echo ""
    echo "4. Checking .env file exists locally..."
    if [ -f "$PROJECT_ROOT/.env" ]; then
        print_success ".env file exists (not tracked)"
    else
        print_warning ".env file not found - copy from .env.example"
    fi

    echo ""
    print_success "Quick check complete"
}

# ============================================================================
# Main Function
# ============================================================================

main() {
    local method="${1:-help}"

    case "$method" in
        analyze)
            analyze_secrets
            ;;
        bfg)
            cleanup_with_bfg
            ;;
        filter-repo)
            cleanup_with_filter_repo
            ;;
        check)
            quick_check
            ;;
        help|*)
            echo "Git Secret Cleanup Script"
            echo ""
            echo "Usage: $0 [method]"
            echo ""
            echo "Methods:"
            echo "  analyze       - Analyze repository for secrets (safe)"
            echo "  check         - Quick security check (safe)"
            echo "  bfg           - Clean with BFG Repo-Cleaner (⚠️  rewrites history)"
            echo "  filter-repo   - Clean with git-filter-repo (⚠️  rewrites history)"
            echo "  help          - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 check              # Quick security check"
            echo "  $0 analyze            # Analyze for secrets"
            echo "  $0 bfg                # Clean with BFG (recommended)"
            echo ""
            echo "⚠️  WARNING:"
            echo "  - Rewriting history requires force push"
            echo "  - All team members must re-clone repository"
            echo "  - Always create backup before cleaning"
            echo "  - Rotate all exposed secrets immediately"
            echo ""
            exit 0
            ;;
    esac
}

# Run main function
main "$@"
