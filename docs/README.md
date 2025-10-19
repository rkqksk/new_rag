# 📚 Documentation

프로젝트의 기술 문서, 아키텍처 설계 및 API 명세를 관리하는 폴더입니다.

## 📁 폴더 구조

```
docs/
├── architecture/          # 시스템 아키텍처 설계 문서
│   ├── system-design.md
│   └── database-schema.md
├── api/                   # API 명세 및 레퍼런스
│   ├── rest-api.md
│   └── endpoints.md
├── guides/                # 개발 가이드 및 튜토리얼
│   ├── getting-started.md
│   └── deployment.md
└── assets/                # 다이어그램, 이미지 등
```

## 🎯 주요 파일 설명

- **architecture/**: 시스템 구조, 데이터 흐름, ERD 등 설계 문서
- **api/**: RESTful API 엔드포인트, 요청/응답 스펙, 인증 방식
- **guides/**: 프로젝트 설정, 배포, 트러블슈팅 가이드
- **assets/**: 문서에 사용되는 이미지 및 다이어그램 파일

## 🚀 빠른 시작

1. **아키텍처 이해**: `architecture/system-design.md` 참고
2. **API 사용**: `api/rest-api.md`에서 엔드포인트 확인
3. **개발 시작**: `guides/getting-started.md` 따라하기

## 🔗 관련 문서

### 핵심 문서
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 5-layer system architecture
- [TECH_STACK.md](./TECH_STACK.md) - Technology stack and tools
- [TESTING.md](./TESTING.md) - Testing strategy and patterns
- [PERFORMANCE.md](./PERFORMANCE.md) - Performance optimization
- [OPERATIONS.md](./OPERATIONS.md) - Deployment and operations

### Observability Documentation (NEW)
- **[OBSERVABILITY_INDEX.md](./OBSERVABILITY_INDEX.md)** - Start here for health checks & metrics
- [OBSERVABILITY_ARCHITECTURE.md](./OBSERVABILITY_ARCHITECTURE.md) - Complete technical specification (49KB)
- [OBSERVABILITY_QUICKSTART.md](./OBSERVABILITY_QUICKSTART.md) - Implementation guide (20KB)
- [OBSERVABILITY_DESIGN_DECISIONS.md](./OBSERVABILITY_DESIGN_DECISIONS.md) - Design rationale (16KB)
- [OBSERVABILITY_VISUAL_REFERENCE.md](./OBSERVABILITY_VISUAL_REFERENCE.md) - Diagrams and flows (47KB)

## 📝 문서 작성 가이드

- Markdown 형식 사용
- 다이어그램은 Mermaid 또는 이미지로 작성
- 코드 예제는 언어별 syntax highlighting 적용