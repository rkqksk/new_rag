#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

echo "🔍 Qdrant 데이터 검증"
echo "=================================="
echo ""

# .env 로드
if [ -f ".env" ]; then
    source .env
fi

QDRANT_HOST=${QDRANT_HOST:-localhost}
QDRANT_PORT=${QDRANT_HTTP_PORT:-6333}
COLLECTION_NAME=${QDRANT_COLLECTION:-onehago_v2}

# 1. Qdrant 실행 확인
echo "📌 Qdrant 연결"
if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ curl이 설치되지 않았습니다${NC}"
    exit 1
fi

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$QDRANT_HOST:$QDRANT_PORT" 2>/dev/null)
if [[ "$HTTP_CODE" == "200" ]] || [[ "$HTTP_CODE" == "404" ]]; then
    echo -e "${GREEN}✅ Qdrant: 실행 중 (http://$QDRANT_HOST:$QDRANT_PORT)${NC}"
else
    echo -e "${RED}❌ Qdrant가 실행되지 않았습니다${NC}"
    echo "   다음 명령어로 시작하세요:"
    echo "   docker-compose up -d"
    exit 1
fi
echo ""

# 2. Collection 존재 확인
echo "📌 Collection: $COLLECTION_NAME"
COLLECTION_INFO=$(curl -s "http://$QDRANT_HOST:$QDRANT_PORT/collections/$COLLECTION_NAME" 2>/dev/null)

if ! echo "$COLLECTION_INFO" | grep -q "\"status\":\"ok\""; then
    echo -e "${RED}❌ Collection '$COLLECTION_NAME'이 존재하지 않습니다${NC}"
    echo ""
    echo "데이터 준비 필요:"
    echo "  ./scripts/prepare_data.sh --sample    # 샘플 데이터 (테스트용)"
    echo "  ./scripts/prepare_data.sh --snapshot  # Snapshot 복원 (실제 데이터)"
    exit 1
fi

echo -e "${GREEN}✅ Collection: 존재${NC}"
echo ""

# 3. Vector 개수 확인
echo "📌 Vector 개수"
VECTOR_COUNT=$(echo "$COLLECTION_INFO" | grep -o '"points_count":[0-9]*' | cut -d':' -f2)

if [ -z "$VECTOR_COUNT" ]; then
    echo -e "${RED}❌ Vector 개수를 가져올 수 없습니다${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✅ Vector 개수: $VECTOR_COUNT${NC}"

    # 예상 개수와 비교 (샘플 데이터: 3개, 실제 데이터: 22,870개)
    if [ "$VECTOR_COUNT" -lt 3 ]; then
        echo -e "   ${RED}⚠️  Vector가 너무 적습니다 (최소: 3개)${NC}"
        ((WARNINGS++))
    elif [ "$VECTOR_COUNT" -eq 3 ]; then
        echo -e "   ${YELLOW}ℹ️  샘플 데이터 모드${NC}"
    elif [ "$VECTOR_COUNT" -gt 20000 ]; then
        echo -e "   ${GREEN}ℹ️  프로덕션 데이터 모드 (onehago)${NC}"
    fi
fi
echo ""

# 4. Dimension 확인
echo "📌 Vector Dimension"
VECTOR_SIZE=$(echo "$COLLECTION_INFO" | grep -o '"size":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$VECTOR_SIZE" ]; then
    echo -e "${RED}❌ Dimension을 가져올 수 없습니다${NC}"
    ((ERRORS++))
else
    if [ "$VECTOR_SIZE" -eq 384 ]; then
        echo -e "${GREEN}✅ Dimension: $VECTOR_SIZE (sentence-transformers/all-MiniLM-L6-v2)${NC}"
    else
        echo -e "${YELLOW}⚠️  Dimension: $VECTOR_SIZE (예상: 384)${NC}"
        ((WARNINGS++))
    fi
fi
echo ""

# 5. 샘플 검색 테스트
echo "📌 검색 테스트"

# Python으로 샘플 검색 실행
SEARCH_RESULT=$(python << 'PYEOF'
import sys
import os
from qdrant_client import QdrantClient

try:
    qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
    qdrant_port = os.getenv('QDRANT_HTTP_PORT', '6333')
    collection_name = os.getenv('QDRANT_COLLECTION', 'onehago_v2')

    client = QdrantClient(url=f"http://{qdrant_host}:{qdrant_port}")

    # 첫 번째 포인트 가져오기
    points = client.scroll(
        collection_name=collection_name,
        limit=1,
        with_payload=True,
        with_vectors=False
    )[0]

    if not points:
        print("ERROR: No points found")
        sys.exit(1)

    point = points[0]

    # Payload 필드 확인
    payload_keys = list(point.payload.keys()) if point.payload else []

    print(f"SUCCESS: {len(payload_keys)} fields")
    print("FIELDS: " + ", ".join(payload_keys[:5]))  # 처음 5개만

    # 샘플 데이터 표시
    if 'name' in payload_keys:
        print(f"SAMPLE_NAME: {point.payload.get('name', 'N/A')}")
    if 'category' in payload_keys:
        print(f"SAMPLE_CATEGORY: {point.payload.get('category', 'N/A')}")

except Exception as e:
    print(f"ERROR: {str(e)}")
    sys.exit(1)
PYEOF
)

SEARCH_EXIT_CODE=$?

if [ $SEARCH_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ 검색 성공${NC}"

    # 결과 파싱
    FIELD_COUNT=$(echo "$SEARCH_RESULT" | grep "SUCCESS:" | cut -d':' -f2 | xargs)
    FIELDS=$(echo "$SEARCH_RESULT" | grep "FIELDS:" | cut -d':' -f2- | xargs)
    SAMPLE_NAME=$(echo "$SEARCH_RESULT" | grep "SAMPLE_NAME:" | cut -d':' -f2- | xargs)
    SAMPLE_CATEGORY=$(echo "$SEARCH_RESULT" | grep "SAMPLE_CATEGORY:" | cut -d':' -f2- | xargs)

    echo "   Payload 필드: $FIELD_COUNT개"
    echo "   필드 예시: $FIELDS"

    if [ -n "$SAMPLE_NAME" ]; then
        echo ""
        echo "   ${BLUE}샘플 데이터:${NC}"
        echo "   - 이름: $SAMPLE_NAME"
        [ -n "$SAMPLE_CATEGORY" ] && echo "   - 카테고리: $SAMPLE_CATEGORY"
    fi
else
    echo -e "${RED}❌ 검색 실패${NC}"
    echo "$SEARCH_RESULT"
    ((ERRORS++))
fi
echo ""

# 6. Distance 메트릭 확인
echo "📌 Distance Metric"
DISTANCE=$(echo "$COLLECTION_INFO" | grep -o '"distance":"[^"]*"' | cut -d'"' -f4)

if [ -n "$DISTANCE" ]; then
    echo -e "${GREEN}✅ Distance: $DISTANCE${NC}"

    if [ "$DISTANCE" != "Cosine" ]; then
        echo -e "   ${YELLOW}⚠️  권장 Distance: Cosine (현재: $DISTANCE)${NC}"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠️  Distance를 가져올 수 없습니다${NC}"
    ((WARNINGS++))
fi
echo ""

# 최종 결과
echo "=================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ 모든 데이터 검증 통과!${NC}"
    echo "=================================="
    echo ""
    echo "다음 단계:"
    echo "  python scripts/run_chat_server.py"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  경고 $WARNINGS개${NC}"
    echo "=================================="
    echo ""
    echo "데이터는 사용 가능하지만 일부 권장사항이 있습니다."
    exit 0
else
    echo -e "${RED}❌ 오류 $ERRORS개, 경고 $WARNINGS개${NC}"
    echo "=================================="
    echo ""
    echo "데이터 준비 필요:"
    echo "  ./scripts/prepare_data.sh --sample"
    exit 1
fi
