#!/usr/bin/env bash
# =============================================================================
# Ollama Configuration Validation Script
# =============================================================================
# Validates that Ollama is properly configured and accessible for RAG Enterprise
#
# Usage:
#   ./scripts/validate_ollama.sh [options]
#
# Options:
#   --url URL        Override Ollama URL (default: http://localhost:11434)
#   --model MODEL    Override model name (default: qwen2.5:7b-instruct-q4_K_M)
#   --verbose        Enable verbose output
#   --fix            Attempt to fix common issues
#   --help           Show this help message
#
# Exit Codes:
#   0: All checks passed
#   1: Configuration check failed
#   2: Connectivity check failed
#   3: Model check failed
#   4: Inference check failed
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:7b-instruct-q4_K_M}"
VERBOSE=false
FIX_ISSUES=false
EXIT_CODE=0

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --url)
                OLLAMA_URL="$2"
                shift 2
                ;;
            --model)
                OLLAMA_MODEL="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --fix)
                FIX_ISSUES=true
                shift
                ;;
            --help)
                grep '^#' "$0" | sed 's/^# //' | sed 's/^#//'
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $*"
}

log_error() {
    echo -e "${RED}[✗]${NC} $*"
}

log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $*"
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Validation functions
check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing_deps=()
    
    if ! command_exists curl; then
        missing_deps+=("curl")
    fi
    
    if ! command_exists jq; then
        log_warning "jq not found (optional, enables pretty JSON output)"
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_info "Install with: brew install ${missing_deps[*]}"
        return 1
    fi
    
    log_success "All required dependencies installed"
    return 0
}

check_configuration() {
    log_info "Checking configuration..."
    
    log_verbose "Ollama URL: $OLLAMA_URL"
    log_verbose "Ollama Model: $OLLAMA_MODEL"
    
    # Load from .env if exists
    if [ -f .env ]; then
        log_verbose "Loading configuration from .env"
        # Source .env (safely)
        while IFS='=' read -r key value; do
            # Skip comments and empty lines
            [[ "$key" =~ ^#.*$ ]] && continue
            [[ -z "$key" ]] && continue
            
            # Remove quotes from value
            value="${value%\"}"
            value="${value#\"}"
            
            if [[ "$key" == "OLLAMA_URL" ]]; then
                OLLAMA_URL="$value"
                log_verbose "Loaded OLLAMA_URL from .env: $OLLAMA_URL"
            elif [[ "$key" == "OLLAMA_MODEL" ]]; then
                OLLAMA_MODEL="$value"
                log_verbose "Loaded OLLAMA_MODEL from .env: $OLLAMA_MODEL"
            fi
        done < .env
    else
        log_warning ".env file not found, using defaults"
    fi
    
    log_success "Configuration loaded"
    log_info "  URL: $OLLAMA_URL"
    log_info "  Model: $OLLAMA_MODEL"
    return 0
}

check_ollama_running() {
    log_info "Checking if Ollama is running..."
    
    local response
    local http_code
    
    # Try to connect to Ollama API
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$OLLAMA_URL/api/tags" 2>/dev/null || echo "000")
    
    log_verbose "HTTP response code: $http_code"
    
    if [ "$http_code" == "200" ]; then
        log_success "Ollama is running and accessible at $OLLAMA_URL"
        return 0
    elif [ "$http_code" == "000" ]; then
        log_error "Cannot connect to Ollama at $OLLAMA_URL"
        log_info "Possible causes:"
        log_info "  1. Ollama is not running"
        log_info "  2. Wrong URL configuration"
        log_info "  3. Network/firewall issue"
        
        if [[ "$FIX_ISSUES" == "true" ]]; then
            attempt_fix_ollama_not_running
        else
            log_info ""
            log_info "To fix:"
            log_info "  macOS: brew services start ollama"
            log_info "  Linux: sudo systemctl start ollama"
            log_info "  Manual: ollama serve"
        fi
        return 1
    else
        log_error "Unexpected response from Ollama: HTTP $http_code"
        return 1
    fi
}

check_model_available() {
    log_info "Checking if model is available..."
    
    local models_json
    models_json=$(curl -s "$OLLAMA_URL/api/tags" 2>/dev/null)
    
    log_verbose "Models response: $models_json"
    
    if command_exists jq; then
        local model_names
        model_names=$(echo "$models_json" | jq -r '.models[].name' 2>/dev/null)
        
        log_verbose "Available models:"
        echo "$model_names" | while read -r model; do
            log_verbose "  - $model"
        done
        
        if echo "$model_names" | grep -q "^${OLLAMA_MODEL}$"; then
            log_success "Model '$OLLAMA_MODEL' is available"
            return 0
        else
            log_error "Model '$OLLAMA_MODEL' not found"
            log_info "Available models:"
            echo "$model_names" | while read -r model; do
                log_info "  - $model"
            done
            
            if [[ "$FIX_ISSUES" == "true" ]]; then
                attempt_fix_missing_model
            else
                log_info ""
                log_info "To fix:"
                log_info "  ollama pull $OLLAMA_MODEL"
            fi
            return 1
        fi
    else
        # Fallback without jq
        if echo "$models_json" | grep -q "\"$OLLAMA_MODEL\""; then
            log_success "Model '$OLLAMA_MODEL' appears to be available"
            return 0
        else
            log_error "Model '$OLLAMA_MODEL' not found (jq not available for detailed check)"
            log_info "Install jq for better model validation: brew install jq"
            
            if [[ "$FIX_ISSUES" == "true" ]]; then
                attempt_fix_missing_model
            else
                log_info ""
                log_info "To fix:"
                log_info "  ollama pull $OLLAMA_MODEL"
            fi
            return 1
        fi
    fi
}

check_model_inference() {
    log_info "Testing model inference..."
    
    local test_prompt="Hello, this is a test."
    local response
    
    log_verbose "Sending test prompt: $test_prompt"
    
    # Send test generation request
    response=$(curl -s "$OLLAMA_URL/api/generate" \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$OLLAMA_MODEL\",\"prompt\":\"$test_prompt\",\"stream\":false}" \
        2>/dev/null)
    
    log_verbose "Inference response: $response"
    
    if echo "$response" | grep -q "\"response\""; then
        log_success "Model inference is working"
        
        if command_exists jq && [[ "$VERBOSE" == "true" ]]; then
            local generated_text
            generated_text=$(echo "$response" | jq -r '.response' 2>/dev/null | head -c 100)
            log_verbose "Generated text (first 100 chars): $generated_text"
        fi
        
        return 0
    else
        log_error "Model inference failed"
        log_verbose "Response: $response"
        return 1
    fi
}

check_rag_enterprise_integration() {
    log_info "Checking RAG Enterprise integration..."
    
    # Check if we're in the RAG Enterprise project directory
    if [ ! -f "app/core/dependencies.py" ]; then
        log_warning "Not in RAG Enterprise project directory"
        log_info "Skipping integration check"
        return 0
    fi
    
    # Check Python environment
    if ! command_exists python3; then
        log_warning "Python3 not found, skipping integration check"
        return 0
    fi
    
    # Test configuration loading
    log_verbose "Testing Python configuration loading..."
    
    local python_check
    python_check=$(POSTGRES_PASSWORD=test python3 << 'EOF'
import os
import sys
try:
    from app.core.dependencies import get_config
    config = get_config()
    print(f"URL:{config.ollama_url}")
    print(f"MODEL:{config.ollama_model}")
    sys.exit(0)
except Exception as e:
    print(f"ERROR:{e}", file=sys.stderr)
    sys.exit(1)
EOF
)
    
    if [ $? -eq 0 ]; then
        local py_url=$(echo "$python_check" | grep "^URL:" | cut -d: -f2-)
        local py_model=$(echo "$python_check" | grep "^MODEL:" | cut -d: -f2-)
        
        log_success "RAG Enterprise configuration loaded"
        log_info "  Python config URL: $py_url"
        log_info "  Python config Model: $py_model"
        
        if [ "$py_url" == "$OLLAMA_URL" ]; then
            log_success "URL matches expected configuration"
        else
            log_warning "URL mismatch: expected $OLLAMA_URL, got $py_url"
        fi
        
        return 0
    else
        log_error "Failed to load RAG Enterprise configuration"
        log_verbose "Error: $python_check"
        return 1
    fi
}

# Fix attempt functions
attempt_fix_ollama_not_running() {
    log_info "Attempting to start Ollama..."
    
    if command_exists brew; then
        log_info "Starting Ollama via Homebrew..."
        brew services start ollama
        sleep 3
        
        # Check if it worked
        if curl -s "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
            log_success "Ollama started successfully"
            return 0
        fi
    fi
    
    if command_exists systemctl; then
        log_info "Starting Ollama via systemd..."
        sudo systemctl start ollama
        sleep 3
        
        # Check if it worked
        if curl -s "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
            log_success "Ollama started successfully"
            return 0
        fi
    fi
    
    log_error "Could not start Ollama automatically"
    log_info "Please start Ollama manually: ollama serve"
    return 1
}

attempt_fix_missing_model() {
    log_info "Attempting to pull model: $OLLAMA_MODEL"
    
    if command_exists ollama; then
        log_info "Pulling model (this may take several minutes)..."
        if ollama pull "$OLLAMA_MODEL"; then
            log_success "Model pulled successfully"
            return 0
        else
            log_error "Failed to pull model"
            return 1
        fi
    else
        log_error "Ollama CLI not found, cannot pull model"
        log_info "Install Ollama: https://ollama.com/download"
        return 1
    fi
}

# Main validation flow
main() {
    parse_args "$@"
    
    echo "==============================================================================="
    echo "Ollama Configuration Validation"
    echo "==============================================================================="
    echo ""
    
    # Run all checks
    check_dependencies || EXIT_CODE=1
    echo ""
    
    check_configuration || EXIT_CODE=1
    echo ""
    
    if ! check_ollama_running; then
        EXIT_CODE=2
        echo ""
        echo "==============================================================================="
        log_error "Validation failed: Ollama is not running"
        echo "==============================================================================="
        exit $EXIT_CODE
    fi
    echo ""
    
    if ! check_model_available; then
        EXIT_CODE=3
        echo ""
        echo "==============================================================================="
        log_error "Validation failed: Model not available"
        echo "==============================================================================="
        exit $EXIT_CODE
    fi
    echo ""
    
    if ! check_model_inference; then
        EXIT_CODE=4
        echo ""
        echo "==============================================================================="
        log_error "Validation failed: Model inference not working"
        echo "==============================================================================="
        exit $EXIT_CODE
    fi
    echo ""
    
    check_rag_enterprise_integration
    echo ""
    
    # Final summary
    echo "==============================================================================="
    if [ $EXIT_CODE -eq 0 ]; then
        log_success "All validation checks passed!"
        echo ""
        log_info "Ollama is properly configured and ready for RAG Enterprise"
        log_info "  URL: $OLLAMA_URL"
        log_info "  Model: $OLLAMA_MODEL"
    else
        log_error "Some validation checks failed (exit code: $EXIT_CODE)"
        echo ""
        log_info "Please fix the issues above and run validation again"
    fi
    echo "==============================================================================="
    
    exit $EXIT_CODE
}

# Run main function
main "$@"
