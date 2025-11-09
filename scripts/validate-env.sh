#!/bin/bash
# ========================================
# Environment Validation Script
# ========================================
# Validates that all required environment variables
# and dependencies are properly configured
#
# Usage: ./scripts/validate-env.sh
# ========================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0
PASSED=0

echo "========================================="
echo "Environment Validation - RAG Enterprise"
echo "========================================="
echo ""

# =========================================================================
# Helper Functions
# =========================================================================

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# =========================================================================
# Check 1: Required Files
# =========================================================================

echo "📁 Checking Required Files..."
echo "-----------------------------------"

# .env file
if [ -f ".env" ]; then
    check_pass ".env file exists"
else
    check_fail ".env file not found (copy from .env.example)"
fi

# Docker files
if [ -f "Dockerfile" ]; then
    check_pass "Dockerfile exists"
else
    check_fail "Dockerfile not found"
fi

if [ -f "docker-compose.yml" ]; then
    check_pass "docker-compose.yml exists"
else
    check_fail "docker-compose.yml not found"
fi

# Alembic
if [ -f "alembic.ini" ]; then
    check_pass "alembic.ini exists"
else
    check_fail "alembic.ini not found"
fi

# Makefile
if [ -f "Makefile" ]; then
    check_pass "Makefile exists"
else
    check_warn "Makefile not found (optional but recommended)"
fi

echo ""

# =========================================================================
# Check 2: Python Dependencies
# =========================================================================

echo "🐍 Checking Python Environment..."
echo "-----------------------------------"

# Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    if [[ "$PYTHON_VERSION" == "3.11"* ]] || [[ "$PYTHON_VERSION" == "3.12"* ]]; then
        check_pass "Python $PYTHON_VERSION installed"
    else
        check_warn "Python $PYTHON_VERSION (recommended: 3.11+)"
    fi
else
    check_fail "Python 3 not found"
fi

# pip
if command -v pip3 &> /dev/null; then
    check_pass "pip3 installed"
else
    check_warn "pip3 not found"
fi

# requirements.txt
if [ -f "requirements.txt" ]; then
    check_pass "requirements.txt exists"
else
    check_fail "requirements.txt not found"
fi

echo ""

# =========================================================================
# Check 3: Docker
# =========================================================================

echo "🐳 Checking Docker..."
echo "-----------------------------------"

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | tr -d ',')
    check_pass "Docker $DOCKER_VERSION installed"

    # Docker daemon running
    if docker info &> /dev/null; then
        check_pass "Docker daemon is running"
    else
        check_fail "Docker daemon is not running"
    fi
else
    check_fail "Docker not installed"
fi

# Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | awk '{print $3}' | tr -d ',')
    check_pass "Docker Compose $COMPOSE_VERSION installed"
else
    check_warn "docker-compose not found (try 'docker compose' instead)"
fi

echo ""

# =========================================================================
# Check 4: Database Tools
# =========================================================================

echo "🗄️  Checking Database Tools..."
echo "-----------------------------------"

# Alembic
if python3 -c "import alembic" 2>/dev/null; then
    check_pass "Alembic installed"
else
    check_warn "Alembic not installed (run: pip install alembic)"
fi

# SQLAlchemy
if python3 -c "import sqlalchemy" 2>/dev/null; then
    check_pass "SQLAlchemy installed"
else
    check_fail "SQLAlchemy not installed"
fi

# psycopg2
if python3 -c "import psycopg2" 2>/dev/null; then
    check_pass "psycopg2 installed"
else
    check_warn "psycopg2 not installed (run: pip install psycopg2-binary)"
fi

echo ""

# =========================================================================
# Check 5: Monitoring Setup
# =========================================================================

echo "📊 Checking Monitoring Setup..."
echo "-----------------------------------"

# Prometheus config
if [ -f "monitoring/prometheus/prometheus.yml" ]; then
    check_pass "Prometheus config exists"
else
    check_fail "monitoring/prometheus/prometheus.yml not found"
fi

# Grafana config
if [ -d "monitoring/grafana/provisioning" ]; then
    check_pass "Grafana provisioning directory exists"
else
    check_fail "monitoring/grafana/provisioning not found"
fi

# Alert rules
if [ -f "monitoring/prometheus/alerts.yml" ]; then
    check_pass "Prometheus alert rules exist"
else
    check_warn "monitoring/prometheus/alerts.yml not found"
fi

echo ""

# =========================================================================
# Check 6: Migrations
# =========================================================================

echo "🔄 Checking Migrations..."
echo "-----------------------------------"

# Alembic versions directory
if [ -d "alembic/versions" ]; then
    MIGRATION_COUNT=$(find alembic/versions -name "*.py" -not -name "__init__.py" | wc -l)
    check_pass "$MIGRATION_COUNT migration files found"
else
    check_fail "alembic/versions directory not found"
fi

echo ""

# =========================================================================
# Check 7: Test Suite
# =========================================================================

echo "🧪 Checking Test Suite..."
echo "-----------------------------------"

# pytest
if python3 -c "import pytest" 2>/dev/null; then
    check_pass "pytest installed"
else
    check_warn "pytest not installed (run: pip install pytest)"
fi

# Test directories
if [ -d "tests" ]; then
    TEST_COUNT=$(find tests -name "test_*.py" | wc -l)
    check_pass "$TEST_COUNT test files found"
else
    check_fail "tests directory not found"
fi

# Integration tests
if [ -d "tests/integration" ]; then
    INTEGRATION_COUNT=$(find tests/integration -name "test_*.py" | wc -l)
    check_pass "$INTEGRATION_COUNT integration test files"
else
    check_warn "tests/integration directory not found"
fi

echo ""

# =========================================================================
# Summary
# =========================================================================

echo "========================================="
echo "Validation Summary"
echo "========================================="
echo -e "${GREEN}✓ Passed:${NC}   $PASSED"
echo -e "${YELLOW}⚠ Warnings:${NC} $WARNINGS"
echo -e "${RED}✗ Errors:${NC}   $ERRORS"
echo "========================================="

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo -e "${RED}Validation failed with $ERRORS error(s)${NC}"
    echo "Please fix the errors above before proceeding."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}Validation passed with $WARNINGS warning(s)${NC}"
    echo "Warnings are optional but recommended to fix."
    exit 0
else
    echo ""
    echo -e "${GREEN}All checks passed! ✓${NC}"
    echo "Environment is properly configured."
    exit 0
fi
