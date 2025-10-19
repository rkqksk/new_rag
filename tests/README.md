# tests/

이 폴더는 프로젝트의 모든 테스트 코드를 포함합니다. pytest 프레임워크를 사용하여 단위 테스트, 통합 테스트, E2E 테스트를 관리합니다.

## 📁 폴더 구조

```
tests/
├── unit/              # 단위 테스트
├── integration/       # 통합 테스트
├── e2e/              # End-to-End 테스트
├── fixtures/         # 테스트 픽스처 및 목 데이터
├── conftest.py       # pytest 설정 및 공통 픽스처
└── README.md
```

## 🎯 각 폴더의 역할

- **unit/**: 개별 함수/클래스의 독립적인 테스트
- **integration/**: 여러 모듈 간 상호작용 테스트
- **e2e/**: 전체 시스템 워크플로우 테스트
- **fixtures/**: 재사용 가능한 테스트 데이터 및 설정
- **conftest.py**: 전역 pytest 설정 및 공유 픽스처

## 🚀 빠른 시작

```bash
# 모든 테스트 실행
pytest

# 특정 폴더 테스트
pytest tests/unit

# 커버리지 포함 실행
pytest --cov=src --cov-report=html

# 상세 출력
pytest -v
```

## 📋 커버리지 요구사항

- **최소 커버리지**: 80%
- **핵심 모듈**: 90% 이상
- **리포트 생성**: `htmlcov/index.html`

## 📚 상세 문서

- [테스트 가이드](../.claude/testing-guide.md)
- [픽스처 사용법](../.claude/fixtures-guide.md)
- [CI/CD 통합](../.claude/ci-cd.md)

## 🔧 주요 명령어

```bash
pytest -k "test_name"     # 특정 테스트 실행
pytest -m "slow"          # 마커별 실행
pytest --lf               # 실패한 테스트만 재실행
```