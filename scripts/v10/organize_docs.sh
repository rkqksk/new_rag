#!/usr/bin/env bash
# Organize documentation structure for v10.0.0
# Move 22 root docs → 5 root docs + organized docs/ structure

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=================================================="
echo "Documentation Organization for v10.0.0"
echo "=================================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Create directory structure
log_info "Creating documentation directories..."
mkdir -p docs/{guides,planning/{v9,v10,sessions,checklists,diagnostics},architecture}

# Count current root docs
CURRENT_COUNT=$(ls -1 *.md 2>/dev/null | wc -l)
log_info "Current root documents: $CURRENT_COUNT"

# Move guides
log_info "Moving guides → docs/guides/"
mv DEPLOYMENT.md docs/guides/ 2>/dev/null && log_info "  ✓ DEPLOYMENT.md" || log_warn "  - DEPLOYMENT.md not found"
mv QUICK_START_UPDATED.md docs/guides/quick-start.md 2>/dev/null && log_info "  ✓ QUICK_START_UPDATED.md → quick-start.md" || log_warn "  - QUICK_START_UPDATED.md not found"

# Move v9 planning docs
log_info "Moving v9 planning docs → docs/planning/v9/"
mv BACKEND_MIGRATION_PLAN.md docs/planning/v9/ 2>/dev/null && log_info "  ✓ BACKEND_MIGRATION_PLAN.md" || log_warn "  - BACKEND_MIGRATION_PLAN.md not found"
mv COMPLETE_INTEGRATION_MASTER_PLAN.md docs/planning/v9/ 2>/dev/null && log_info "  ✓ COMPLETE_INTEGRATION_MASTER_PLAN.md" || log_warn "  - COMPLETE_INTEGRATION_MASTER_PLAN.md not found"
mv FRONTEND_FILE_STRUCTURE_PLAN.md docs/planning/v9/ 2>/dev/null && log_info "  ✓ FRONTEND_FILE_STRUCTURE_PLAN.md" || log_warn "  - FRONTEND_FILE_STRUCTURE_PLAN.md not found"
mv FRONTEND_INTEGRATION_SUMMARY.md docs/planning/v9/ 2>/dev/null && log_info "  ✓ FRONTEND_INTEGRATION_SUMMARY.md" || log_warn "  - FRONTEND_INTEGRATION_SUMMARY.md not found"
mv SUB_AGENTS_COLLABORATION_PLAN.md docs/planning/v9/ 2>/dev/null && log_info "  ✓ SUB_AGENTS_COLLABORATION_PLAN.md" || log_warn "  - SUB_AGENTS_COLLABORATION_PLAN.md not found"

# Move v10 planning docs
log_info "Moving v10 planning docs → docs/planning/v10/"
mv INTEGRATION_PLAN_V10.md docs/planning/v10/ 2>/dev/null && log_info "  ✓ INTEGRATION_PLAN_V10.md" || log_warn "  - INTEGRATION_PLAN_V10.md not found"
# Note: V10_MAXIMAL_UPGRADE_PLAN.md and V10_READY_TO_EXECUTE.md already in docs/v10/
# We'll move them to docs/planning/v10/ for consistency
[ -f "V10_MAXIMAL_UPGRADE_PLAN.md" ] && mv V10_MAXIMAL_UPGRADE_PLAN.md docs/planning/v10/ && log_info "  ✓ V10_MAXIMAL_UPGRADE_PLAN.md"
[ -f "V10_READY_TO_EXECUTE.md" ] && mv V10_READY_TO_EXECUTE.md docs/planning/v10/ && log_info "  ✓ V10_READY_TO_EXECUTE.md"

# Move session docs
log_info "Moving session docs → docs/planning/sessions/"
mv SESSION_*.md docs/planning/sessions/ 2>/dev/null && log_info "  ✓ SESSION_*.md" || log_warn "  - No SESSION_*.md files"
mv READY_TO_EXECUTE_SUMMARY.md docs/planning/sessions/ 2>/dev/null && log_info "  ✓ READY_TO_EXECUTE_SUMMARY.md" || log_warn "  - READY_TO_EXECUTE_SUMMARY.md not found"
mv UPDATED_ANALYSIS_AND_ROADMAP.md docs/planning/sessions/ 2>/dev/null && log_info "  ✓ UPDATED_ANALYSIS_AND_ROADMAP.md" || log_warn "  - UPDATED_ANALYSIS_AND_ROADMAP.md not found"

# Move checklists
log_info "Moving checklists → docs/planning/checklists/"
mv PHASE1_DEPLOYMENT_CHECKLIST.md docs/planning/checklists/ 2>/dev/null && log_info "  ✓ PHASE1_DEPLOYMENT_CHECKLIST.md" || log_warn "  - PHASE1_DEPLOYMENT_CHECKLIST.md not found"
mv MIGRATION_CHECKLIST.md docs/planning/checklists/ 2>/dev/null && log_info "  ✓ MIGRATION_CHECKLIST.md" || log_warn "  - MIGRATION_CHECKLIST.md not found"

# Move diagnostics
log_info "Moving diagnostics → docs/planning/diagnostics/"
mv FINAL_DIAGNOSIS.md docs/planning/diagnostics/ 2>/dev/null && log_info "  ✓ FINAL_DIAGNOSIS.md" || log_warn "  - FINAL_DIAGNOSIS.md not found"

# Move architecture docs
log_info "Moving architecture docs → docs/architecture/"
mv DEVELOPMENT_ENVIRONMENT_EXECUTION_PLAN.md docs/architecture/ 2>/dev/null && log_info "  ✓ DEVELOPMENT_ENVIRONMENT_EXECUTION_PLAN.md" || log_warn "  - DEVELOPMENT_ENVIRONMENT_EXECUTION_PLAN.md not found"

# Move this analysis doc
log_info "Moving this analysis → docs/guides/"
mv DOCUMENTATION_RULES_ANALYSIS.md docs/guides/documentation-rules.md 2>/dev/null && log_info "  ✓ DOCUMENTATION_RULES_ANALYSIS.md → documentation-rules.md" || log_warn "  - DOCUMENTATION_RULES_ANALYSIS.md not found"

# Count remaining root docs
echo ""
log_info "Checking remaining root documents..."
REMAINING_COUNT=$(ls -1 *.md 2>/dev/null | wc -l)
log_info "Remaining root documents: $REMAINING_COUNT"

if [ "$REMAINING_COUNT" -le 6 ]; then
    echo ""
    log_info "✅ Documentation organization successful!"
    echo ""
    echo "Remaining root docs (should be ≤6):"
    ls -1 *.md 2>/dev/null || echo "  (none)"
else
    echo ""
    log_warn "⚠️  Still too many root docs: $REMAINING_COUNT"
    echo ""
    echo "Remaining root docs:"
    ls -1 *.md
fi

# Show new structure
echo ""
log_info "New documentation structure:"
echo ""
find docs -type f -name "*.md" | sort | head -30

echo ""
echo "=================================================="
echo "Documentation Organization Complete"
echo "=================================================="
echo ""
echo "Summary:"
echo "  Before: $CURRENT_COUNT root docs"
echo "  After: $REMAINING_COUNT root docs"
echo "  Organized: docs/guides/, docs/planning/, docs/architecture/"
echo ""
echo "Next: Review and commit changes"
echo "  git status"
echo "  git add docs/"
echo "  git commit -m 'docs: Organize documentation structure'"
echo ""
