# Teacher-Student LLM Architecture

## 🎯 시스템 목표

제조업 특화 RAG 상담 시스템에서:
- **Teacher (Qwen2.5-7B)**: 고품질 데이터 생성 및 평가
- **Student (Qwen2.5-3B)**: 실제 서비스 운영 (저비용, 저리소스)
- **목표**: RAG + Fine-tuning으로 특정 도메인 최적화

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Server                        │
│           (상담 요청 엔드포인트 수신)                      │
└────────────────┬────────────────────────────────────────┘
                 │
         ┌───────┴────────┐
         │                │
    ┌────▼────┐      ┌────▼────┐
    │   RAG   │      │  Query  │
    │ Retrieval│     │ Embedding│
    │(Qdrant) │      │(Sentence │
    └────┬────┘      │Transform)│
         │           └────┬────┘
         │                │
    ┌────┴─────────────┬──┴────┐
    │                  │       │
┌───▼─────────┐  ┌────▼──┐  ┌─▼──────────┐
│ Production  │  │Teacher│  │ Training   │
│ Inference   │  │ Mode  │  │ Mode       │
│ (Student)   │  │       │  │ (Teacher)  │
└─────────────┘  └───┬───┘  └────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
    ┌─────▼──────┐      ┌──────▼──────┐
    │ Quality    │      │  Feedback   │
    │ Evaluation │      │  & Score    │
    │(RAGAS)     │      │ (0.0~1.0)   │
    └────────────┘      └─────────────┘
```

---

## 📊 상세 처리 흐름

### 1️⃣ **Production 모드 (일반 사용자)**

```
사용자 질문
    ↓
1. Query Embedding (Sentence-Transformers)
    ↓
2. RAG 검색 (Qdrant, top-5)
    ↓
3. Student 모델 (qwen2.5:3b) 응답 생성
    ↓
4. 사용자에게 응답
```

**특징:**
- 빠른 응답 (3B 모델)
- 저리소스 (GPU 메모리 6GB)
- 프로덕션 서빙

---

### 2️⃣ **Teacher 모드 (데이터 생성/평가)**

```
상담 요청 + RAG 검색 결과
    ↓
1. Teacher (qwen2.5:7b) 고품질 응답 생성
    ↓
2. 응답 분석:
   - Confidence Score 계산
   - Source 인용도 평가
   - 정확성 검증
    ↓
3. Feedback 생성:
   - 수정 사항 지적
   - 개선 방안 제시
   - 신뢰도 점수 (RAGAS)
    ↓
4. 훈련 데이터 저장
```

**특징:**
- 고품질 응답 (7B 모델)
- 상세한 Feedback
- Student 학습용 데이터 생성

---

## 🔄 데이터 흐름: Teacher → Student

### Phase 1: Data Generation (Teacher)

```python
{
  "question": "50미리 용기 추천해줘",
  "context": "소량 상품",
  "teacher_response": "고품질 응답...",
  "reasoning": "추론 과정...",
  "confidence": 0.92,
  "sources": [
    {
      "doc": "sample_products.txt",
      "relevance": 0.85,
      "snippet": "..."
    }
  ],
  "feedback": "개선점 없음",
  "quality_score": 0.92
}
```

### Phase 2: Filtering (평가)

**조건:**
- quality_score >= 0.8 → 훈련 데이터로 사용
- quality_score < 0.8 → 거부 또는 Teacher 재검토

### Phase 3: Student Fine-tuning

```python
training_data = [
  {
    "input": "50미리 용기 추천해줘 [CONTEXT]...",
    "output": "Teacher가 생성한 고품질 응답"
  },
  ...
]

# LoRA Fine-tuning
# Student 모델이 Teacher 응답 패턴 학습
```

---

## 📈 평가 시스템 (Evaluation Metrics)

### 1. RAGAS Score (Retrieval-Augmented Generation Assessment)

```python
ragas_score = {
  "faithfulness": 0.85,      # 원본 문서와의 일관성
  "answer_relevancy": 0.90,  # 질문 관련성
  "context_recall": 0.88,    # 컨텍스트 회수율
  "context_precision": 0.92, # 컨텍스트 정밀도
  "overall": 0.89            # 종합 점수
}
```

### 2. Custom Metrics (제조업 특화)

```python
manufacturing_metrics = {
  "product_accuracy": 0.95,      # 제품 정보 정확성
  "defect_diagnosis_quality": 0.88,  # 불량 진단 정확성
  "recommendation_relevance": 0.91,  # 추천 적합성
  "safety_compliance": 1.0,      # 안전 규정 준수
}
```

### 3. Response Quality

```python
quality_metrics = {
  "length_appropriate": True,        # 길이 적절성
  "grammar_correct": True,           # 문법 정확성
  "sources_cited": True,             # 출처 인용 여부
  "confidence_calibrated": 0.92,     # 신뢰도 교정
}
```

---

## 🎓 Fine-tuning 전략

### Infrastructure: 분산 구조 (Colima + External Linux)

```
┌──────────────────────────────────────┐
│   Colima (MacOS - Apple Silicon)     │
│  ┌────────────────────────────────┐  │
│  │ Teacher (7B) + Student (3B)    │  │
│  │ - 상담 데이터 생성              │  │
│  │ - 훈련 데이터 수집              │  │
│  │ - 모델 평가 (RAGAS)            │  │
│  └────────────────────────────────┘  │
└────────────┬─────────────────────────┘
             │ (Export training data)
             ↓
┌──────────────────────────────────────┐
│   External Linux (RTX 3070Ti GPU)    │
│  ┌────────────────────────────────┐  │
│  │ Fine-tuning Server             │  │
│  │ - LoRA Fine-tuning             │  │
│  │ - 일반 Fine-tuning              │  │
│  │ - 모델 검증 및 평가             │  │
│  └────────────────────────────────┘  │
└────────────┬─────────────────────────┘
             │ (Return fine-tuned model)
             ↓
┌──────────────────────────────────────┐
│   Colima (Production Deployment)     │
│  ┌────────────────────────────────┐  │
│  │ Fine-tuned Student (3B)        │  │
│  │ - 프로덕션 서빙                  │  │
│  │ - 실시간 상담                    │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

### Fine-tuning Approach: LoRA + General Fine-tuning

#### Option 1: LoRA (Low-Rank Adaptation) - 추천
**장점:**
- 적은 계산량 (5-10% 파라미터만 학습)
- 빠른 수렴 (1-2 hours on RTX 3070Ti)
- 기본 능력 유지
- 메모리 효율적

**설정:**
```python
lora_config = {
  "r": 16,
  "lora_alpha": 32,
  "target_modules": ["q_proj", "v_proj"],
  "lora_dropout": 0.05,
  "bias": "none",
}

training_config = {
  "epochs": 3,
  "batch_size": 8,  # RTX 3070Ti (8GB VRAM)
  "learning_rate": 1e-4,
  "warmup_steps": 100,
  "max_steps": 2000,
  "gradient_accumulation_steps": 2,
}
```

#### Option 2: General Fine-tuning
**특징:**
- 전체 모델 학습 가능
- 더 높은 성능 (시간 소요)
- RTX 3070Ti에서도 가능 (8GB VRAM)
- 배치 크기 제약 (2-4)

**설정:**
```python
training_config = {
  "epochs": 2,
  "batch_size": 2,  # Memory-constrained
  "learning_rate": 2e-5,  # Lower LR for full training
  "warmup_steps": 200,
  "max_steps": 1500,
  "gradient_accumulation_steps": 4,
}
```

### 추천 전략

**Stage 1: LoRA (빠른 검증)**
- 1-2시간 내 완료
- 성능 70-80% 개선 기대
- 첫 번째 배포

**Stage 2: General Fine-tuning (고도화)**
- 필요시 추가 학습
- 성능 90%+ 목표
- 추가 최적화

---

## 📝 구현 세부사항

### File Structure

```
app/
├── services/
│   ├── consultation_service.py      # 기존
│   ├── teacher_service.py           # NEW: Teacher 모드
│   ├── evaluation_service.py        # NEW: 평가 시스템
│   └── student_finetuning_service.py # NEW: Student 학습
├── models/
│   ├── teacher_student_models.py    # NEW: 데이터 모델
│   └── metrics.py                   # NEW: 평가 메트릭
└── api/
    ├── main.py                      # 기존
    └── teacher_student_routes.py    # NEW: API 엔드포인트
```

### 새로운 API 엔드포인트

```
POST /api/v1/consult/recommend/teacher
  - Teacher 모드 상담 (고품질)

POST /api/v1/consult/recommend/student
  - Student 모드 상담 (빠름)

POST /api/v1/teacher/evaluate
  - 응답 평가 및 Feedback 생성

POST /api/v1/student/finetune/prepare
  - 훈련 데이터 준비

GET /api/v1/metrics/quality
  - 시스템 품질 메트릭 조회
```

---

## 🚀 구현 단계

### Week 1: Foundation
- ✅ Ollama 모델 설치 (진행 중)
- [ ] Teacher/Student API 엔드포인트
- [ ] 기본 평가 시스템 (RAGAS)

### Week 2: Integration
- [ ] Teacher 데이터 생성 파이프라인
- [ ] 훈련 데이터 수집 로직
- [ ] Student Fine-tuning 프레임워크

### Week 3: Optimization
- [ ] LoRA 파인튜닝 실행
- [ ] 성능 비교 (Teacher vs Student)
- [ ] 프로덕션 배포

---

## 📊 예상 성능

| 메트릭 | Teacher | Student | 목표 |
|--------|---------|---------|------|
| RAGAS Score | 0.90+ | 0.85+ | 0.88+ |
| Response Time | 3-5s | 0.5-1s | <2s |
| Memory (VRAM) | 14GB | 6GB | 유지 |
| Accuracy | 95%+ | 90%+ | 90%+ |

---

## ⚙️ 설정 파일

### config/teacher_student_config.yaml

```yaml
models:
  teacher:
    name: "qwen2.5:7b"
    context_size: 32000
    temperature: 0.7
    top_p: 0.9

  student:
    name: "qwen2.5:3b"
    context_size: 32000
    temperature: 0.5
    top_p: 0.95

evaluation:
  ragas_threshold: 0.80
  min_confidence: 0.75
  max_retries: 2

finetuning:
  lora_r: 16
  lora_alpha: 32
  epochs: 3
  batch_size: 4
  learning_rate: 1e-4
```

---

## 🔐 주의사항

1. **메모리 관리**
   - Teacher + Student 동시 로드 불가
   - 요청에 따라 모델 스위칭 필요

2. **데이터 품질**
   - RAGAS 점수 < 0.8 데이터는 필터링
   - 주기적 재평가 필수

3. **모니터링**
   - Student 성능 저하 감지
   - 신뢰도 캘리브레이션 확인

---

*Last Updated: 2025-10-17*
*Status: Architecture Design Complete*
