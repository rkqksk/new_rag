#!/bin/bash
# Testing utilities for system validation
# Source this file: source scripts/lib/test.sh

# Test counter
TEST_PASSED=0
TEST_FAILED=0

# Run a test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"

    if eval "$test_command" > /dev/null 2>&1; then
        print_success "$test_name"
        ((TEST_PASSED++))
        return 0
    else
        print_error "$test_name"
        ((TEST_FAILED++))
        return 1
    fi
}

# Show test summary
show_test_summary() {
    local total=$((TEST_PASSED + TEST_FAILED))

    echo ""
    print_header "Test Summary"
    echo "Total tests: $total"
    echo -e "${GREEN}Passed: $TEST_PASSED${NC}"
    echo -e "${RED}Failed: $TEST_FAILED${NC}"

    if [ $TEST_FAILED -eq 0 ]; then
        echo ""
        print_success "All tests passed! ✨"
        return 0
    else
        echo ""
        print_error "Some tests failed"
        return 1
    fi
}

# Reset test counters
reset_test_counters() {
    TEST_PASSED=0
    TEST_FAILED=0
}

# Test API endpoint
test_endpoint() {
    local url="$1"
    local expected_status="${2:-200}"
    local method="${3:-GET}"

    local actual_status=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url")

    if [ "$actual_status" = "$expected_status" ]; then
        return 0
    else
        return 1
    fi
}

# Test API with JSON data
test_endpoint_json() {
    local url="$1"
    local json_data="$2"
    local expected_status="${3:-200}"

    local actual_status=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$json_data" \
        "$url")

    if [ "$actual_status" = "$expected_status" ]; then
        return 0
    else
        return 1
    fi
}

# Run pytest with coverage
run_pytest() {
    local test_path="${1:-tests/}"
    local coverage_threshold="${2:-80}"

    print_header "Running Python Tests"

    if pytest "$test_path" -v --cov=src --cov=app --cov-report=term-missing --cov-fail-under="$coverage_threshold"; then
        print_success "Pytest passed (coverage ≥ ${coverage_threshold}%)"
        return 0
    else
        print_error "Pytest failed or coverage below ${coverage_threshold}%"
        return 1
    fi
}

# Test OCR pipeline
test_ocr_pipeline() {
    print_header "Testing OCR Pipeline"

    # Check if OCR modules exist
    local ocr_modules=(
        "src/core/ocr/image_preprocessor.py"
        "src/core/ocr/ocr_engine.py"
        "src/core/ocr/pdf_extractor.py"
        "src/core/ocr/excel_parser.py"
        "src/core/ocr/entity_recognizer.py"
        "src/core/ocr/document_processor.py"
    )

    local failed=0
    for module in "${ocr_modules[@]}"; do
        if [ -f "$module" ]; then
            print_success "Found: $module"
        else
            print_error "Missing: $module"
            ((failed++))
        fi
    done

    if [ $failed -eq 0 ]; then
        print_success "All OCR modules present"
        return 0
    else
        print_error "$failed OCR module(s) missing"
        return 1
    fi
}
