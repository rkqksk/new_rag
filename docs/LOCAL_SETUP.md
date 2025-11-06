# 로컬 설정 가이드 (Local Setup)

RAG Enterprise 프로젝트의 로컬 개발 환경 설정 가이드입니다.

---

## 📋 목차

1. [Gitignored 파일 관리](#gitignored-파일-관리)
2. [.env 설정](#env-설정)
3. [가상환경 (.venv) 설정](#가상환경-venv-설정)
4. [PYTHONPATH 설정](#pythonpath-설정)
5. [데이터 디렉토리 구조](#데이터-디렉토리-구조)
6. [Mac vs Docker 차이점](#mac-vs-docker-차이점)
7. [문제 해결](#문제-해결)

---

## Gitignored 파일 관리

### 왜 일부 파일이 Git에 없나요?

다음 파일/디렉토리는 보안 또는 환경별 차이로 인해 `.gitignore`에 포함됩니다:

```
.env              # API 키, 비밀 정보
.venv/            # 가상환경 (OS마다 다름)
data/             # 대용량 데이터 (Git LFS 미사용)
*.pyc             # Python 컴파일 파일
__pycache__/      # Python 캐시
.DS_Store         # Mac 시스템 파일
```

### Gitignored 파일 공유 전략

| 파일/디렉토리 | 공유 방법 | 이유 |
|---------------|-----------|------|
| `.env` | 문서화 (템플릿) | 보안 (API 키 포함) |
| `.venv/` | `requirements.txt` | OS마다 바이너리 다름 |
| `data/` | Snapshot 또는 스크립트 | 크기 (수 GB) |

### .env 관리

**절대 하지 말 것**:
```bash
# ❌ .env를 Git에 커밋하지 마세요!
git add .env
```

**올바른 방법**:
```bash
# 1. .env.example을 Git에 커밋 (실제 값 제외)
cat > .env.example << 'EOF'
QDRANT_HOST=localhost
QDRANT_HTTP_PORT=6333
QDRANT_COLLECTION=onehago_v2
USE_VECTOR_RAG=true
OLLAMA_DEFAULT_MODEL=qwen2.5:7b-instruct
# API_KEY=your-api-key-here  # (예시)
EOF

git add .env.example
git commit -m "docs: Add .env template"

# 2. 각 개발자는 .env.example을 복사해서 사용
cp .env.example .env
# .env 파일을 실제 값으로 수정
```

---

## .env 설정

### 전체 .env 예시

```bash
# ====================
# Qdrant Configuration
# ====================
QDRANT_HOST=localhost
QDRANT_HTTP_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_COLLECTION=onehago_v2

# ====================
# RAG Configuration
# ====================
USE_VECTOR_RAG=true

# ====================
# Ollama Configuration
# ====================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=qwen2.5:7b-instruct

# ====================
# API Configuration
# ====================
API_HOST=0.0.0.0
API_PORT=8001

# ====================
# Development
# ====================
DEBUG=true
LOG_LEVEL=INFO

# ====================
# Optional: External APIs
# ====================
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=...
```

### 환경별 .env 설정

#### Mac 로컬 환경

```bash
QDRANT_HOST=localhost
OLLAMA_BASE_URL=http://localhost:11434
```

#### Claude Code CLI (Docker)

```bash
QDRANT_HOST=host.docker.internal
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

#### Linux Docker

```bash
QDRANT_HOST=172.17.0.1  # Docker bridge IP
OLLAMA_BASE_URL=http://172.17.0.1:11434
```

### .env 로드 확인

```python
# Python에서 확인
from dotenv import load_dotenv
import os

load_dotenv()

print(f"QDRANT_HOST: {os.getenv('QDRANT_HOST')}")
print(f"USE_VECTOR_RAG: {os.getenv('USE_VECTOR_RAG')}")
print(f"QDRANT_COLLECTION: {os.getenv('QDRANT_COLLECTION')}")
```

```bash
# Bash에서 확인
source .env
echo $QDRANT_HOST
echo $USE_VECTOR_RAG
```

---

## 가상환경 (.venv) 설정

### 왜 가상환경이 필요한가?

- **격리**: 프로젝트별 독립적인 패키지 관리
- **버전 충돌 방지**: 시스템 Python과 분리
- **재현성**: 팀원 모두 동일한 환경

### 생성 방법

```bash
# Python 3.11 확인
python3 --version
# Python 3.11.14

# 가상환경 생성
python3 -m venv .venv
```

### 활성화

#### Mac / Linux

```bash
source .venv/bin/activate

# 확인
which python
# 출력: /path/to/rag-enterprise/.venv/bin/python
```

#### Windows (PowerShell)

```powershell
.venv\Scripts\Activate.ps1
```

#### Windows (CMD)

```cmd
.venv\Scripts\activate.bat
```

### 비활성화

```bash
deactivate
```

### 자동 활성화 (선택사항)

#### direnv 사용 (Mac / Linux)

```bash
# 1. direnv 설치
brew install direnv  # Mac
# 또는
sudo apt install direnv  # Ubuntu

# 2. Shell 설정에 추가
# ~/.zshrc 또는 ~/.bashrc
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
source ~/.zshrc

# 3. 프로젝트 루트에 .envrc 생성
echo 'source .venv/bin/activate' > .envrc
direnv allow .

# 이제 디렉토리 진입 시 자동 활성화!
```

### 가상환경 재생성

```bash
# 기존 가상환경 삭제
rm -rf .venv

# 새로 생성
python3 -m venv .venv
source .venv/bin/activate

# 의존성 재설치
pip install -r requirements-lock.txt
```

---

## PYTHONPATH 설정

### 왜 필요한가?

프로젝트 루트에서 모듈을 import하기 위해:

```python
# src/api/chat.py에서
from src.core.rag_pipeline import RAGPipeline  # ✅ PYTHONPATH 필요
```

### 설정 방법

#### Mac (Zsh)

```bash
# 임시 설정 (현재 세션만)
export PYTHONPATH=/Users/yourusername/Project/rag-enterprise:$PYTHONPATH

# 영구 설정
echo 'export PYTHONPATH=/Users/yourusername/Project/rag-enterprise:$PYTHONPATH' >> ~/.zshrc
source ~/.zshrc
```

#### Mac (Bash)

```bash
echo 'export PYTHONPATH=/Users/yourusername/Project/rag-enterprise:$PYTHONPATH' >> ~/.bashrc
source ~/.bashrc
```

#### Linux

```bash
# ~/.bashrc
echo 'export PYTHONPATH=/home/yourusername/rag-enterprise:$PYTHONPATH' >> ~/.bashrc
source ~/.bashrc
```

#### Windows (PowerShell)

```powershell
# 현재 세션
$env:PYTHONPATH = "C:\Users\yourusername\rag-enterprise;$env:PYTHONPATH"

# 영구 설정 (시스템 환경 변수)
[Environment]::SetEnvironmentVariable("PYTHONPATH", "C:\Users\yourusername\rag-enterprise", "User")
```

#### Windows (CMD)

```cmd
set PYTHONPATH=C:\Users\yourusername\rag-enterprise;%PYTHONPATH%
```

### 동적 설정 (추천)

프로젝트 루트를 자동으로 찾는 방법:

```python
# scripts/run_chat_server.py
import sys
import os
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 이제 import 가능
from src.core.rag_pipeline import RAGPipeline
```

### 확인 방법

```bash
# 환경 변수 확인
echo $PYTHONPATH

# Python에서 확인
python -c "import sys; print('\n'.join(sys.path))"

# Import 테스트
python -c "from src.core.rag_pipeline import RAGPipeline; print('✅ OK')"
```

---

## 데이터 디렉토리 구조

### 표준 구조

```
rag-enterprise/
├── data/                    # ← .gitignore에 포함
│   ├── raw/                 # 원본 크롤링 데이터
│   │   ├── onehago_crawled.json
│   │   └── products_2024.json
│   ├── processed/           # 전처리된 데이터
│   │   └── cleaned_products.json
│   ├── embeddings/          # 임베딩 캐시 (선택)
│   │   └── embeddings.pkl
│   └── snapshots/           # Qdrant snapshots
│       └── onehago_v2_20241106.snapshot
├── .env                     # 환경 변수 (Git 제외)
├── .venv/                   # 가상환경 (Git 제외)
└── ...
```

### data/ 디렉토리 관리

#### 초기 설정

```bash
# 디렉토리 생성
mkdir -p data/{raw,processed,embeddings,snapshots}

# .gitkeep으로 빈 디렉토리 유지
touch data/raw/.gitkeep
touch data/processed/.gitkeep

# .gitkeep만 커밋
git add data/*/.gitkeep
git commit -m "chore: Add data directory structure"
```

#### 데이터 다운로드

```bash
# Option 1: Snapshot (권장)
./scripts/prepare_data.sh --snapshot

# Option 2: 원본 데이터에서 임베딩
# 1. 원본 데이터 다운로드 (Google Drive, S3 등)
# 2. data/raw/에 저장
# 3. 임베딩 스크립트 실행
./scripts/prepare_data.sh --embedding
```

---

## Mac vs Docker 차이점

### 비교표

| 항목 | Mac 로컬 | Claude CLI (Docker) |
|------|----------|---------------------|
| **Python 경로** | `/usr/local/bin/python3` | `/usr/bin/python` |
| **프로젝트 경로** | `/Users/user/Project/rag-enterprise` | `/home/user/rag-enterprise` |
| **localhost 접근** | 직접 접근 | `host.docker.internal` |
| **.env 위치** | 프로젝트 루트 | 프로젝트 루트 (동일) |
| **파일 권한** | user:staff | root:root |
| **네트워크** | 호스트 네트워크 | 브리지 네트워크 |

### localhost vs host.docker.internal

#### Mac 로컬에서 Qdrant 접근

```python
# .env
QDRANT_HOST=localhost

# Python
from qdrant_client import QdrantClient
client = QdrantClient(url="http://localhost:6333")
```

#### Docker에서 Mac의 Qdrant 접근

```python
# .env
QDRANT_HOST=host.docker.internal

# Python
from qdrant_client import QdrantClient
client = QdrantClient(url="http://host.docker.internal:6333")
```

#### 자동 감지 (추천)

```python
import os

# Docker 환경 감지
def is_docker():
    return os.path.exists('/.dockerenv')

# 자동으로 호스트 설정
if is_docker():
    default_host = 'host.docker.internal'
else:
    default_host = 'localhost'

qdrant_host = os.getenv('QDRANT_HOST', default_host)
```

### 파일 권한 문제

#### 문제

Docker에서 생성한 파일이 root 소유:

```bash
# Docker에서 파일 생성
echo "test" > test.txt

# Mac에서 확인
ls -la test.txt
# -rw-r--r-- 1 root root 5 Nov  6 00:00 test.txt

# Mac에서 수정 불가
nano test.txt  # Permission denied
```

#### 해결

**방법 1: Docker에서 권한 변경**

```bash
# Docker에서
chown 1000:1000 test.txt
```

**방법 2: Mac에서 권한 변경**

```bash
sudo chown $(whoami):staff test.txt
```

**방법 3: Docker user 매핑 (근본 해결)**

```yaml
# docker-compose.yml
services:
  claude-cli:
    user: "1000:1000"  # Mac user ID
```

---

## 문제 해결

### Q1: "command not found: python"

**원인**: Python이 `python3`로 설치됨

**해결**:
```bash
# 심볼릭 링크 생성
sudo ln -s /usr/local/bin/python3 /usr/local/bin/python

# 또는 alias 사용
echo 'alias python=python3' >> ~/.zshrc
source ~/.zshrc
```

### Q2: "pip: command not found"

**원인**: 가상환경이 활성화되지 않음

**해결**:
```bash
source .venv/bin/activate
which pip
# /path/to/.venv/bin/pip
```

### Q3: .env 파일이 로드되지 않음

**원인**: `python-dotenv` 미설치 또는 `load_dotenv()` 호출 안 함

**해결**:
```python
# 1. 패키지 설치
pip install python-dotenv

# 2. 코드에서 로드
from dotenv import load_dotenv
load_dotenv()  # ← 이 줄 추가!

import os
print(os.getenv('QDRANT_HOST'))
```

### Q4: 데이터 디렉토리가 비어있음

**원인**: Git에 포함되지 않음 (.gitignore)

**해결**:
```bash
# 샘플 데이터 생성
./scripts/prepare_data.sh --sample

# 또는 실제 데이터 복원
./scripts/prepare_data.sh --snapshot
```

### Q5: 가상환경에서 시스템 패키지가 보임

**원인**: `--system-site-packages` 옵션 사용

**해결**:
```bash
# 가상환경 재생성 (격리 모드)
rm -rf .venv
python3 -m venv .venv  # --system-site-packages 제외
source .venv/bin/activate
pip install -r requirements-lock.txt
```

---

## 자동화 스크립트 사용 (권장)

수동 설정 대신 자동화 스크립트 사용:

```bash
# 1. 전체 환경 자동 설정
./scripts/setup_dev_environment.sh

# 2. 환경 검증
./scripts/verify_environment.sh

# 3. 데이터 준비
./scripts/prepare_data.sh --sample

# 4. 데이터 검증
./scripts/verify_data.sh
```

---

## 다음 단계

로컬 설정 완료 후:

1. **서버 실행**:
   ```bash
   python scripts/run_chat_server.py
   ```

2. **프론트엔드 실행** (별도 터미널):
   ```bash
   cd frontend
   python3 -m http.server 8080
   # http://localhost:8080/chat.html
   ```

3. **API 테스트**:
   ```bash
   curl -X POST http://localhost:8001/chat/query \
     -H "Content-Type: application/json" \
     -d '{"session_id": "test", "query": "100ml 보틀 추천해줘"}'
   ```

---

## 관련 문서

- [ENVIRONMENT_PARITY.md](ENVIRONMENT_PARITY.md) - 환경 동일성 가이드
- [DATA_PREPARATION.md](DATA_PREPARATION.md) - 데이터 준비 가이드
- [CLAUDE_CLI_WORKFLOW.md](CLAUDE_CLI_WORKFLOW.md) - Claude CLI 워크플로우

---

**최종 업데이트**: 2025-11-06
**버전**: 1.0.0
