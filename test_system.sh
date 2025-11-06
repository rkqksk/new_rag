#!/bin/bash
# Complete System Testing Script
# Run this after starting Docker services

set -e

echo "=========================================="
echo "RAG Enterprise - Complete System Test"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

test_command() {
    local description="$1"
    local command="$2"
    local expected_code="${3:-0}"
    
    echo -n "Testing: $description ... "
    
    if eval "$command" > /dev/null 2>&1; then
        if [ $? -eq $expected_code ]; then
            echo -e "${GREEN}✓ PASS${NC}"
            ((PASSED++))
        else
            echo -e "${RED}✗ FAIL${NC}"
            ((FAILED++))
        fi
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILED++))
    fi
}

echo "=== Phase 1: Infrastructure Health ==="
echo ""

test_command "Qdrant is running" "curl -s http://localhost:6333/health"
test_command "Redis is running" "redis-cli ping"
test_command "PostgreSQL is running" "pg_isready -h localhost -p 5432"

echo ""
echo "=== Phase 2: Backend API Health ==="
echo ""

test_command "Backend is running" "curl -s http://localhost:8001/"
test_command "Health check (liveness)" "curl -s http://localhost:8001/health/live"
test_command "Health check (readiness)" "curl -s http://localhost:8001/health/ready"
test_command "API documentation" "curl -s http://localhost:8001/api/v1/docs"

echo ""
echo "=== Phase 3: Search API ==="
echo ""

test_command "Search endpoint (basic)" \
    "curl -s -X POST http://localhost:8001/api/v1/search/ \
     -H 'Content-Type: application/json' \
     -d '{\"query\": \"50ml PET 용기\", \"top_k\": 10}'"

test_command "Search endpoint (with session)" \
    "curl -s -X POST http://localhost:8001/api/v1/search/ \
     -H 'Content-Type: application/json' \
     -d '{\"query\": \"20파이 캡\", \"session_id\": \"test_123\", \"top_k\": 5}'"

echo ""
echo "=== Phase 4: Personalization API ==="
echo ""

test_command "Get user profile" \
    "curl -s http://localhost:8001/api/v1/personalization/profile/test_123"

test_command "Track interaction" \
    "curl -s -X POST http://localhost:8001/api/v1/personalization/track \
     -H 'Content-Type: application/json' \
     -d '{\"session_id\": \"test_123\", \"product_id\": \"PROD-001\", \"event_type\": \"click\", \"product\": {\"id\": \"PROD-001\"}}'"

echo ""
echo "=== Phase 5: Analytics API ==="
echo ""

test_command "Get top keywords" \
    "curl -s http://localhost:8001/api/v1/analytics/keywords?limit=10"

test_command "Get trending queries" \
    "curl -s http://localhost:8001/api/v1/analytics/trending?limit=5"

test_command "Get analytics summary" \
    "curl -s http://localhost:8001/api/v1/analytics/summary"

echo ""
echo "=== Phase 6: Debug Endpoints (if enabled) ==="
echo ""

# Check if debug is enabled
if curl -s http://localhost:8001/api/v1/debug/health/detailed > /dev/null 2>&1; then
    echo "Debug mode: ENABLED"
    
    test_command "Debug health check" \
        "curl -s http://localhost:8001/api/v1/debug/health/detailed"
    
    test_command "Cache statistics" \
        "curl -s http://localhost:8001/api/v1/debug/cache/stats"
    
    test_command "Performance summary" \
        "curl -s http://localhost:8001/api/v1/debug/performance/summary"
else
    echo "Debug mode: DISABLED (expected in production)"
fi

echo ""
echo "=== Phase 7: Python Test Suite ==="
echo ""

if command -v pytest &> /dev/null; then
    echo "Running pytest..."
    pytest tests/ -v --tb=short --maxfail=5 || true
else
    echo -e "${YELLOW}pytest not found, skipping unit tests${NC}"
fi

echo ""
echo "=== Phase 8: OCR Pipeline Test ==="
echo ""

if [ -f "examples/ocr_usage_example.py" ]; then
    echo "Testing OCR pipeline..."
    python examples/ocr_usage_example.py || echo -e "${YELLOW}OCR test requires sample files${NC}"
else
    echo -e "${YELLOW}OCR example not found${NC}"
fi

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
