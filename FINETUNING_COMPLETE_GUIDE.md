# Teacher-Student LoRA Fine-tuning 완벽 가이드

## 개요

이 가이드는 Colima (MacOS)에서 RAG 기반 학습 데이터를 생성하고, 외부 Linux (RTX 3070Ti)에서 LoRA 미세조정을 수행한 후, Colima로 모델을 반환하여 프로덕션에 배포하는 전체 프로세스를 설명합니다.

---

## 아키텍처 흐름

```
┌────────────────────────────────┐
│   Colima (MacOS)              │
│   - Teacher (7B): 데이터 생성   │
│   - Student (3B): 원본 모델     │
│   - RAG DB (Qdrant)            │
└──────────────┬─────────────────┘
               │
      1. 훈련 데이터 생성
      2. 데이터 + 모델 내보내기
      3. SCP 전송
               │
               ▼
┌────────────────────────────────┐
│   Linux (RTX 3070Ti)           │
│   - LoRA Fine-tuning           │
│   - 1-2시간 소요               │
│   - 미세조정 모델 저장          │
└──────────────┬─────────────────┘
               │
      4. SCP 반환
               │
               ▼
┌────────────────────────────────┐
│   Colima (MacOS)              │
│   - Ollama에 모델 등록         │
│   - 프로덕션 배포              │
└────────────────────────────────┘
```

---

## Phase 1: Colima에서 훈련 데이터 생성

### 1.1 Teacher 서비스 호출

Teacher 모델 (Qwen2.5:7B)을 사용하여 RAG 데이터 기반 고품질 응답 생성:

```python
from app.services.teacher_service import TeacherService, TeacherGenerationRequest
from app.services.evaluation_service import RAGASEvaluator

# Teacher 서비스 초기화
teacher_service = TeacherService(ollama_host="http://localhost:11434")
evaluator = RAGASEvaluator()

# RAG 검색 결과 예시
rag_context = [
    "50미리 용기는 소량 상품용으로 적합합니다. PET 투명 또는 HDPE 불투명...",
    "제품 규격: 직경 50mm, 높이 80mm, 용량 100ml...",
    "가격: 1,000원/개 (최소 주문 1,000개)"
]

# 요청 생성
request = TeacherGenerationRequest(
    query="50미리 용기 추천해줘",
    rag_context=rag_context,
    consultation_type="product_recommendation"
)

# 데이터 생성
response, is_high_quality = await teacher_service.generate_training_data(request)

# 평가
if is_high_quality:
    eval_result = evaluator.evaluate(
        query=request.query,
        response=response.teacher_response,
        rag_context=rag_context,
        confidence=response.confidence,
        consultation_type="product_recommendation"
    )
    print(f"Quality Score: {eval_result.overall_score:.2f}")
    print(f"Feedback: {eval_result.feedback}")
```

### 1.2 배치 처리: 여러 질문으로 훈련 데이터 생성

```python
import asyncio
from app.services.teacher_service import TrainingDataExporter

# 다양한 질문 시뮬레이션
consultation_queries = [
    {
        "query": "50미리 용기 추천해줘",
        "context": ["50ml 용기 정보...", "제품 규격...", "가격 정보..."],
        "type": "product_recommendation"
    },
    {
        "query": "제품에서 냄새가 나요",
        "context": ["포장재 설명...", "보관 방법...", "처리 방법..."],
        "type": "defect_inquiry"
    },
    # ... 더 많은 질문들
]

# 배치 처리
high_quality_responses = []

for query_data in consultation_queries:
    request = TeacherGenerationRequest(
        query=query_data["query"],
        rag_context=query_data["context"],
        consultation_type=query_data["type"]
    )
    
    response, is_high_quality = await teacher_service.generate_training_data(request)
    
    if is_high_quality:
        high_quality_responses.append(response)
        print(f"✓ 고품질 데이터 생성: {query_data['query']}")
    else:
        print(f"✗ 품질 미달: {query_data['query']}")

print(f"총 생성된 훈련 샘플: {len(high_quality_responses)}")
```

### 1.3 훈련 데이터 내보내기

```python
from app.services.export_import_service import TrainingDataExporter, ExportConfig

# 내보내기 설정
export_config = ExportConfig(
    output_dir="./exports",
    include_metadata=True,
    timestamp=True
)

exporter = TrainingDataExporter(export_config)

# 훈련 데이터 내보내기
output_file = exporter.export_training_data(high_quality_responses)
print(f"훈련 데이터 저장: {output_file}")

# LoRA 설정 내보내기
lora_config = {
    "r": 16,
    "lora_alpha": 32,
    "target_modules": ["q_proj", "v_proj"],
    "lora_dropout": 0.05,
    "bias": "none",
    "epochs": 3,
    "batch_size": 8,
    "learning_rate": 1e-4
}

config_file = exporter.export_config(lora_config)
print(f"LoRA 설정 저장: {config_file}")

# 내보내기 매니페스트
manifest = exporter.get_export_manifest()
print(f"내보낼 파일:")
for file_info in manifest["files"]:
    print(f"  - {file_info['name']} ({file_info['size_mb']:.2f}MB)")
```

---

## Phase 2: 파일 전송 (Colima → Linux)

### 2.1 SCP를 이용한 파일 전송

```bash
# 변수 설정
REMOTE_HOST="192.168.1.100"      # Linux 서버 IP
REMOTE_USER="ubuntu"              # Linux 사용자명
REMOTE_PATH="/home/ubuntu/finetuning/data"
SSH_KEY="/path/to/ssh/key"

# 훈련 데이터 전송
scp -i $SSH_KEY ./exports/training_data_*.json $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/

# LoRA 설정 전송
scp -i $SSH_KEY ./exports/lora_config_*.json $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/

# 확인
ssh -i $SSH_KEY $REMOTE_USER@$REMOTE_HOST "ls -lh $REMOTE_PATH"
```

### 2.2 Python을 이용한 자동화 파일 전송

```python
from app.services.export_import_service import SCPFileTransfer

# SCP 전송 설정
scp_transfer = SCPFileTransfer(
    remote_host="192.168.1.100",
    remote_user="ubuntu",
    remote_path="/home/ubuntu/finetuning/data",
    ssh_key="/Users/oypnus/.ssh/id_rsa"
)

# 훈련 데이터 전송
success = scp_transfer.send_file(
    local_path="./exports/training_data_20251017_120000.json",
    remote_filename="training_data.json"
)

if success:
    print("✓ 훈련 데이터 전송 완료")
else:
    print("✗ 훈련 데이터 전송 실패")

# LoRA 설정 전송
success = scp_transfer.send_file(
    local_path="./exports/lora_config_20251017_120000.json",
    remote_filename="lora_config.json"
)

if success:
    print("✓ LoRA 설정 전송 완료")
```

---

## Phase 3: Linux에서 LoRA Fine-tuning 실행

### 3.1 리눅스 서버 준비

```bash
# SSH로 Linux 서버 접속
ssh -i /path/to/ssh/key ubuntu@192.168.1.100

# 작업 디렉토리 생성
mkdir -p ~/finetuning/{data,output,logs}
cd ~/finetuning

# Python 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers datasets peft accelerate bitsandbytes

# 또는 requirements.txt 사용
pip install -r requirements.txt
```

### 3.2 LoRA 훈련 실행

```bash
# 훈련 스크립트 다운로드 (Colima에서 전송)
scp -i /path/to/ssh/key /Users/oypnus/Project/rag-enterprise/finetuning/lora_trainer.py ubuntu@192.168.1.100:~/finetuning/

# 실행 (방법 1: 직접 Python)
python lora_trainer.py \
  --model_name "Qwen/Qwen2.5-3B-Instruct" \
  --training_data ./data/training_data.json \
  --output_dir ./output \
  --batch_size 8 \
  --epochs 3 \
  --learning_rate 1e-4 \
  --device cuda

# 실행 (방법 2: 배시 스크립트)
bash run_lora.sh \
  --model_name "Qwen/Qwen2.5-3B-Instruct" \
  --training_data ./data/training_data.json \
  --output_dir ./output \
  --batch_size 8 \
  --epochs 3
```

### 3.3 훈련 진행 모니터링

```bash
# 실시간 VRAM 모니터링
watch -n 1 nvidia-smi

# 로그 확인
tail -f ~/finetuning/output/training_logs.txt

# 경과 시간 계산
# 예상 소요 시간: 1-2시간 (RTX 3070Ti 8GB, batch_size=8)
```

### 3.4 훈련 완료 확인

```bash
# 출력 모델 확인
ls -lh ~/finetuning/output/student-lora/

# 파일 구성 확인
ls ~/finetuning/output/student-lora/
# 예상 출력:
# adapter_config.json
# adapter_model.bin
# special_tokens_map.json
# tokenizer.json
# tokenizer_config.json
# metadata.json

# 메트릭 확인
cat ~/finetuning/output/metrics.json
```

---

## Phase 4: Colima로 모델 반환 및 배포

### 4.1 미세조정 모델 다운로드

```bash
# 모델 다운로드 (Colima에서)
scp -i /path/to/ssh/key -r ubuntu@192.168.1.100:~/finetuning/output/student-lora ./models/

# 확인
ls -lh ./models/student-lora/
```

### 4.2 Ollama에 모델 등록

```python
from app.services.export_import_service import ModelImporter

importer = ModelImporter(ollama_host="http://localhost:11434")

# 모델 임포트
success = importer.import_finetuned_model(
    model_path="./models/student-lora",
    model_name="qwen2.5:3b-finetuned"
)

if success:
    print("✓ 모델 임포트 완료")
    
    # 모델 확인
    verified = importer.verify_model("qwen2.5:3b-finetuned")
    print(f"모델 확인: {'✓ 성공' if verified else '✗ 실패'}")
    
    # 등록된 모델 목록
    models = importer.list_models()
    print(f"등록된 모델: {models}")
else:
    print("✗ 모델 임포트 실패")
```

### 4.3 모델 테스트

```bash
# Ollama CLI로 테스트
ollama run qwen2.5:3b-finetuned "50미리 용기 추천해줘"

# 또는 API로 테스트
curl http://localhost:11434/api/generate \
  -d '{
    "model": "qwen2.5:3b-finetuned",
    "prompt": "50미리 용기 추천해줘",
    "stream": false
  }' | jq '.response'
```

### 4.4 프로덕션 배포

```python
# FastAPI에서 Student 모델 사용
from app.services.consultation_service import ConsultationService

consultation_service = ConsultationService(
    search_client=qdrant_client,
    embedding_model=sentence_transformer_model,
    llm_client="qwen2.5:3b-finetuned"  # 미세조정 모델 사용
)

# 상담 요청
response = await consultation_service.recommend_product(
    ConsultationRequest(
        query="50미리 용기 추천해줘",
        consultation_type="product_recommendation"
    )
)
```

---

## 전체 워크플로우 자동화

### 통합 워크플로우 함수

```python
from app.services.export_import_service import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator(
    ollama_host="http://localhost:11434",
    export_dir="./exports"
)

# 1. Fine-tuning 준비
prep_result = await orchestrator.prepare_fine_tuning(
    training_samples=high_quality_responses,
    lora_config={
        "r": 16,
        "lora_alpha": 32,
        "target_modules": ["q_proj", "v_proj"],
        "lora_dropout": 0.05,
        "bias": "none",
        "epochs": 3,
        "batch_size": 8,
        "learning_rate": 1e-4
    }
)

print(f"준비 상태: {prep_result['status']}")
print(f"훈련 샘플: {prep_result['total_samples']}")

# 2. [수동] Linux에서 훈련 실행
print("Linux에서 run_lora.sh 실행 대기 중...")
print(f"훈련 매니페스트: {prep_result['manifest']}")

# 3. Fine-tuning 완료 처리
completion_result = await orchestrator.complete_fine_tuning(
    model_path="./models/student-lora",
    model_name="qwen2.5:3b-finetuned"
)

print(f"완료 상태: {completion_result['status']}")
print(f"사용 가능한 모델: {completion_result['available_models']}")
```

---

## 성능 예상치

### 훈련 시간
- **모델**: Qwen2.5:3B
- **데이터**: 200-500 샘플
- **배치 크기**: 8
- **에포크**: 3
- **GPU**: RTX 3070Ti (8GB VRAM)
- **예상 시간**: 1-2시간

### 메모리 사용
- **기본 모델**: ~6GB
- **LoRA 어댑터**: ~500MB
- **활성화/그래디언트**: ~2GB
- **총합**: ~8.5GB (RTX 3070Ti 한계)

### 성능 개선
- **기본 Student (3B)**: RAGAS 0.70-0.75
- **미세조정 후**: RAGAS 0.80-0.88
- **응답 시간**: ~0.5-1초

---

## 트러블슈팅

### 문제 1: CUDA 메모리 부족
```
RuntimeError: CUDA out of memory
```

해결책:
```bash
# 배치 크기 축소
--batch_size 4

# 그래디언트 누적 증가
export GRADIENT_ACCUMULATION_STEPS=4

# 정밀도 8비트 양자화
export FP8_TRAINING=1
```

### 문제 2: 훈련 완료되지 않음
```
# 진행 상황 확인
ps aux | grep lora_trainer

# VRAM 모니터링
nvidia-smi

# 로그 확인
tail -f output/training_logs.txt
```

### 문제 3: 모델 로드 실패
```
# 모델 폴더 권한 확인
ls -l models/student-lora/

# 필수 파일 확인
ls -la models/student-lora/ | grep -E "adapter_config|adapter_model"
```

---

## 베스트 프랙티스

1. **데이터 품질**: RAGAS 스코어 >= 0.80만 사용
2. **배치 처리**: 최소 100 샘플 이상 수집 후 훈련
3. **주기적 재훈련**: 1개월마다 새 데이터로 재훈련
4. **모델 백업**: 훈련 전후 모델 스냅샷 저장
5. **A/B 테스트**: 미세조정 전후 성능 비교

---

## 참고 자료

- **Teacher-Student 아키텍처**: `TEACHER_STUDENT_ARCHITECTURE.md`
- **Data Flow 상세**: `DATA_FLOW_FOR_TRAINING.md`
- **배포 전략**: `FINETUNING_DEPLOYMENT_STRATEGY.md`
- **LoRA 논문**: https://arxiv.org/abs/2106.09685
- **Qwen 모델**: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct

---

**Last Updated**: 2025-10-17  
**Status**: Ready for Production
