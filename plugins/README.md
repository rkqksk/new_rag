# RAG Enterprise Domain Expert Plugins

하이브리드 플러그인 아키텍처: 코드 로직 + 설정 파일

## 📋 개요

Skill 파일을 플러그인 + 설정 파일로 변환하여 RAG Enterprise 프로젝트에 통합했습니다.

### 변환 완료 항목
- ✅ **Manufacturing Expert Plugin**: 제조/생산 문서 처리
- ✅ **Packaging Expert Plugin**: 패키징/포장 문서 처리

## 🏗️ 구조

```
plugins/
├── base_plugin.py                          # 베이스 클래스
│
├── manufacturing_expert/
│   ├── __init__.py
│   ├── plugin.py                           # 핵심 로직
│   └── config/
│       ├── terminology.yaml                # 제조 용어
│       ├── document_types.yaml             # 문서 타입
│       └── patterns.yaml                   # 추출 패턴
│
├── packaging_expert/
│   ├── __init__.py
│   ├── plugin.py                           # 핵심 로직
│   └── config/
│       ├── materials.yaml                  # 패키징 재질
│       ├── standards.yaml                  # 규격/표준
│       └── patterns.yaml                   # 추출 패턴
│
└── test_plugins.py                         # 테스트 코드
```

## 🎯 주요 기능

### Manufacturing Expert
- 문서 분류 (SOP, 장비 사양, 품질 계획, 결함 분석 등)
- 제조 용어 추출 (Cpk, OEE, PPM 등)
- 공정 파라미터 추출 (온도, 압력, 시간 등)
- 품질 지표 인식
- 규격 참조 (ISO 9001, FDA, GMP 등)

### Packaging Expert
- 문서 분류 (재질 사양, 컨테이너 도면, 규제 문서 등)
- 재질 정보 추출 (PET, HDPE, PP 등)
- 치수 및 용량 추출
- 차단 특성 (산소, 수분 투과율)
- 규제 준수 (FDA, EU, REACH 등)

## 🚀 설치 및 사용

### 1. 프로젝트에 복사

```bash
# RAG Enterprise 프로젝트 루트로 이동
cd /Users/oypnus/Project/rag-enterprise

# plugins 디렉토리가 없으면 생성
mkdir -p plugins

# 플러그인 파일들을 복사
# (이 파일들을 /home/claude/rag_plugins/에서 로컬로 복사)
```

### 2. 의존성 설치

```bash
# 프로젝트 가상환경 활성화
source .venv/bin/activate

# 필요한 패키지 설치
pip install pyyaml --break-system-packages
```

### 3. 테스트 실행

```bash
# 플러그인 테스트
python plugins/test_plugins.py
```

## 💻 사용 예제

### 기본 사용법

```python
from plugins.manufacturing_expert import ManufacturingExpertPlugin
from plugins.packaging_expert import PackagingExpertPlugin

# 플러그인 초기화
mfg_plugin = ManufacturingExpertPlugin()
pkg_plugin = PackagingExpertPlugin()

# 문서 처리
document = {
    'filename': 'SOP-001.pdf',
    'content': '문서 내용...',
    'metadata': {}
}

# 처리 가능 여부 확인
if mfg_plugin.can_process(document):
    result = mfg_plugin.process_document(document)
    
    if result.success:
        print(f"문서 타입: {result.metadata.doc_type}")
        print(f"추출된 용어: {result.metadata.terminology}")
        print(f"생성된 청크: {len(result.chunks)}")
```

### PluginManager 사용

```python
from plugins.test_plugins import PluginManager

# 매니저 초기화 (모든 플러그인 자동 로드)
manager = PluginManager()

# 문서 처리 (자동으로 적절한 플러그인 선택)
result = manager.process_document(document)
```

### RAG Orchestrator 통합

```python
# mcp_servers/rag_orchestrator.py에 추가

from plugins.test_plugins import PluginManager

class RAGOrchestrator:
    def __init__(self):
        self.plugin_manager = PluginManager()
    
    def ingest_document(self, document):
        # 도메인 전문 지식으로 문서 처리
        result = self.plugin_manager.process_document(document)
        
        if result.success:
            # 강화된 콘텐츠와 메타데이터를 벡터 DB에 저장
            enriched_chunks = result.chunks
            metadata = {
                'doc_type': result.metadata.doc_type,
                'domain': result.metadata.domain,
                'terminology': result.metadata.terminology,
                # ...
            }
            
            # Qdrant에 저장
            self.store_in_vector_db(enriched_chunks, metadata)
        
        return result
```

## 🔧 설정 커스터마이징

### 용어 추가 (terminology.yaml)

```yaml
# plugins/manufacturing_expert/config/terminology.yaml

process_operations:
  - setup
  - changeover
  - validation
  - your_custom_term  # 추가
```

### 추출 패턴 추가 (patterns.yaml)

```yaml
# plugins/manufacturing_expert/config/patterns.yaml

parameters:
  your_parameter:
    patterns:
      - "your_regex_pattern"
    unit_conversion:
      unit1: standard_unit
```

### 문서 타입 추가 (document_types.yaml)

```yaml
# plugins/manufacturing_expert/config/document_types.yaml

document_types:
  your_doc_type:
    name: "Your Document Type"
    description: "Description"
    indicators:
      - "keyword1"
      - "keyword2"
```

## 📊 성능 및 안정성

### 장점
- ✅ **경량**: MCP 서버보다 훨씬 적은 오버헤드
- ✅ **빠른 개발**: 1-2일이면 새 플러그인 추가 가능
- ✅ **쉬운 테스트**: 단위 테스트 작성 간단
- ✅ **유연성**: 설정 파일로 코드 수정 없이 업데이트
- ✅ **확장성**: 새 도메인 추가 용이

### 제약사항
- ⚠️ Claude Code에서 직접 사용 불가 (RAG 시스템 통해서만)
- ⚠️ 실행 중 설정 변경 시 재시작 필요

## 🧪 테스트 결과 예상 출력

```
============================================================
RAG Enterprise Domain Expert Plugins Test Suite
============================================================

============================================================
TEST 3: Plugin Manager Info
============================================================
✓ Loaded: Manufacturing Expert Plugin
✓ Loaded: Packaging Expert Plugin

Loaded 2 plugins:

  Domain: manufacturing
  Class: ManufacturingExpertPlugin
  Config loaded: True

  Domain: packaging
  Class: PackagingExpertPlugin
  Config loaded: True

============================================================
TEST 1: Manufacturing SOP
============================================================
Processing with: manufacturing (confidence: 0.70)

✓ Success!
Document Type: sop
Domain: manufacturing
Categories: process, quality, compliance
Confidence: 0.70

Terminology extracted: 15 terms
  Sample: cpk, oee, iso 9001, fda 21 cfr part 11, calibration

Parameters extracted: 3
  - temperature: 150 °C
  - temperature: 2 °C
  - pressure: 45 psi

Chunks created: 2
```

## 🔄 Web Skills와의 차이

| 기능 | Web Skills | 플러그인 |
|------|-----------|----------|
| 사용 환경 | 웹 전용 | 로컬 코드 |
| Claude Code 지원 | ❌ | ✅ |
| 커스터마이징 | 제한적 | 완전 제어 |
| 설정 변경 | 불가 | 파일 편집 |
| 디버깅 | 어려움 | 쉬움 |
| 성능 | N/A | 빠름 |

## 📝 다음 단계

### 즉시 가능
1. 로컬 프로젝트에 복사
2. 테스트 실행
3. RAG Orchestrator에 통합

### 향후 확장
1. 새 도메인 플러그인 추가 (예: 의료, 법률)
2. ML 모델 통합 (NER, 분류)
3. 실시간 학습 기능
4. GraphRAG 통합

## 🤝 기여

새 도메인 전문 지식이 필요하면:
1. `base_plugin.py`를 상속
2. `config/` 디렉토리에 YAML 파일 추가
3. 테스트 케이스 작성
4. Pull Request

## 📄 라이선스

프로젝트 라이선스와 동일

## 🙋 문의

프로젝트 메인테이너에게 문의하세요.
