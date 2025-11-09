#!/bin/bash

###############################################################################
# Environment Setup Automation Script
#
# Purpose: Automatically generate and validate .env file
# Usage: ./scripts/setup-env.sh [--production|--development]
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Environment mode (default: development)
ENV_MODE="${1:-development}"

echo -e "${BLUE}🔧 RAG Enterprise - Environment Setup${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "Mode: ${GREEN}${ENV_MODE}${NC}"
echo ""

# Check if .env already exists
if [ -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file already exists${NC}"
    read -p "Do you want to backup and regenerate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"
        mv .env "$BACKUP_FILE"
        echo -e "${GREEN}✅ Backed up to ${BACKUP_FILE}${NC}"
    else
        echo -e "${YELLOW}Skipping .env generation${NC}"
        exit 0
    fi
fi

# Generate secure random keys
generate_secret_key() {
    python3 -c "import secrets; print(secrets.token_urlsafe(${1:-64}))"
}

echo -e "${BLUE}📝 Generating .env file...${NC}"

# Create .env file
cat > .env << 'EOF'
# ============================================================================
# RAG Enterprise - Environment Configuration
# Generated: $(date +"%Y-%m-%d %H:%M:%S")
# Mode: ${ENV_MODE}
# ============================================================================

# ============================================================================
# Application
# ============================================================================
ENVIRONMENT=${ENV_MODE}
DEBUG_ENABLED=${DEBUG_ENABLED}
APP_NAME="RAG Enterprise API"
API_PREFIX=/api/v1

# ============================================================================
# Database - PostgreSQL
# ============================================================================
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_POOL_SIZE=20

# ============================================================================
# Redis Cache
# ============================================================================
REDIS_HOST=${REDIS_HOST}
REDIS_PORT=${REDIS_PORT}
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_DB=0
REDIS_MAX_CONNECTIONS=50

# ============================================================================
# Qdrant Vector Database
# ============================================================================
QDRANT_HOST=${QDRANT_HOST}
QDRANT_PORT=${QDRANT_PORT}
QDRANT_API_KEY=${QDRANT_API_KEY}
QDRANT_COLLECTION=products_multimodal

# ============================================================================
# API Server
# ============================================================================
API_HOST=0.0.0.0
API_PORT=8001

# ============================================================================
# Authentication & Security
# ============================================================================
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_EXPIRATION=24
API_KEY_SALT=${API_KEY_SALT}

# ============================================================================
# SaaS Platform
# ============================================================================
# Stripe (Payment processing)
STRIPE_API_KEY=${STRIPE_API_KEY}
STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET}
STRIPE_PRICE_FREE=price_free
STRIPE_PRICE_PRO=price_pro
STRIPE_PRICE_ENTERPRISE=price_enterprise

# ============================================================================
# AI/ML Services
# ============================================================================
# NexaAI (Optional - Fast LLM)
NEXA_ENABLED=${NEXA_ENABLED}
NEXA_API_KEY=${NEXA_API_KEY}
NEXA_MODEL=qwen2.5:7b-instruct
NEXA_TIMEOUT=30

# Ollama (Local LLM)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct

# Model Router Thresholds
MODEL_ROUTER_SIMPLE_THRESHOLD=0.3
MODEL_ROUTER_COMPLEX_THRESHOLD=0.7

# ============================================================================
# Embedding & Vectors
# ============================================================================
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
EMBEDDING_BATCH_SIZE=32

# ============================================================================
# OCR & Image Processing
# ============================================================================
OCR_ENGINE=paddleocr
OCR_LANG=korean+english
IMAGE_MAX_SIZE=10485760  # 10MB

# ============================================================================
# Debug & Monitoring
# ============================================================================
DEBUG_LOG_REQUESTS=true
DEBUG_LOG_RESPONSES=false
DEBUG_LOG_SQL=true
DEBUG_LOG_CACHE=true
DEBUG_PROFILE_REQUESTS=true
DEBUG_SLOW_REQUEST_MS=500
DEBUG_EXPLAIN_SEARCH=true

LOG_LEVEL=INFO
LOG_FILE=logs/rag-enterprise.log

# ============================================================================
# CORS
# ============================================================================
ALLOWED_ORIGINS=http://localhost:8080,http://localhost:3000,http://localhost:5173

# ============================================================================
# Rate Limiting
# ============================================================================
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# ============================================================================
# MCP Servers & Sub-Agents
# ============================================================================
# TestSprite (AI-powered testing) - RECOMMENDED
TESTSPRITE_API_KEY=${TESTSPRITE_API_KEY}

# GitHub (for private repos only)
GITHUB_PERSONAL_ACCESS_TOKEN=${GITHUB_TOKEN}

# Tavily (AI search - optional)
TAVILY_API_KEY=${TAVILY_API_KEY}

# PostgreSQL (for data-agent)
POSTGRES_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# ============================================================================
# Performance & Optimization
# ============================================================================
CACHE_TTL=3600
MAX_WORKERS=4
REQUEST_TIMEOUT=30

# ============================================================================
# Feature Flags
# ============================================================================
FEATURE_MULTIMODAL=true
FEATURE_PERSONALIZATION=true
FEATURE_ANALYTICS=true
FEATURE_SAAS=true
FEATURE_IMAGE_PROCESSING=true

EOF

# Now substitute environment-specific values
if [ "$ENV_MODE" = "production" ]; then
    # Production settings
    DEBUG_ENABLED="false"
    DB_HOST="${DB_HOST:-postgres}"
    DB_PORT="${DB_PORT:-5432}"
    DB_NAME="${DB_NAME:-rag_enterprise}"
    DB_USER="${DB_USER:-postgres}"
    DB_PASSWORD="$(generate_secret_key 32)"
    REDIS_HOST="${REDIS_HOST:-redis}"
    REDIS_PORT="${REDIS_PORT:-6379}"
    REDIS_PASSWORD="$(generate_secret_key 32)"
    QDRANT_HOST="${QDRANT_HOST:-qdrant}"
    QDRANT_PORT="${QDRANT_PORT:-6333}"
    QDRANT_API_KEY="$(generate_secret_key 32)"
    JWT_SECRET="$(generate_secret_key 64)"
    API_KEY_SALT="$(generate_secret_key 32)"
    STRIPE_API_KEY="${STRIPE_API_KEY:-sk_live_YOUR_LIVE_KEY_HERE}"
    STRIPE_WEBHOOK_SECRET="${STRIPE_WEBHOOK_SECRET:-whsec_YOUR_WEBHOOK_SECRET_HERE}"
    NEXA_ENABLED="${NEXA_ENABLED:-false}"
    NEXA_API_KEY="${NEXA_API_KEY:-}"
    TESTSPRITE_API_KEY="${TESTSPRITE_API_KEY:-}"
    GITHUB_TOKEN="${GITHUB_TOKEN:-}"
    TAVILY_API_KEY="${TAVILY_API_KEY:-}"
else
    # Development settings
    DEBUG_ENABLED="true"
    DB_HOST="postgres"
    DB_PORT="5432"
    DB_NAME="rag_enterprise"
    DB_USER="postgres"
    DB_PASSWORD="postgres"
    REDIS_HOST="redis"
    REDIS_PORT="6379"
    REDIS_PASSWORD=""
    QDRANT_HOST="qdrant"
    QDRANT_PORT="6333"
    QDRANT_API_KEY=""
    JWT_SECRET="$(generate_secret_key 64)"
    API_KEY_SALT="$(generate_secret_key 32)"
    STRIPE_API_KEY="sk_test_YOUR_TEST_KEY_HERE"
    STRIPE_WEBHOOK_SECRET="whsec_YOUR_TEST_WEBHOOK_SECRET_HERE"
    NEXA_ENABLED="false"
    NEXA_API_KEY=""
    TESTSPRITE_API_KEY=""
    GITHUB_TOKEN=""
    TAVILY_API_KEY=""
fi

# Replace placeholders
sed -i "s|\${ENV_MODE}|${ENV_MODE}|g" .env
sed -i "s|\${DEBUG_ENABLED}|${DEBUG_ENABLED}|g" .env
sed -i "s|\${DB_HOST}|${DB_HOST}|g" .env
sed -i "s|\${DB_PORT}|${DB_PORT}|g" .env
sed -i "s|\${DB_NAME}|${DB_NAME}|g" .env
sed -i "s|\${DB_USER}|${DB_USER}|g" .env
sed -i "s|\${DB_PASSWORD}|${DB_PASSWORD}|g" .env
sed -i "s|\${REDIS_HOST}|${REDIS_HOST}|g" .env
sed -i "s|\${REDIS_PORT}|${REDIS_PORT}|g" .env
sed -i "s|\${REDIS_PASSWORD}|${REDIS_PASSWORD}|g" .env
sed -i "s|\${QDRANT_HOST}|${QDRANT_HOST}|g" .env
sed -i "s|\${QDRANT_PORT}|${QDRANT_PORT}|g" .env
sed -i "s|\${QDRANT_API_KEY}|${QDRANT_API_KEY}|g" .env
sed -i "s|\${JWT_SECRET}|${JWT_SECRET}|g" .env
sed -i "s|\${API_KEY_SALT}|${API_KEY_SALT}|g" .env
sed -i "s|\${STRIPE_API_KEY}|${STRIPE_API_KEY}|g" .env
sed -i "s|\${STRIPE_WEBHOOK_SECRET}|${STRIPE_WEBHOOK_SECRET}|g" .env
sed -i "s|\${NEXA_ENABLED}|${NEXA_ENABLED}|g" .env
sed -i "s|\${NEXA_API_KEY}|${NEXA_API_KEY}|g" .env
sed -i "s|\${TESTSPRITE_API_KEY}|${TESTSPRITE_API_KEY}|g" .env
sed -i "s|\${GITHUB_TOKEN}|${GITHUB_TOKEN}|g" .env
sed -i "s|\${TAVILY_API_KEY}|${TAVILY_API_KEY}|g" .env

echo -e "${GREEN}✅ .env file created successfully${NC}"
echo ""

# Validate required variables
echo -e "${BLUE}🔍 Validating environment variables...${NC}"

REQUIRED_VARS=(
    "ENVIRONMENT"
    "DB_HOST"
    "DB_NAME"
    "DB_USER"
    "JWT_SECRET_KEY"
    "API_KEY_SALT"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" .env || grep -q "^${var}=$" .env; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ All required variables are set${NC}"
else
    echo -e "${RED}❌ Missing required variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo -e "${RED}   - ${var}${NC}"
    done
    exit 1
fi

# Security check
echo ""
echo -e "${BLUE}🔐 Security recommendations:${NC}"
echo ""

if [ "$ENV_MODE" = "production" ]; then
    echo -e "${YELLOW}⚠️  PRODUCTION MODE${NC}"
    echo -e "   - Update STRIPE_API_KEY with your live key"
    echo -e "   - Update STRIPE_WEBHOOK_SECRET"
    echo -e "   - Consider using a secrets manager (Vault, AWS Secrets, etc.)"
    echo -e "   - Do NOT commit .env to git"
else
    echo -e "${GREEN}✅ DEVELOPMENT MODE${NC}"
    echo -e "   - Using test Stripe keys (update if needed)"
    echo -e "   - Generated secure JWT_SECRET_KEY"
    echo -e "   - Generated secure API_KEY_SALT"
fi

echo ""
echo -e "${BLUE}📚 Optional API Keys:${NC}"
echo ""
echo -e "   ${YELLOW}TestSprite${NC} (Recommended - AI testing):"
echo -e "     Get free key at: ${BLUE}https://testsprite.com${NC}"
echo -e "     Then add to .env: TESTSPRITE_API_KEY=your_key"
echo ""
echo -e "   ${YELLOW}GitHub${NC} (for private repos):"
echo -e "     Get token at: ${BLUE}https://github.com/settings/tokens${NC}"
echo -e "     Then add to .env: GITHUB_PERSONAL_ACCESS_TOKEN=your_token"
echo ""
echo -e "   ${YELLOW}Tavily${NC} (AI search - optional):"
echo -e "     Get free key at: ${BLUE}https://tavily.com${NC}"
echo -e "     Then add to .env: TAVILY_API_KEY=your_key"
echo ""

# Create logs directory
mkdir -p logs
echo -e "${GREEN}✅ Created logs/ directory${NC}"

# Summary
echo ""
echo -e "${GREEN}🎉 Environment setup complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "   1. Review .env file and update API keys if needed"
echo -e "   2. Run: ${GREEN}make docker-up${NC} to start services"
echo -e "   3. Run: ${GREEN}make test${NC} to verify setup"
echo ""
