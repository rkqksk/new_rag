# Fine-tuning & Deployment Strategy
## Colima + External Linux RTX 3070Ti 통신 방식

---

## 🤔 현재 상황 분석

### Option A: SSH 직접 연결 (원격 접근)
```
Colima (MacOS)
    ↓ SSH 명령 전송
External Linux (RTX 3070Ti)
    ↓ Fine-tuning 실행
    ↓ 결과 반환
Colima (모델 다운로드)
```
**장점:** 실시간 연동, 네트워크만 있으면 됨
**단점:** 네트워크 의존, 모델 전송 시간 (수 GB)

---

### Option B: 모델 파일 전송 (Export-Process-Import)
```
Colima (MacOS)
├─ Student 모델 내보내기 (.gguf 또는 .safetensors)
├─ 훈련 데이터 내보내기 (.json, .csv)
    ↓ SCP/SFTP/HTTP로 전송
External Linux (RTX 3070Ti)
├─ 모델 + 데이터 수신
├─ Fine-tuning 실행
├─ 미세조정 모델 저장
    ↓ SCP/SFTP/HTTP로 전송
Colima (MacOS)
├─ 미세조정 모델 수신
├─ Ollama에 등록
└─ 프로덕션 배포
```
**장점:** 명확한 워크플로우, 각 단계 독립적
**단점:** 파일 전송 시간 (수십 분), 수동 작업

---

### Option C: Docker 마이그레이션 (전체 환경 이동)
```
Colima (MacOS)
├─ Docker 이미지 생성 (.tar 또는 Registry)
├─ Fine-tuning 환경 포함
    ↓ 이미지 전송 (Large)
External Linux (RTX 3070Ti)
├─ Docker 로드 및 실행
├─ Fine-tuning 실행
├─ 결과 저장
    ↓ 결과만 전송
Colima (MacOS)
├─ 결과 수신
└─ 기존 Docker에 적용
```
**장점:** 환경 일관성, 재현 가능
**단점:** 이미지 크기 (5-10GB), 복잡한 오케스트레이션

---

## ✅ 추천: Option B (Export-Process-Import)

### 이유:
1. **명확한 책임 분리**
   - Colima: 데이터 생성 & 평가 & 배포
   - Linux: 고강도 계산 (Fine-tuning)

2. **효율성**
   - 모델 파일만 전송 (1-2GB)
   - 빠른 전송 (대역폭에 따라 5-30분)

3. **유연성**
   - 언제든지 재학습 가능
   - 다른 Linux 머신 추가 가능

4. **운영 단순성**
   - SSH 명령만으로 제어 가능
   - 자동화 스크립트 작성 용이

---

## 🏗️ Option B 상세 구조

```
┌─────────────────────────────────────────────────────┐
│          PHASE 1: 데이터 준비 (Colima)              │
│                                                      │
│  Teacher (7B) 상담 응답 생성                        │
│         ↓                                            │
│  RAGAS 평가 필터링 (score >= 0.80)                 │
│         ↓                                            │
│  훈련 데이터 포맷 변환                               │
│         ↓                                            │
│  최종 훈련 데이터셋 생성 (.json)                     │
│         ↓                                            │
│  Student 모델 추출 (.gguf 또는 safetensors)        │
└──────────────┬──────────────────────────────────────┘
               │
      ┌────────▼────────┐
      │   SCP/SFTP/HTTP │ 파일 전송 (5-30분)
      │  - training.json │
      │  - student.gguf  │
      └────────┬────────┘
               │
┌──────────────▼──────────────────────────────────────┐
│     PHASE 2: Fine-tuning (External Linux)           │
│                                                      │
│  모델 + 데이터 수신                                  │
│         ↓                                            │
│  LoRA 설정 로드                                      │
│         ↓                                            │
│  Fine-tuning 실행 (1-2시간)                         │
│  - 배치 크기: 8 (LoRA)                              │
│  - 에포크: 3                                        │
│  - 학습률: 1e-4                                     │
│         ↓                                            │
│  평가 메트릭 계산                                    │
│         ↓                                            │
│  미세조정 모델 저장 (.gguf)                         │
└──────────────┬──────────────────────────────────────┘
               │
      ┌────────▼────────┐
      │   SCP/SFTP/HTTP │ 결과 전송 (10-20분)
      │ - student-lora. │
      │   gguf           │
      │ - metrics.json   │
      └────────┬────────┘
               │
┌──────────────▼──────────────────────────────────────┐
│    PHASE 3: 배포 (Colima)                           │
│                                                      │
│  미세조정 모델 수신                                  │
│         ↓                                            │
│  Ollama에 모델 등록                                 │
│         ↓                                            │
│  프로덕션 테스트                                     │
│         ↓                                            │
│  메트릭 비교 (Before vs After)                       │
│         ↓                                            │
│  배포 완료                                           │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 구현 세부사항

### 1. 데이터 내보내기 (Colima)

```python
# app/services/export_service.py
import json
from pathlib import Path

class ExportService:
    """학습 데이터를 외부 Linux로 전송하기 위해 준비"""

    def export_training_data(self, output_dir: str = "./exports"):
        """
        훈련 데이터를 JSON 형식으로 내보내기

        Output:
        {
          "data": [
            {
              "input": "50미리 용기 추천해줘 [CONTEXT]",
              "output": "Teacher 고품질 응답",
              "metadata": {
                "ragas_score": 0.92,
                "sources": [...],
                "confidence": 0.85
              }
            },
            ...
          ]
        }
        """
        training_data = self._collect_from_database()

        output_file = Path(output_dir) / f"training_data_{date.today()}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, ensure_ascii=False, indent=2)

        return output_file

    def export_model(self, model_name: str = "qwen2.5:3b"):
        """
        Ollama 모델을 GGUF 형식으로 추출
        """
        # ollama pull qwen2.5:3b → ~/.ollama/models/
        model_path = Path.home() / ".ollama" / "models" / model_name
        return model_path
```

### 2. Fine-tuning 스크립트 (External Linux)

```bash
#!/bin/bash
# finetuning/run_lora.sh (Linux 머신에서 실행)

MODEL_PATH="./models/student.gguf"
TRAINING_DATA="./data/training_data.json"
OUTPUT_DIR="./output/finetuned_model"

# Python 환경 설정
source /path/to/venv/bin/activate

# LoRA Fine-tuning 실행
python finetuning/lora_trainer.py \
  --model_path "$MODEL_PATH" \
  --training_data "$TRAINING_DATA" \
  --output_dir "$OUTPUT_DIR" \
  --batch_size 8 \
  --epochs 3 \
  --learning_rate 1e-4

# 결과 압축
tar -czf "$OUTPUT_DIR/finetuned_student.tar.gz" "$OUTPUT_DIR"

echo "✓ Fine-tuning 완료"
```

### 3. 파일 전송 (SCP)

```bash
# Colima → Linux 전송
scp -r ./exports/training_data.json user@linux_ip:/path/to/data/
scp -r ~/.ollama/models/qwen2.5:3b user@linux_ip:/path/to/models/

# Linux → Colima 전송
scp -r user@linux_ip:/path/to/output/finetuned_student.tar.gz ./models/
```

### 4. 모델 등록 (Colima)

```python
# app/services/import_service.py
import subprocess
from pathlib import Path

class ImportService:
    """미세조정된 모델을 Ollama에 등록"""

    def import_finetuned_model(self, model_path: str, name: str = "qwen2.5:3b-finetuned"):
        """
        GGUF 파일을 Ollama에 등록
        """
        modelfile = f"""
FROM {model_path}
"""

        # Ollama에 모델 등록
        result = subprocess.run([
            "ollama", "create", name, "-f", "-"
        ], input=modelfile, text=True)

        return result.returncode == 0
```

---

## 📊 각 옵션 비교

| 항목 | Option A (SSH) | Option B (파일 전송) | Option C (Docker) |
|------|--------|--------|-------|
| 설정 난이도 | 중 | 낮 | 높 |
| 네트워크 의존 | 높음 | 중간 | 낮음 |
| 전송 시간 | 짧음 | 중간 | 길음 |
| 자동화 용이 | 중 | 높음 | 중 |
| 환경 일관성 | 낮음 | 중 | 높음 |
| **추천도** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 🎯 결론

**Option B (Export-Process-Import) 추천:**
1. 훈련 데이터 내보내기
2. 모델 파일 전송 (SCP)
3. Linux에서 Fine-tuning 실행
4. 결과 수신 및 배포

**이점:**
- 명확한 워크플로우
- 쉬운 자동화 (스크립트화)
- 빠른 전송 속도
- 운영 단순성

---

*당신의 선택:*
- A. SSH 직접 연결 원하시나요?
- B. 파일 전송 방식이 맞나요?
- C. Docker 마이그레이션 하시나요?
- D. 다른 방식 제안?
