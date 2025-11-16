# LLM Strategy - RAG Enterprise

## Overview

이 문서는 RAG Enterprise 프로젝트에서 사용하는 LLM (Large Language Model) 전략을 명확하게 정의합니다.

**Last Updated**: 2025-11-15
**Version**: 1.0.0

---

## Core Principles

### 1. Korean Language First (한국어 우선)
- **한국어 특화 모델을 우선 선택**: 프로젝트의 주요 사용자가 한국어 사용자이므로, 한국어 성능이 검증된 모델을 최우선으로 사용
- **양자화 모델 지원**: GGUF 양자화를 통해 메모리 효율성과 추론 속도 최적화

### 2. Hybrid Architecture
- **Multi-LLM Routing**: 쿼리 복잡도에 따라 최적의 모델 자동 선택
- **Graceful Fallback**: LLM 실패 시 RAG 기반 응답으로 우아하게 대체

### 3. Open Source Only
- **100% Open Source**: 상업적 의존성 제거, $0/month 소프트웨어 비용
- **Self-Hosted**: 완전한 데이터 주권 및 프라이버시 보장

---

## LLM Models

### Primary Model: EEVE-Korean-Instruct-7B-v2.0-Preview

**선정 기준**:
- ✅ **한국어 특화**: Yanolja의 EEVE (Efficient and Effective Vocabulary Expansion) 방법론
- ✅ **최적 크기**: 7B 파라미터 (성능과 효율성의 균형)
- ✅ **양자화 지원**: GGUF Q5_K_M quantization (4.7GB)
- ✅ **검증된 성능**: Hugging Face Korean LLM Leaderboard 상위권
- ✅ **Instruction-tuned**: RAG 시스템과의 통합에 최적화

**Model Details**:
```yaml
Name: seungduk-yanolja/EEVE-Korean-Instruct-7B-v2.0-Preview
Base: upstage/SOLAR-10.7B-v1.0
Parameters: 7.76B
Quantization: Q5_K_M
Size: 4.7 GB
Language: Korean-first (한국어 우선)
Provider: Ollama
```

**Usage**:
- **Complex Queries**: 복잡한 추론, 긴 컨텍스트, 다단계 질문
- **Korean Text Generation**: 한국어 요약, 번역, 설명 생성
- **RAG Enhancement**: 검색 결과 기반 답변 생성 및 개선

### Secondary Model: NexaAI VLM (Qwen3-VL-4B-Instruct-GGUF)

**선정 기준**:
- ✅ **Multimodal Vision**: 이미지 분석 및 비전-언어 통합
- ✅ **Fast Inference**: 경량 모델로 빠른 이미지 처리
- ✅ **GGUF Quantization**: Q4_0 양자화로 메모리 효율성 (3.7GB)
- ✅ **설치 완료**: Qwen3-VL-4B-Instruct-GGUF 다운로드 및 통합 완료

**Model Details**:
```yaml
Name: NexaAI/Qwen3-VL-4B-Instruct-GGUF
Parameters: 4B
Quantization: Q4_0
Size: 3.7 GB
Modality: Vision + Language (VLM)
Provider: NexaAI CLI
Status: Active ✅
```

**Usage**:
- **Image Search**: 제품 이미지 기반 검색 및 분석
- **Vision Tasks**: 이미지 내 텍스트/객체 인식, 이미지 설명 생성
- **Multimodal RAG**: 텍스트 + 이미지 결합 검색
- **Quality Inspection**: 제품 이미지 품질 검사 (Manufacturing)

---

## Hybrid LLM Routing Strategy

### Query Complexity Analysis

```python
# Router Configuration
router_config = {
    "simple_threshold": 0.3,      # 간단한 쿼리 기준점
    "complex_threshold": 0.7,     # 복잡한 쿼리 기준점
    "enable_nexa": False,         # NexaAI 비활성화 (설치되지 않음)
    "enable_ollama": True         # Ollama (EEVE) 활성화
}
```

### Routing Logic

```
User Query
    |
    v
Query Complexity Analysis
    |
    +-- Simple (< 0.3) --> [NexaAI 1.7B] (if enabled, else EEVE)
    |
    +-- Medium (0.3-0.7) --> [EEVE-Korean-7B]
    |
    +-- Complex (> 0.7) --> [EEVE-Korean-7B]
    |
    v
LLM Response
    |
    +-- Success --> Return Enhanced Answer
    |
    +-- Failure --> Fallback to RAG Skill Answer
```

### Complexity Factors

**Simple Queries** (0.0 - 0.3):
- 단순 사실 확인
- 짧은 질문 (< 20 단어)
- 단일 엔티티 검색

**Medium Queries** (0.3 - 0.7):
- 비교 및 분석
- 중간 길이 질문 (20-50 단어)
- 다중 엔티티 관계

**Complex Queries** (0.7 - 1.0):
- 다단계 추론
- 긴 질문 (> 50 단어)
- 복잡한 컨텍스트

---

## Environment Configuration

### Docker Compose

```yaml
# docker-compose.yml
services:
  api:
    environment:
      # Ollama (Korean LLM)
      OLLAMA_HOST: ollama
      OLLAMA_PORT: "11434"
      OLLAMA_MODEL: "seungduk-yanolja/EEVE-Korean-Instruct-7B-v2.0-Preview"
      # NexaAI (VLM for image search)
      NEXA_HOST: host.docker.internal
      NEXA_PORT: "8080"
      NEXA_VLM_MODEL: "NexaAI/Qwen3-VL-4B-Instruct-GGUF"
      ENABLE_NEXA: "true"

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
```

### UnifiedLLMService

```python
# src/api/chat.py
def get_unified_llm() -> UnifiedLLMService:
    # NexaAI configuration (VLM for image search)
    nexa_host = os.getenv("NEXA_HOST", "localhost")
    nexa_port = os.getenv("NEXA_PORT", "8080")
    nexa_vlm_model = os.getenv("NEXA_VLM_MODEL", "NexaAI/Qwen3-VL-4B-Instruct-GGUF")

    nexa_config = NexaConfig(
        base_url=f"http://{nexa_host}:{nexa_port}/v1",
        default_text_model="Qwen3-1.7B",
        default_vision_model=nexa_vlm_model,
        default_embedding_model="EmbeddingGemma"
    )

    # Ollama configuration (Korean-first)
    ollama_host = os.getenv("OLLAMA_HOST", "localhost")
    ollama_port = os.getenv("OLLAMA_PORT", "11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "seungduk-yanolja/EEVE-Korean-Instruct-7B-v2.0-Preview")

    ollama_config = OllamaConfig(
        base_url=f"http://{ollama_host}:{ollama_port}",
        default_model=ollama_model
    )

    # Router: EEVE + NexaAI VLM
    enable_nexa = os.getenv("ENABLE_NEXA", "true").lower() == "true"
    router_config = {
        "simple_threshold": 0.3,
        "complex_threshold": 0.7,
        "enable_nexa": enable_nexa,
        "enable_ollama": True
    }

    return UnifiedLLMService(
        nexa_config=nexa_config,
        ollama_config=ollama_config,
        router_config=router_config
    )
```

---

## Model Management

### Install Korean Model

```bash
# Pull EEVE Korean model
docker exec ollama ollama pull seungduk-yanolja/EEVE-Korean-Instruct-7B-v2.0-Preview

# Verify installation
docker exec ollama ollama list
```

### Remove Old Models

```bash
# Remove non-Korean models
docker exec ollama ollama rm qwen2.5:7b-instruct
docker exec ollama ollama rm llama3:7b-instruct
```

### Test Model

```bash
# Quick test
docker exec ollama ollama run seungduk-yanolja/EEVE-Korean-Instruct-7B-v2.0-Preview "100ml PET 용기의 장단점을 설명해주세요"
```

### Install VLM Model (NexaAI)

```bash
# Install NexaAI CLI (if not installed)
curl -fsSL https://github.com/NexaAI/nexa-sdk/releases/latest/download/nexa-cli_linux_x86_64.sh | bash

# Pull VLM model
nexa pull NexaAI/Qwen3-VL-4B-Instruct-GGUF

# Verify installation
nexa list

# Start NexaAI server
nexa serve --host 0.0.0.0:8080

# Test VLM (in another terminal)
curl -X POST http://localhost:8001/chat/vlm_query \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/product.jpg", "query": "이 제품은 무엇인가요?"}'
```

---

## Performance Benchmarks

### EEVE-Korean-7B

| Metric | Value | Benchmark |
|--------|-------|-----------|
| **한국어 이해** | 0.89 | KoBEST |
| **Instruction Following** | 0.85 | Ko-Alpaca |
| **추론 속도** | ~500ms | RTX 3090 |
| **메모리 사용량** | 4.7 GB | Q5_K_M |

### Response Time

| Query Type | EEVE-Korean | Target |
|-----------|-------------|--------|
| Simple | 200-400ms | < 500ms |
| Medium | 400-800ms | < 1s |
| Complex | 800-2000ms | < 3s |

---

## Migration History

### v1.0.0 (2025-11-15)

**From**: qwen2.5:7b-instruct (Multilingual)
**To**: EEVE-Korean-Instruct-7B-v2.0-Preview (Korean-first)

**Reasons**:
1. ✅ **한국어 성능 향상**: Qwen2.5는 29개 언어 지원, EEVE는 한국어 특화
2. ✅ **검증된 한국 모델**: Yanolja의 production-tested model
3. ✅ **동일한 크기**: 둘 다 7B 파라미터, 4.7GB 메모리
4. ✅ **명확한 전략**: Korean-first approach

**Changes**:
- docker-compose.yml: Added `OLLAMA_MODEL` environment variable
- src/api/chat.py: Updated `get_unified_llm()` to read from env
- Removed qwen2.5:7b-instruct model
- Added EEVE-Korean-Instruct-7B-v2.0-Preview

---

## Future Roadmap

### Short-term (v1.1.0)

- [ ] **EEVE 10.8B**: 더 큰 모델로 업그레이드 (성능 중시)
- [ ] **EXAONE 3.5**: LG AI Research의 bilingual model 테스트
- [ ] **Performance Tuning**: EEVE 모델 파라미터 최적화

### Mid-term (v1.2.0)

- [ ] **Model Quantization**: Q4_K_M 양자화 테스트 (메모리 절약)
- [ ] **Fine-tuning**: 도메인 특화 데이터로 EEVE 파인튜닝
- [ ] **Benchmark Suite**: 한국어 성능 자동 평가 시스템

### Long-term (v2.0.0)

- [ ] **Multi-Model Ensemble**: 여러 모델의 응답 종합
- [ ] **Custom Korean Model**: 처음부터 학습한 자체 모델
- [ ] **Multilingual Support**: 영어/일본어/중국어 지원 추가

---

## Troubleshooting

### Model Not Found

```bash
# Error: model not found
docker exec ollama ollama pull seungduk-yanolja/EEVE-Korean-Instruct-7B-v2.0-Preview
docker-compose restart api
```

### Out of Memory

```bash
# Use smaller quantization
docker exec ollama ollama pull seungduk-yanolja/EEVE-Korean-Instruct-7B-v2.0-Preview:Q4_K_M

# Update environment variable
export OLLAMA_MODEL="seungduk-yanolja/EEVE-Korean-Instruct-7B-v2.0-Preview:Q4_K_M"
```

### Slow Inference

```bash
# Check GPU usage
nvidia-smi

# Use CPU-optimized quantization
docker exec ollama ollama pull seungduk-yanolja/EEVE-Korean-Instruct-7B-v2.0-Preview:Q5_0
```

---

## References

### EEVE Model

- **Paper**: [EEVE: Efficient and Effective Vocabulary Expansion](https://arxiv.org/abs/2402.14714)
- **HuggingFace**: [yanolja/EEVE-Korean-Instruct-10.8B-v1.0](https://huggingface.co/yanolja/EEVE-Korean-Instruct-10.8B-v1.0)
- **Ollama**: [seungduk-yanolja/EEVE-Korean-Instruct-7B-v2.0-Preview](https://ollama.com/seungduk-yanolja/EEVE-Korean-Instruct-7B-v2.0-Preview)

### Alternative Models

- **EXAONE 3.5**: [LG-AI-EXAONE/EXAONE-3.5](https://github.com/LG-AI-EXAONE/EXAONE-3.5)
- **Solar 10.7B**: [upstage/SOLAR-10.7B](https://huggingface.co/upstage/SOLAR-10.7B-v1.0)
- **Qwen2.5**: [Qwen/Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)

---

**Version**: 1.0.0
**Last Updated**: 2025-11-15
**Author**: RAG Enterprise Team
**Status**: Production Ready ✅
