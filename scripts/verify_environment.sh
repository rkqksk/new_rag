#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

echo "🔍 RAG Enterprise 환경 검증"
echo "=================================="
echo ""

# 1. Python 버전 확인
echo "📌 Python 버전"
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    if [[ $PYTHON_VERSION == 3.11.* ]]; then
        echo -e "${GREEN}✅ Python: $PYTHON_VERSION${NC}"
    else
        echo -e "${RED}❌ Python: $PYTHON_VERSION (요구사항: 3.11.x)${NC}"
        ((ERRORS++))
    fi
else
    echo -e "${RED}❌ Python이 설치되지 않았습니다${NC}"
    ((ERRORS++))
fi
echo ""

# 2. 가상환경 확인
echo "📌 가상환경"
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}✅ 가상환경: 활성화됨${NC}"
    echo "   경로: $VIRTUAL_ENV"
else
    echo -e "${YELLOW}⚠️  가상환경: 비활성화${NC}"
    echo "   다음 명령어로 활성화하세요:"
    echo "   source .venv/bin/activate"
    ((WARNINGS++))
fi
echo ""

# 3. PYTHONPATH 확인
echo "📌 PYTHONPATH"
if [[ "$PYTHONPATH" == *"$PROJECT_ROOT"* ]]; then
    echo -e "${GREEN}✅ PYTHONPATH: 설정됨${NC}"
    echo "   $PYTHONPATH"
else
    echo -e "${YELLOW}⚠️  PYTHONPATH: 설정되지 않음${NC}"
    echo "   다음 명령어를 실행하세요:"
    echo "   export PYTHONPATH=$PROJECT_ROOT:\$PYTHONPATH"
    ((WARNINGS++))
fi
echo ""

# 4. .env 파일 확인
echo "📌 .env 파일"
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env: 존재${NC}"

    # 4.1 필수 환경 변수 확인
    source .env 2>/dev/null

    # QDRANT_HOST
    if [ -n "$QDRANT_HOST" ]; then
        echo -e "   ${GREEN}✅ QDRANT_HOST=$QDRANT_HOST${NC}"
    else
        echo -e "   ${RED}❌ QDRANT_HOST: 설정되지 않음${NC}"
        ((ERRORS++))
    fi

    # USE_VECTOR_RAG
    if [ -n "$USE_VECTOR_RAG" ]; then
        echo -e "   ${GREEN}✅ USE_VECTOR_RAG=$USE_VECTOR_RAG${NC}"
    else
        echo -e "   ${YELLOW}⚠️  USE_VECTOR_RAG: 설정되지 않음${NC}"
        ((WARNINGS++))
    fi

    # QDRANT_COLLECTION
    if [ -n "$QDRANT_COLLECTION" ]; then
        echo -e "   ${GREEN}✅ QDRANT_COLLECTION=$QDRANT_COLLECTION${NC}"
    else
        echo -e "   ${RED}❌ QDRANT_COLLECTION: 설정되지 않음${NC}"
        ((ERRORS++))
    fi

else
    echo -e "${RED}❌ .env: 존재하지 않음${NC}"
    echo "   다음 명령어로 생성하세요:"
    echo "   ./scripts/setup_dev_environment.sh"
    ((ERRORS++))
fi
echo ""

# 5. Qdrant 실행 확인
echo "📌 Qdrant"
QDRANT_HOST=${QDRANT_HOST:-localhost}
QDRANT_PORT=${QDRANT_HTTP_PORT:-6333}

if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$QDRANT_HOST:$QDRANT_PORT" 2>/dev/null)
    if [[ "$HTTP_CODE" == "200" ]] || [[ "$HTTP_CODE" == "404" ]]; then
        echo -e "${GREEN}✅ Qdrant: 실행 중 (http://$QDRANT_HOST:$QDRANT_PORT)${NC}"

        # 5.1 Collection 확인
        COLLECTION_NAME=${QDRANT_COLLECTION:-onehago_v2}
        COLLECTION_INFO=$(curl -s "http://$QDRANT_HOST:$QDRANT_PORT/collections/$COLLECTION_NAME" 2>/dev/null)

        if echo "$COLLECTION_INFO" | grep -q "\"status\":\"ok\""; then
            # Vector 개수 추출
            VECTOR_COUNT=$(echo "$COLLECTION_INFO" | grep -o '"points_count":[0-9]*' | cut -d':' -f2)
            echo -e "   ${GREEN}✅ Collection '$COLLECTION_NAME': 존재 ($VECTOR_COUNT vectors)${NC}"
        else
            echo -e "   ${YELLOW}⚠️  Collection '$COLLECTION_NAME': 존재하지 않음${NC}"
            echo "   데이터 준비 필요:"
            echo "   ./scripts/prepare_data.sh --sample"
            ((WARNINGS++))
        fi
    else
        echo -e "${RED}❌ Qdrant: 실행되지 않음${NC}"
        echo "   다음 명령어로 시작하세요:"
        echo "   docker-compose up -d"
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠️  curl이 설치되지 않아 확인 불가${NC}"
    ((WARNINGS++))
fi
echo ""

# 6. Python 패키지 확인
echo "📌 Python 패키지"

check_package() {
    local package=$1
    if python -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}✅ $package${NC}"
    else
        echo -e "${RED}❌ $package: 설치되지 않음${NC}"
        ((ERRORS++))
    fi
}

check_package "fastapi"
check_package "qdrant_client"
check_package "sentence_transformers"
check_package "pydantic"
check_package "dotenv"

echo ""

# 최종 결과
echo "=================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ 모든 검증 통과!${NC}"
    echo "=================================="
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  경고 $WARNINGS개${NC}"
    echo "=================================="
    echo ""
    echo "환경은 작동하지만 일부 설정을 권장합니다."
    exit 0
else
    echo -e "${RED}❌ 오류 $ERRORS개, 경고 $WARNINGS개${NC}"
    echo "=================================="
    echo ""
    echo "환경 설정을 완료하세요:"
    echo "  ./scripts/setup_dev_environment.sh"
    exit 1
fi
