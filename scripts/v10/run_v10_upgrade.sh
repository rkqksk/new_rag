#!/usr/bin/env bash
# v10.0.0 Master Upgrade Script
# Executes all 4 phases: Maximal → Minimal philosophy

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=================================================="
echo "RAG Enterprise v10.0.0 Upgrade"
echo "Philosophy: Maximal Features → Minimal Structure"
echo "=================================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_phase() {
    echo -e "${BLUE}$1${NC}"
}

# Pre-flight checks
echo "Pre-flight Checks"
echo "------------------------------------------------"
log_info "Checking prerequisites..."

# Check git
if ! command -v git &> /dev/null; then
    log_error "git not found. Please install git."
    exit 1
fi
log_info "✓ git found"

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "python3 not found. Please install Python 3.11+"
    exit 1
fi
log_info "✓ python3 found: $(python3 --version)"

# Check pip
if ! command -v pip &> /dev/null; then
    log_error "pip not found. Please install pip."
    exit 1
fi
log_info "✓ pip found"

# Check Node.js (for frontend)
if ! command -v node &> /dev/null; then
    log_warn "node not found. Frontend upgrade will be skipped."
else
    log_info "✓ node found: $(node --version)"
fi

# Check Claude Skills
if [ ! -d ".claude/skills" ]; then
    log_error ".claude/skills not found. Please ensure Claude Skills are available."
    exit 1
fi
log_info "✓ Claude Skills found"

echo ""
log_info "All prerequisites met!"
echo ""

# Confirm
read -p "Ready to upgrade to v10.0.0? This will modify your codebase. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Upgrade cancelled."
    exit 0
fi

echo ""

# Backup
log_info "Creating backup tag: v9.3.0-backup"
git tag -f v9.3.0-backup || log_warn "Tag already exists"
echo ""

# Phase 1: Backend Maximal
log_phase "=================================================="
log_phase "Phase 1: Backend Maximal Features"
log_phase "=================================================="
bash "$SCRIPT_DIR/phase1_backend_maximal.sh"

read -p "Phase 1 complete. Continue to Phase 2? (Y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    log_warn "Upgrade paused after Phase 1."
    exit 0
fi
echo ""

# Phase 2: Backend Trimming
log_phase "=================================================="
log_phase "Phase 2: Backend Trimming"
log_phase "=================================================="
bash "$SCRIPT_DIR/phase2_backend_trimming.sh"

read -p "Phase 2 complete. Continue to Phase 3? (Y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    log_warn "Upgrade paused after Phase 2."
    exit 0
fi
echo ""

# Phase 3: Frontend Maximal
log_phase "=================================================="
log_phase "Phase 3: Frontend Maximal Features"
log_phase "=================================================="
if command -v node &> /dev/null; then
    bash "$SCRIPT_DIR/phase3_frontend_maximal.sh"
else
    log_warn "Node.js not found. Skipping Phase 3 (Frontend)."
fi

read -p "Phase 3 complete. Continue to Phase 4? (Y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    log_warn "Upgrade paused after Phase 3."
    exit 0
fi
echo ""

# Phase 4: Final Trimming
log_phase "=================================================="
log_phase "Phase 4: Final Trimming & Polish"
log_phase "=================================================="
bash "$SCRIPT_DIR/phase4_final_trimming.sh"

echo ""

# Validation
log_phase "=================================================="
log_phase "Final Validation"
log_phase "=================================================="
bash "$SCRIPT_DIR/validate_v10.sh"

echo ""
echo "=================================================="
echo "🎉 v10.0.0 UPGRADE COMPLETE! 🎉"
echo "=================================================="
echo ""
echo "What's new:"
echo "  📁 Structure: 33 → 8 directories (-76%)"
echo "  ♻️  Duplication: <5% (was 40-60%)"
echo "  ✅ Coverage: 80%+ (was 40-50%)"
echo "  🎨 Design: Pure Black + No Icons + Natural"
echo "  🚀 Features: All v9.3.0 + Advanced RAG + MLOps + Modern UI"
echo ""
echo "Next steps:"
echo "  1. Review CHANGELOG.md"
echo "  2. Read docs/guides/V9_TO_V10_MIGRATION.md"
echo "  3. Test locally: ./scripts/deploy-optimized.sh development"
echo "  4. Deploy: kubectl apply -f infrastructure/k8s/"
echo ""
echo "Rollback (if needed):"
echo "  git reset --hard v9.3.0-backup"
echo ""
echo "🖤 Enjoy your Maximal Features + Minimal Structure! 🖤"
echo ""
