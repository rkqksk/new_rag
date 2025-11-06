#!/bin/bash
set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 기본 설정
QDRANT_HOST=${QDRANT_HOST:-localhost}
QDRANT_PORT=${QDRANT_HTTP_PORT:-6333}
COLLECTION_NAME=${1:-onehago_v2}
SNAPSHOT_DIR="data/snapshots"

echo -e "${BLUE}📦 Qdrant Snapshot 생성 도구${NC}"
echo "=================================="
echo ""

# 1. Qdrant 연결 확인
echo "📌 Qdrant 연결 확인..."
if ! curl -s -o /dev/null -w "%{http_code}" "http://$QDRANT_HOST:$QDRANT_PORT" | grep -q "200\|404"; then
    echo -e "${RED}❌ Qdrant가 실행되지 않았습니다${NC}"
    echo "   다음 명령어로 시작하세요:"
    echo "   docker-compose up -d qdrant"
    exit 1
fi
echo -e "${GREEN}✅ Qdrant 실행 중${NC}"
echo ""

# 2. Collection 존재 확인
echo "📌 Collection '$COLLECTION_NAME' 확인..."
COLLECTION_INFO=$(curl -s "http://$QDRANT_HOST:$QDRANT_PORT/collections/$COLLECTION_NAME")

if ! echo "$COLLECTION_INFO" | grep -q '"status":"ok"'; then
    echo -e "${RED}❌ Collection '$COLLECTION_NAME'이 존재하지 않습니다${NC}"
    echo ""
    echo "사용 가능한 Collections:"
    curl -s "http://$QDRANT_HOST:$QDRANT_PORT/collections" | grep -o '"name":"[^"]*"' | cut -d'"' -f4
    exit 1
fi

VECTOR_COUNT=$(echo "$COLLECTION_INFO" | grep -o '"points_count":[0-9]*' | cut -d':' -f2)
echo -e "${GREEN}✅ Collection 존재: $VECTOR_COUNT vectors${NC}"
echo ""

# 3. Snapshot 디렉토리 생성
echo "📌 Snapshot 디렉토리 준비..."
mkdir -p "$SNAPSHOT_DIR"
echo -e "${GREEN}✅ 디렉토리: $SNAPSHOT_DIR${NC}"
echo ""

# 4. Snapshot 생성
echo "📌 Snapshot 생성 중..."
echo "   Collection: $COLLECTION_NAME"
echo "   Vectors: $VECTOR_COUNT"
echo ""

SNAPSHOT_RESPONSE=$(curl -s -X POST "http://$QDRANT_HOST:$QDRANT_PORT/collections/$COLLECTION_NAME/snapshots")

if echo "$SNAPSHOT_RESPONSE" | grep -q '"status":"ok"'; then
    SNAPSHOT_NAME=$(echo "$SNAPSHOT_RESPONSE" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✅ Snapshot 생성됨: $SNAPSHOT_NAME${NC}"
else
    echo -e "${RED}❌ Snapshot 생성 실패${NC}"
    echo "$SNAPSHOT_RESPONSE"
    exit 1
fi
echo ""

# 5. Snapshot 다운로드
echo "📌 Snapshot 다운로드 중..."
OUTPUT_FILE="$SNAPSHOT_DIR/${COLLECTION_NAME}_$(date +%Y%m%d_%H%M%S).snapshot"

if curl -s "http://$QDRANT_HOST:$QDRANT_PORT/collections/$COLLECTION_NAME/snapshots/$SNAPSHOT_NAME" \
    --output "$OUTPUT_FILE"; then

    FILE_SIZE=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')
    echo -e "${GREEN}✅ 다운로드 완료${NC}"
    echo "   파일: $OUTPUT_FILE"
    echo "   크기: $FILE_SIZE"
else
    echo -e "${RED}❌ 다운로드 실패${NC}"
    exit 1
fi
echo ""

# 6. 검증
echo "📌 Snapshot 검증..."
if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE_BYTES=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)

    if [ "$FILE_SIZE_BYTES" -gt 1000 ]; then
        echo -e "${GREEN}✅ 유효한 Snapshot 파일${NC}"
    else
        echo -e "${YELLOW}⚠️  파일 크기가 작습니다 (${FILE_SIZE_BYTES} bytes)${NC}"
    fi
else
    echo -e "${RED}❌ 파일이 생성되지 않았습니다${NC}"
    exit 1
fi
echo ""

# 7. 완료 안내
echo "=================================="
echo -e "${GREEN}✅ Snapshot 생성 완료!${NC}"
echo "=================================="
echo ""
echo -e "${BLUE}다음 단계:${NC}"
echo ""
echo "1. Snapshot 파일 확인:"
echo "   ls -lh $OUTPUT_FILE"
echo ""
echo "2. 다른 환경에서 복원:"
echo "   ./scripts/prepare_data.sh --snapshot $OUTPUT_FILE"
echo ""
echo "3. (선택) Google Drive 업로드:"
echo "   - 파일을 Google Drive에 업로드"
echo "   - 공유 링크 생성"
echo "   - docs/DATA_PREPARATION.md에 링크 추가"
echo ""
echo -e "${YELLOW}참고:${NC}"
echo "- Snapshot 파일은 .gitignore에 포함되어 Git에 커밋되지 않습니다"
echo "- 팀원과 공유하려면 Google Drive 또는 S3 사용을 권장합니다"
echo "- Snapshot 크기: 약 $(echo "scale=1; $FILE_SIZE_BYTES / 1024 / 1024" | bc 2>/dev/null || echo "?")MB"
echo ""
