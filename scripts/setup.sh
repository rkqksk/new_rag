#!/usr/bin/env bash
# Complete System Setup Script
# One command to set up the entire development environment

set -e

echo "🚀 RAG Enterprise v10.0.0 Setup"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Node.js
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠️  Node.js not found. Please install Node.js 20+${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js $(node --version)${NC}"

# pnpm
if ! command -v pnpm &> /dev/null; then
    echo "Installing pnpm..."
    npm install -g pnpm@9
fi
echo -e "${GREEN}✓ pnpm $(pnpm --version)${NC}"

# Python
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Python not found. Please install Python 3.11+${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $(python3 --version)${NC}"

# Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker not found (optional for local development)${NC}"
else
    echo -e "${GREEN}✓ Docker $(docker --version)${NC}"
fi

echo ""
echo -e "${BLUE}Installing dependencies...${NC}"

# Install Node dependencies
echo "Installing Node.js packages..."
pnpm install

# Install Python dependencies
echo "Installing Python packages..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    python3 -m venv .venv
    source .venv/bin/activate
fi
pip install -r requirements.txt
pip install -r requirements-test.txt

echo ""
echo -e "${BLUE}Setting up environment...${NC}"

# Copy environment files
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please update .env with your actual values${NC}"
fi

# Create necessary directories
mkdir -p logs
mkdir -p data
mkdir -p uploads

echo ""
echo -e "${BLUE}Running initial checks...${NC}"

# Type check
echo "Type checking..."
pnpm type-check || echo -e "${YELLOW}⚠️  Type errors found (expected in scaffolds)${NC}"

# Build packages
echo "Building packages..."
pnpm --filter "./packages/*" build || echo -e "${YELLOW}⚠️  Some packages need implementation${NC}"

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Update .env with your configuration"
echo "  2. Start services: ./scripts/dev.sh"
echo "  3. Run tests: ./scripts/test-all.sh"
echo ""
echo "Documentation:"
echo "  - Quick Start: QUICK_START.md"
echo "  - Deployment: docs/deployment/DEPLOYMENT_RUNBOOK.md"
echo "  - API Docs: docs/API_REFERENCE.md"
