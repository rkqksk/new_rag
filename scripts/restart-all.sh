#!/bin/bash

##############################################################################
# RAG Enterprise - Automated Restart Script
#
# Purpose: Fully automated troubleshooting and service restart
# Usage: ./scripts/restart-all.sh [--clean]
#
# This script:
# 1. Kills all running services (Docker, Ollama, Python, NexaAI)
# 2. Cleans up Docker resources (optional: --clean for full cleanup)
# 3. Restarts all services in correct order
# 4. Waits for health checks
# 5. Displays service status
#
# Version: 1.0.0
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "$PROJECT_ROOT"

# Parse arguments
CLEAN_MODE=false
if [[ "$1" == "--clean" ]]; then
    CLEAN_MODE=true
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RAG Enterprise - Automated Restart${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

##############################################################################
# Step 1: Kill All Running Services
##############################################################################

echo -e "${YELLOW}[1/5] Killing all running services...${NC}"

# Kill Python HTTP servers (frontend)
echo -e "  Stopping Python HTTP servers..."
pkill -f "python.*http.server" 2>/dev/null || true
pkill -f "python3.*http.server" 2>/dev/null || true

# Kill any processes on critical ports
echo -e "  Freeing up ports..."
for port in 8001 8080 6333 6379 5432 11434 9000; do
    PID=$(lsof -ti:$port 2>/dev/null || true)
    if [[ -n "$PID" ]]; then
        echo -e "    Killing process on port $port (PID: $PID)"
        kill -9 $PID 2>/dev/null || true
    fi
done

# Stop Docker services
echo -e "  Stopping Docker services..."
if docker-compose ps -q 2>/dev/null | grep -q .; then
    docker-compose down 2>/dev/null || true
fi

# Kill any orphaned Docker containers
echo -e "  Cleaning up Docker containers..."
docker ps -q --filter "name=rag-enterprise" 2>/dev/null | xargs -r docker stop 2>/dev/null || true
docker ps -aq --filter "name=rag-enterprise" 2>/dev/null | xargs -r docker rm 2>/dev/null || true

# Kill NexaAI server if running
echo -e "  Stopping NexaAI server..."
pkill -f "nexa.*server" 2>/dev/null || true

echo -e "${GREEN}✅ All services stopped${NC}"
echo ""

##############################################################################
# Step 2: Clean Up Docker Resources (Optional)
##############################################################################

if [[ "$CLEAN_MODE" == true ]]; then
    echo -e "${YELLOW}[2/5] Cleaning up Docker resources (--clean mode)...${NC}"

    # Remove volumes (WARNING: This deletes all data!)
    echo -e "  ${RED}WARNING: Removing Docker volumes (all data will be lost!)${NC}"
    docker volume ls -q --filter "name=rag-enterprise" 2>/dev/null | xargs -r docker volume rm 2>/dev/null || true

    # Prune system
    echo -e "  Pruning Docker system..."
    docker system prune -af --volumes 2>/dev/null || true

    echo -e "${GREEN}✅ Docker resources cleaned${NC}"
else
    echo -e "${YELLOW}[2/5] Skipping Docker cleanup (use --clean to remove volumes)${NC}"
fi
echo ""

##############################################################################
# Step 3: Restart Services
##############################################################################

echo -e "${YELLOW}[3/5] Starting services...${NC}"

# Check if docker-compose.yml exists
if [[ ! -f "docker-compose.yml" ]]; then
    echo -e "${RED}❌ docker-compose.yml not found${NC}"
    exit 1
fi

# Start Docker services
echo -e "  Starting Docker Compose..."
docker-compose up -d

# Wait a bit for services to initialize
sleep 5

echo -e "${GREEN}✅ Services started${NC}"
echo ""

##############################################################################
# Step 4: Health Checks
##############################################################################

echo -e "${YELLOW}[4/5] Running health checks...${NC}"

# Function to wait for service
wait_for_service() {
    local service_name=$1
    local health_url=$2
    local max_wait=$3
    local elapsed=0

    echo -ne "  Waiting for ${service_name}..."

    while [[ $elapsed -lt $max_wait ]]; do
        if curl -sf "${health_url}" > /dev/null 2>&1; then
            echo -e " ${GREEN}✅${NC}"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
        echo -ne "."
    done

    echo -e " ${RED}❌ (timeout after ${max_wait}s)${NC}"
    return 1
}

# Check each service
SERVICES_OK=true

wait_for_service "Qdrant" "http://localhost:6333/health" 30 || SERVICES_OK=false
wait_for_service "Redis" "http://localhost:6379" 20 || SERVICES_OK=false
wait_for_service "API" "http://localhost:8001/health" 60 || SERVICES_OK=false

# Optional: Check Ollama (may take longer to start)
if wait_for_service "Ollama" "http://localhost:11434/api/tags" 30; then
    echo -e "  ${GREEN}✅ Ollama is ready${NC}"
else
    echo -e "  ${YELLOW}⚠️  Ollama is starting (this may take a minute)${NC}"
fi

if [[ "$SERVICES_OK" == false ]]; then
    echo -e "${RED}⚠️  Some services failed health checks${NC}"
    echo -e "${YELLOW}View logs: docker-compose logs -f${NC}"
fi

echo ""

##############################################################################
# Step 5: Display Service Status
##############################################################################

echo -e "${YELLOW}[5/5] Service Status${NC}"
echo ""

# Check Docker containers
echo -e "${BLUE}Docker Containers:${NC}"
docker-compose ps

echo ""

# Display service URLs
echo -e "${BLUE}Service URLs:${NC}"
echo -e "  ${GREEN}API:${NC}        http://localhost:8001/api/v1/docs"
echo -e "  ${GREEN}Health:${NC}     http://localhost:8001/health"
echo -e "  ${GREEN}Qdrant:${NC}     http://localhost:6333/dashboard"
echo -e "  ${GREEN}Frontend:${NC}   http://localhost:8080/chat.html (manual start required)"

echo ""

# Display manual commands
echo -e "${BLUE}Manual Commands:${NC}"
echo -e "  ${YELLOW}Start frontend:${NC}  cd frontend && python3 -m http.server 8080"
echo -e "  ${YELLOW}View logs:${NC}       docker-compose logs -f"
echo -e "  ${YELLOW}View API logs:${NC}   docker-compose logs -f api"
echo -e "  ${YELLOW}Restart API:${NC}     docker-compose restart api"

echo ""

# Check if NexaAI is available
if command -v nexa &> /dev/null; then
    echo -e "${BLUE}Optional: Start NexaAI Server${NC}"
    echo -e "  ${YELLOW}nexa server start${NC}"
    echo ""
fi

##############################################################################
# Final Summary
##############################################################################

if [[ "$SERVICES_OK" == true ]]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ Restart Complete - All Services OK${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}⚠️  Restart Complete with Warnings${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}Some services may need additional time to start.${NC}"
    echo -e "${YELLOW}Run: docker-compose logs -f${NC}"
    exit 1
fi
