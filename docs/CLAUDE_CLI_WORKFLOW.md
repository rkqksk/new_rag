# Claude CLI 워크플로우: 환경 동일성 확보

**목적**: Claude Code CLI에서 읽고 실행하여 협업 환경을 완벽하게 구축

**사용법**:
```
사용자: "docs/CLAUDE_CLI_WORKFLOW.md를 읽고 Phase 1부터 순서대로 실행해줘"
```

---

## 📋 전체 개요

### 목표
- Claude Code Web ↔ CLI 환경에서 동일한 결과 보장
- 누구나 동일한 환경에서 협업 가능
- 자동화된 설정 및 검증

### 완료 후 상태
- ✅ Python 3.11.14 고정
- ✅ 모든 의존성 버전 고정 (requirements-lock.txt)
- ✅ 자동 환경 설정 스크립트
- ✅ 환경 검증 스크립트
- ✅ 데이터 준비 가이드
- ✅ 완전한 문서화

---

## Phase 1: 버전 고정 (필수) 🔴

### 1.1 Python 버전 고정

**작업**: `.python-version` 파일 생성

**Claude CLI 실행 내용**:
```python
# .python-version 파일 생성
content = "3.11.14\n"
```

**Write 명령어**:
- file_path: `/home/user/rag-enterprise/.python-version`
- content: `3.11.14\n`

**검증**:
```bash
cat .python-version
# 출력: 3.11.14
```

---

### 1.2 의존성 버전 고정

**작업**: `requirements-lock.txt` 생성

**Claude CLI 실행 내용**:
```bash
# 현재 설치된 패키지의 정확한 버전을 기록
pip freeze
```

**결과를 `requirements-lock.txt`에 저장**

**검증**:
```bash
wc -l requirements-lock.txt
# 출력: 약 50-100줄
```

---

### 1.3 requirements.txt 업데이트

**작업**: >= 를 == 로 변경

**현재 문제**:
```python
transformers>=4.36.0    # 버전이 계속 바뀜
torch>=2.2.0            # 위험!
```

**수정 후**:
```python
transformers==4.36.0
torch==2.2.0
```

**Claude CLI 실행 내용**:
- Read: `requirements.txt`
- Edit: `>=` → `==` 로 변경
- 주요 패키지만 수정 (transformers, torch, sentence-transformers, redis)

**검증**:
```bash
grep ">=" requirements.txt
# 출력: (거의 없어야 함)
```

---

## Phase 2: 자동 Setup 스크립트 (필수) 🔴

### 2.1 개발 환경 Setup 스크립트

**파일**: `scripts/setup_dev_environment.sh`

**Claude CLI 실행 내용**:

전체 스크립트를 생성. 포함 사항:
1. Python 3.11 버전 확인
2. .venv 가상환경 생성
3. 가상환경 활성화
4. pip 업그레이드
5. requirements-lock.txt 설치 (있으면), 없으면 requirements.txt
6. .env 파일 확인 및 생성 안내
7. PYTHONPATH 설정 안내
8. Qdrant 연결 확인
9. 완료 메시지 및 다음 단계 안내

**스크립트 구조**:
```bash
#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 RAG Enterprise 개발 환경 설정"
echo "=================================="

# 1. Python 버전 확인
# ... (상세 내용)

# 2-9. 나머지 단계
# ... (상세 내용)

echo "✅ 환경 설정 완료!"
```

**Write 명령어**:
- file_path: `/home/user/rag-enterprise/scripts/setup_dev_environment.sh`
- content: (전체 스크립트)

**실행 권한 부여**:
```bash
chmod +x scripts/setup_dev_environment.sh
```

**테스트**:
```bash
./scripts/setup_dev_environment.sh --help
```

---

### 2.2 데이터 준비 스크립트 템플릿

**파일**: `scripts/prepare_data.sh`

**Claude CLI 실행 내용**:

스크립트 생성. 포함 사항:
1. Qdrant snapshot 다운로드 옵션
2. 원본 데이터에서 임베딩 옵션
3. 샘플 데이터 생성 옵션
4. 진행 상황 표시

**Write 명령어**:
- file_path: `/home/user/rag-enterprise/scripts/prepare_data.sh`

---

## Phase 3: 검증 스크립트 (필수) 🔴

### 3.1 환경 검증 스크립트

**파일**: `scripts/verify_environment.sh`

**Claude CLI 실행 내용**:

검증 스크립트 생성. 체크 항목:
1. Python 버전 (3.11.x)
2. 가상환경 활성화 여부
3. PYTHONPATH 설정 여부
4. .env 파일 존재 여부
5. .env 필수 변수 (QDRANT_HOST, USE_VECTOR_RAG, QDRANT_COLLECTION)
6. Qdrant 실행 여부
7. onehago_v2 collection 존재 여부
8. 필수 Python 패키지 설치 여부

**출력 형식**:
```
✅ Python: 3.11.14
✅ 가상환경: 활성화됨
✅ PYTHONPATH: 설정됨
✅ .env: 존재
   ✅ QDRANT_HOST=localhost
   ✅ USE_VECTOR_RAG=true
✅ Qdrant: 실행 중
   ✅ onehago_v2 collection 존재 (22,870 vectors)
✅ FastAPI
✅ Qdrant Client
✅ Sentence Transformers

================================
✅ 모든 검증 통과!
================================
```

**Write 명령어**:
- file_path: `/home/user/rag-enterprise/scripts/verify_environment.sh`

**실행 권한**:
```bash
chmod +x scripts/verify_environment.sh
```

---

### 3.2 데이터 검증 스크립트

**파일**: `scripts/verify_data.sh`

**Claude CLI 실행 내용**:

Qdrant collection 검증. 체크 항목:
1. onehago_v2 collection 존재
2. Vector 개수 (22,870개)
3. Dimension (384)
4. Payload schema (10개 필드)
5. 샘플 검색 테스트

**Write 명령어**:
- file_path: `/home/user/rag-enterprise/scripts/verify_data.sh`

---

## Phase 4: 문서화 (필수) 🔴

### 4.1 데이터 준비 가이드

**파일**: `docs/DATA_PREPARATION.md`

**Claude CLI 실행 내용**:

포함 사항:
1. Option 1: Qdrant Snapshot 복원 (빠름, 5분)
   - 전제조건
   - 다운로드 방법
   - 복원 절차
   - 검증 방법

2. Option 2: 원본 데이터에서 임베딩 (느림, 2-3시간)
   - 전제조건
   - 데이터 다운로드
   - 임베딩 스크립트 실행
   - 진행 상황 모니터링

3. Option 3: 샘플 데이터 (테스트용, 1분)
   - 용도 설명
   - 생성 방법

4. 검증 방법

**Write 명령어**:
- file_path: `/home/user/rag-enterprise/docs/DATA_PREPARATION.md`

---

### 4.2 환경 동일성 가이드

**파일**: `docs/ENVIRONMENT_PARITY.md`

**Claude CLI 실행 내용**:

포함 사항:
1. 목표 설명
2. 환경별 차이점 (Claude Code CLI vs Mac 로컬)
3. 공통 요구사항
4. Troubleshooting (자주 발생하는 문제)
5. Quick Check 명령어

**Write 명령어**:
- file_path: `/home/user/rag-enterprise/docs/ENVIRONMENT_PARITY.md`

---

### 4.3 로컬 설정 가이드

**파일**: `docs/LOCAL_SETUP.md`

**Claude CLI 실행 내용**:

포함 사항:
1. Gitignored 파일 관리 전략
2. .env 설정 예시
3. .venv 생성 방법
4. PYTHONPATH 설정 (Mac, Linux, Windows)
5. 데이터 디렉토리 구조
6. Mac vs Docker 차이점

**Write 명령어**:
- file_path: `/home/user/rag-enterprise/docs/LOCAL_SETUP.md`

---

## Phase 5: README 및 기타 문서 업데이트 (권장) 🟠

### 5.1 README.md 업데이트

**Claude CLI 실행 내용**:

**기존 Quick Start 섹션을 확장**:

```markdown
## Quick Start

### Prerequisites

- Python 3.11.14 (required)
- Docker Desktop or Colima
- 10GB free disk space

### Installation

```bash
# 1. Clone
git clone <repo-url> && cd rag-enterprise

# 2. Automated Setup
./scripts/setup_dev_environment.sh

# 3. Verify
./scripts/verify_environment.sh

# 4. Prepare Data (choose one)
./scripts/prepare_data.sh --snapshot    # Fast (5 min)
./scripts/prepare_data.sh --sample      # Test (1 min)

# 5. Run
python scripts/run_chat_server.py
```

### Manual Setup (if automated fails)

See `docs/LOCAL_SETUP.md`
```

**Edit 명령어**:
- file_path: `/home/user/rag-enterprise/README.md`
- old_string: (기존 Quick Start)
- new_string: (새 Quick Start)

---

### 5.2 CONTRIBUTING.md 생성

**파일**: `CONTRIBUTING.md`

**Claude CLI 실행 내용**:

포함 사항:
1. 기여 방법 개요
2. 개발 환경 설정
3. 브랜치 전략
4. 커밋 메시지 규칙
5. PR 생성 방법
6. 코드 리뷰 프로세스

**Write 명령어**:
- file_path: `/home/user/rag-enterprise/CONTRIBUTING.md`

---

### 5.3 LICENSE 파일 생성

**파일**: `LICENSE`

**Claude CLI 실행 내용**:

MIT License 템플릿 사용

**Write 명령어**:
- file_path: `/home/user/rag-enterprise/LICENSE`

---

## Phase 6: GitHub Templates (권장) 🟠

### 6.1 Pull Request Template

**파일**: `.github/PULL_REQUEST_TEMPLATE.md`

**Claude CLI 실행 내용**:

템플릿 생성:
```markdown
## Description

<!-- 변경 사항을 간략히 설명해주세요 -->

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Checklist

- [ ] 코드가 프로젝트 스타일을 따름
- [ ] 자체 코드 리뷰 완료
- [ ] 주석 추가 (복잡한 부분)
- [ ] 문서 업데이트
- [ ] 테스트 추가/업데이트
- [ ] 모든 테스트 통과
- [ ] 환경 검증 통과 (`./scripts/verify_environment.sh`)

## Testing

<!-- 테스트 방법을 설명해주세요 -->

```bash
# 테스트 실행 명령어
pytest tests/
```

## Related Issues

<!-- 관련 이슈 번호 -->
Closes #
```

**Write 명령어**:
- file_path: `/home/user/rag-enterprise/.github/PULL_REQUEST_TEMPLATE.md`

---

### 6.2 Bug Report Template

**파일**: `.github/ISSUE_TEMPLATE/bug_report.md`

**Claude CLI 실행 내용**:

템플릿 생성 (GitHub Issue Template 형식)

**Write 명령어**:
- file_path: `/home/user/rag-enterprise/.github/ISSUE_TEMPLATE/bug_report.md`

---

### 6.3 Feature Request Template

**파일**: `.github/ISSUE_TEMPLATE/feature_request.md`

**Claude CLI 실행 내용**:

템플릿 생성

**Write 명령어**:
- file_path: `/home/user/rag-enterprise/.github/ISSUE_TEMPLATE/feature_request.md`

---

## Phase 7: 최종 검증 및 커밋 (필수) 🔴

### 7.1 생성된 파일 확인

**Claude CLI 실행 내용**:

```bash
# 생성된 파일 목록 확인
ls -la .python-version
ls -la requirements-lock.txt
ls -la scripts/setup_dev_environment.sh
ls -la scripts/verify_environment.sh
ls -la scripts/verify_data.sh
ls -la scripts/prepare_data.sh
ls -la docs/DATA_PREPARATION.md
ls -la docs/ENVIRONMENT_PARITY.md
ls -la docs/LOCAL_SETUP.md
ls -la CONTRIBUTING.md
ls -la LICENSE
ls -la .github/PULL_REQUEST_TEMPLATE.md
```

**검증**:
- 모든 파일 존재 확인
- 실행 권한 확인 (.sh 파일)

---

### 7.2 Git 상태 확인

**Claude CLI 실행 내용**:

```bash
git status
```

**예상 출력**:
```
Untracked files:
  .python-version
  requirements-lock.txt
  scripts/setup_dev_environment.sh
  scripts/verify_environment.sh
  scripts/verify_data.sh
  scripts/prepare_data.sh
  docs/DATA_PREPARATION.md
  docs/ENVIRONMENT_PARITY.md
  docs/LOCAL_SETUP.md
  CONTRIBUTING.md
  LICENSE
  .github/PULL_REQUEST_TEMPLATE.md
  .github/ISSUE_TEMPLATE/bug_report.md
  .github/ISSUE_TEMPLATE/feature_request.md

Modified files:
  README.md
  requirements.txt
```

---

### 7.3 커밋 준비

**Claude CLI 실행 내용**:

여러 커밋으로 분리:

**커밋 1: 버전 고정**
```bash
git add .python-version requirements-lock.txt requirements.txt
git commit -m "chore: Pin Python and dependency versions for environment parity

- Add .python-version (3.11.14)
- Add requirements-lock.txt with exact versions
- Update requirements.txt: >= to == for critical packages

This ensures consistent behavior across all development environments."
```

**커밋 2: 자동화 스크립트**
```bash
git add scripts/setup_dev_environment.sh scripts/verify_environment.sh scripts/verify_data.sh scripts/prepare_data.sh
git commit -m "feat: Add automated environment setup and verification scripts

- setup_dev_environment.sh: One-command dev environment setup
- verify_environment.sh: Comprehensive environment validation
- verify_data.sh: Qdrant data validation
- prepare_data.sh: Automated data preparation (snapshot/embedding/sample)

These scripts ensure consistent environment setup across all developers."
```

**커밋 3: 문서화**
```bash
git add docs/DATA_PREPARATION.md docs/ENVIRONMENT_PARITY.md docs/LOCAL_SETUP.md CONTRIBUTING.md LICENSE
git commit -m "docs: Add comprehensive environment and contribution guides

- DATA_PREPARATION.md: Three options for data setup
- ENVIRONMENT_PARITY.md: Web vs CLI environment consistency
- LOCAL_SETUP.md: Local development setup guide
- CONTRIBUTING.md: Contribution guidelines
- LICENSE: MIT License

These docs enable seamless onboarding and collaboration."
```

**커밋 4: GitHub Templates**
```bash
git add .github/PULL_REQUEST_TEMPLATE.md .github/ISSUE_TEMPLATE/
git commit -m "feat: Add GitHub PR and Issue templates

- PR template with checklist
- Bug report template
- Feature request template

Standardizes contribution process."
```

**커밋 5: README 업데이트**
```bash
git add README.md
git commit -m "docs: Update README with automated setup instructions

- Add prerequisites
- Update Quick Start with automated setup
- Link to new documentation"
```

---

### 7.4 최종 푸시

**Claude CLI 실행 내용**:

```bash
git push -u origin claude/korean-greeting-test-011CUoxjDrMsTdm9SPcHK8qh
```

---

## Phase 8: 테스트 및 검증 (필수) 🔴

### 8.1 스크립트 실행 테스트

**Mac 로컬에서 테스트** (사용자가 직접):

```bash
# 1. Setup 스크립트 테스트
./scripts/setup_dev_environment.sh

# 2. 검증 스크립트 테스트
./scripts/verify_environment.sh

# 3. 데이터 검증 (Qdrant 있다면)
./scripts/verify_data.sh
```

**예상 결과**:
- ✅ 모든 검증 통과
- 또는 명확한 오류 메시지와 해결 방법 표시

---

### 8.2 신규 개발자 시뮬레이션

**새 디렉토리에서 테스트**:

```bash
# 1. Clone
git clone <repo> test-env && cd test-env

# 2. Checkout PR 브랜치
git checkout claude/korean-greeting-test-011CUoxjDrMsTdm9SPcHK8qh

# 3. Setup
./scripts/setup_dev_environment.sh

# 4. Verify
./scripts/verify_environment.sh

# 5. Expected: 모든 검증 통과 (데이터 제외)
```

---

## 📊 완료 체크리스트

### Phase 1: 버전 고정
- [ ] `.python-version` 생성
- [ ] `requirements-lock.txt` 생성
- [ ] `requirements.txt` 업데이트 (>= → ==)

### Phase 2: 자동화 스크립트
- [ ] `scripts/setup_dev_environment.sh` 생성
- [ ] `scripts/prepare_data.sh` 생성
- [ ] 실행 권한 부여

### Phase 3: 검증 스크립트
- [ ] `scripts/verify_environment.sh` 생성
- [ ] `scripts/verify_data.sh` 생성
- [ ] 실행 권한 부여

### Phase 4: 문서화
- [ ] `docs/DATA_PREPARATION.md` 생성
- [ ] `docs/ENVIRONMENT_PARITY.md` 생성
- [ ] `docs/LOCAL_SETUP.md` 생성

### Phase 5: 기타 문서
- [ ] `README.md` 업데이트
- [ ] `CONTRIBUTING.md` 생성
- [ ] `LICENSE` 생성

### Phase 6: GitHub Templates
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` 생성
- [ ] `.github/ISSUE_TEMPLATE/bug_report.md` 생성
- [ ] `.github/ISSUE_TEMPLATE/feature_request.md` 생성

### Phase 7: Git 커밋
- [ ] 5개 커밋 생성
- [ ] 푸시 완료

### Phase 8: 검증
- [ ] 스크립트 테스트 완료
- [ ] 신규 개발자 시뮬레이션 통과

---

## 🎯 예상 결과

완료 후:
- ✅ 누구나 `./scripts/setup_dev_environment.sh` 한 번으로 환경 구축
- ✅ `./scripts/verify_environment.sh`로 즉시 검증
- ✅ Python 3.11.14, 의존성 버전 고정으로 일관성 보장
- ✅ 완전한 문서화로 온보딩 시간 90% 단축
- ✅ GitHub Templates로 기여 프로세스 표준화

---

## 💡 Claude CLI 사용 예시

**사용자**:
```
docs/CLAUDE_CLI_WORKFLOW.md를 읽고 Phase 1부터 시작해줘
```

**Claude CLI**:
```
Phase 1.1을 시작합니다.
.python-version 파일을 생성하겠습니다...
[Write 실행]
완료했습니다.

Phase 1.2를 시작합니다.
pip freeze로 설치된 패키지 목록을 가져와서...
[Bash 실행 → Write 실행]
완료했습니다.

Phase 1.3을 시작합니다...
```

---

**End of Workflow Guide**
