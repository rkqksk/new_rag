# App Directory

FastAPI 애플리케이션의 핵심 구조를 포함하는 디렉토리입니다.

## 📁 폴더 구조

```
app/
├── main.py              # FastAPI 애플리케이션 진입점
├── config.py            # 설정 및 환경 변수
├── dependencies.py      # 공통 의존성
├── routers/            # API 라우터
│   ├── __init__.py
│   ├── users.py
│   └── items.py
├── services/           # 비즈니스 로직
│   ├── __init__.py
│   ├── user_service.py
│   └── item_service.py
├── models/             # 데이터 모델
│   └── schemas.py
└── utils/              # 유틸리티 함수
    └── helpers.py
```

## 🎯 주요 구성 요소

- **main.py**: FastAPI 앱 초기화 및 라우터 등록
- **routers/**: API 엔드포인트 정의 (경로별 분리)
- **services/**: 비즈니스 로직 및 데이터 처리
- **models/**: Pydantic 스키마 및 데이터 모델
- **config.py**: 환경 설정 및 상수 관리
- **dependencies.py**: 인증, DB 세션 등 공통 의존성

## 🚀 빠른 시작

```bash
# 개발 서버 실행
uvicorn app.main:app --reload

# 또는
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API 문서: `http://localhost:8000/docs`

## 📖 아키텍처 패턴

- **라우터 계층**: HTTP 요청/응답 처리
- **서비스 계층**: 비즈니스 로직 구현
- **모델 계층**: 데이터 검증 및 직렬화

## 📚 상세 문서

- [프로젝트 구조 가이드](../.claude/project-structure.md)
- [API 개발 가이드](../.claude/api-development.md)
- [코딩 컨벤션](../.claude/coding-conventions.md)