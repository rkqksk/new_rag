# 데이터 준비 가이드

RAG Enterprise를 위한 Qdrant 벡터 데이터베이스 설정 가이드입니다.

---

## 📋 개요

3가지 옵션 중 하나를 선택하세요:

| 옵션 | 시간 | 용도 | 데이터 크기 |
|------|------|------|-------------|
| **Option 1: Snapshot 복원** | 5분 | 프로덕션 | 22,870 vectors |
| **Option 2: 원본 임베딩** | 2-3시간 | 커스텀 데이터 | 가변 |
| **Option 3: 샘플 데이터** | 1분 | 개발/테스트 | 3 vectors |

---

## Option 1: Qdrant Snapshot 복원 (권장) ⚡

**예상 시간**: 5분
**용도**: 프로덕션 환경, 빠른 시작
**결과**: 22,870개의 onehago 제품 벡터

### 전제조건

- Qdrant 실행 중 (`docker-compose up -d`)
- Snapshot 파일 접근 권한

### 단계

#### 1. Snapshot 파일 다운로드

```bash
# Google Drive 또는 공유 위치에서 다운로드
# 파일명: onehago_v2_snapshot.tar.gz
```

**참고**: Snapshot 파일은 팀 내부 공유 위치에서 제공됩니다.

#### 2. Snapshot 압축 해제

```bash
mkdir -p snapshots
tar -xzf onehago_v2_snapshot.tar.gz -C snapshots/
```

#### 3. Qdrant에 복원

**방법 A: API를 통한 복원**

```bash
curl -X POST "http://localhost:6333/collections/onehago_v2/snapshots/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "snapshot=@snapshots/onehago_v2_snapshot.snapshot"
```

**방법 B: 파일 시스템 복원** (Docker 사용 시)

```bash
# 1. Qdrant 중지
docker-compose stop qdrant

# 2. Snapshot 파일 복사
docker cp snapshots/onehago_v2_snapshot.snapshot \
  rag-enterprise-qdrant-1:/qdrant/snapshots/

# 3. Qdrant 재시작
docker-compose start qdrant

# 4. 복원 확인 (약 30초 대기 후)
curl -s "http://localhost:6333/collections/onehago_v2" | jq '.result.points_count'
```

#### 4. 검증

```bash
./scripts/verify_data.sh
```

**예상 출력**:
```
✅ Collection: 존재
✅ Vector 개수: 22,870
✅ Dimension: 384
✅ 검색 성공
```

---

## Option 2: 원본 데이터에서 임베딩 🔨

**예상 시간**: 2-3시간 (데이터 크기에 따라)
**용도**: 커스텀 데이터, 새로운 크롤링 결과
**전제조건**: 크롤링된 원본 데이터 (JSON)

### 단계

#### 1. 원본 데이터 확인

```bash
ls -lh data/onehago_crawled.json
# 또는
ls -lh data/*.json
```

**데이터 형식 예시**:
```json
[
  {
    "name": "제품명",
    "category": "Bottle",
    "material": "PET",
    "volume": "100ml",
    "description": "제품 설명...",
    "url": "https://example.com/product/123"
  }
]
```

#### 2. 임베딩 스크립트 실행

**방법 A: 자동 스크립트 (권장)**

```bash
./scripts/prepare_data.sh --embedding
```

**방법 B: Python 직접 실행**

```python
from src.core.rag_pipeline import RAGPipeline
from src.core.embedding_service import EmbeddingService
import json

# 1. 데이터 로드
with open('data/onehago_crawled.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

print(f"총 {len(products)}개 제품 로드됨")

# 2. RAG Pipeline 초기화
pipeline = RAGPipeline(
    collection_name='onehago_v2',
    embedding_model='sentence-transformers/all-MiniLM-L6-v2'
)

# 3. 문서 준비
documents = []
for product in products:
    text = f"{product['name']} {product.get('description', '')}"
    documents.append({
        'text': text,
        'metadata': product
    })

# 4. 임베딩 및 업로드 (배치 처리)
batch_size = 100
for i in range(0, len(documents), batch_size):
    batch = documents[i:i+batch_size]
    pipeline.ingest_documents(batch)
    print(f"진행: {i+len(batch)}/{len(documents)}")

print("✅ 임베딩 완료!")
```

#### 3. 진행 상황 모니터링

```bash
# 별도 터미널에서
watch -n 5 'curl -s "http://localhost:6333/collections/onehago_v2" | jq ".result.points_count"'
```

#### 4. 검증

```bash
./scripts/verify_data.sh
```

---

## Option 3: 샘플 데이터 생성 🧪

**예상 시간**: 1분
**용도**: 개발, 테스트, CI/CD
**결과**: 3개의 샘플 제품 벡터

### 단계

#### 1. 샘플 데이터 생성

```bash
./scripts/prepare_data.sh --sample
```

**생성되는 샘플 데이터**:
- Sample Bottle 100ml (Bottle, PET)
- Sample Jar 50ml (Jar, PP)
- Sample Pump Cap (Cap, ABS)

#### 2. 검증

```bash
./scripts/verify_data.sh
```

**예상 출력**:
```
✅ Vector 개수: 3
ℹ️  샘플 데이터 모드
```

---

## 검증 방법

### 자동 검증

```bash
./scripts/verify_data.sh
```

### 수동 검증

#### 1. Collection 존재 확인

```bash
curl -s "http://localhost:6333/collections/onehago_v2" | jq '.'
```

#### 2. Vector 개수 확인

```bash
curl -s "http://localhost:6333/collections/onehago_v2" | jq '.result.points_count'
```

#### 3. 샘플 검색 테스트

```python
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")

# 첫 번째 포인트 조회
points = client.scroll(
    collection_name="onehago_v2",
    limit=1,
    with_payload=True
)[0]

if points:
    print("✅ 데이터 존재")
    print(f"샘플: {points[0].payload}")
else:
    print("❌ 데이터 없음")
```

---

## 문제 해결

### Collection이 존재하지 않음

```bash
# Collection 생성
curl -X PUT "http://localhost:6333/collections/onehago_v2" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }'
```

### Vector 개수가 0

1. 임베딩 스크립트가 완료되었는지 확인
2. Qdrant 로그 확인: `docker logs rag-enterprise-qdrant-1`
3. 데이터 재생성: `./scripts/prepare_data.sh --sample`

### 임베딩 속도가 느림

- **GPU 사용**: CUDA가 설치된 경우 자동으로 사용됨
- **배치 크기 조정**: `batch_size=100` → `batch_size=50` (메모리 부족 시)
- **모델 변경**: 더 작은 모델 사용 (성능 저하 가능)

### Snapshot 복원 실패

1. Snapshot 파일 무결성 확인
2. Qdrant 버전 호환성 확인
3. 디스크 공간 확인: `df -h`

---

## 데이터 백업

### Snapshot 생성

```bash
# API를 통한 Snapshot 생성
curl -X POST "http://localhost:6333/collections/onehago_v2/snapshots"

# Snapshot 목록 조회
curl "http://localhost:6333/collections/onehago_v2/snapshots"

# Snapshot 다운로드
curl "http://localhost:6333/collections/onehago_v2/snapshots/[snapshot-name]" \
  --output backup.snapshot
```

### 정기 백업 스크립트

```bash
#!/bin/bash
# 매일 자동 백업

BACKUP_DIR="backups/qdrant"
mkdir -p "$BACKUP_DIR"

DATE=$(date +%Y%m%d)
SNAPSHOT_NAME="onehago_v2_${DATE}.snapshot"

# Snapshot 생성 및 다운로드
curl -X POST "http://localhost:6333/collections/onehago_v2/snapshots"
# (snapshot name 파싱 로직 필요)
# curl "http://localhost:6333/collections/onehago_v2/snapshots/${SNAPSHOT_NAME}" \
#   --output "${BACKUP_DIR}/${SNAPSHOT_NAME}"
```

---

## 다음 단계

데이터 준비 완료 후:

1. **환경 검증**:
   ```bash
   ./scripts/verify_environment.sh
   ```

2. **서버 실행**:
   ```bash
   python scripts/run_chat_server.py
   ```

3. **프론트엔드 실행**:
   ```bash
   cd frontend && python3 -m http.server 8080
   ```

4. **테스트 쿼리**:
   ```bash
   curl -X POST "http://localhost:8001/chat/query" \
     -H "Content-Type: application/json" \
     -d '{"session_id": "test", "query": "100ml 용량의 PET 보틀을 찾고 있어요"}'
   ```

---

**관련 문서**:
- [ENVIRONMENT_PARITY.md](ENVIRONMENT_PARITY.md) - 환경 동일성 가이드
- [LOCAL_SETUP.md](LOCAL_SETUP.md) - 로컬 설정 가이드
- [ARCHITECTURE.md](ARCHITECTURE.md) - 시스템 아키텍처
