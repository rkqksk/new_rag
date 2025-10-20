# RAG Cloud Integration 계획 - INDEX

**Date**: 2025-10-20
**Status**: 완료 (3부 + 보강 완료)
**Target**: NotebookLM-like Platform with Cloud Integration

---

## 📚 문서 구조

이 INDEX는 3개의 상세 계획 문서를 네비게이션하는 가이드입니다.

각 PART는 **독립적으로 완전**하며, 프로젝트 진행 중 필요한 PART만 참조할 수 있습니다.

---

## 🎯 PART 1: Cloud Integration 기술 (OneDrive/Google Drive VFS)

**파일**: `RAG_CLOUD_INTEGRATION_REVISED_PART1.md`

### 포함 내용

1. **기술 개요: VFS 패턴**
   - 클라우드 파일을 로컬 파일처럼 동작
   - OAuth2 인증 플로우
   - Delta API 동기화 (변경사항만 추적)

2. **OneDrive 구현 (Microsoft Graph API)**
   - Delta Query를 활용한 효율적 동기화
   - 첫 sync: 5분, 다음 sync: 10초
   - Webhook 자동 갱신 (3일 주기)

3. **Google Drive 구현**
   - modifiedTime 기반 증분 동기화
   - Push Notification (7일 유효)
   - Changes API 통합

4. **로컬 캐시 구조**
   - SHA256 중복 감지
   - SQLite 메타데이터 저장
   - 파일 해시 매핑

5. **처리 전략: 기본 vs 고급**
   - 파일 타입별 자동 선택 로직
   - 비용-효율 분석 (3가지 시나리오)
   - 선별 고급 처리 권장 (42% 비용 절감)

6. **Webhook 검증**
   - OneDrive Subscription API
   - Google Drive Watch API
   - Fallback 메커니즘 (Periodic + Full Resync)

7. **PostgreSQL 스키마** ⭐ (신규)
   - cloud_sources, processing_jobs, sync_events 테이블
   - OAuth 토큰 암호화 저장
   - Webhook 상태 관리

8. **API 엔드포인트 상세** ⭐ (신규)
   - 6가지 REST API 정의
   - 요청/응답 포맷
   - 오류 처리

9. **보안 & 암호화 전략** ⭐ (신규)
   - Fernet 기반 토큰 암호화
   - Webhook 서명 검증 (HMAC)
   - Google Drive Push 검증

10. **에러 처리 & 재시도** ⭐ (신규)
    - OAuth 토큰 자동 갱신
    - Exponential backoff 재시도
    - Celery 비동기 처리

---

## 🎯 PART 2: Advanced Processing + RBAC

**파일**: `RAG_CLOUD_INTEGRATION_REVISED_PART2.md`

### 포함 내용

1. **PaddleOCR-VL 기술 평가**
   - Tesseract vs EasyOCR vs PaddleOCR-VL 비교
   - 한국어 정확도: 95% (최고)
   - 표 구조 인식: JSON 자동 구조화
   - 처리 속도: 15초 (GPU), 40초 (CPU)

2. **거래명세서 처리 예시**
   - Tesseract 결과 (70% 정확도, 구조 손실)
   - PaddleOCR-VL 결과 (95% 정확도, JSON 구조)
   - Qdrant 저장 구조 (청크 단위)

3. **구현 계획**
   - 설치 명령어
   - 코드 예제
   - 성능 메트릭

4. **RBAC: 5단계 권한 모델**
   - 사용자 레벨: 1~10 (Guest ~ Super Admin)
   - 데이터 분류: 1~5 (Public ~ Secret)
   - Qdrant 메타데이터 필터링
   - API 이중 검증

5. **PaddleOCR-VL 환경 설정** ⭐ (신규)
   - PaddlePaddle GPU 설치
   - 모델 다운로드 (500MB)
   - Singleton 패턴으로 메모리 절약
   - 한국어 지원 (lang='ch')

6. **한국어 처리 최적화** ⭐ (신규)
   - 이미지 전처리 (CLAHE, 노이즈 제거, 이진화)
   - 한국어 유니코드 범위 (AC00-D7A3)
   - 신뢰도 점수 추출

7. **테스트 전략** ⭐ (신규)
   - OCR 정확도 검증 (Levenshtein 유사도)
   - 표 구조 보존 테스트
   - RBAC 접근 제어 테스트
   - 부서별 필터링 테스트

8. **RBAC 마이그레이션 전략** ⭐ (신규)
   - 기존 1,587개 문서에 권한 할당
   - 문서 타입별 정책 매핑
   - Qdrant 페이로드 업데이트
   - 감사 로그 기록

9. **모니터링 지표** ⭐ (신규)
   - OCR 성능 메트릭 (처리 시간, 정확도)
   - RBAC 접근 통계 (성공/실패)
   - Prometheus 통합

---

## 🎯 PART 3: 최종 타임라인 + 배포

**파일**: `RAG_CLOUD_INTEGRATION_REVISED_PART3.md`

### 포함 내용

1. **6주 상세 타임라인**
   - Week 1: OAuth2 + Database Schema (40h)
   - Week 2: Cloud Adapters + Sync (42h)
   - Week 3: PaddleOCR-VL (40h)
   - Week 4: Webhook + Real-time (40h)
   - Week 5: RBAC + Chat Integration (30h)
   - Week 6: 최적화 + 통합 테스트 (20h)

2. **팀 리소스 분석**
   - 1명 (8주), 2명 (6주) ⭐권장, 3명 (5주)
   - 병렬화 비율 (40%, 50%)
   - 비용 비교 ($16k ~ $30k)

3. **위험 요소 및 완화 전략** ⭐ (신규)
   - 6가지 주요 위험 식별
   - 심각도 별 분류 (Medium, High)
   - 구체적 완화 코드 제공

4. **작업 의존성 맵** ⭐ (신규)
   - Critical Path (순차 필수)
   - 병렬화 가능 작업
   - 데이터 흐름 시각화

5. **Phase별 검증 기준 (Go/No-Go)** ⭐ (신규)
   - Phase 1: OAuth2 + DB (PASS 기준 4개)
   - Phase 2: Cloud Adapters (PASS 기준 4개)
   - Phase 3: PaddleOCR-VL (PASS 기준 4개)
   - Phase 4: Webhook + Real-time (PASS 기준 4개)
   - Phase 5: RBAC (PASS 기준 4개)
   - Phase 6: 통합 테스트 (PASS 기준 5개)

6. **배포 전략** ⭐ (신규)
   - Blue-Green 배포
   - 롤백 계획 (RTO <5분)
   - 배포 체크리스트 (Pre/During/Post)

7. **최종 승인 체크리스트** ⭐ (신규)
   - 기술 아키텍처 (5개 항목)
   - 리소스 및 일정 (4개 항목)
   - 비용 및 운영 (4개 항목)
   - 보안 및 준수 (4개 항목)
   - 사용자 및 테스트 (4개 항목)

---

## 🔍 어떤 PART를 언제 참조할까?

### Phase 1 실행 중
📖 **PART 1 섹션 7-9** (PostgreSQL, API, 보안)
- PostgreSQL 스키마 구현
- API 엔드포인트 개발
- 토큰 암호화 구현

### Phase 2 실행 중
📖 **PART 1 섹션 1-6** (VFS, OneDrive/Google Drive, Webhook)
- Delta API 구현
- Fallback 메커니즘 설계
- 캐시 구조 구현

### Phase 3 실행 중
📖 **PART 2 섹션 1-6** (PaddleOCR-VL, 환경설정, 최적화)
- PaddleOCR-VL 설치
- 한국어 처리 최적화
- OCR 테스트 작성

### Phase 4 실행 중
📖 **PART 1 섹션 3 + PART 3 섹션 8** (Webhook 검증, 위험 완화)
- Webhook 구현
- 재시도 로직
- Rate limit 처리

### Phase 5 실행 중
📖 **PART 2 섹션 4-9** (RBAC, 마이그레이션, 모니터링)
- RBAC 구현
- 기존 문서 마이그레이션
- 감사 로그

### Phase 6 실행 중
📖 **PART 3 섹션 10-12** (검증 기준, 배포, 승인)
- 검증 기준 확인
- 배포 체크리스트
- 최종 승인

---

## 📊 빠른 참조

### 기술 결정사항
| 결정 | 권장안 | 참조 |
|------|--------|------|
| Cloud Provider | OneDrive + Google Drive | PART 1: 1-2절 |
| Processing | PaddleOCR-VL (95% 정확도) | PART 2: 1-3절 |
| OCR 선택 | 선별 고급 (30% 고급) | PART 1: 5절 |
| Sync 전략 | Webhook + Periodic 백업 | PART 1: 3-4절 |
| RBAC 구조 | 5단계 권한 + 분류 | PART 2: 4절 |

### 리소스 결정사항
| 항목 | 권장안 | 참조 |
|------|--------|------|
| 팀 구성 | 2명 Full-time | PART 3: 2절 |
| 일정 | 6주 | PART 3: 1절 |
| 비용 | $24,000 | PART 3: 2절 |
| 배포 | Blue-Green | PART 3: 11절 |

### 위험 및 검증
| 항목 | 세부사항 | 참조 |
|------|---------|------|
| 주요 위험 | 6가지 (레이트 제한, GPU 메모리 등) | PART 3: 8절 |
| Go/No-Go | Phase별 검증 기준 | PART 3: 10절 |
| 승인 체크리스트 | 21개 항목 | PART 3: 12절 |

---

## ✅ 프로젝트 진행 체크리스트

- [ ] **PART 1 완독**: VFS 기술 이해
- [ ] **PART 2 완독**: PaddleOCR-VL + RBAC 이해
- [ ] **PART 3 완독**: 타임라인 및 배포 계획 이해
- [ ] **최종 승인 체크리스트 작성** (PART 3: 12절)
- [ ] **Phase 1 시작**: OAuth2 + Database
- [ ] **각 Phase 후**: 해당 검증 기준 확인 (PART 3: 10절)
- [ ] **배포 전**: 배포 체크리스트 완료 (PART 3: 11절)

---

## 📞 문의 및 리뷰

각 PART는 **독립적으로 리뷰 가능**하며, 다음과 같이 진행합니다:

1. **기술 리뷰**: PART 1-2 기술 결정사항 검토
2. **일정 리뷰**: PART 3 타임라인 및 리소스 검토
3. **최종 승인**: PART 3 체크리스트 모두 체크 후 시작

---

**Status**: 🎯 계획 수립 완료 - Phase 1 실행 대기 중

**다음 단계**: 모든 체크리스트 검토 후 Haiku 4.5 실행 모드 시작

