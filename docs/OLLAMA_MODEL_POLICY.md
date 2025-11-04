# Ollama Model Management Policy

> **Symbol Reference**: §ollama.*
> **Quick Access**: See `CLAUDE.md` for production models.
> **Full Map**: `docs/SYMBOL_SYSTEM.md`

## 📋 현재 프로덕션 모델 (고정)

### ✅ 승인된 모델

#### 1. qwen2.5:7b-instruct (메인 생성 모델)
```yaml
Name: qwen2.5:7b-instruct
ID: 845dbda0ea48
Size: 4.7GB
Purpose: RAG 답변 생성, 대화, 질의응답
Status: ✅ Production Ready
Tested: 2025-11-03

Performance:
  Latency: 1-2s per response
  Quality: 85-90% vs Claude Sonnet
  RAM Usage: 4-5GB (4-bit quantized)
  
Supported Languages:
  - Korean (한국어) - Primary
  - English - Secondary

Domain Expertise:
  - Manufacturing: Cpk, OEE, ISO 9001, FMEA
  - Packaging: PET, PETG, PP, HDPE, LLDPE, LDPE, PS
  - Regulatory: FDA 21 CFR 177, EU 10/2011, REACH, 식품위생법
```

#### 2. nomic-embed-text:latest (로컬 임베딩 모델)
```yaml
Name: nomic-embed-text:latest
ID: 0a109f422b47
Size: 274MB
Purpose: 로컬 임베딩 생성 (sentence-transformers 대안)
Status: ✅ Optional
Tested: 2025-11-03

Performance:
  Latency: 10-30ms
  Dimension: 768
  RAM Usage: 200-300MB
  Quality: Good for local embeddings

Note: Primary embedding은 sentence-transformers 사용
      이 모델은 백업/대안용
```

---

## ❌ 삭제된 모델 (사용 금지)

### 제거 이유

1. **qwen2.5:3b**
   - ❌ 모델 크기가 작아 품질 저하
   - ❌ 복잡한 제조/포장 질문 처리 부족
   - ❌ 한국어 생성 품질 낮음
   - Status: 2025-11-04 삭제됨

2. **qwen2.5:7b-instruct-q4_K_M**
   - ❌ qwen2.5:7b-instruct와 동일한 모델 (중복 태그)
   - ❌ ID 충돌 (845dbda0ea48 동일)
   - ❌ 혼란 방지 위해 제거
   - Status: 2025-11-04 삭제됨

---

## 🔒 모델 고정 정책

### 원칙
1. **프로덕션 모델은 함부로 변경하지 않음**
2. **새 모델 추가는 반드시 테스트 후 승인**
3. **기존 모델 삭제는 팀 합의 필요**
4. **변경 시 반드시 롤백 계획 수립**

### 금지 사항
```bash
# ❌ 금지: 승인되지 않은 모델 설치
ollama pull llama2
ollama pull llama3
ollama pull qwen2.5:3b  # 이미 삭제됨

# ❌ 금지: 프로덕션 모델 삭제
ollama rm qwen2.5:7b-instruct  # 절대 금지!

# ❌ 금지: 모델 이름 변경
ollama cp qwen2.5:7b-instruct my-model
```

### 허용 사항
```bash
# ✅ 허용: 현재 모델 확인
ollama list

# ✅ 허용: 모델 테스트
ollama run qwen2.5:7b-instruct "Test question"

# ✅ 허용: 승인된 모델 재설치 (손상 시)
ollama pull qwen2.5:7b-instruct
```

---

## 📖 설치 가이드

### 초기 설치

```bash
# 1. Ollama 설치
brew install ollama

# 2. 필수 모델 다운로드
ollama pull qwen2.5:7b-instruct  # 4.7GB

# 3. 선택적 모델 다운로드
ollama pull nomic-embed-text:latest  # 274MB

# 4. 확인
ollama list

# 예상 출력:
# NAME                       ID              SIZE      MODIFIED
# qwen2.5:7b-instruct        845dbda0ea48    4.7 GB    ...
# nomic-embed-text:latest    0a109f422b47    274 MB    ...
```

### 정리 (필요 시)

```bash
# 불필요한 모델 확인
ollama list

# 승인되지 않은 모델 삭제
ollama rm <model-name>

# 예: 작은 모델 삭제
ollama rm qwen2.5:3b

# 예: 중복 태그 삭제
ollama rm qwen2.5:7b-instruct-q4_K_M
```

---

## 🔄 모델 업그레이드 절차

### Phase 1: 평가 (1-2일)
```bash
# 개발 환경에서 새 모델 테스트
ollama pull <new-model>
ollama run <new-model> < test_queries.txt > results.txt

# 성능 비교
python scripts/benchmark_models.py \
  --baseline qwen2.5:7b-instruct \
  --candidate <new-model>
```

### Phase 2: 검증 (2-3일)
```yaml
테스트 항목:
  - 답변 품질 (Korean + English)
  - 레이턴시 (< 2s)
  - 메모리 사용량 (< 6GB)
  - 도메인 지식 (Manufacturing + Packaging)
  - Regulatory 정확도

벤치마크:
  - 100개 샘플 쿼리
  - Human evaluation (5명)
  - Precision@5, Recall@10, MRR
```

### Phase 3: 승인 (1일)
```yaml
Required:
  - 벤치마크 보고서
  - 성능 비교표
  - 메모리/디스크 요구사항
  - 롤백 계획
  - 팀 승인 (3명 이상)
```

### Phase 4: 배포 (0.5일)
```bash
# 1. 현재 모델 백업
ollama list > backup_models_$(date +%Y%m%d).txt

# 2. 새 모델 다운로드
ollama pull <new-model>

# 3. 설정 업데이트
# .env
OLLAMA_MODEL=<new-model>

# config/ollama_models.yaml
production:
  generation:
    name: <new-model>
    tested_date: $(date +%Y-%m-%d)

# 4. 재시작 및 검증
docker-compose restart
python scripts/verify_model.py
```

### Phase 5: 모니터링 (1주일)
```yaml
Metrics:
  - Error rate
  - Response latency
  - User satisfaction
  - Quality regression

Alert Conditions:
  - Error rate > 5%
  - Latency > 3s (P95)
  - Quality score < 0.7
```

---

## 🚨 긴급 롤백 절차

### Trigger Conditions
- 에러율 > 10%
- 레이턴시 > 5s
- 치명적 버그 발견
- 답변 품질 심각한 저하

### Rollback Steps

```bash
# 1. 즉시 이전 모델로 전환
# .env
OLLAMA_MODEL=qwen2.5:7b-instruct  # 이전 안정 버전

# 2. 서비스 재시작
docker-compose restart

# 3. 새 모델 제거 (선택)
ollama rm <problematic-model>

# 4. 인시던트 보고서 작성
# - 문제 설명
# - 영향 범위
# - 근본 원인
# - 재발 방지 대책
```

---

## 📊 리소스 요구사항

### 디스크 용량
```
qwen2.5:7b-instruct:     4.7GB
nomic-embed-text:        274MB
───────────────────────────────
Total:                   ~5GB
Buffer:                  +2GB (권장)
───────────────────────────────
Recommended:             7GB+ free
```

### 메모리 (RAM)
```
qwen2.5:7b-instruct:     4-5GB (inference)
nomic-embed-text:        200-300MB
System + Buffer:         6-8GB
───────────────────────────────
Total:                   ~11-13GB
Recommended:             16GB+ total RAM
```

### CPU
```
Minimum:    4 cores
Recommended: 8 cores
Optimal:    Apple Silicon M1/M2/M3/M4
```

---

## 🔗 관련 문서

- **환경 설정**: `.env.example`
- **모델 설정**: `config/ollama_models.yaml`
- **아키텍처**: `docs/ARCHITECTURE.md`
- **RAG 전략**: `docs/RAG_ACTIVATION_STRATEGY.md`

---

## 📞 문의

모델 변경 또는 업그레이드 관련 문의:
1. 이슈 생성: `GitHub Issues`
2. 테스트 요청: `#rag-team` 채널
3. 긴급 문의: `oncall-engineer@company.com`

---

**Last Updated**: 2025-11-04
**Policy Version**: 1.0
**Status**: Active
