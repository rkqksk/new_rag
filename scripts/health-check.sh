#!/bin/bash

##############################################################################
# RAG Enterprise - Health Check Script
#
# Purpose: Comprehensive health check for all services
# Usage: ./scripts/health-check.sh [--verbose]
#
# Exit codes:
#   0: All services healthy
#   1: Some services unhealthy
#   2: Critical services down
#
# Version: 1.0.0
##############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Verbose mode
VERBOSE=false
if [[ "$1" == "--verbose" ]] || [[ "$1" == "-v" ]]; then
    VERBOSE=true
fi

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RAG Enterprise - Health Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

##############################################################################
# Helper Functions
##############################################################################

check_service() {
    local service_name=$1
    local check_command=$2
    local is_critical=${3:-true}  # Default: critical

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -ne "Checking ${service_name}... "

    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        if [[ "$is_critical" == true ]]; then
            echo -e "${RED}❌ FAILED${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        else
            echo -e "${YELLOW}⚠️  WARNING${NC}"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
        fi
        return 1
    fi
}

check_port() {
    local service_name=$1
    local port=$2
    local is_critical=${3:-true}

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -ne "Checking ${service_name} (port ${port})... "

    if lsof -i:"$port" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        if [[ "$is_critical" == true ]]; then
            echo -e "${RED}❌ FAILED (port not open)${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        else
            echo -e "${YELLOW}⚠️  WARNING (port not open)${NC}"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
        fi
        return 1
    fi
}

check_docker_container() {
    local container_name=$1
    local is_critical=${2:-true}

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -ne "Checking Docker container: ${container_name}... "

    if docker ps --filter "name=${container_name}" --filter "status=running" | grep -q "${container_name}"; then
        echo -e "${GREEN}✅ OK${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        if [[ "$is_critical" == true ]]; then
            echo -e "${RED}❌ FAILED (not running)${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        else
            echo -e "${YELLOW}⚠️  WARNING (not running)${NC}"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
        fi
        return 1
    fi
}

##############################################################################
# Critical Services
##############################################################################

echo -e "${YELLOW}[Critical Services]${NC}"
echo ""

# Qdrant (Vector DB)
check_service "Qdrant Health" "curl -sf http://localhost:6333/health" true
check_docker_container "qdrant" true

# API Server
check_service "API Health" "curl -sf http://localhost:8001/health" true
check_service "API Ready" "curl -sf http://localhost:8001/health/ready" true
check_docker_container "api" true

# Redis (Cache)
check_docker_container "redis" true
check_service "Redis Ping" "docker exec redis redis-cli ping | grep -q PONG" true

# PostgreSQL (Database)
check_docker_container "postgres" true
check_service "PostgreSQL Ready" "docker exec postgres pg_isready" true

echo ""

##############################################################################
# Important Services
##############################################################################

echo -e "${YELLOW}[Important Services]${NC}"
echo ""

# Ollama (LLM)
check_docker_container "ollama" false
check_service "Ollama API" "curl -sf http://localhost:11434/api/tags" false

# Check if Ollama model is pulled
if docker exec ollama ollama list 2>/dev/null | grep -q "qwen2.5:7b"; then
    echo -e "Ollama Model (qwen2.5:7b)... ${GREEN}✅ OK${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "Ollama Model (qwen2.5:7b)... ${YELLOW}⚠️  Not found${NC}"
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""

##############################################################################
# Optional Services
##############################################################################

echo -e "${YELLOW}[Optional Services]${NC}"
echo ""

# NexaAI (optional)
if command -v nexa &> /dev/null; then
    check_service "NexaAI Server" "curl -sf http://localhost:8080/v1/models" false
else
    echo -e "NexaAI... ${YELLOW}⚠️  Not installed (optional)${NC}"
fi

# Frontend (Python HTTP server)
check_port "Frontend Server" 8080 false

# MinIO (optional object storage)
if docker ps --filter "name=minio" | grep -q minio; then
    check_docker_container "minio" false
    check_service "MinIO Health" "curl -sf http://localhost:9000/minio/health/live" false
else
    echo -e "MinIO... ${YELLOW}⚠️  Not running (optional)${NC}"
fi

echo ""

##############################################################################
# API Endpoints Check
##############################################################################

if [[ "$VERBOSE" == true ]]; then
    echo -e "${YELLOW}[API Endpoints - Verbose Mode]${NC}"
    echo ""

    # RAG endpoints
    check_service "  RAG Search Endpoint" "curl -sf -X POST http://localhost:8001/api/v1/search -H 'Content-Type: application/json' -d '{\"query\":\"test\",\"top_k\":1}'" false

    # Health endpoints
    check_service "  Health Liveness" "curl -sf http://localhost:8001/health/live" false
    check_service "  Health Readiness" "curl -sf http://localhost:8001/health/ready" false

    # Debug endpoints
    check_service "  Debug Performance" "curl -sf http://localhost:8001/api/v1/debug/performance/summary" false

    echo ""
fi

##############################################################################
# Docker Resources Check
##############################################################################

if [[ "$VERBOSE" == true ]]; then
    echo -e "${YELLOW}[Docker Resources]${NC}"
    echo ""

    # Check Docker disk usage
    DOCKER_DISK=$(docker system df --format "{{.Size}}" 2>/dev/null | head -1 || echo "Unknown")
    echo -e "  Docker Disk Usage: ${DOCKER_DISK}"

    # Check running containers
    RUNNING_CONTAINERS=$(docker ps -q | wc -l)
    echo -e "  Running Containers: ${RUNNING_CONTAINERS}"

    # Check Docker volumes
    VOLUMES=$(docker volume ls -q | wc -l)
    echo -e "  Docker Volumes: ${VOLUMES}"

    echo ""
fi

##############################################################################
# Summary
##############################################################################

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Health Check Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "Total Checks:    ${TOTAL_CHECKS}"
echo -e "Passed:          ${GREEN}${PASSED_CHECKS}${NC}"
echo -e "Failed:          ${RED}${FAILED_CHECKS}${NC}"
echo -e "Warnings:        ${YELLOW}${WARNING_CHECKS}${NC}"

echo ""

# Determine exit code
if [[ $FAILED_CHECKS -eq 0 ]] && [[ $WARNING_CHECKS -eq 0 ]]; then
    echo -e "${GREEN}✅ All services are healthy!${NC}"
    echo ""
    exit 0
elif [[ $FAILED_CHECKS -eq 0 ]]; then
    echo -e "${YELLOW}⚠️  All critical services OK, but some warnings exist${NC}"
    echo -e "${YELLOW}Review warnings above. Non-critical services may need attention.${NC}"
    echo ""
    exit 0
elif [[ $FAILED_CHECKS -gt 0 ]]; then
    echo -e "${RED}❌ Some services are unhealthy!${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo -e "  1. View logs:        ${BLUE}docker-compose logs -f${NC}"
    echo -e "  2. Restart services: ${BLUE}./scripts/restart-all.sh${NC}"
    echo -e "  3. Full reset:       ${BLUE}./scripts/restart-all.sh --clean${NC}"
    echo ""
    exit 2
fi
