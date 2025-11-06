#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

show_help() {
    echo "RAG Enterprise - 데이터 준비 스크립트"
    echo ""
    echo "사용법:"
    echo "  $0 [OPTION]"
    echo ""
    echo "옵션:"
    echo "  --snapshot        Qdrant snapshot 복원 (빠름, 5분)"
    echo "  --embedding       원본 데이터에서 임베딩 (느림, 2-3시간)"
    echo "  --sample          샘플 데이터 생성 (테스트용, 1분)"
    echo "  --help            이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  $0 --snapshot     # Snapshot 복원 (권장)"
    echo "  $0 --sample       # 테스트용 샘플 데이터"
    echo ""
}

check_prerequisites() {
    echo -e "${GREEN}📌 사전 요구사항 확인${NC}"

    # Python 확인
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ Python이 설치되지 않았습니다${NC}"
        exit 1
    fi
    echo -e "✅ Python: $(python --version)"

    # Qdrant 확인
    QDRANT_HOST=${QDRANT_HOST:-localhost}
    QDRANT_PORT=${QDRANT_HTTP_PORT:-6333}

    if command -v curl &> /dev/null; then
        if curl -s -o /dev/null -w "%{http_code}" "http://$QDRANT_HOST:$QDRANT_PORT" | grep -q "200\|404"; then
            echo -e "✅ Qdrant: 실행 중 (http://$QDRANT_HOST:$QDRANT_PORT)"
        else
            echo -e "${YELLOW}⚠️  Qdrant가 실행되지 않았습니다${NC}"
            echo "   다음 명령어로 시작하세요:"
            echo "   docker-compose up -d"
            exit 1
        fi
    fi

    echo ""
}

prepare_snapshot() {
    echo -e "${GREEN}📦 Option 1: Qdrant Snapshot 복원${NC}"
    echo "예상 시간: 5분"
    echo ""

    check_prerequisites

    # Snapshot 파일 경로
    SNAPSHOT_FILE="${1:-}"
    if [ -z "$SNAPSHOT_FILE" ]; then
        echo -e "${YELLOW}사용법: $0 --snapshot <snapshot-file-path>${NC}"
        echo ""
        echo "사용 가능한 Snapshot 파일:"
        if [ -d "data/snapshots" ]; then
            ls -lh data/snapshots/*.snapshot 2>/dev/null || echo "  (없음)"
        else
            echo "  data/snapshots/ 디렉토리가 없습니다"
        fi
        echo ""
        echo "Snapshot 생성 방법:"
        echo "  ./scripts/create_snapshot.sh onehago_v2"
        exit 1
    fi

    # 파일 존재 확인
    if [ ! -f "$SNAPSHOT_FILE" ]; then
        echo -e "${RED}❌ Snapshot 파일을 찾을 수 없습니다: $SNAPSHOT_FILE${NC}"
        exit 1
    fi

    FILE_SIZE=$(ls -lh "$SNAPSHOT_FILE" | awk '{print $5}')
    echo "✅ Snapshot 파일: $SNAPSHOT_FILE ($FILE_SIZE)"
    echo ""

    # Collection 이름 (파일명에서 추출)
    COLLECTION_NAME=$(basename "$SNAPSHOT_FILE" | sed 's/_[0-9]*\.snapshot$//')
    echo "📌 Collection: $COLLECTION_NAME"
    echo ""

    # 기존 Collection 삭제 확인
    echo "⚠️  기존 Collection을 삭제하고 복원합니다"
    read -p "계속하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "취소되었습니다"
        exit 0
    fi

    # Collection 삭제
    echo "🗑️  기존 Collection 삭제 중..."
    curl -s -X DELETE "http://$QDRANT_HOST:$QDRANT_PORT/collections/$COLLECTION_NAME" >/dev/null 2>&1 || true
    sleep 2
    echo "✅ 삭제 완료"
    echo ""

    # Snapshot 업로드
    echo "📤 Snapshot 업로드 중..."
    UPLOAD_RESPONSE=$(curl -s -X POST \
        "http://$QDRANT_HOST:$QDRANT_PORT/collections/$COLLECTION_NAME/snapshots/upload" \
        -H "Content-Type: multipart/form-data" \
        -F "snapshot=@$SNAPSHOT_FILE")

    if echo "$UPLOAD_RESPONSE" | grep -q '"status":"ok"'; then
        echo -e "${GREEN}✅ 업로드 완료${NC}"
    else
        echo -e "${RED}❌ 업로드 실패${NC}"
        echo "$UPLOAD_RESPONSE"
        exit 1
    fi
    echo ""

    # 복원 대기
    echo "⏳ Collection 복원 중..."
    sleep 5

    # 검증
    echo "🔍 복원 검증 중..."
    COLLECTION_INFO=$(curl -s "http://$QDRANT_HOST:$QDRANT_PORT/collections/$COLLECTION_NAME")

    if echo "$COLLECTION_INFO" | grep -q '"status":"ok"'; then
        VECTOR_COUNT=$(echo "$COLLECTION_INFO" | grep -o '"points_count":[0-9]*' | cut -d':' -f2)
        echo -e "${GREEN}✅ 복원 성공!${NC}"
        echo "   Collection: $COLLECTION_NAME"
        echo "   Vectors: $VECTOR_COUNT"
    else
        echo -e "${RED}❌ 복원 실패${NC}"
        echo "$COLLECTION_INFO"
        exit 1
    fi
    echo ""

    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}✅ Snapshot 복원 완료!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo "다음 단계:"
    echo "  ./scripts/verify_data.sh"
}

prepare_embedding() {
    echo -e "${GREEN}🔨 Option 2: 원본 데이터에서 임베딩${NC}"
    echo "예상 시간: 2-3시간"
    echo ""

    check_prerequisites

    # 데이터 디렉토리 확인
    if [ ! -d "data" ]; then
        echo -e "${YELLOW}⚠️  data/ 디렉토리가 없습니다${NC}"
        mkdir -p data
        echo "✅ data/ 디렉토리 생성됨"
    fi

    # 원본 데이터 확인
    CRAWLED_DATA="data/onehago_crawled.json"
    if [ ! -f "$CRAWLED_DATA" ]; then
        echo -e "${RED}❌ 원본 데이터 파일이 없습니다: $CRAWLED_DATA${NC}"
        echo ""
        echo "다음 단계를 따르세요:"
        echo "1. 크롤러 실행 또는"
        echo "2. 기존 크롤링 데이터 다운로드"
        echo ""
        echo "자세한 내용은 docs/DATA_PREPARATION.md를 참조하세요"
        exit 1
    fi

    echo "✅ 원본 데이터 파일 확인: $CRAWLED_DATA"

    # 임베딩 스크립트 확인
    EMBED_SCRIPT="scripts/embed_products.py"
    if [ -f "$EMBED_SCRIPT" ]; then
        echo "🚀 임베딩 시작..."
        python "$EMBED_SCRIPT"
        echo -e "${GREEN}✅ 임베딩 완료!${NC}"
    else
        echo -e "${YELLOW}⚠️  임베딩 스크립트를 찾을 수 없습니다: $EMBED_SCRIPT${NC}"
        echo ""
        echo "Python에서 직접 실행:"
        echo ""
        cat << 'PYEOF'
from src.core.rag_pipeline import RAGPipeline
import json

# 1. 데이터 로드
with open('data/onehago_crawled.json', 'r') as f:
    products = json.load(f)

# 2. RAG Pipeline 초기화
pipeline = RAGPipeline(collection_name='onehago_v2')

# 3. 임베딩 및 업로드
documents = [
    {
        'text': f"{p['name']} {p.get('description', '')}",
        'metadata': p
    }
    for p in products
]

pipeline.ingest_documents(documents)
print(f"✅ {len(documents)}개 제품 임베딩 완료!")
PYEOF
    fi
}

prepare_sample() {
    echo -e "${GREEN}🧪 Option 3: 샘플 데이터 생성${NC}"
    echo "예상 시간: 1분"
    echo "용도: 개발 및 테스트"
    echo ""

    check_prerequisites

    echo "🚀 샘플 데이터 생성 중..."

    # Python으로 샘플 데이터 생성
    python << 'PYEOF'
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import random

# Qdrant 연결
client = QdrantClient(url="http://localhost:6333")

# Collection 생성 또는 재생성
collection_name = "onehago_v2"

try:
    client.delete_collection(collection_name)
    print(f"✅ 기존 collection '{collection_name}' 삭제됨")
except:
    pass

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)
print(f"✅ Collection '{collection_name}' 생성됨")

# 샘플 제품 데이터
sample_products = [
    {
        "name": "Sample Bottle 100ml",
        "category": "Bottle",
        "material": "PET",
        "volume": "100ml",
        "description": "투명한 PET 소재의 100ml 용량 보틀"
    },
    {
        "name": "Sample Jar 50ml",
        "category": "Jar",
        "material": "PP",
        "volume": "50ml",
        "description": "고급 PP 소재의 50ml 용량 크림 용기"
    },
    {
        "name": "Sample Pump Cap",
        "category": "Cap",
        "material": "ABS",
        "volume": "N/A",
        "description": "내구성 좋은 ABS 소재 펌프 캡"
    }
]

# 샘플 벡터 생성 (실제로는 embedding model 사용)
points = []
for idx, product in enumerate(sample_products):
    # 랜덤 벡터 (384 차원)
    vector = [random.random() for _ in range(384)]

    points.append(PointStruct(
        id=idx,
        vector=vector,
        payload=product
    ))

client.upsert(
    collection_name=collection_name,
    points=points
)

print(f"✅ {len(sample_products)}개 샘플 제품 업로드 완료!")
print("")
print("샘플 데이터:")
for p in sample_products:
    print(f"  - {p['name']} ({p['category']}, {p['volume']})")
PYEOF

    echo ""
    echo -e "${GREEN}✅ 샘플 데이터 생성 완료!${NC}"
    echo ""
    echo "다음 명령어로 확인:"
    echo "  ./scripts/verify_data.sh"
}

# 메인 로직
case "${1:-}" in
    --snapshot)
        prepare_snapshot "$2"
        ;;
    --embedding)
        prepare_embedding
        ;;
    --sample)
        prepare_sample
        ;;
    --help)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
