#!/bin/bash
# MCP 서버 테스트 실행 스크립트

set -e

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   MCP Server Test Utility${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# 가상환경 확인
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
    echo -e "${YELLOW}   Attempting to activate...${NC}"

    if [ -d "venv" ]; then
        source venv/bin/activate
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
    else
        echo -e "${RED}❌ No virtual environment found${NC}"
        echo -e "${YELLOW}   Run: python -m venv venv && source venv/bin/activate${NC}"
        exit 1
    fi
fi

# 필수 패키지 확인
echo -e "\n${BLUE}Checking dependencies...${NC}"
python -c "import anthropic" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  anthropic not installed${NC}"
    pip install anthropic
}

python -c "import qdrant_client" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  qdrant-client not installed${NC}"
    pip install qdrant-client
}

python -c "import aiohttp" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  aiohttp not installed${NC}"
    pip install aiohttp
}

python -c "import dotenv" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  python-dotenv not installed${NC}"
    pip install python-dotenv
}

echo -e "${GREEN}✅ All dependencies installed${NC}"

# .env 파일 확인
echo -e "\n${BLUE}Checking .env file...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo -e "${YELLOW}   Creating from .env.example...${NC}"

    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ .env file created${NC}"
        echo -e "${YELLOW}   ⚠️  Please edit .env and add your API keys!${NC}"
    else
        echo -e "${RED}❌ .env.example not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env file exists${NC}"
fi

# Docker 상태 확인
echo -e "\n${BLUE}Checking Docker services...${NC}"
if command -v docker-compose &> /dev/null; then
    if docker-compose ps | grep -q "Up"; then
        echo -e "${GREEN}✅ Docker services running${NC}"
    else
        echo -e "${YELLOW}⚠️  Docker services not running${NC}"
        echo -e "${YELLOW}   Start with: docker-compose up -d${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  docker-compose not found${NC}"
fi

# MCP 서버 테스트 실행
echo -e "\n${BLUE}Running MCP server tests...${NC}"
echo ""

python tests/test_mcp_servers.py

# 종료 상태 확인
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}   ✅ All tests completed${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "\n${RED}========================================${NC}"
    echo -e "${RED}   ❌ Tests failed${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi
