# 환경 동일성 가이드 (Environment Parity)

**목표**: Claude Code Web과 Claude Code CLI에서 동일한 품질의 작업 결과를 보장합니다.

---

## 🎯 핵심 원칙

> "어떤 환경에서든 동일한 코드는 동일하게 작동해야 한다"

### 보장해야 할 것

1. **Python 버전**: 3.11.14 고정
2. **의존성 버전**: 모든 패키지 버전 고정 (`requirements-lock.txt`)
3. **환경 변수**: `.env` 파일로 통일
4. **데이터**: 동일한 Qdrant collection 사용
5. **설정 파일**: 모든 설정 파일 Git 관리

---

## 🔄 환경별 차이점

### Claude Code CLI (Docker 기반)

**특징**:
- Docker 컨테이너에서 실행
- 격리된 파일 시스템
- Volume mount로 프로젝트 동기화
- `host.docker.internal`로 Mac의 서비스 접근

**장점**:
- 깨끗한 환경 (항상 동일한 시작점)
- 의존성 충돌 없음
- 재현 가능한 환경

**제약**:
- Mac의 `localhost` 직접 접근 불가
- Gitignored 파일 동기화 안 됨 (`.env`, `data/`, `.venv/`)
- 파일 권한 차이 (root vs user)

### Mac 로컬 환경

**특징**:
- 네이티브 Python 실행
- 로컬 파일 시스템 직접 접근
- `localhost`로 모든 서비스 접근

**장점**:
- 빠른 파일 I/O
- IDE 통합 용이
- 디버깅 편리

**제약**:
- 시스템 패키지와 충돌 가능
- 환경 오염 가능성
- 개발자마다 환경 차이

---

## ✅ 공통 요구사항

두 환경 모두에서 충족해야 할 요구사항:

### 1. Python 버전

```bash
# 확인
python --version
# 출력: Python 3.11.14

# 설정 방법
# Mac 로컬:
brew install python@3.11

# CLI (자동):
# .python-version 파일로 자동 관리
```

### 2. 의존성 버전

```bash
# 확인
pip list

# 설정 방법
# requirements-lock.txt 사용 (권장)
pip install -r requirements-lock.txt

# 또는 requirements.txt
pip install -r requirements.txt
```

### 3. 환경 변수

**필수 변수**:
```bash
# .env 파일
QDRANT_HOST=localhost                    # CLI는 host.docker.internal
QDRANT_HTTP_PORT=6333
QDRANT_COLLECTION=onehago_v2
USE_VECTOR_RAG=true
OLLAMA_DEFAULT_MODEL=qwen2.5:7b-instruct
```

**환경별 차이 처리**:
```python
# src/api/chat.py
import os

# Docker 환경 자동 감지
if os.path.exists('/.dockerenv'):
    qdrant_host = os.getenv('QDRANT_HOST', 'host.docker.internal')
else:
    qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
```

### 4. PYTHONPATH 설정

```bash
# 확인
echo $PYTHONPATH

# 설정
export PYTHONPATH=/path/to/rag-enterprise:$PYTHONPATH

# 영구 설정 (Mac)
echo 'export PYTHONPATH=/Users/yourusername/Project/rag-enterprise:$PYTHONPATH' >> ~/.zshrc
source ~/.zshrc
```

### 5. 데이터 동기화

**Qdrant Collection**:
- Collection 이름: `onehago_v2`
- Vector 개수: 22,870개 (프로덕션) 또는 3개 (샘플)
- Dimension: 384
- Distance: Cosine

**동기화 방법**:
```bash
# Option 1: Snapshot 공유 (권장)
./scripts/prepare_data.sh --snapshot

# Option 2: 샘플 데이터 (개발/테스트)
./scripts/prepare_data.sh --sample
```

---

## 🔧 환경 검증 절차

### 자동 검증 (권장)

```bash
# 1. 환경 검증
./scripts/verify_environment.sh

# 2. 데이터 검증
./scripts/verify_data.sh
```

### 수동 검증 체크리스트

#### Python & 의존성
- [ ] Python 3.11.x 설치됨
- [ ] 가상환경 활성화됨 (`source .venv/bin/activate`)
- [ ] 모든 패키지 설치됨 (`pip list`)

#### 환경 변수
- [ ] `.env` 파일 존재
- [ ] `QDRANT_HOST` 설정됨
- [ ] `USE_VECTOR_RAG=true`
- [ ] `QDRANT_COLLECTION` 설정됨

#### PYTHONPATH
- [ ] `PYTHONPATH`에 프로젝트 루트 포함
- [ ] `python -c "from src.core.rag_pipeline import RAGPipeline"` 성공

#### Qdrant
- [ ] Qdrant 실행 중 (`docker ps | grep qdrant`)
- [ ] Collection 존재 (`curl http://localhost:6333/collections/onehago_v2`)
- [ ] Vector 개수 확인

---

## 🐛 Troubleshooting

### 문제 1: ModuleNotFoundError: No module named 'src'

**원인**: PYTHONPATH 설정 안 됨

**해결**:
```bash
# 임시 해결
export PYTHONPATH=/path/to/rag-enterprise:$PYTHONPATH

# 영구 해결
# ~/.zshrc 또는 ~/.bashrc에 추가
echo 'export PYTHONPATH=/path/to/rag-enterprise:$PYTHONPATH' >> ~/.zshrc
source ~/.zshrc
```

### 문제 2: Qdrant Connection Refused

**환경**: Claude Code CLI (Docker)

**원인**: `localhost`는 컨테이너 내부를 가리킴

**해결**:
```bash
# .env 파일 수정
QDRANT_HOST=host.docker.internal  # Mac에서 Docker 사용 시
# 또는
QDRANT_HOST=172.17.0.1            # Linux에서 Docker 사용 시
```

### 문제 3: 검색 결과가 없음 (No results)

**가능한 원인**:

1. **Collection이 비어있음**
   ```bash
   ./scripts/verify_data.sh
   # Vector 개수 확인
   ```

2. **잘못된 Collection 사용**
   ```bash
   # .env 확인
   grep QDRANT_COLLECTION .env
   # 출력: QDRANT_COLLECTION=onehago_v2
   ```

3. **USE_VECTOR_RAG=false**
   ```bash
   # .env 확인
   grep USE_VECTOR_RAG .env
   # 출력: USE_VECTOR_RAG=true
   ```

4. **서버 재시작 필요**
   ```bash
   # .env 수정 후 서버 재시작
   pkill -f run_chat_server
   python scripts/run_chat_server.py
   ```

### 문제 4: 의존성 버전 충돌

**원인**: `requirements.txt`의 `>=` 연산자로 인한 버전 불일치

**해결**:
```bash
# requirements-lock.txt 사용 (정확한 버전)
pip install -r requirements-lock.txt

# 또는 현재 환경을 lock 파일로 저장
pip freeze > requirements-lock.txt
```

### 문제 5: .env 파일이 Git에 없음

**원인**: `.env`는 `.gitignore`에 포함됨 (보안상 정상)

**해결**:
```bash
# 1. 템플릿에서 복사
cp .env.example .env  # (있다면)

# 2. 또는 setup 스크립트로 생성
./scripts/setup_dev_environment.sh

# 3. 또는 수동 생성
cat > .env << 'EOF'
QDRANT_HOST=localhost
QDRANT_HTTP_PORT=6333
QDRANT_COLLECTION=onehago_v2
USE_VECTOR_RAG=true
OLLAMA_DEFAULT_MODEL=qwen2.5:7b-instruct
EOF
```

### 문제 6: 가상환경이 활성화되지 않음

**증상**: `which python`이 시스템 Python을 가리킴

**해결**:
```bash
# 가상환경 생성 (없다면)
python3 -m venv .venv

# 활성화
source .venv/bin/activate

# 확인
which python
# 출력: /path/to/rag-enterprise/.venv/bin/python
```

---

## 🚀 Quick Check 명령어

환경이 올바르게 설정되었는지 빠르게 확인:

```bash
# 한 줄 검증
python --version && \
  echo $PYTHONPATH && \
  python -c "from src.core.rag_pipeline import RAGPipeline; print('✅ Import OK')" && \
  curl -s http://localhost:6333/collections/onehago_v2 | grep -q points_count && \
  echo "✅ All checks passed!"
```

개별 확인:

```bash
# Python 버전
python --version

# PYTHONPATH
echo $PYTHONPATH | grep rag-enterprise

# Import 테스트
python -c "from src.core.rag_pipeline import RAGPipeline"

# Qdrant 연결
curl -s http://localhost:6333/collections/onehago_v2

# 환경 변수
source .env && echo $USE_VECTOR_RAG
```

---

## 📊 환경 비교표

| 항목 | Mac 로컬 | Claude CLI (Docker) | 동기화 방법 |
|------|----------|---------------------|-------------|
| **코드** | Git | Git | `git push` / `git pull` |
| **Python 버전** | 3.11.14 | 3.11.14 | `.python-version` |
| **의존성** | pip install | pip install | `requirements-lock.txt` |
| **.env** | 수동 생성 | 수동 생성 | 문서화 (Git 제외) |
| **데이터** | Qdrant | Qdrant | Snapshot 또는 스크립트 |
| **Qdrant 접근** | `localhost` | `host.docker.internal` | 환경 변수 |

---

## 🎓 Best Practices

### 1. 버전 고정

**나쁜 예**:
```txt
# requirements.txt
transformers>=4.36.0  # 버전이 계속 바뀜
```

**좋은 예**:
```txt
# requirements-lock.txt
transformers==4.36.0  # 항상 동일한 버전
```

### 2. 환경 변수 관리

**나쁜 예**:
```python
# 하드코딩
qdrant_client = QdrantClient(url="http://localhost:6333")
```

**좋은 예**:
```python
# 환경 변수 사용
import os
qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
qdrant_port = os.getenv('QDRANT_HTTP_PORT', '6333')
qdrant_client = QdrantClient(url=f"http://{qdrant_host}:{qdrant_port}")
```

### 3. 데이터 동기화

**나쁜 예**:
- "내 컴퓨터에서는 되는데..." (데이터 불일치)

**좋은 예**:
- Snapshot 공유 또는
- 자동 데이터 준비 스크립트 사용

### 4. 문서화

**나쁜 예**:
- 구두로 전달: "이거 설치하고 저거 설정하면 돼"

**좋은 예**:
- 자동화 스크립트: `./scripts/setup_dev_environment.sh`
- 명확한 문서: `docs/LOCAL_SETUP.md`

---

## 📝 체크리스트: 새 개발자 온보딩

새 팀원이 합류했을 때:

- [ ] Repository clone: `git clone <repo>`
- [ ] 브랜치 checkout: `git checkout <branch>`
- [ ] 자동 환경 설정: `./scripts/setup_dev_environment.sh`
- [ ] 환경 검증: `./scripts/verify_environment.sh`
- [ ] 샘플 데이터 준비: `./scripts/prepare_data.sh --sample`
- [ ] 데이터 검증: `./scripts/verify_data.sh`
- [ ] 서버 실행: `python scripts/run_chat_server.py`
- [ ] 테스트 쿼리 실행

**예상 소요 시간**: 10-15분 (샘플 데이터 기준)

---

## 🔗 관련 문서

- [DATA_PREPARATION.md](DATA_PREPARATION.md) - 데이터 준비 가이드
- [LOCAL_SETUP.md](LOCAL_SETUP.md) - 로컬 설정 상세 가이드
- [ARCHITECTURE.md](ARCHITECTURE.md) - 시스템 아키텍처
- [docs/CLAUDE_CLI_WORKFLOW.md](CLAUDE_CLI_WORKFLOW.md) - Claude CLI 워크플로우

---

**최종 업데이트**: 2025-11-06
**버전**: 1.0.0
