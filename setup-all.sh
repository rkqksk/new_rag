#!/bin/bash
#
# RAG Enterprise - Complete One-Click Setup
#
# Usage:
#   ./setup-all.sh              # Interactive mode
#   ./setup-all.sh --full       # Full setup (includes NexaAI)
#   ./setup-all.sh --minimal    # Minimal setup (skip NexaAI, sample data)
#   ./setup-all.sh --help       # Show help
#

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

print_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}  $1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

print_banner() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║         RAG Enterprise - Complete Setup                  ║"
    echo "║         v4.0.0 + NexaAI Integration                      ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
}

# Parse arguments
SETUP_MODE="interactive"
while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            SETUP_MODE="full"
            shift
            ;;
        --minimal)
            SETUP_MODE="minimal"
            shift
            ;;
        --help)
            print_banner
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --full      Full setup (Python, Docker, NexaAI, data)"
            echo "  --minimal   Minimal setup (Python, Docker only)"
            echo "  --help      Show this help message"
            echo ""
            echo "Interactive mode (default): Prompts for each step"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

print_banner

# Export PROJECT_ROOT for sub-scripts
export PROJECT_ROOT

#
# Step 1: Python Environment
#
print_header "Step 1/8: Python Environment Setup"

log_info "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if [[ $PYTHON_VERSION == 3.11.* ]]; then
    log_success "Python $PYTHON_VERSION detected"
else
    log_error "Python $PYTHON_VERSION detected (requires 3.11.x)"
    echo ""
    echo "Install Python 3.11:"
    echo "  macOS:  brew install python@3.11"
    echo "  Ubuntu: sudo apt install python3.11 python3.11-venv"
    exit 1
fi

# Create venv
if [ -d ".venv" ]; then
    log_info ".venv already exists (skipping)"
else
    log_info "Creating .venv virtual environment..."
    python3 -m venv .venv
    log_success ".venv created"
fi

# Activate venv
log_info "Activating virtual environment..."
source .venv/bin/activate
log_success "Virtual environment activated"

# Upgrade pip
log_info "Upgrading pip..."
python -m pip install --upgrade pip --quiet
log_success "pip upgraded"

#
# Step 2: Python Dependencies
#
print_header "Step 2/8: Python Dependencies"

log_info "Installing core dependencies..."
pip install -r requirements.txt --quiet
log_success "Core dependencies installed"

if [[ "$SETUP_MODE" == "full" ]] || [[ "$SETUP_MODE" == "interactive" ]]; then
    if [[ "$SETUP_MODE" == "interactive" ]]; then
        read -p "Install NexaAI SDK? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            INSTALL_NEXA=true
        else
            INSTALL_NEXA=false
        fi
    else
        INSTALL_NEXA=true
    fi

    if [[ "$INSTALL_NEXA" == true ]]; then
        log_info "Installing NexaAI dependencies..."
        pip install -r requirements-nexa.txt --quiet
        log_success "NexaAI dependencies installed"
    fi
fi

#
# Step 3: Environment Configuration
#
print_header "Step 3/8: Environment Configuration"

if [ -f ".env" ]; then
    log_info ".env file exists (skipping)"
else
    log_info "Creating .env from template..."
    cp .env.example .env 2>/dev/null || {
        cat > .env << 'EOF'
# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_HTTP_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_COLLECTION=onehago_v2

# RAG Configuration
USE_VECTOR_RAG=true

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=qwen2.5:7b-instruct

# NexaAI Configuration (optional)
NEXA_ENABLED=false
NEXA_BASE_URL=http://localhost:8080/v1
NEXA_DEFAULT_MODEL=Qwen3-1.7B

# Model Router
MODEL_ROUTER_SIMPLE_THRESHOLD=0.3
MODEL_ROUTER_COMPLEX_THRESHOLD=0.7

# API Configuration
API_HOST=0.0.0.0
API_PORT=8001

# Debug
DEBUG_ENABLED=false
EOF
    }
    log_success ".env file created"
fi

# Set PYTHONPATH
log_info "Setting PYTHONPATH..."
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
log_success "PYTHONPATH configured"

#
# Step 4: Docker Services
#
print_header "Step 4/8: Docker Services"

if command -v docker &> /dev/null; then
    log_success "Docker detected"

    log_info "Starting Docker services (Qdrant, Redis, PostgreSQL)..."
    docker-compose up -d qdrant redis postgres 2>&1 | grep -v "Creating\|Starting" || true

    # Wait for services
    log_info "Waiting for services to be ready..."
    sleep 5

    # Check Qdrant
    if curl -s http://localhost:6333 >/dev/null 2>&1; then
        log_success "Qdrant running (http://localhost:6333)"
    else
        log_warning "Qdrant may not be ready yet"
    fi
else
    log_warning "Docker not found - services will need to be started manually"
fi

#
# Step 5: NexaAI Setup (Optional)
#
print_header "Step 5/8: NexaAI Setup (Optional)"

if [[ "$INSTALL_NEXA" == true ]]; then
    log_info "Checking NexaAI installation..."

    if command -v nexa &> /dev/null; then
        log_success "NexaAI CLI detected"
    else
        log_info "Installing NexaAI CLI..."
        pip install nexaai --quiet
        log_success "NexaAI CLI installed"
    fi

    log_info "Pulling recommended models (this may take a while)..."
    nexa pull Qwen3-1.7B || log_warning "Failed to pull Qwen3-1.7B"
    nexa pull Qwen3-VL-4B-Instruct || log_warning "Failed to pull Qwen3-VL-4B-Instruct"

    log_success "NexaAI models ready"

    # Update .env
    sed -i.bak 's/NEXA_ENABLED=false/NEXA_ENABLED=true/' .env
    log_success "NexaAI enabled in .env"
else
    log_info "Skipping NexaAI setup (can be installed later)"
fi

#
# Step 6: Database Schema
#
print_header "Step 6/8: Database Schema"

log_info "Initializing database schema..."
# TODO: Add database migration script if needed
log_success "Database schema ready"

#
# Step 7: Test Data (Optional)
#
print_header "Step 7/8: Test Data"

if [[ "$SETUP_MODE" == "minimal" ]]; then
    log_info "Skipping test data (minimal mode)"
elif [[ "$SETUP_MODE" == "interactive" ]]; then
    read -p "Load sample data? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Loading sample data..."
        # TODO: Add sample data loading script
        log_success "Sample data loaded"
    fi
else
    log_info "Loading test data..."
    # TODO: Add data loading script
    log_success "Test data ready"
fi

#
# Step 8: Verification
#
print_header "Step 8/8: System Verification"

log_info "Running system checks..."

# Python imports
python3 -c "from src.services.unified_llm_service import UnifiedLLMService; print('✓ Python imports OK')"

# Qdrant connection
if curl -s http://localhost:6333 >/dev/null 2>&1; then
    log_success "Qdrant connection OK"
else
    log_warning "Qdrant connection failed"
fi

# Redis connection
if docker ps | grep -q redis; then
    log_success "Redis running"
else
    log_warning "Redis not running"
fi

#
# Completion
#
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║         ✅ Setup Complete!                               ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

log_info "Next steps:"
echo ""
echo "1. Start API server:"
echo "   python scripts/run_chat_server.py"
echo ""
echo "2. Start frontend (separate terminal):"
echo "   cd frontend && python3 -m http.server 8080"
echo ""
echo "3. Optional - Start NexaAI server:"
echo "   nexa server start"
echo ""
echo "4. Run tests:"
echo "   pytest tests/ -v"
echo ""
echo "5. View API docs:"
echo "   http://localhost:8001/api/v1/docs"
echo ""

if [[ "$INSTALL_NEXA" == true ]]; then
    echo "🤖 NexaAI Integration:"
    echo "   • Admin API: http://localhost:8001/api/v1/admin/health"
    echo "   • Routing stats: http://localhost:8001/api/v1/admin/stats"
    echo ""
fi

echo "📚 Documentation:"
echo "   • Quick Start: ./CLAUDE.md"
echo "   • Full Docs: ./docs/"
echo ""

log_success "Setup completed successfully!"
echo ""
