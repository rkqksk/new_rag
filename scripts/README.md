# Scripts

유틸리티 스크립트 모음 및 자동화 도구를 제공합니다.

## 📁 폴더 구조

```
scripts/
├── setup/          # 초기 설정 스크립트
├── build/          # 빌드 자동화
├── deploy/         # 배포 스크립트
├── test/           # 테스트 유틸리티
└── utils/          # 공통 헬퍼 함수
```

## 🎯 주요 파일 설명

### Setup Scripts
- **`setup/init.sh`** - 프로젝트 초기 환경 설정
- **`setup/install-deps.sh`** - 의존성 자동 설치

### Build Scripts
- **`build/compile.sh`** - 소스 코드 컴파일
- **`build/bundle.sh`** - 프로덕션 번들 생성

### Deploy Scripts
- **`deploy/staging.sh`** - 스테이징 환경 배포
- **`deploy/production.sh`** - 프로덕션 배포

### Test Utilities
- **`test/run-tests.sh`** - 전체 테스트 실행
- **`test/coverage.sh`** - 코드 커버리지 분석

## 🚀 빠른 시작

```bash
# 프로젝트 초기 설정
./scripts/setup/init.sh

# 빌드 실행
./scripts/build/compile.sh

# 테스트 실행
./scripts/test/run-tests.sh

# 배포 (스테이징)
./scripts/deploy/staging.sh
```

## 💡 사용 팁

- 모든 스크립트는 프로젝트 루트에서 실행하세요
- 실행 권한이 필요한 경우: `chmod +x scripts/**/*.sh`
- 환경 변수는 `.env` 파일에서 관리됩니다

## 📚 상세 문서

- [스크립트 개발 가이드](../.claude/scripts-guide.md)
- [배포 프로세스](../.claude/deployment.md)
- [트러블슈팅](../.claude/troubleshooting.md)

---

**Note**: 스크립트 수정 시 반드시 테스트 후 커밋하세요.