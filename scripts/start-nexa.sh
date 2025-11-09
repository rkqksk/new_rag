#!/bin/bash

# ==============================================================================
# RAG Enterprise - NexaAI Integration Startup Script
# ==============================================================================
#
# This script:
# 1. Checks/installs NexaAI CLI
# 2. Pulls required models
# 3. Starts NexaAI server
# 4. Starts Docker services
# 5. Verifies health
#
# Usage:
#   ./scripts/start-nexa.sh [development|production]
#
# ==============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Environment
ENV=${1:-development}

echo -e "${BLUE}"
echo "========================================================================"
echo "  RAG Enterprise - NexaAI SDK Integration"
echo "========================================================================"
echo -e "${NC}"
echo ""
echo -e "${YELLOW}Environment:${NC} $ENV"
echo ""

# ==============================================================================
# Step 1: Check NexaAI CLI Installation
# ==============================================================================

echo -e "${BLUE}[Step 1/6]${NC} Checking NexaAI CLI..."

if ! command -v nexa &> /dev/null; then
    echo -e "${YELLOW}NexaAI CLI not found. Installing...${NC}"

    # Detect platform
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo "Detected Linux platform"
        curl -fsSL https://github.com/NexaAI/nexa-sdk/releases/latest/download/nexa-cli_linux_x86_64.sh -o /tmp/nexa-install.sh
        chmod +x /tmp/nexa-install.sh
        /tmp/nexa-install.sh
        rm /tmp/nexa-install.sh

    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo "Detected macOS platform"
        echo -e "${YELLOW}Please install NexaAI manually:${NC}"
        echo "  Visit: https://www.nexaai.com/downloads"
        echo "  Or use Homebrew: brew install nexa"
        exit 1

    else
        echo -e "${RED}Unsupported platform: $OSTYPE${NC}"
        echo "Please install NexaAI manually from https://www.nexaai.com/downloads"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} NexaAI CLI found: $(nexa --version)"
fi

echo ""

# ==============================================================================
# Step 2: Pull Required Models
# ==============================================================================

echo -e "${BLUE}[Step 2/6]${NC} Pulling required models..."

# List of required models
MODELS=(
    "NexaAI/Qwen3-1.7B-GGUF"
    "NexaAI/Qwen3-VL-4B-Instruct-GGUF"
    "NexaAI/EmbeddingGemma-GGUF"
)

for model in "${MODELS[@]}"; do
    echo -e "${YELLOW}→${NC} Pulling $model..."

    # Check if model already exists
    if nexa list 2>/dev/null | grep -q "$model"; then
        echo -e "${GREEN}  ✓ Already cached${NC}"
    else
        nexa pull "$model"
        echo -e "${GREEN}  ✓ Downloaded${NC}"
    fi
done

echo -e "${GREEN}✓${NC} All models ready"
echo ""

# ==============================================================================
# Step 3: Start NexaAI Server
# ==============================================================================

echo -e "${BLUE}[Step 3/6]${NC} Starting NexaAI server..."

# Check if already running
if curl -s http://localhost:8080/health &>/dev/null; then
    echo -e "${GREEN}✓${NC} NexaAI server already running"
else
    echo -e "${YELLOW}Starting NexaAI server in background...${NC}"

    # Start server in background
    nohup nexa serve --host 0.0.0.0:8080 > logs/nexa-server.log 2>&1 &
    NEXA_PID=$!

    echo "  PID: $NEXA_PID"
    echo "$NEXA_PID" > .nexa.pid

    # Wait for server to start
    echo -n "  Waiting for server to start"
    for i in {1..30}; do
        if curl -s http://localhost:8080/health &>/dev/null; then
            echo ""
            echo -e "${GREEN}  ✓ Server ready${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done

    if ! curl -s http://localhost:8080/health &>/dev/null; then
        echo ""
        echo -e "${RED}  ✗ Server failed to start${NC}"
        echo "  Check logs: logs/nexa-server.log"
        exit 1
    fi
fi

echo ""

# ==============================================================================
# Step 4: Install Python Dependencies
# ==============================================================================

echo -e "${BLUE}[Step 4/6]${NC} Installing Python dependencies..."

if [ -f "requirements-nexa.txt" ]; then
    pip install -q -r requirements-nexa.txt
    echo -e "${GREEN}✓${NC} Dependencies installed"
else
    echo -e "${YELLOW}⚠${NC} requirements-nexa.txt not found, skipping"
fi

echo ""

# ==============================================================================
# Step 5: Start Docker Services
# ==============================================================================

echo -e "${BLUE}[Step 5/6]${NC} Starting Docker services..."

# Load environment variables
if [ -f ".env.nexa" ]; then
    echo "Loading .env.nexa"
    export $(cat .env.nexa | grep -v '^#' | xargs)
elif [ -f ".env.nexa.example" ]; then
    echo -e "${YELLOW}⚠ .env.nexa not found, using .env.nexa.example${NC}"
    export $(cat .env.nexa.example | grep -v '^#' | xargs)
fi

# Start services
if [ "$ENV" == "production" ]; then
    echo "Starting production services..."
    docker-compose -f docker-compose.yml -f docker-compose.nexa.yml up -d
else
    echo "Starting development services..."
    docker-compose -f docker-compose.yml -f docker-compose.nexa.yml up -d
fi

echo -e "${GREEN}✓${NC} Docker services started"
echo ""

# ==============================================================================
# Step 6: Health Checks
# ==============================================================================

echo -e "${BLUE}[Step 6/6]${NC} Running health checks..."
echo ""

# Wait for services
echo -n "Waiting for services to be ready"
for i in {1..30}; do
    echo -n "."
    sleep 1
done
echo ""

# Check NexaAI
echo -n "NexaAI (http://localhost:8080): "
if curl -sf http://localhost:8080/health > /dev/null; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
fi

# Check API
echo -n "API (http://localhost:8001): "
if curl -sf http://localhost:8001/health/ready > /dev/null; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
fi

# Check Qdrant
echo -n "Qdrant (http://localhost:6333): "
if curl -sf http://localhost:6333/dashboard > /dev/null; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
fi

# Check Redis
echo -n "Redis (localhost:6379): "
if docker exec -it rag-redis redis-cli ping 2>/dev/null | grep -q PONG; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
fi

echo ""

# ==============================================================================
# Done
# ==============================================================================

echo -e "${GREEN}"
echo "========================================================================"
echo "  ✓ RAG Enterprise with NexaAI is ready!"
echo "========================================================================"
echo -e "${NC}"
echo ""
echo -e "${YELLOW}Services:${NC}"
echo "  • NexaAI Server:   http://localhost:8080"
echo "  • API:             http://localhost:8001"
echo "  • API Docs:        http://localhost:8001/api/v1/docs"
echo "  • Qdrant UI:       http://localhost:6333/dashboard"
echo "  • Frontend:        http://localhost:8000 (run: cd frontend && python3 -m http.server 8000)"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo "  • NexaAI:   tail -f logs/nexa-server.log"
echo "  • API:      docker-compose logs -f api"
echo "  • All:      docker-compose logs -f"
echo ""
echo -e "${YELLOW}Quick Test:${NC}"
echo '  curl -X POST http://localhost:8001/api/v1/search/ \'
echo '    -H "Content-Type: application/json" \'
echo '    -d '"'"'{"query":"50ml PET 용기","top_k":5}'"'"
echo ""
echo -e "${YELLOW}Stop Services:${NC}"
echo "  ./scripts/stop-nexa.sh"
echo ""
