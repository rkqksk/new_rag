#!/bin/bash
# Optimized testing script for RAG Enterprise
# Uses modular library functions for better maintainability

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source library functions
source "$SCRIPT_DIR/lib/colors.sh"
source "$SCRIPT_DIR/lib/health.sh"
source "$SCRIPT_DIR/lib/test.sh"

# Configuration
BASE_URL="${API_BASE_URL:-http://localhost:8001}"

# Main testing function
main() {
    cd "$PROJECT_ROOT"

    print_header "RAG Enterprise System Tests"
    reset_test_counters

    # Phase 1: Infrastructure Health
    print_section "Phase 1: Infrastructure Health"
    run_test "Qdrant health check" "check_qdrant localhost 6333"
    run_test "Redis health check" "check_redis localhost 6379"
    run_test "PostgreSQL health check" "check_postgres localhost 5432 postgres rag_enterprise"
    run_test "API health check" "check_api localhost 8001"

    # Phase 2: API Endpoints
    print_section "Phase 2: API Endpoints"
    run_test "API liveness endpoint" "test_endpoint $BASE_URL/health/live 200"
    run_test "API readiness endpoint" "test_endpoint $BASE_URL/health/ready 200"
    run_test "API documentation endpoint" "test_endpoint $BASE_URL/api/v1/docs 200"

    # Phase 3: Search API
    print_section "Phase 3: Search API"
    run_test "Text search endpoint" "test_endpoint_json $BASE_URL/api/v1/search/ '{\"query\":\"test\",\"top_k\":5}' 200"

    # Phase 4: Personalization API
    print_section "Phase 4: Personalization API"
    run_test "User profile endpoint (404 expected)" "test_endpoint $BASE_URL/api/v1/personalization/profile/test_user 404"

    # Phase 5: Analytics API
    print_section "Phase 5: Analytics API"
    run_test "Top keywords endpoint" "test_endpoint '$BASE_URL/api/v1/analytics/keywords?limit=5' 200"
    run_test "Trending queries endpoint" "test_endpoint '$BASE_URL/api/v1/analytics/trending?limit=5' 200"
    run_test "Analytics summary endpoint" "test_endpoint $BASE_URL/api/v1/analytics/summary 200"

    # Phase 6: Debug Endpoints (if enabled)
    if curl -sf "$BASE_URL/api/v1/debug/health/detailed" > /dev/null 2>&1; then
        print_section "Phase 6: Debug Endpoints"
        run_test "Debug health endpoint" "test_endpoint $BASE_URL/api/v1/debug/health/detailed 200"
        run_test "Debug cache stats" "test_endpoint $BASE_URL/api/v1/debug/cache/stats 200"
        run_test "Debug Qdrant stats" "test_endpoint $BASE_URL/api/v1/debug/qdrant/stats 200"
    else
        print_warning "Debug endpoints not enabled (skipping Phase 6)"
    fi

    # Phase 7: Python Tests (optional, if pytest is installed)
    if command -v pytest &> /dev/null && [ -d "tests" ]; then
        print_section "Phase 7: Python Test Suite"
        if run_pytest "tests/" 80; then
            ((TEST_PASSED++))
        else
            ((TEST_FAILED++))
        fi
    else
        print_warning "Pytest not available or no tests found (skipping Phase 7)"
    fi

    # Phase 8: OCR Pipeline
    print_section "Phase 8: OCR Pipeline"
    if test_ocr_pipeline; then
        ((TEST_PASSED++))
    else
        ((TEST_FAILED++))
    fi

    # Show summary
    show_test_summary
}

# Run main function
main "$@"
