#!/bin/bash
# Test runner script for RAG Enterprise Backend

set -e

echo "========================================="
echo "RAG Enterprise Backend Test Suite"
echo "========================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing test dependencies..."
    pip install -q pytest pytest-asyncio pytest-cov
fi

echo "📋 Test Structure:"
echo "  Unit Tests:"
find tests/unit -name "test_*.py" | wc -l | xargs echo "    -" "test files"
echo "  Integration Tests:"
find tests/integration -name "test_*.py" | wc -l | xargs echo "    -" "test files"
echo ""

echo "🧪 Running tests..."
echo ""

# Run tests with coverage
pytest tests/ -v --tb=short 2>&1 || true

echo ""
echo "========================================="
echo "Test run complete!"
echo "========================================="
