# 📊 RAG Enterprise 운영 가이드

## 모니터링

### Prometheus 메트릭
```python
from prometheus_client import Counter, Histogram, Gauge

# 문서 처리
documents_processed = Counter('documents_processed_total', 'Total documents processed')
embedding_latency = Histogram('embedding_duration_seconds', 'Embedding generation time')

# 검색 성능
search_queries = Counter('search_queries_total', 'Total search queries')
search_latency = Histogram('search_duration_seconds', 'Search response time')
search_accuracy = Gauge('search_relevance_score', 'Average relevance score')

# 시스템 상태
system_health = Gauge('system_health_status', 'System health (1=healthy, 0=unhealthy)')
active_users = Gauge('active_users', 'Number of active users')
error_rate = Gauge('error_rate', 'Error rate percentage')
```

### 알림 정책
```yaml
Critical (즉시 대응):
  - 시스템 다운타임 (가용성 <95%)
  - 데이터 손실 감지
  - 보안 침해 시도 (3회 이상 실패)
  - API 에러율 >10%

Warning (1시간 내 대응):
  - 처리 지연 >5분
  - 메모리 사용률 >80%
  - 디스크 사용률 >85%
  - 에러율 >5%

Info (일일 리포트):
  - 일일 처리 통계
  - 모델 성능 리포트
  - 사용자 활동 분석
```

---

## 배포 전략

### Clean Deploy Policy
```bash
# clean_deploy.sh
1. 개발 전용 코드 제거
   - 디버그 로그
   - 테스트 데이터
   - 개발 엔드포인트

2. 테스트 데이터 삭제
   - data/test_*
   - temp/
   - *.tmp

3. 디버그 로그 비활성화
   - LOG_LEVEL=INFO

4. 프로덕션 설정 적용
   - ENVIRONMENT=production
   - ENABLE_MONITORING=true
   - ENABLE_MCP=false

5. 보안 검증 실행
   - Bandit (Python security)
   - Safety (dependency check)
   - Snyk (vulnerability scan)
```

### 환경별 설정
```ini
# .env.production
ENVIRONMENT=production
LOG_LEVEL=INFO
ENABLE_MONITORING=true
ENABLE_MCP=false
ENABLE_DEBUG=false
MAX_WORKERS=8
CACHE_TTL=3600

# .env.development
ENVIRONMENT=development
LOG_LEVEL=DEBUG
ENABLE_MONITORING=false
ENABLE_MCP=true
ENABLE_DEBUG=true
MAX_WORKERS=2
CACHE_TTL=60
```

---

## 보안

### 인증/인가
```yaml
JWT 토큰:
  - 발급: /api/auth/login
  - 갱신: /api/auth/refresh
  - 만료: 24시간 (access), 7일 (refresh)

RBAC:
  - 역할: super_admin, internal, client
  - 권한: resource:action (예: product:read)
  - 동적 권한 체크

API Rate Limiting:
  - 익명: 10 req/min
  - 인증: 100 req/min
  - Admin: 1000 req/min

IP Whitelist:
  - 관리자 페이지: 내부 IP만
  - API: 화이트리스트 또는 API 키
```

### 데이터 보안
```yaml
암호화:
  - 저장: AES-256-GCM
  - 전송: TLS 1.3
  - 민감 데이터 마스킹

Audit 로깅:
  - 모든 인증 시도
  - 데이터 변경 이력
  - 권한 변경
  - API 접근
```

---

*Last Updated: 2025-10-18*
