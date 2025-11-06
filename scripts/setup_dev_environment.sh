#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 RAG Enterprise 개발 환경 설정"
echo "=================================="
echo ""

# 1. Python 버전 확인
echo "📌 Step 1: Python 버전 확인"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if [[ $PYTHON_VERSION == 3.11.* ]]; then
    echo "✅ Python $PYTHON_VERSION (요구사항: 3.11.x)"
else
    echo "❌ Python $PYTHON_VERSION 감지됨"
    echo "   요구사항: Python 3.11.x"
    echo "   설치 방법:"
    echo "     - Mac: brew install python@3.11"
    echo "     - Ubuntu: sudo apt install python3.11"
    exit 1
fi
echo ""

# 2. .venv 가상환경 생성
echo "📌 Step 2: 가상환경 생성"
if [ -d ".venv" ]; then
    echo "ℹ️  .venv 이미 존재함 (건너뜀)"
else
    echo "   .venv 생성 중..."
    python3 -m venv .venv
    echo "✅ .venv 생성 완료"
fi
echo ""

# 3. 가상환경 활성화 안내
echo "📌 Step 3: 가상환경 활성화"
echo "   다음 명령어를 실행하세요:"
echo "   source .venv/bin/activate"
echo ""
echo "   계속하려면 아무 키나 누르세요..."
read -n 1 -s
echo ""

# 가상환경 활성화 확인
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  가상환경이 활성화되지 않았습니다"
    echo "   다음 명령어를 실행한 후 다시 이 스크립트를 실행하세요:"
    echo "   source .venv/bin/activate && ./scripts/setup_dev_environment.sh"
    exit 1
else
    echo "✅ 가상환경 활성화됨: $VIRTUAL_ENV"
fi
echo ""

# 4. pip 업그레이드
echo "📌 Step 4: pip 업그레이드"
python -m pip install --upgrade pip --quiet
echo "✅ pip 업그레이드 완료"
echo ""

# 5. 의존성 설치
echo "📌 Step 5: 의존성 설치"
if [ -f "requirements-lock.txt" ]; then
    echo "   requirements-lock.txt로 설치 중 (정확한 버전)..."
    pip install -r requirements-lock.txt --quiet
    echo "✅ requirements-lock.txt 설치 완료"
else
    echo "   requirements.txt로 설치 중..."
    pip install -r requirements.txt --quiet
    echo "✅ requirements.txt 설치 완료"
fi
echo ""

# 6. .env 파일 확인
echo "📌 Step 6: .env 파일 확인"
if [ -f ".env" ]; then
    echo "✅ .env 파일 존재"

    # 필수 환경 변수 확인
    echo "   필수 환경 변수 확인 중..."
    MISSING_VARS=()

    if ! grep -q "^QDRANT_HOST=" .env; then
        MISSING_VARS+=("QDRANT_HOST")
    fi
    if ! grep -q "^USE_VECTOR_RAG=" .env; then
        MISSING_VARS+=("USE_VECTOR_RAG")
    fi
    if ! grep -q "^QDRANT_COLLECTION=" .env; then
        MISSING_VARS+=("QDRANT_COLLECTION")
    fi

    if [ ${#MISSING_VARS[@]} -gt 0 ]; then
        echo "   ⚠️  다음 환경 변수가 누락되었습니다:"
        for var in "${MISSING_VARS[@]}"; do
            echo "      - $var"
        done
        echo ""
        echo "   .env 파일에 다음 내용을 추가하세요:"
        echo "   QDRANT_HOST=localhost"
        echo "   USE_VECTOR_RAG=true"
        echo "   QDRANT_COLLECTION=onehago_v2"
    else
        echo "   ✅ 모든 필수 환경 변수 확인됨"
    fi
else
    echo "⚠️  .env 파일이 없습니다"
    echo "   템플릿을 생성합니다..."
    cat > .env << 'EOF'
# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_HTTP_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_COLLECTION=onehago_v2

# RAG Configuration
USE_VECTOR_RAG=true

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=qwen2.5:7b-instruct

# API Configuration
API_HOST=0.0.0.0
API_PORT=8001
EOF
    echo "✅ .env 템플릿 생성 완료"
    echo "   필요에 따라 .env 파일을 수정하세요"
fi
echo ""

# 7. PYTHONPATH 설정 안내
echo "📌 Step 7: PYTHONPATH 설정"
echo "   다음 명령어를 실행하거나 ~/.bashrc 또는 ~/.zshrc에 추가하세요:"
echo "   export PYTHONPATH=$PROJECT_ROOT:\$PYTHONPATH"
echo ""
if [[ "$PYTHONPATH" == *"$PROJECT_ROOT"* ]]; then
    echo "✅ PYTHONPATH 이미 설정됨"
else
    echo "⚠️  현재 세션에 PYTHONPATH가 설정되지 않았습니다"
    echo "   다음 명령어를 실행하세요:"
    echo "   export PYTHONPATH=$PROJECT_ROOT:\$PYTHONPATH"
fi
echo ""

# 8. Qdrant 연결 확인
echo "📌 Step 8: Qdrant 연결 확인"
QDRANT_HOST=${QDRANT_HOST:-localhost}
QDRANT_PORT=${QDRANT_HTTP_PORT:-6333}

if command -v curl &> /dev/null; then
    if curl -s -o /dev/null -w "%{http_code}" "http://$QDRANT_HOST:$QDRANT_PORT" | grep -q "200\|404"; then
        echo "✅ Qdrant 실행 중 (http://$QDRANT_HOST:$QDRANT_PORT)"
    else
        echo "⚠️  Qdrant가 실행되지 않았습니다"
        echo "   Docker Compose로 시작:"
        echo "   docker-compose up -d"
        echo "   또는 Colima 사용:"
        echo "   colima start --cpu 4 --memory 8"
        echo "   docker-compose up -d"
    fi
else
    echo "ℹ️  curl이 설치되지 않아 Qdrant 확인을 건너뜁니다"
fi
echo ""

# 9. 완료 메시지
echo "=================================="
echo "✅ 환경 설정 완료!"
echo "=================================="
echo ""
echo "다음 단계:"
echo "1. 환경 검증:"
echo "   ./scripts/verify_environment.sh"
echo ""
echo "2. 데이터 준비 (선택):"
echo "   ./scripts/prepare_data.sh --snapshot    # Qdrant snapshot 복원 (빠름)"
echo "   ./scripts/prepare_data.sh --sample      # 샘플 데이터 생성 (테스트용)"
echo ""
echo "3. 서버 실행:"
echo "   python scripts/run_chat_server.py"
echo ""
echo "4. 프론트엔드 실행 (별도 터미널):"
echo "   cd frontend && python3 -m http.server 8080"
echo ""
