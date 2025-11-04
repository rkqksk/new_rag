# RAG Cloud Integration Enhanced Plan - PART 3

**Date**: 2025-10-20
**Status**: 최종 (타임라인 + 실행 계획)

---

## 7️⃣ 최종 타임라인 (6주)

### Week 1: OAuth2 + Database Schema (40h)
**담당**: Dev1 (1명)

```
Day 1-2: PostgreSQL 스키마 설계
├─ cloud_sources (OneDrive/Google Drive 연결)
├─ document_permissions (RBAC)
├─ processing_jobs (상태 추적)
└─ sync_events (감사 로그)

Day 2-3: OAuth2 구현
├─ Microsoft Graph API (OneDrive)
├─ Google Drive API v3
├─ JWT + Refresh Token 관리
└─ Encrypted credential storage

Day 4: API 엔드포인트
├─ POST /cloud-sources (연결 추가)
├─ GET /cloud-sources/{id}/authorize (OAuth redirect)
└─ POST /webhooks/{provider} (웹훅 수신)

결과: 2명 포함 모두 OneDrive/Google Drive 계정 연동 가능
```

**테스트**: Chat UI에서 "클라우드 연결하기" 버튼 작동 확인

---

### Week 2: Cloud Adapters + Sync Pipeline (42h)
**담당**: Dev1 + Dev2 (병렬)

```
Dev1: OneDrive Adapter
├─ Delta Query 구현
├─ File list_files_delta()
└─ download_file(SHA256 중복 감지)

Dev2: Google Drive Adapter (동시 진행)
├─ modifiedTime 기반 증분 동기화
├─ Changes API 통합
└─ Push notification 핸들러

공통 (Day 5):
├─ Celery 작업 큐 설정
├─ SHA256 캐시 시스템
└─ 동기화 상태 대시보드

결과: 1000개 파일 5분 내 초기 동기화, 10초 증분 동기화
```

**테스트**: 클라우드 폴더 선택 후 파일 리스트 표시 확인

---

### Week 3: PaddleOCR-VL Integration (40h)
**담당**: Dev2 (전담)

```
Day 1-2: PaddleOCR-VL 설치 및 테스트
├─ paddlepaddle GPU 설정
├─ 모델 다운로드 (500MB)
└─ 테스트 문서 처리 (거래명세서)

Day 3-4: Processing Pipeline
├─ 파일 타입 자동 감지 (기본/고급)
├─ 거래명세서 → JSON 구조화
├─ 표 → Qdrant 청크
└─ 이미지 임베딩

Day 5: 최적화
├─ GPU 가속 검증 (15초 vs 40초 CPU)
├─ 배치 처리 (100개 문서 25분)
└─ 오류 처리 (파일 손상, 타임아웃)

결과: 거래명세서 95% 정확도로 처리
```

**테스트**: 샘플 거래명세서 업로드 → JSON 구조 확인

---

### Week 4: Webhook + Real-time (40h)
**담당**: Dev1 + Dev3 (병렬)

```
Dev1: Webhook 구현
├─ OneDrive Subscription API
├─ Google Drive Watch API
├─ Celery Beat (자동 갱신)
└─ 재시도 로직 (exponential backoff)

Dev3: WebSocket Real-time UI (동시 진행)
├─ 처리 상태 브로드캐스트
├─ 진행률 표시
└─ 오류 알림

테스트:
├─ 클라우드에 파일 추가
└─ 1-5초 내 Chat UI에 표시 확인

결과: 실시간 동기화 완전 작동
```

**테스트**: 파일 업로드 후 즉시 Chat UI 업데이트 확인

---

### Week 5: RBAC + Chat Integration (30h)
**담당**: Dev2 + Dev3 (병렬)

```
Dev2: RBAC 데이터 레이어
├─ 5단계 권한 검증
├─ Qdrant 페이로드 필터
├─ Redis 권한 캐싱 (1h TTL)
└─ 감사 로그 (access_audit)

Dev3: Chat UI 통합 (동시 진행)
├─ 클라우드 문서 컨텍스트
├─ Citation 추적 (신뢰도 점수)
├─ RBAC 마스킹 (권한 없음 문서)
└─ 소스 필터링

결과: 사용자 권한별 다른 문서 보임
```

**테스트**: 다른 권한의 사용자로 로그인 → 문서 접근 제한 확인

---

### Week 6: 최적화 + 통합 테스트 (20h)
**담당**: 전체 팀

```
├─ 성능 측정 (동기화 속도, OCR 정확도)
├─ 부하 테스트 (100 concurrent users)
├─ 오류 복구 시나리오
├─ 문서 마이그레이션 (기존 → 클라우드)
└─ 배포 준비 (Docker, 모니터링)

결과: MVP 배포 준비 완료
```

---

## 📊 총 비용 및 일정

| 시나리오 | 달력 기간 | 총 비용 | 병렬화 | 특징 |
|---------|---------|-------|--------|------|
| 1명 Full-time | 8주 | $16,000 | 0% | 느림, 저비용 |
| **2명 Full-time** ⭐ | **6주** | **$24,000** | **40%** | **최적 속도-비용** |
| 3명 Full-time | 5주 | $30,000 | 50% | 통신 오버헤드 |

**권장**: **2명 병렬 (6주, $24,000)**
- Dev1: OneDrive/Google Drive Adapters
- Dev2: PaddleOCR-VL + RBAC

---

## ✅ 최종 승인 체크리스트

실행 전 확인 사항:

- [ ] **클라우드 제공자**: OneDrive + Google Drive 우선?
- [ ] **OCR**: PaddleOCR-VL 도입?
- [ ] **동기화**: Webhook 우선, Periodic 백업?
- [ ] **RBAC**: 5단계 권한 구조 적용?
- [ ] **팀 리소스**: 2명 6주 일정 가능?
- [ ] **Chat UI 테스트**: 각 Phase 후 실제 테스트?

모두 확인되면 → **Haiku 4.5 실행 모드 시작**

---

## 8️⃣ 위험 요소 및 완화 전략

### 8.1 주요 위험 분석

| 위험 | 심각도 | 발생 시점 | 영향 | 완화 전략 |
|------|--------|---------|------|---------|
| OneDrive API 레이트 제한 | 🟡 Medium | Week 2 | 동기화 지연 | Exponential backoff + 요청 큐잉 |
| PaddleOCR GPU 메모리 부족 | 🟡 Medium | Week 3 | OCR 실패 | 배치 크기 감소 + CPU 폴백 |
| Webhook 전달 실패 | 🟡 Medium | Week 4 | 실시간 감지 안 됨 | Periodic sync (1시간 백업) |
| 기존 1,587개 문서 RBAC 할당 오류 | 🔴 High | Week 5 | 권한 없는 접근 또는 과도한 차단 | 테스트 데이터로 검증 후 배포 |
| OAuth 토큰 갱신 실패 | 🔴 High | Week 6 | 클라우드 접근 불가 | 자동 재인증 + 사용자 알림 |
| Chat UI WebSocket 연결 끊김 | 🟡 Medium | Week 4 | 실시간 업데이트 손실 | 자동 재연결 + fallback 폴링 |

### 8.2 완화 계획 상세

```python
# OneDrive API 레이트 제한 대응
class RateLimitHandler:
    def __init__(self, max_retries=5):
        self.max_retries = max_retries
        self.backoff_factor = 2

    async def call_with_retry(self, api_func, *args):
        """지수 백오프로 재시도"""
        for attempt in range(self.max_retries):
            try:
                return await api_func(*args)
            except RateLimitError as e:
                wait_time = self.backoff_factor ** attempt
                logger.warning(f"Rate limit hit, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
                if attempt == self.max_retries - 1:
                    raise

# PaddleOCR 메모리 오류 대응
async def process_with_fallback(file_path):
    """GPU 실패 시 CPU로 폴백"""
    try:
        return await paddle_ocr.process(file_path, use_gpu=True)
    except RuntimeError as e:
        if "CUDA" in str(e) or "memory" in str(e):
            logger.warning("GPU OCR failed, falling back to CPU")
            return await paddle_ocr.process(file_path, use_gpu=False)
        raise

# Webhook 실패 시 주기적 동기화
@celery_app.task
async def periodic_sync_backup():
    """Webhook 통지 실패 대비 주기적 동기화"""
    async for source in db.iterate_cloud_sources():
        if source['webhook_status'] != 'active':
            await perform_delta_sync(source['id'])
```

---

## 9️⃣ 작업 의존성 맵

### 9.1 Critical Path (순차 필수)

```
Day 1-2: PostgreSQL 스키마
         ↓ (필수: DB 없이 진행 불가)
Day 2-3: OAuth2 구현
         ↓ (필수: 토큰 저장소 필요)
Day 4: API 엔드포인트
         ↓ (필수: Cloud 연결 필요)
Week 2: Cloud Adapters (병렬 가능)
         ├─ Dev1: OneDrive Adapter
         └─ Dev2: Google Drive Adapter
         ↓ (필수: 파일 다운로드 필요)
Week 3: PaddleOCR-VL
         ↓ (필수: 처리된 파일 필요)
Week 4: Webhook + Real-time (병렬 가능)
         ├─ Dev1: Webhook
         └─ Dev3: WebSocket UI
         ↓ (필수: 동기화 필요)
Week 5: RBAC (병렬 가능)
         ├─ Dev2: 데이터 레이어
         └─ Dev3: Chat UI
         ↓ (필수: 권한 체크 필요)
Week 6: 통합 테스트
```

### 9.2 병렬화 가능 작업

```
독립적 (동시 진행 가능):
├─ Dev1: OneDrive Adapter (Week 2)
├─ Dev2: Google Drive Adapter (Week 2)
├─ Dev1: Webhook 구현 (Week 4)
└─ Dev3: WebSocket UI (Week 4)

단, 이전 Phase 완료 필수:
├─ PaddleOCR-VL (Week 3) → API 엔드포인트 필요
├─ RBAC (Week 5) → PaddleOCR-VL 완료 필요
└─ 통합 테스트 (Week 6) → 모든 Phase 완료 필수
```

---

## 🔟 검증 기준 (Go/No-Go)

### 10.1 Phase별 검증 기준

**Phase 1: OAuth2 + Database (기준: 모두 PASS)**
```
✅ PASS 기준:
- [ ] PostgreSQL 스키마 생성 성공 (3개 테이블)
- [ ] OAuth2 토큰 암호화/복호화 작동
- [ ] 2명의 테스트 사용자 OneDrive/Google Drive 연동 성공
- [ ] API 엔드포인트 응답 시간 <200ms

❌ NO-GO 기준:
- 토큰 저장 실패
- 스키마 마이그레이션 오류
- OAuth 콜백 루프
→ Phase 2 진행 X
```

**Phase 2: Cloud Adapters (기준: 모두 PASS)**
```
✅ PASS 기준:
- [ ] 1000개 파일 초기 동기화 <5분
- [ ] 증분 동기화 <10초
- [ ] SHA256 중복 감지 100% 정확도
- [ ] 파일 다운로드 오류율 <1%

❌ NO-GO 기준:
- 초기 동기화 >10분
- 중복 감지 오류 (같은 파일 2번 다운로드)
→ Phase 3 진행 X (최적화 필요)
```

**Phase 3: PaddleOCR-VL (기준: 모두 PASS)**
```
✅ PASS 기준:
- [ ] 거래명세서 OCR 정확도 >90%
- [ ] 표 구조 보존 정확도 >95%
- [ ] 처리 시간 <15초 (GPU), <40초 (CPU)
- [ ] 100개 문서 배치 처리 성공

❌ NO-GO 기준:
- OCR 정확도 <85%
- 표 구조 손실 >5%
- 처리 시간 >60초
→ Phase 4 진행 X (모델 파라미터 조정 필요)
```

**Phase 4: Webhook + Real-time (기준: 모두 PASS)**
```
✅ PASS 기준:
- [ ] Webhook 수신 <5초 (OneDrive, Google Drive)
- [ ] WebSocket 연결 안정성 >99%
- [ ] Chat UI 실시간 업데이트 지연 <1초
- [ ] 100 concurrent connections 에러율 <0.1%

❌ NO-GO 기준:
- Webhook 수신 >10초
- WebSocket 연결 끊김 횟수 >10/시간
→ Phase 5 진행 X (네트워크 최적화 필요)
```

**Phase 5: RBAC (기준: 모두 PASS)**
```
✅ PASS 기준:
- [ ] 권한 검증 오류율 <0.01%
- [ ] 1,587개 문서 마이그레이션 100% 성공
- [ ] Redis 캐싱 히트율 >95%
- [ ] 검색 쿼리 필터 시간 <100ms

❌ NO-GO 기준:
- 권한 검증 오류 (부정 접근 허용 또는 정상 접근 차단)
- 마이그레이션 실패 >1% (>15개 문서)
→ Phase 6 진행 X (권한 데이터 재검증)
```

**Phase 6: 통합 테스트 (기준: 모두 PASS)**
```
✅ PASS 기준:
- [ ] E2E 시나리오 성공률 >99%
- [ ] 100 concurrent users 처리 가능
- [ ] Chat UI에서 클라우드 문서 검색 작동
- [ ] 부하 테스트 (1시간) 안정성 >99.5%
- [ ] 배포 체크리스트 100% 완료

✅ MVP 배포 준비 완료
```

---

## 1️⃣1️⃣ 배포 전략

### 11.1 Blue-Green 배포

```
Current (Blue):
├─ 기존 RAG 시스템 운영 중
└─ 클라우드 통합 없음

Next (Green):
├─ 새로운 클라우드 통합 버전
└─ 모든 Phase 완료

전환:
1. Green 배포 (별도 인스턴스)
2. 헬스 체크 통과
3. 트래픽 점진적 전환 (10% → 50% → 100%)
4. 모니터링 (24시간)
5. Blue 유지 (즉시 롤백 대비)
```

### 11.2 롤백 계획

```
Rollback 트리거:
- 에러율 >5% (실시간 모니터링)
- 응답 시간 >2초 (SLA 위반)
- 클라우드 파일 손실 감지
- RBAC 권한 오류 (부정 접근)

Rollback 절차:
1. 즉시 트래픽 100% Blue로 전환
2. 원인 분석 (로그 수집)
3. 롤백 이후 수정 (새 빌드)
4. 다시 배포 (Canary 10% 시작)

예상 RTO: <5분 (트래픽 전환)
예상 RPO: 0분 (상태 비저장 앱)
```

### 11.3 배포 체크리스트

```yaml
Pre-Deployment:
  - [ ] 모든 Phase 검증 기준 PASS
  - [ ] E2E 테스트 성공률 >99%
  - [ ] 보안 감시 완료 (OWASP 10)
  - [ ] 성능 테스트 완료 (부하 테스트)
  - [ ] 데이터 백업 완료
  - [ ] 롤백 프로세스 테스트 완료

Deployment:
  - [ ] 배포 팀 준비 (온콜 엔지니어)
  - [ ] Monitoring 대시보드 준비
  - [ ] 커뮤니케이션 채널 활성화
  - [ ] Green 배포 시작
  - [ ] 헬스 체크 (자동 + 수동)
  - [ ] 5% 트래픽 전환
  - [ ] 15분 모니터링
  - [ ] 25% 트래픽 전환
  - [ ] 30분 모니터링
  - [ ] 100% 트래픽 전환
  - [ ] 24시간 안정성 모니터링

Post-Deployment:
  - [ ] 성능 메트릭 정상 확인
  - [ ] 사용자 피드백 수집
  - [ ] 로그 분석 (에러, 경고)
  - [ ] 용량 계획 재평가
  - [ ] 문서 업데이트
```

---

## 1️⃣2️⃣ 최종 승인 체크리스트 (상세)

### 12.1 기술 아키텍처 승인

- [ ] **OneDrive/Google Drive VFS 패턴**: 승인됨?
- [ ] **OAuth2 토큰 암호화 (Fernet)**: 승인됨?
- [ ] **PaddleOCR-VL (95% 정확도)**: 도입 결정?
- [ ] **RBAC 5단계 (role-based + classification)**: 승인됨?
- [ ] **Webhook + Periodic 백업**: 동기화 전략 확정?

### 12.2 리소스 및 일정 승인

- [ ] **팀 리소스: 2명 Full-time 6주**: 가능한가?
- [ ] **개발 환경**: Staging 환경 준비됨?
- [ ] **GPU 인프라**: PaddleOCR-VL용 GPU 확보?
- [ ] **배포 일정**: 2025년 Q4 중 완료 가능?

### 12.3 비용 및 운영 승인

- [ ] **개발 비용: $24,000**: 예산 승인됨?
- [ ] **인프라 비용**: GPU 클라우드 + PaddleOCR 라이선스?
- [ ] **운영 체계**: 모니터링, 알림, 이슈 대응?
- [ ] **SLA**: 99.5% 가용성 목표 동의?

### 12.4 보안 및 준수 승인

- [ ] **OAuth 토큰 암호화**: 보안 검토 통과?
- [ ] **RBAC 권한 모델**: 정보 보안팀 승인?
- [ ] **감시 로깅**: 접근 감시 로그 정책 승인?
- [ ] **데이터 분류**: 5단계 분류 기준 확정?

### 12.5 사용자 및 테스트 승인

- [ ] **Chat UI 테스트**: 각 Phase 후 실제 테스트 가능?
- [ ] **베타 사용자**: 5-10명 테스트 참여 가능?
- [ ] **피드백 루프**: 주 1회 피드백 회의 가능?
- [ ] **배포 공지**: 사용자 커뮤니케이션 계획 수립?

---

**Status**: 🎯 최종 계획 + 보강 완료 - 모든 CheckList 검토 후 승인 요청

