# Qdrant Snapshot 워크플로우

22,870개 onehago 벡터 데이터를 환경간 공유하는 완벽한 가이드

---

## 📊 데이터 현황

| 항목 | 개수 |
|------|------|
| **원본 JSON 파일** | 24,745개 |
| **Qdrant 임베딩 Vectors** | 22,870개 |
| **Collection** | `onehago_v2` |
| **Dimension** | 384 (all-MiniLM-L6-v2) |
| **예상 Snapshot 크기** | 100-500MB |

---

## 🚀 Quick Start

### Mac 로컬 → Claude Code CLI/Web

```bash
# Step 1: Mac 로컬에서 Snapshot 생성 (1분)
cd ~/Project/rag-enterprise
./scripts/create_snapshot.sh onehago_v2

# Step 2: Snapshot 파일 확인
ls -lh data/snapshots/onehago_v2_*.snapshot

# Step 3: Claude Code CLI/Web에서 복원 (5분)
# (Docker/다른 환경에서)
./scripts/prepare_data.sh --snapshot data/snapshots/onehago_v2_20251106.snapshot

# Step 4: 검증
./scripts/verify_data.sh
```

---

## 📋 상세 워크플로우

### Phase 1: Snapshot 생성 (Mac 로컬)

#### 1.1 사전 요구사항

```bash
# Qdrant 실행 확인
curl http://localhost:6333

# Collection 확인
curl -s http://localhost:6333/collections/onehago_v2 | jq '.result.points_count'
# 출력: 22870
```

#### 1.2 Snapshot 생성

```bash
cd ~/Project/rag-enterprise

# 스크립트 실행
./scripts/create_snapshot.sh onehago_v2

# 또는 수동:
curl -X POST "http://localhost:6333/collections/onehago_v2/snapshots"
```

**출력 예시**:
```
📦 Qdrant Snapshot 생성 도구
==================================

📌 Qdrant 연결 확인...
✅ Qdrant 실행 중

📌 Collection 'onehago_v2' 확인...
✅ Collection 존재: 22870 vectors

📌 Snapshot 디렉토리 준비...
✅ 디렉토리: data/snapshots

📌 Snapshot 생성 중...
   Collection: onehago_v2
   Vectors: 22870

✅ Snapshot 생성됨: onehago_v2-2025-11-06-12-34-56.snapshot

📌 Snapshot 다운로드 중...
✅ 다운로드 완료
   파일: data/snapshots/onehago_v2_20251106_123456.snapshot
   크기: 245M

==================================
✅ Snapshot 생성 완료!
==================================
```

#### 1.3 Snapshot 검증

```bash
# 파일 존재 확인
ls -lh data/snapshots/onehago_v2_*.snapshot

# 크기 확인 (최소 10MB 이상이어야 함)
du -h data/snapshots/onehago_v2_*.snapshot
```

---

### Phase 2: Snapshot 공유

Snapshot 파일은 `.gitignore`에 포함되어 Git에 커밋되지 않습니다.

#### Option A: Google Drive (권장)

```bash
# 1. Finder에서 data/snapshots/ 열기
open data/snapshots/

# 2. Google Drive에 업로드
# - drive.google.com 접속
# - 폴더 생성: "rag-enterprise/snapshots"
# - 파일 업로드: onehago_v2_20251106.snapshot

# 3. 공유 링크 생성
# - 파일 우클릭 → 공유 → 링크 복사
# - 권한: "링크가 있는 모든 사용자"

# 4. 링크 문서화 (선택)
echo "https://drive.google.com/file/d/ABC123..." >> docs/SNAPSHOT_LINKS.md
```

#### Option B: 로컬 복사 (같은 머신)

```bash
# Mac 로컬 → Docker volume
cp data/snapshots/onehago_v2_*.snapshot \
   /path/to/docker/volume/data/snapshots/
```

#### Option C: SCP/rsync (서버 배포)

```bash
# 서버로 전송
scp data/snapshots/onehago_v2_*.snapshot \
    user@server:/path/to/rag-enterprise/data/snapshots/
```

---

### Phase 3: Snapshot 복원

#### 3.1 사전 요구사항 (복원 환경)

```bash
# Qdrant 실행
docker-compose up -d qdrant

# 또는
colima start && docker-compose up -d qdrant

# 연결 확인
curl http://localhost:6333
```

#### 3.2 Snapshot 파일 준비

**Method 1: Google Drive에서 다운로드**

```bash
# Google Drive 링크에서 다운로드
mkdir -p data/snapshots
cd data/snapshots

# gdown 사용 (설치: pip install gdown)
gdown "https://drive.google.com/uc?id=FILE_ID"

# 또는 브라우저에서 수동 다운로드 후 data/snapshots/에 저장
```

**Method 2: 로컬 파일 사용**

```bash
# 이미 data/snapshots/에 있다면 건너뜀
ls -lh data/snapshots/onehago_v2_*.snapshot
```

#### 3.3 복원 실행

```bash
cd ~/Project/rag-enterprise  # 또는 Docker 내부

# 스크립트 실행
./scripts/prepare_data.sh --snapshot data/snapshots/onehago_v2_20251106.snapshot
```

**출력 예시**:
```
📦 Option 1: Qdrant Snapshot 복원
예상 시간: 5분

📌 사전 요구사항 확인
✅ Python: Python 3.11.14
✅ Qdrant: 실행 중 (http://localhost:6333)

✅ Snapshot 파일: data/snapshots/onehago_v2_20251106.snapshot (245M)

📌 Collection: onehago_v2

⚠️  기존 Collection을 삭제하고 복원합니다
계속하시겠습니까? (y/N): y

🗑️  기존 Collection 삭제 중...
✅ 삭제 완료

📤 Snapshot 업로드 중...
✅ 업로드 완료

⏳ Collection 복원 중...

🔍 복원 검증 중...
✅ 복원 성공!
   Collection: onehago_v2
   Vectors: 22870

================================
✅ Snapshot 복원 완료!
================================

다음 단계:
  ./scripts/verify_data.sh
```

#### 3.4 복원 검증

```bash
# 검증 스크립트 실행
./scripts/verify_data.sh
```

**예상 출력**:
```
📌 Qdrant 연결
✅ Qdrant: 실행 중 (http://localhost:6333)

📌 Collection: onehago_v2
✅ Collection: 존재

📌 Vector 개수
✅ Vector 개수: 22870
   ℹ️  프로덕션 데이터 모드 (onehago)

📌 Vector Dimension
✅ Dimension: 384 (sentence-transformers/all-MiniLM-L6-v2)

📌 검색 테스트
✅ 검색 성공

📌 Distance Metric
✅ Distance: Cosine

==================================
✅ 모든 데이터 검증 통과!
==================================
```

---

## 🔧 문제 해결

### Q1: "Snapshot 파일을 찾을 수 없습니다"

**원인**: 파일 경로가 잘못되었거나 파일이 없음

**해결**:
```bash
# 파일 위치 확인
find . -name "*.snapshot"

# 올바른 경로로 다시 실행
./scripts/prepare_data.sh --snapshot data/snapshots/onehago_v2_20251106.snapshot
```

### Q2: "Qdrant가 실행되지 않았습니다"

**원인**: Qdrant 컨테이너가 실행 중이 아님

**해결**:
```bash
# Docker 확인
docker ps | grep qdrant

# Qdrant 시작
docker-compose up -d qdrant

# 연결 확인
curl http://localhost:6333
```

### Q3: "업로드 실패"

**원인**: Snapshot 파일이 손상되었거나 호환되지 않음

**해결**:
```bash
# 1. 파일 크기 확인 (최소 10MB)
ls -lh data/snapshots/onehago_v2_*.snapshot

# 2. Snapshot 재생성 (Mac 로컬)
./scripts/create_snapshot.sh onehago_v2

# 3. 다시 복원
./scripts/prepare_data.sh --snapshot data/snapshots/onehago_v2_NEW.snapshot
```

### Q4: Docker에서 "host.docker.internal: Connection refused"

**원인**: Docker 컨테이너에서 Mac의 Qdrant에 접근 불가

**해결**:
```bash
# .env 파일 확인
cat .env | grep QDRANT_HOST

# Docker 내부에서는:
QDRANT_HOST=host.docker.internal  # Mac에서

# Mac 로컬에서는:
QDRANT_HOST=localhost
```

---

## 📊 성능 벤치마크

| 작업 | 시간 | 비고 |
|------|------|------|
| **Snapshot 생성** | 1-2분 | 22,870 vectors |
| **Snapshot 다운로드** (Google Drive) | 2-3분 | 245MB, 네트워크 속도 의존 |
| **Snapshot 업로드** | 30초 | Qdrant API |
| **Collection 복원** | 2-3분 | 인덱스 재구성 |
| **검증** | 10초 | |
| **Total** | **5-10분** | |

---

## 🎯 Best Practices

### 1. 정기 Snapshot 생성

```bash
# 매일 자동 백업 (cron)
0 2 * * * cd ~/Project/rag-enterprise && ./scripts/create_snapshot.sh onehago_v2
```

### 2. 버전 관리

```bash
# Snapshot 파일명에 날짜 포함
onehago_v2_20251106.snapshot  ✅
onehago_v2_latest.snapshot    ❌ (덮어쓰기 위험)
```

### 3. 저장 공간 관리

```bash
# 오래된 Snapshot 삭제 (30일 이상)
find data/snapshots -name "*.snapshot" -mtime +30 -delete
```

### 4. 문서화

```bash
# docs/SNAPSHOT_LINKS.md 업데이트
echo "## 최신 Snapshot" >> docs/SNAPSHOT_LINKS.md
echo "- Date: 2025-11-06" >> docs/SNAPSHOT_LINKS.md
echo "- Vectors: 22,870" >> docs/SNAPSHOT_LINKS.md
echo "- Link: https://drive.google.com/..." >> docs/SNAPSHOT_LINKS.md
```

---

## 🔗 관련 문서

- [DATA_PREPARATION.md](DATA_PREPARATION.md) - 데이터 준비 전체 가이드
- [ENVIRONMENT_PARITY.md](ENVIRONMENT_PARITY.md) - 환경 동일성 보장
- [LOCAL_SETUP.md](LOCAL_SETUP.md) - 로컬 환경 설정

---

**최종 업데이트**: 2025-11-06
**버전**: 1.0.0
**Snapshot 크기**: ~245MB (22,870 vectors)
