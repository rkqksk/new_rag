#!/usr/bin/env bash
# Run all tests (frontend + backend)

set -e

echo "🧪 Running All Tests"
echo "===================="
echo ""

# Backend tests
echo "📦 Backend Tests (pytest)..."
source .venv/bin/activate
pytest tests/ -v --cov=apps/api --cov-report=term --cov-report=html

echo ""
echo "📦 Frontend Tests (Jest)..."
pnpm test

echo ""
echo "📦 E2E Tests (Playwright)..."
pnpm exec playwright test

echo ""
echo "✅ All tests complete!"
echo ""
echo "Coverage reports:"
echo "  - Backend: htmlcov/index.html"
echo "  - Frontend: coverage/index.html"
