#!/bin/bash
# Master Migration Script
# Orchestrates the complete backend migration process

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
DRY_RUN=false
SKIP_TESTS=false
AUTO_COMMIT=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --auto-commit)
            AUTO_COMMIT=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--dry-run] [--skip-tests] [--auto-commit]"
            exit 1
            ;;
    esac
done

clear
echo ""
echo -e "${BOLD}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║  Backend Migration: app/ + src/ → backend/     ║${NC}"
echo -e "${BOLD}║  Version: v10.0.0 Migration                    ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}⚠ DRY RUN MODE - No changes will be made${NC}"
    echo ""
fi

# Pre-flight checks
echo -e "${BLUE}Pre-flight Checks${NC}"
echo "=================="

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "src" ]; then
    echo -e "${RED}✗${NC} Error: Must run from project root with backend/ and src/ directories"
    exit 1
fi
echo -e "${GREEN}✓${NC} Correct directory"

# Check if git is clean
if [ "$DRY_RUN" = false ]; then
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        echo -e "${YELLOW}⚠${NC} Git working directory has uncommitted changes"
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${GREEN}✓${NC} Git working directory clean"
    fi
fi

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python $python_version"

# Check required tools
for tool in sed grep find docker docker-compose pytest; do
    if command -v $tool &> /dev/null; then
        echo -e "${GREEN}✓${NC} $tool installed"
    else
        echo -e "${RED}✗${NC} $tool not found"
        exit 1
    fi
done

echo ""
echo -e "${BOLD}Migration Plan${NC}"
echo "=============="
echo ""
echo "  Phase 3A: Preparation (backup, branch)"
echo "  Phase 3B: Copy src/ features to backend/"
echo "  Phase 3C: Update imports (app.*/src.* → backend.*)"
echo "  Phase 3D: Update Docker & config files"
echo "  Phase 3E: Testing & validation"
echo ""
echo -e "${YELLOW}⚠ Estimated time: 4-6 hours${NC}"
echo -e "${YELLOW}⚠ Services will be rebuilt (brief downtime)${NC}"
echo ""

if [ "$DRY_RUN" = false ]; then
    read -p "Proceed with migration? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Migration cancelled"
        exit 0
    fi
fi

# Start migration
START_TIME=$(date +%s)

echo ""
echo -e "${BOLD}════════════════════════════════════════${NC}"
echo -e "${BOLD}Phase 3A: Preparation${NC}"
echo -e "${BOLD}════════════════════════════════════════${NC}"
echo ""

# Create backup branch
if [ "$DRY_RUN" = false ]; then
    echo "Creating backup branch..."
    git branch backup-before-migration-$(date +%Y%m%d_%H%M%S) || true
    echo -e "${GREEN}✓${NC} Backup branch created"

    # Create migration branch
    echo "Creating migration branch..."
    git checkout -b backend-migration || git checkout backend-migration
    echo -e "${GREEN}✓${NC} Migration branch ready"
fi

# Run pre-migration tests
if [ "$SKIP_TESTS" = false ]; then
    echo ""
    echo "Running pre-migration tests..."
    if pytest tests/test_api_quick.py -v --tb=short > /tmp/pre_migration_tests.log 2>&1; then
        echo -e "${GREEN}✓${NC} Pre-migration tests passed"
    else
        echo -e "${YELLOW}⚠${NC} Some tests failed (see /tmp/pre_migration_tests.log)"
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

echo ""
echo -e "${BOLD}════════════════════════════════════════${NC}"
echo -e "${BOLD}Phase 3B: Copy src/ to backend/${NC}"
echo -e "${BOLD}════════════════════════════════════════${NC}"
echo ""

if [ "$DRY_RUN" = false ]; then
    bash scripts/migration/01_copy_src_to_backend.sh
else
    echo -e "${YELLOW}[DRY RUN]${NC} Would run: 01_copy_src_to_backend.sh"
fi

echo ""
echo -e "${BOLD}════════════════════════════════════════${NC}"
echo -e "${BOLD}Phase 3C: Update Imports${NC}"
echo -e "${BOLD}════════════════════════════════════════${NC}"
echo ""

if [ "$DRY_RUN" = false ]; then
    bash scripts/migration/02_update_imports.sh
else
    echo -e "${YELLOW}[DRY RUN]${NC} Would run: 02_update_imports.sh"
fi

echo ""
echo -e "${BOLD}════════════════════════════════════════${NC}"
echo -e "${BOLD}Phase 3D: Update Docker & Config${NC}"
echo -e "${BOLD}════════════════════════════════════════${NC}"
echo ""

if [ "$DRY_RUN" = false ]; then
    echo "Updating docker-compose.yml..."
    if grep -q "app.main:app" docker-compose.yml 2>/dev/null; then
        sed -i 's/app\.main:app/backend.main:app/g' docker-compose.yml
        echo -e "${GREEN}✓${NC} docker-compose.yml updated"
    else
        echo -e "${YELLOW}⚠${NC} docker-compose.yml already updated or not found"
    fi

    echo "Updating Dockerfile..."
    if [ -f "Dockerfile" ] && grep -q "app.main" Dockerfile 2>/dev/null; then
        sed -i 's/app\.main/backend.main/g' Dockerfile
        echo -e "${GREEN}✓${NC} Dockerfile updated"
    else
        echo -e "${YELLOW}⚠${NC} Dockerfile already updated or not found"
    fi

    echo "Updating deployment scripts..."
    for script in scripts/*.sh; do
        if grep -q "app\.main" "$script" 2>/dev/null; then
            sed -i 's/app\.main/backend.main/g' "$script"
            echo -e "${GREEN}✓${NC} Updated $script"
        fi
    done
else
    echo -e "${YELLOW}[DRY RUN]${NC} Would update Docker and config files"
fi

echo ""
echo -e "${BOLD}════════════════════════════════════════${NC}"
echo -e "${BOLD}Phase 3E: Validation${NC}"
echo -e "${BOLD}════════════════════════════════════════${NC}"
echo ""

if [ "$DRY_RUN" = false ]; then
    bash scripts/migration/03_validate_structure.sh
    validation_result=$?

    if [ $validation_result -ne 0 ]; then
        echo ""
        echo -e "${RED}✗ Validation failed${NC}"
        echo ""
        echo "Migration incomplete. Please review errors above."
        echo ""
        echo "To rollback:"
        echo "  git checkout backup-before-migration-*"
        exit 1
    fi
else
    echo -e "${YELLOW}[DRY RUN]${NC} Would run: 03_validate_structure.sh"
fi

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo -e "${BOLD}════════════════════════════════════════${NC}"
echo -e "${BOLD}Migration Complete!${NC}"
echo -e "${BOLD}════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}✅ Backend migration successful${NC}"
echo ""
echo "Duration: ${MINUTES}m ${SECONDS}s"
echo ""

if [ "$DRY_RUN" = false ]; then
    echo "Next steps:"
    echo ""
    echo "1. Manual updates (if needed):"
    echo "   - Review backend/main.py imports"
    echo "   - Check backend/api/v2/__init__.py"
    echo ""
    echo "2. Rebuild and test:"
    echo "   docker-compose build api"
    echo "   docker-compose up -d"
    echo "   curl http://localhost:8001/health/ready"
    echo ""
    echo "3. Run full test suite:"
    echo "   pytest tests/ -v"
    echo ""

    if [ "$AUTO_COMMIT" = true ]; then
        echo "Auto-committing changes..."
        git add backend/ pytest.ini alembic/env.py docker-compose.yml Dockerfile scripts/
        git commit -m "feat: Unify app/ and src/ into backend/

- Create backend/api/v2/ for v8-v9 experimental features
- Create backend/middleware/advanced/ for Phase 9 middleware
- Update all imports: app.* → backend.*, src.* → backend.*
- Update Docker, pytest, alembic configs

BREAKING CHANGE: Import paths changed from app.*/src.* to backend.*

Migrated files: 316 total
Duration: ${MINUTES}m ${SECONDS}s

Co-authored-by: Claude <noreply@anthropic.com>"
        echo -e "${GREEN}✓${NC} Changes committed"
        echo ""
        echo "To create a PR, run:"
        echo "  git push -u origin backend-migration"
        echo "  gh pr create --title 'Backend Migration' --body 'See BACKEND_MIGRATION_PLAN.md'"
    else
        echo "4. Review and commit:"
        echo "   git status"
        echo "   git add backend/ pytest.ini alembic/env.py docker-compose.yml"
        echo "   git commit -m 'feat: Unify app/ and src/ into backend/'"
    fi
else
    echo -e "${YELLOW}DRY RUN complete - no changes made${NC}"
    echo ""
    echo "To run actual migration:"
    echo "  bash scripts/migration/00_run_migration.sh"
fi

echo ""
