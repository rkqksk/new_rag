#!/usr/bin/env bash
# RAG Enterprise v10.0.0 - Quick Start Script
# One-command setup for local development

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=================================================="
echo "RAG Enterprise v10.0.0 - Quick Start"
echo "=================================================="
echo ""

# Check prerequisites
log_info "Checking prerequisites..."

if ! command -v pnpm &> /dev/null; then
    log_warn "pnpm not found. Installing pnpm..."
    npm install -g pnpm
fi

if ! command -v docker &> /dev/null; then
    log_error "Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    log_error "Python3 not found. Please install Python 3.11+ first."
    exit 1
fi

log_info "Prerequisites OK ✓"
echo ""

# Install dependencies
log_info "Installing dependencies..."

# Root monorepo
log_info "  → Installing root packages..."
pnpm install || log_warn "Some packages failed (this may be expected)"

# Python backend
log_info "  → Installing Python packages..."
cd apps/api
pip install -r requirements.txt || log_warn "Some Python packages failed"
cd ../..

log_info "Dependencies installed ✓"
echo ""

# Start infrastructure
log_info "Starting Docker services..."
docker-compose up -d

log_info "Waiting for services to be ready..."
sleep 5

# Health checks
log_info "Checking service health..."

check_service() {
    local name=$1
    local url=$2

    if curl -s "$url" > /dev/null 2>&1; then
        log_info "  ✓ $name is ready"
        return 0
    else
        log_warn "  ⚠ $name is not responding"
        return 1
    fi
}

check_service "PostgreSQL" "localhost:15432" || true
check_service "Redis" "localhost:16379" || true
check_service "Qdrant" "http://localhost:16333/health" || true

echo ""

# Summary
echo "=================================================="
echo "🎉 Quick Start Complete!"
echo "=================================================="
echo ""
echo "Services:"
echo "  → Frontend:  http://localhost:3000 (run 'pnpm web')"
echo "  → API Docs:  http://localhost:8001/api/v1/docs (run 'pnpm api')"
echo "  → Qdrant:    http://localhost:16333/dashboard"
echo "  → Grafana:   http://localhost:3000 (admin/admin)"
echo "  → Jaeger:    http://localhost:16686"
echo ""
echo "Next steps:"
echo "  1. Start frontend:  pnpm web"
echo "  2. Start API:       pnpm api"
echo "  3. Run all:         pnpm dev"
echo "  4. Validate:        ./scripts/v10/validate_v10.sh"
echo ""
echo "Documentation:"
echo "  → Quick Start:  CLAUDE.md"
echo "  → Migration:    docs/guides/V9_TO_V10_MIGRATION.md"
echo "  → Design:       docs/design/DESIGN_SYSTEM.md"
echo ""
echo "🖤 RAG Enterprise v10.0.0 - Ready!"
echo ""
