# 🚀 RAG Enterprise 개발 플로우 가이드

## 핵심 개념: CLAUDE.md 중심 개발

**기존 방식** ❌:
- 코드 작성 → 문서화 → 설정 파일 수정 → 배포
- 라우팅 로직 분산 (여러 파일에 중복)
- 설정 불일치 위험

**새로운 방식** ✅:
- **CLAUDE.md 수정** → 자동 설정 생성 → 파이프라인 등록 → 검증
- 중앙 집중식 오케스트레이터
- 단일 진실의 원천 (Single Source of Truth)

## 🔄 이중 오케스트레이터 아키텍처

### 시스템 분리 전략

RAG Enterprise는 **두 가지 독립적인 오케스트레이터**를 사용합니다:

#### 1. Document Processing Orchestrator (`workflow_orchestrator_v3.py`)
**목적**: 문서 수집, 파싱, 임베딩, 인덱싱 파이프라인

**책임**:
- 웹 크롤링 (Bottle, Jar, Cap&Pump)
- 파일 파싱 (PDF, Excel, Image, HTML)
- 문서 청킹 및 임베딩
- 벡터 DB 인덱싱
- 파일 정리 (cleanup)
- 디버깅 워크플로우

**API 엔드포인트**:
```
POST /api/v1/workflow/execute
POST /api/v1/workflow/cleanup
GET  /api/v1/workflow/status
GET  /api/v1/workflow/health
```

**사용 시나리오**:
- 정기 크롤링 작업 실행
- 대량 문서 업로드 및 처리
- 시스템 정리 및 유지보수

---

#### 2. LLM-Powered Orchestrator (`unified_workflow_orchestrator.py`)
**목적**: AI 상담 및 지능형 서비스 파이프라인

**책임**:
- LLM 라우팅 (Haiku 4.5 ↔ Sonnet 4.5)
- 상담 파이프라인 (제품 추천, 불량 분석)
- 복잡도 기반 비용 최적화
- 사용 통계 및 모니터링

**API 엔드포인트**:
```
GET  /api/v1/workflow/pipelines
POST /api/v1/workflow/pipelines/{pipeline_name}
GET  /api/v1/workflow/llm/stats
GET  /api/v1/workflow/llm/health
```

**사용 시나리오**:
- 고객 상담 (챗봇)
- 제품 추천
- 불량 진단
- 지능형 검색

---

### 왜 두 개로 분리했는가?

| 특성 | Document Processing | LLM-Powered |
|------|---------------------|-------------|
| **주요 작업** | ETL, 데이터 수집 | AI 추론, 상담 |
| **LLM 사용** | ❌ 없음 | ✅ 핵심 기능 |
| **실행 주기** | 정기 스케줄 (6시간) | 실시간 요청 |
| **리소스** | CPU, 메모리 | API 비용, 토큰 |
| **확장성** | 병렬 문서 처리 | 파이프라인 추가 |
| **비용** | 인프라 비용 | LLM API 비용 |

**결론**: 각 오케스트레이터는 **독립적으로 확장**되며, **서로 다른 목적과 SLA**를 가집니다.

---

## 🏗️ 통합 아키텍처

### Document Processing 아키텍처
```
CLAUDE.md (설정 정의)
    ↓
agents/config_loader.py (설정 파싱)
    ↓
config/system_config.yaml
    ↓
agents/workflow_orchestrator.py (기본 파이프라인)
    ↓
agents/workflow_orchestrator_v3.py (통합 + 정리)
    ├─ CleanDeployAgent (파일 정리)
    ├─ DebuggingAgent (디버깅)
    └─ WorkflowOrchestrator (문서 처리)
    ↓
app/api/workflow_routes.py (API)
```

### LLM-Powered 아키텍처
```
CLAUDE.md (파이프라인 정의)
    ↓
agents/config_loader.py (자동 파싱)
    ↓
config/system_config.yaml (구조화된 설정)
    ↓
agents/unified_workflow_orchestrator.py (중앙 허브)
    ├─ LLMRouter (haiku/sonnet 자동 선택)
    ├─ PipelineRegistry (모든 워크플로우)
    └─ ExecutionEngine (비동기 실행)
    ↓
app/api/workflow_routes.py (API)
```

---

## 📋 개발 플로우 단계별 가이드

### 1단계: 새 기능 정의 (CLAUDE.md 수정)

**시나리오**: 주문 상태 조회 파이프라인 추가

```markdown
# CLAUDE.md에 추가

## 🔌 Pipelines

**등록된 파이프라인**:
```yaml
product_recommendation:
  description: 제품 추천 상담
  stages: [query_understanding, retrieval, ranking, generation]
  llm_complexity: 0.4-0.6  # Haiku/Sonnet 혼용

defect_analysis:
  description: 불량 문의 분석
  stages: [image_analysis, pattern_matching, diagnosis, recommendation]
  llm_complexity: 0.9  # Sonnet 고정

document_processing:
  description: 문서 수집 및 임베딩
  stages: [parsing, chunking, embedding, storage]
  llm_complexity: N/A  # LLM 미사용

# 새로 추가 ⬇️
order_status_inquiry:
  description: 주문 상태 조회
  stages: [order_lookup, status_check, estimated_delivery]
  llm_complexity: 0.3  # Haiku 사용
  config:
    max_workers: 2
    timeout: 60
```
```

### 2단계: 설정 생성 (자동)

```bash
# 설정 파싱 및 생성
python agents/config_loader.py

# 출력:
# ✅ Configuration is valid
# ✅ Configuration saved to config/system_config.yaml
# ✅ Configuration applied to system
```

### 3단계: 파이프라인 구현

```python
# agents/pipelines/order_status.py

from agents.unified_workflow_orchestrator import LLMRequest
from typing import Dict, Any

async def order_status_inquiry_pipeline(
    order_id: str,
    llm_router,  # 자동 주입
    **kwargs
) -> Dict[str, Any]:
    """주문 상태 조회 파이프라인"""

    # Stage 1: Order Lookup (DB 조회)
    order_info = await lookup_order_from_db(order_id)

    if not order_info:
        return {
            'status': 'not_found',
            'message': f'주문 번호 {order_id}를 찾을 수 없습니다.'
        }

    # Stage 2: Status Check
    current_status = order_info['status']

    # Stage 3: LLM 기반 응답 생성 (Haiku 사용)
    request = LLMRequest(
        prompt=f"""다음 주문 정보를 바탕으로 고객에게 친절한 안내 메시지를 작성하세요:

주문 번호: {order_id}
현재 상태: {current_status}
예상 배송일: {order_info.get('estimated_delivery', '미정')}

고객이 이해하기 쉽고 정확한 안내를 제공하세요.""",
        system_prompt="당신은 친절한 고객 서비스 AI입니다.",
        max_tokens=300,
        complexity=0.3  # Haiku로 라우팅
    )

    response = await llm_router.generate(request)

    return {
        'order_id': order_id,
        'status': current_status,
        'message': response['text'],
        'model_used': response['model'],
        'raw_data': order_info
    }


async def lookup_order_from_db(order_id: str) -> Dict:
    """주문 조회 (실제로는 DB 쿼리)"""
    # TODO: PostgreSQL 연동
    return {
        'order_id': order_id,
        'status': '배송 중',
        'estimated_delivery': '2025-10-20'
    }
```

### 4단계: 파이프라인 등록

```python
# agents/unified_workflow_orchestrator.py에 추가

from agents.pipelines.order_status import order_status_inquiry_pipeline
from agents.unified_workflow_orchestrator import PipelineConfig

def _register_default_pipelines(self):
    """기본 파이프라인 등록"""

    # ... 기존 파이프라인 ...

    # 새 파이프라인 등록
    self.registry.register(
        config=PipelineConfig(
            name="order_status_inquiry",
            description="주문 상태 조회",
            stages=["order_lookup", "status_check", "estimated_delivery"],
            max_workers=2,
            timeout=60
        ),
        handler=order_status_inquiry_pipeline
    )
```

**또는 동적 등록** (런타임):
```python
orchestrator = WorkflowOrchestrator()

orchestrator.add_pipeline(
    config=PipelineConfig(
        name="order_status_inquiry",
        description="주문 상태 조회",
        stages=["order_lookup", "status_check", "estimated_delivery"]
    ),
    handler=order_status_inquiry_pipeline
)
```

### 5단계: API 엔드포인트 추가

```python
# app/api/main.py

@app.post("/api/v1/consult/order-status")
async def check_order_status(order_id: str):
    """주문 상태 조회"""

    result = await orchestrator.execute(
        "order_status_inquiry",
        order_id=order_id
    )

    return result
```

### 6단계: 검증

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. 파이프라인 목록 확인
curl http://localhost:8000/api/v1/pipelines

# 3. 실행 테스트
curl -X POST http://localhost:8000/api/v1/consult/order-status \
  -H "Content-Type: application/json" \
  -d '{"order_id": "ORD-12345"}'

# 4. LLM 사용 통계 확인
curl http://localhost:8000/api/v1/llm/stats
```

---

## 🎯 LLM 라우팅 전략

### 복잡도 기준

| 복잡도 | 모델 | 사용 사례 | 비용 |
|--------|------|----------|------|
| 0.0 - 0.3 | **Haiku 4.5** | 간단한 질의, 템플릿 응답 | $0.25/1M (input) |
| 0.3 - 0.7 | **자동 선택** | 일반 상담, 제품 추천 | 혼합 |
| 0.7 - 1.0 | **Sonnet 4.5** | 복잡한 분석, 불량 진단 | $3/1M (input) |

### 복잡도 결정 요소

```python
complexity = (
    0.3 * 프롬프트_길이 +      # 500단어 = 1.0
    0.2 * 시스템_프롬프트 +     # 존재하면 0.3
    0.3 * 추론_키워드 +         # analyze, explain 등
    0.2 * 출력_길이_요구        # 4000 tokens = 1.0
)
```

### 수동 복잡도 지정

```python
# 명시적으로 Haiku 강제
request = LLMRequest(
    prompt="...",
    complexity=0.2  # Haiku 사용
)

# 명시적으로 Sonnet 강제
request = LLMRequest(
    prompt="...",
    complexity=0.9  # Sonnet 사용
)
```

---

## 📊 모니터링 및 최적화

### LLM 사용 통계 확인

```python
orchestrator = WorkflowOrchestrator()

# ... 여러 요청 처리 ...

stats = orchestrator.llm_router.get_stats()

print(f"""
=== LLM 사용 통계 ===
총 호출 수: {stats['total_calls']}
총 토큰 수: {stats['total_tokens']}

Haiku 사용률: {stats['haiku_percentage']:.1f}%
  - 호출: {stats['haiku']['count']}
  - 토큰: {stats['haiku']['tokens']}

Sonnet 사용:
  - 호출: {stats['sonnet']['count']}
  - 토큰: {stats['sonnet']['tokens']}

비용 절감: ${stats['cost_saved']:.4f}
""")
```

### 복잡도 임계값 조정

```yaml
# config/system_config.yaml

llm_routing:
  complexity_threshold: 0.7  # 기본값
  # 0.6으로 낮추면 Haiku 사용률 증가 (비용 절감)
  # 0.8로 높이면 Sonnet 사용률 증가 (품질 향상)
```

---

## 🔧 트러블슈팅

### 문제 1: 설정이 적용되지 않음

```bash
# 해결 방법
python agents/config_loader.py  # 설정 재생성
curl http://localhost:8000/health  # 설정 로드 확인
```

### 문제 2: LLM API 키 오류

```bash
# 환경변수 확인
echo $ANTHROPIC_API_KEY
echo $CLAUDE_HAIKU_API_KEY  # Haiku 전용 키 (optional)

# .envrc 확인
cat .envrc | grep API_KEY
```

### 문제 3: 파이프라인 실행 실패

```python
# 디버그 모드 활성화
import logging
logging.basicConfig(level=logging.DEBUG)

# 파이프라인 정보 확인
orchestrator.get_pipeline_info("pipeline_name")

# 직접 실행 테스트
result = await orchestrator.execute("pipeline_name", **kwargs)
print(result['status'])
print(result.get('error'))
```

---

## 📝 베스트 프랙티스

### 1. 파이프라인 명명 규칙

```yaml
Good ✅:
  - product_recommendation
  - order_status_inquiry
  - defect_analysis

Bad ❌:
  - pipeline1
  - my_pipeline
  - test
```

### 2. 복잡도 설정 가이드

```python
# 간단한 DB 조회 + 템플릿 응답
complexity = 0.2

# 일반 상담 (검색 + 생성)
complexity = 0.5

# 복잡한 분석 (다단계 추론)
complexity = 0.8-0.9
```

### 3. 에러 처리

```python
async def my_pipeline(**kwargs):
    try:
        result = await process(**kwargs)
        return {'status': 'success', 'data': result}

    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        return {'status': 'invalid_input', 'error': str(e)}

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return {'status': 'error', 'error': str(e)}
```

### 4. 문서화

**새 파이프라인 추가 시**:
1. `CLAUDE.md`에 파이프라인 정의 추가
2. `docs/ROADMAP.md`에 체크리스트 업데이트
3. `docs/TECH_STACK.md`에 기술 스택 업데이트 (필요시)
4. API 문서 (OpenAPI/Swagger) 자동 생성

---

## 🚀 다음 단계

### Phase 1 완료 후
1. Teacher-Student LLM 통합
2. 로컬 LLM (Ollama) 라우팅 추가
3. 파이프라인 성능 모니터링
4. A/B 테스트 프레임워크

### Phase 2: 이미지 매칭
1. 멀티모달 파이프라인 추가
2. CLIP/BLIP-2 통합
3. 이미지 유사도 검색

---

**개발 플로우 요약**:
```
CLAUDE.md 수정
  ↓
python agents/config_loader.py
  ↓
파이프라인 구현 (agents/pipelines/)
  ↓
오케스트레이터 등록
  ↓
API 엔드포인트 추가
  ↓
/health 검증
  ↓
배포
```

---

*Last Updated: 2025-10-18*
*Development Flow Version: 1.0*
