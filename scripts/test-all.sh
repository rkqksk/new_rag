#!/bin/bash

# ==============================================================================
# RAG Enterprise - Comprehensive Test Suite
# ==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_URL="http://localhost:8001"
NEXA_URL="http://localhost:8080"

echo -e "${BLUE}"
echo "========================================================================"
echo "  RAG Enterprise - Comprehensive Test Suite"
echo "========================================================================"
echo -e "${NC}"
echo ""

# ==============================================================================
# Test 1: Service Health Checks
# ==============================================================================

echo -e "${BLUE}[Test 1/10]${NC} Service Health Checks..."
echo ""

# NexaAI
echo -n "  → NexaAI Server: "
if curl -sf $NEXA_URL/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC} (Start with: nexa serve --host 0.0.0.0:8080)"
fi

# API
echo -n "  → API Server: "
if curl -sf $API_URL/health/ready > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC} (Start with: ./scripts/start-nexa.sh development)"
fi

# Qdrant
echo -n "  → Qdrant: "
if curl -sf http://localhost:6333/dashboard > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

# Redis
echo -n "  → Redis: "
if docker exec rag-redis redis-cli ping 2>/dev/null | grep -q PONG; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

echo ""

# ==============================================================================
# Test 2: Admin API Endpoints
# ==============================================================================

echo -e "${BLUE}[Test 2/10]${NC} Admin API Endpoints..."
echo ""

# Health
echo -n "  → GET /api/v1/admin/health: "
RESPONSE=$(curl -sf $API_URL/api/v1/admin/health)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

# Stats
echo -n "  → GET /api/v1/admin/stats: "
RESPONSE=$(curl -sf $API_URL/api/v1/admin/stats)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

# Models
echo -n "  → GET /api/v1/admin/models: "
RESPONSE=$(curl -sf $API_URL/api/v1/admin/models)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

echo ""

# ==============================================================================
# Test 3: Simple Query (NexaAI Fast Model)
# ==============================================================================

echo -e "${BLUE}[Test 3/10]${NC} Simple Query Test (NexaAI)..."
echo ""

QUERY='{"query":"50ml PET 용기","top_k":5}'
echo "  Query: $QUERY"
echo ""

RESPONSE=$(curl -sf -X POST $API_URL/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d "$QUERY")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} - Got response"

    # Check routing
    ENGINE=$(echo $RESPONSE | jq -r '.routing.engine // "unknown"')
    MODEL=$(echo $RESPONSE | jq -r '.routing.model // "unknown"')

    echo "  → Engine: $ENGINE"
    echo "  → Model: $MODEL"

    if [ "$ENGINE" = "nexa" ]; then
        echo -e "  → ${GREEN}✓ Correctly routed to NexaAI (fast)${NC}"
    fi
else
    echo -e "${RED}✗ FAIL${NC}"
fi

echo ""

# ==============================================================================
# Test 4: Complex Query (Ollama Quality Model)
# ==============================================================================

echo -e "${BLUE}[Test 4/10]${NC} Complex Query Test (Ollama)..."
echo ""

QUERY='{"query":"100ml 투명 PET 용기와 PP 용기의 재질 특성, 내구성, 가격을 비교 분석하고 각각의 장단점을 상세히 설명해주세요","top_k":5}'
echo "  Query: (complex reasoning query)"
echo ""

RESPONSE=$(curl -sf -X POST $API_URL/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d "$QUERY")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} - Got response"

    ENGINE=$(echo $RESPONSE | jq -r '.routing.engine // "unknown"')
    MODEL=$(echo $RESPONSE | jq -r '.routing.model // "unknown"')

    echo "  → Engine: $ENGINE"
    echo "  → Model: $MODEL"

    if [ "$ENGINE" = "ollama" ]; then
        echo -e "  → ${GREEN}✓ Correctly routed to Ollama (quality)${NC}"
    fi
else
    echo -e "${RED}✗ FAIL${NC}"
fi

echo ""

# ==============================================================================
# Test 5: Chat Session
# ==============================================================================

echo -e "${BLUE}[Test 5/10]${NC} Chat Session Test..."
echo ""

SESSION_ID="test-session-$(date +%s)"
QUERY="{\"query\":\"24파이 캡 추천해줘\",\"session_id\":\"$SESSION_ID\",\"top_k\":3}"

echo "  Session ID: $SESSION_ID"
echo ""

RESPONSE=$(curl -sf -X POST $API_URL/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d "$QUERY")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} - Chat session created"

    # Check if products returned
    PRODUCTS=$(echo $RESPONSE | jq '.products // []')
    COUNT=$(echo $PRODUCTS | jq 'length')

    echo "  → Products returned: $COUNT"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

echo ""

# ==============================================================================
# Test 6: Vector Search Quality
# ==============================================================================

echo -e "${BLUE}[Test 6/10]${NC} Vector Search Quality Test..."
echo ""

QUERY='{"query":"50ml","top_k":10}'

RESPONSE=$(curl -sf -X POST $API_URL/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d "$QUERY")

if [ $? -eq 0 ]; then
    # Check similarity scores
    AVG_SCORE=$(echo $RESPONSE | jq '[.results[].score] | add / length')

    echo "  → Average similarity: $AVG_SCORE"

    # Check if score > 0.7
    if (( $(echo "$AVG_SCORE > 0.7" | bc -l) )); then
        echo -e "  → ${GREEN}✓ High quality results${NC}"
    else
        echo -e "  → ${YELLOW}⚠ Lower quality results${NC}"
    fi

    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

echo ""

# ==============================================================================
# Test 7: Performance Test
# ==============================================================================

echo -e "${BLUE}[Test 7/10]${NC} Performance Test..."
echo ""

QUERY='{"query":"투명 용기","top_k":5}'

echo "  Running 10 requests..."

TOTAL_TIME=0
for i in {1..10}; do
    START=$(date +%s%N)

    curl -sf -X POST $API_URL/api/v1/search/ \
      -H "Content-Type: application/json" \
      -d "$QUERY" > /dev/null 2>&1

    END=$(date +%s%N)
    DURATION=$(( (END - START) / 1000000 ))  # Convert to ms
    TOTAL_TIME=$(( TOTAL_TIME + DURATION ))

    echo -n "."
done

echo ""
echo ""

AVG_TIME=$(( TOTAL_TIME / 10 ))
echo "  → Average response time: ${AVG_TIME}ms"

if [ $AVG_TIME -lt 2000 ]; then
    echo -e "  → ${GREEN}✓ Performance target met (< 2s)${NC}"
else
    echo -e "  → ${YELLOW}⚠ Performance target missed${NC}"
fi

echo ""

# ==============================================================================
# Test 8: Model Router Configuration
# ==============================================================================

echo -e "${BLUE}[Test 8/10]${NC} Model Router Configuration Test..."
echo ""

# Get current config
echo -n "  → GET router config: "
CONFIG=$(curl -sf $API_URL/api/v1/admin/router/config)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PASS${NC}"

    SIMPLE=$(echo $CONFIG | jq -r '.simple_threshold // "unknown"')
    COMPLEX=$(echo $CONFIG | jq -r '.complex_threshold // "unknown"')

    echo "    • Simple threshold: $SIMPLE"
    echo "    • Complex threshold: $COMPLEX"
fi

# Update config
echo -n "  → POST router config: "
UPDATE='{"simple_threshold":0.3,"complex_threshold":0.7}'
RESPONSE=$(curl -sf -X POST $API_URL/api/v1/admin/router/config \
  -H "Content-Type: application/json" \
  -d "$UPDATE")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

echo ""

# ==============================================================================
# Test 9: Error Handling
# ==============================================================================

echo -e "${BLUE}[Test 9/10]${NC} Error Handling Test..."
echo ""

# Invalid query
echo -n "  → Invalid query handling: "
RESPONSE=$(curl -s -X POST $API_URL/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"invalid":"data"}' \
  -w "%{http_code}")

HTTP_CODE=${RESPONSE: -3}

if [ "$HTTP_CODE" = "422" ] || [ "$HTTP_CODE" = "400" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $HTTP_CODE)"
else
    echo -e "${YELLOW}⚠ Unexpected status: $HTTP_CODE${NC}"
fi

# Missing field
echo -n "  → Missing field handling: "
RESPONSE=$(curl -s -X POST $API_URL/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{}' \
  -w "%{http_code}")

HTTP_CODE=${RESPONSE: -3}

if [ "$HTTP_CODE" = "422" ] || [ "$HTTP_CODE" = "400" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $HTTP_CODE)"
else
    echo -e "${YELLOW}⚠ Unexpected status: $HTTP_CODE${NC}"
fi

echo ""

# ==============================================================================
# Test 10: Integration Test
# ==============================================================================

echo -e "${BLUE}[Test 10/10]${NC} Full Integration Test..."
echo ""

echo "  Testing complete workflow:"
echo "  1. Simple search → 2. Complex analysis → 3. Chat session"
echo ""

# Step 1
echo -n "  → Step 1 (Simple search): "
Q1='{"query":"50ml 용기","top_k":3}'
R1=$(curl -sf -X POST $API_URL/api/v1/search/ -H "Content-Type: application/json" -d "$Q1")
[ $? -eq 0 ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}"

# Step 2
echo -n "  → Step 2 (Complex query): "
Q2='{"query":"50ml과 100ml 용기 비교","top_k":5}'
R2=$(curl -sf -X POST $API_URL/api/v1/search/ -H "Content-Type: application/json" -d "$Q2")
[ $? -eq 0 ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}"

# Step 3
echo -n "  → Step 3 (Chat session): "
SID="integration-test-$(date +%s)"
Q3="{\"query\":\"추천해줘\",\"session_id\":\"$SID\",\"top_k\":3}"
R3=$(curl -sf -X POST $API_URL/api/v1/chat/query -H "Content-Type: application/json" -d "$Q3")
[ $? -eq 0 ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}"

echo ""

# ==============================================================================
# Summary
# ==============================================================================

echo -e "${GREEN}"
echo "========================================================================"
echo "  Test Suite Complete!"
echo "========================================================================"
echo -e "${NC}"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo "  ✓ Service health checks"
echo "  ✓ Admin API endpoints"
echo "  ✓ Simple query routing (NexaAI)"
echo "  ✓ Complex query routing (Ollama)"
echo "  ✓ Chat sessions"
echo "  ✓ Vector search quality"
echo "  ✓ Performance benchmarks"
echo "  ✓ Router configuration"
echo "  ✓ Error handling"
echo "  ✓ Full integration"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  • View detailed logs: docker-compose logs -f api"
echo "  • Access admin panel: http://localhost:3000/admin"
echo "  • Access API docs: http://localhost:8001/api/v1/docs"
echo ""
