#!/bin/bash

# ==============================================================================
# RAG Enterprise - NexaAI Stop Script
# ==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "========================================================================"
echo "  Stopping RAG Enterprise with NexaAI"
echo "========================================================================"
echo -e "${NC}"
echo ""

# Stop Docker services
echo -e "${YELLOW}Stopping Docker services...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.nexa.yml down
echo -e "${GREEN}✓${NC} Docker services stopped"
echo ""

# Stop NexaAI server
if [ -f ".nexa.pid" ]; then
    NEXA_PID=$(cat .nexa.pid)
    echo -e "${YELLOW}Stopping NexaAI server (PID: $NEXA_PID)...${NC}"

    if kill -0 $NEXA_PID 2>/dev/null; then
        kill $NEXA_PID
        echo -e "${GREEN}✓${NC} NexaAI server stopped"
    else
        echo -e "${YELLOW}⚠${NC} NexaAI server not running"
    fi

    rm .nexa.pid
else
    echo -e "${YELLOW}⚠${NC} No NexaAI PID file found"

    # Try to find and kill nexa serve process
    NEXA_PID=$(pgrep -f "nexa serve" || true)
    if [ -n "$NEXA_PID" ]; then
        echo -e "${YELLOW}Found NexaAI process (PID: $NEXA_PID), stopping...${NC}"
        kill $NEXA_PID
        echo -e "${GREEN}✓${NC} NexaAI server stopped"
    fi
fi

echo ""
echo -e "${GREEN}✓ All services stopped${NC}"
echo ""
