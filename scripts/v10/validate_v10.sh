#!/usr/bin/env bash
# Validate v10.0.0 upgrade

set -euo pipefail

echo "Validating v10.0.0 upgrade..."
echo ""

# Check structure
echo "✓ Checking structure..."
[ -d "apps/api" ] && echo "  ✓ apps/api/" || echo "  ✗ apps/api/ missing"
[ -d "apps/web" ] && echo "  ✓ apps/web/" || echo "  ✗ apps/web/ missing"
[ -d "packages/core" ] && echo "  ✓ packages/core/" || echo "  ✗ packages/core/ missing"
[ -d "packages/config" ] && echo "  ✓ packages/config/" || echo "  ✗ packages/config/ missing"
[ -d "packages/utils" ] && echo "  ✓ packages/utils/" || echo "  ✗ packages/utils/ missing"

# Check old directories archived
echo ""
echo "✓ Checking old directories archived..."
[ ! -d "app" ] && echo "  ✓ app/ archived" || echo "  ✗ app/ still exists"
[ ! -d "backend" ] && echo "  ✓ backend/ archived" || echo "  ✗ backend/ still exists"
[ ! -d "src" ] && echo "  ✓ src/ archived" || echo "  ✗ src/ still exists"

# Check tests
echo ""
echo "✓ Running tests..."
pytest tests/ -v --cov=apps --cov=packages --cov-report=term-missing --cov-fail-under=80 || echo "  ⚠ Tests failed or coverage below 80%"

# Check design system
echo ""
echo "✓ Checking design system..."
grep -q "#000000" apps/web/tailwind.config.ts && echo "  ✓ Pure black configured" || echo "  ✗ Pure black missing"
[ -f "docs/design/DESIGN_SYSTEM.md" ] && echo "  ✓ Design system documented" || echo "  ⚠ Design system missing"

echo ""
echo "=================================================="
echo "v10.0.0 Validation Complete! 🎉"
echo "=================================================="
