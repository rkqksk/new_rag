#!/bin/bash
# 로컬 환경 설정 가이드
# Mac에서 실행할 명령어들

echo "=============================================="
echo "🚀 Onehago 24,745 데이터 복원 가이드"
echo "=============================================="
echo ""

echo "📍 Step 1: JSON 데이터 위치 확인"
echo "----------------------------------------------"
echo ""
echo "Mac 로컬에서 실행:"
echo ""
echo "# 1-1. 프로젝트 디렉토리로 이동"
echo "cd ~/Project/rag-enterprise"
echo ""
echo "# 1-2. JSON 데이터 확인"
echo "ls -lh data/onehago/"
echo "# 또는"
echo "ls -lh data/crawled_products/"
echo ""
echo "# 1-3. JSON 파일 개수 확인"
echo "find data/onehago -name '*.json' | wc -l"
echo "# 예상 출력: 24745 (또는 비슷한 숫자)"
echo ""
echo "📌 만약 JSON 파일이 없다면:"
echo "   - 크롤러를 실행해야 함"
echo "   - 또는 백업에서 복원"
echo ""

echo "=============================================="
echo "📍 Step 2: Qdrant 시작 (Docker)"
echo "----------------------------------------------"
echo ""
echo "# 2-1. Docker 확인"
echo "docker --version"
echo ""
echo "# 2-2. Colima 시작 (Mac에서 Docker 실행)"
echo "colima start --cpu 4 --memory 8"
echo ""
echo "# 2-3. Qdrant 시작"
echo "docker-compose up -d qdrant"
echo ""
echo "# 2-4. Qdrant 확인"
echo "curl http://localhost:6333"
echo "# 예상 출력: {\"title\":\"qdrant - vector search engine\", ...}"
echo ""
echo "# 2-5. 기존 collections 확인"
echo "curl -s http://localhost:6333/collections | jq '.result.collections'"
echo ""

echo "=============================================="
echo "📍 Step 3: onehago_v2 Collection 생성"
echo "----------------------------------------------"
echo ""
echo "# 3-1. Collection이 이미 있는지 확인"
echo "curl -s http://localhost:6333/collections/onehago_v2 | jq '.result.points_count'"
echo ""
echo "# 3-2. 만약 collection이 없다면 생성"
cat << 'EOF'
curl -X PUT "http://localhost:6333/collections/onehago_v2" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    },
    "optimizers_config": {
      "indexing_threshold": 10000
    }
  }'
EOF
echo ""
echo "# 3-3. Collection 생성 확인"
echo "curl -s http://localhost:6333/collections/onehago_v2 | jq '.result'"
echo ""

echo "=============================================="
echo "📍 Step 4: 임베딩 생성 (2-3시간 소요)"
echo "----------------------------------------------"
echo ""
echo "옵션 A: 기존 Snapshot 사용 (5분) - 권장!"
echo "----------------------------------------------"
echo "# 4A-1. Snapshot 파일이 있는지 확인"
echo "ls -lh data/snapshots/"
echo ""
echo "# 4A-2. Snapshot 복원"
echo "./scripts/prepare_data.sh --snapshot data/snapshots/onehago_v2_*.snapshot"
echo ""
echo ""
echo "옵션 B: 처음부터 임베딩 생성 (2-3시간)"
echo "----------------------------------------------"
echo "# 4B-1. Python 환경 활성화"
echo "source .venv/bin/activate  # 또는 해당 venv"
echo ""
echo "# 4B-2. 필요한 패키지 설치"
echo "pip install sentence-transformers qdrant-client"
echo ""
echo "# 4B-3. 임베딩 스크립트 실행"
cat << 'EOF'
python scripts/embed_onehago_products.py \
  --input data/onehago/*.json \
  --collection onehago_v2 \
  --batch-size 100
EOF
echo ""
echo "# 진행 상황 모니터링"
echo "curl -s http://localhost:6333/collections/onehago_v2 | jq '.result.points_count'"
echo "# 출력이 점점 증가: 100, 500, 1000, ... 22870"
echo ""

echo "=============================================="
echo "📍 Step 5: Snapshot 생성 (재사용을 위해)"
echo "----------------------------------------------"
echo ""
echo "# 5-1. Snapshot 생성"
echo "./scripts/create_snapshot.sh onehago_v2"
echo ""
echo "# 5-2. Snapshot 파일 확인"
echo "ls -lh data/snapshots/onehago_v2_*.snapshot"
echo "# 예상 크기: ~245MB"
echo ""

echo "=============================================="
echo "📍 Step 6: Claude Code CLI로 데이터 전달"
echo "----------------------------------------------"
echo ""
echo "방법 1: Snapshot 파일 복사 (권장)"
echo "----------------------------------------------"
echo "# 6-1. Snapshot을 Claude Code CLI 환경으로 복사"
echo "# (실제 경로는 환경에 따라 다름)"
echo "cp data/snapshots/onehago_v2_*.snapshot /path/to/claude-code-cli/data/snapshots/"
echo ""
echo ""
echo "방법 2: 직접 Qdrant 연결 (로컬 네트워크)"
echo "----------------------------------------------"
echo "# Claude Code CLI에서 Mac 로컬 Qdrant에 연결"
echo "# .env 파일 설정:"
cat << 'EOF'
QDRANT_HOST=host.docker.internal  # Mac Docker → 호스트
QDRANT_PORT=6333
EOF
echo ""
echo ""
echo "방법 3: Google Drive 공유"
echo "----------------------------------------------"
echo "# 6-1. Snapshot을 Google Drive에 업로드"
echo "# 6-2. Claude Code CLI에서 다운로드"
echo "# 6-3. Snapshot 복원"
echo ""

echo "=============================================="
echo "📍 Step 7: 검증"
echo "----------------------------------------------"
echo ""
echo "# 7-1. Collection 확인"
echo "curl -s http://localhost:6333/collections/onehago_v2 | jq '.result'"
echo ""
echo "# 7-2. Vector 개수 확인"
echo "curl -s http://localhost:6333/collections/onehago_v2 | jq '.result.points_count'"
echo "# 예상 출력: 22870"
echo ""
echo "# 7-3. 샘플 검색 테스트"
cat << 'EOF'
curl -X POST "http://localhost:6333/collections/onehago_v2/points/search" \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ...],  # 384 dimensions
    "limit": 5
  }'
EOF
echo ""

echo "=============================================="
echo "✅ 설정 완료!"
echo "=============================================="
echo ""
echo "다음 단계:"
echo "1. Phase 4.3 (Excel/CSV) 테스트"
echo "2. Phase 8.2 (Caching) 성능 측정"
echo "3. 대용량 데이터 검색 테스트"
echo ""
