# 🚀 Onehago 24,745개 데이터 복원 - 빠른 시작

**목표**: Mac 로컬 → 24,745 JSON → Qdrant onehago_v2 → 22,870 vectors

**예상 시간**:
- Option A (Snapshot 복원): **5분** ⭐ 권장
- Option B (처음부터 임베딩): **2-3시간**

---

## ⚡ Option A: Snapshot 복원 (5분) - 권장!

### Mac 로컬에서 실행:

```bash
# 1. 프로젝트 디렉토리
cd ~/Project/rag-enterprise

# 2. Colima + Qdrant 시작
colima start --cpu 4 --memory 8
docker-compose up -d qdrant

# 3. Snapshot 파일 확인
ls -lh data/snapshots/onehago_v2_*.snapshot

# 4. Snapshot 복원
./scripts/prepare_data.sh --snapshot data/snapshots/onehago_v2_*.snapshot

# 5. 검증
curl -s http://localhost:6333/collections/onehago_v2 | jq '.result.points_count'
# 출력: 22870
```

**완료!** ✅

---

## 🔨 Option B: 처음부터 임베딩 (2-3시간)

### 사전 요구사항:

```bash
# Python 패키지 설치
pip install sentence-transformers qdrant-client tqdm
```

### Mac 로컬에서 실행:

```bash
# 1. 프로젝트 디렉토리
cd ~/Project/rag-enterprise

# 2. Colima + Qdrant 시작
colima start --cpu 4 --memory 8
docker-compose up -d qdrant

# 3. JSON 파일 확인
ls -lh data/onehago/
# 또는
find data -name "*.json" -path "*onehago*" | wc -l
# 예상: 24745 (또는 비슷한 숫자)

# 4. 임베딩 생성 (2-3시간 소요)
python scripts/embed_onehago_products.py \
  --input "data/onehago/*.json" \
  --collection onehago_v2 \
  --batch-size 100

# 진행 상황 모니터링 (다른 터미널)
watch -n 5 'curl -s http://localhost:6333/collections/onehago_v2 | jq ".result.points_count"'
# 출력이 점점 증가: 100, 500, 1000, ... 22870

# 5. 검증
curl -s http://localhost:6333/collections/onehago_v2 | jq '.result'
```

### Snapshot 생성 (재사용을 위해):

```bash
# Snapshot 생성
./scripts/create_snapshot.sh onehago_v2

# Snapshot 확인
ls -lh data/snapshots/
# 예상: onehago_v2_20251106_*.snapshot (~245MB)
```

---

## 📦 Claude Code CLI로 데이터 전달

### 방법 1: Snapshot 파일 공유

```bash
# Mac 로컬
# 1. Snapshot 위치 확인
ls -lh data/snapshots/onehago_v2_*.snapshot

# 2. Google Drive 업로드 또는 직접 복사

# Claude Code CLI
# 3. Snapshot 다운로드/복사
# 4. 복원
./scripts/prepare_data.sh --snapshot onehago_v2_20251106.snapshot
```

### 방법 2: 직접 Qdrant 연결

```bash
# Claude Code CLI 환경에서 .env 설정
QDRANT_HOST=host.docker.internal  # Mac Docker → 호스트
QDRANT_PORT=6333

# 또는
QDRANT_HOST=192.168.1.x  # Mac 로컬 IP
QDRANT_PORT=6333
```

---

## 🔍 검증 명령어

```bash
# Collection 정보
curl -s http://localhost:6333/collections/onehago_v2 | jq '.result'

# Vector 개수
curl -s http://localhost:6333/collections/onehago_v2 | jq '.result.points_count'
# 예상: 22870

# 샘플 데이터 조회
curl -s http://localhost:6333/collections/onehago_v2/points/1 | jq '.result'

# 모든 collections 확인
curl -s http://localhost:6333/collections | jq '.result.collections[].name'
```

---

## 🧪 검색 테스트

```python
# Python에서 테스트
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

# Collection 확인
collection = client.get_collection("onehago_v2")
print(f"Points: {collection.points_count}")

# 검색 테스트
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
query_vector = model.encode("20파이 캡").tolist()

results = client.search(
    collection_name="onehago_v2",
    query_vector=query_vector,
    limit=5
)

for hit in results:
    print(f"{hit.payload['product_name']}: {hit.score:.4f}")
```

---

## 📊 대용량 데이터로 Phase 4.3 + 8.2 테스트

### Phase 8.2 (Caching) 성능 측정:

```python
from src.core.caching.cached_search import CachedSearchEngine
from src.core.search_engine import SearchEngine

# Original
engine = SearchEngine(collection_name="onehago_v2")

# With caching
cached_engine = CachedSearchEngine(engine)

# Test queries
queries = [
    "20파이 캡",
    "100ml PET 보틀",
    "화장품 용기",
    "펌프",
    "20파이 캡",  # Repeat - should hit cache
]

for query in queries:
    results = cached_engine.search(query, top_k=5)
    print(f"{query}: {len(results)} results")

# Check stats
cached_engine.print_stats()
# Expected:
# - Total Queries: 5
# - Cache Hits: 1 (20파이 캡 repeated)
# - Hit Rate: 20%
# - Cached response: <50ms
# - Uncached response: ~300ms
```

---

## 🎯 다음 단계

1. ✅ Qdrant 시작
2. ✅ 22,870 vectors 복원
3. ✅ Collection 검증
4. 🎯 **Phase 4.3**: Excel/CSV 업로드로 더 많은 데이터 추가
5. 🎯 **Phase 8.2**: 대용량 데이터로 캐싱 성능 측정
6. 🎯 **검색 품질**: 22,870개 중 정확도 테스트

---

## 📝 참고 문서

- **상세 가이드**: `docs/LOCAL_SETUP_ONEHAGO.md`
- **Snapshot 워크플로우**: `docs/SNAPSHOT_WORKFLOW.md`
- **임베딩 스크립트**: `scripts/embed_onehago_products.py`
- **Progress 문서**: `docs/PROGRESS.md`

---

## ❓ 트러블슈팅

### Q: JSON 파일이 없습니다
```bash
# 크롤러 실행 또는 백업에서 복원
# 자세한 내용은 docs/DATA_PREPARATION.md 참조
```

### Q: Qdrant 연결 실패
```bash
# Qdrant 시작 확인
docker ps | grep qdrant

# 재시작
docker-compose restart qdrant

# 로그 확인
docker-compose logs qdrant
```

### Q: 임베딩 속도가 너무 느림
```bash
# GPU 사용 (CUDA available)
# 또는 batch-size 조정
python scripts/embed_onehago_products.py --batch-size 200
```

### Q: Collection이 이미 존재
```bash
# 기존 collection 삭제
curl -X DELETE http://localhost:6333/collections/onehago_v2

# 또는 덮어쓰기
python scripts/embed_onehago_products.py --skip-create
```

---

**작성일**: 2025-11-06
**버전**: 1.0.0
**상태**: Ready for testing
