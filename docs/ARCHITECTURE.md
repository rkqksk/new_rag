# 🏗️ RAG Enterprise 시스템 아키텍처

## 5계층 아키텍처 상세 설계

---

## Layer 1: UI/UX Layer

### 관리자 대시보드

#### 기능 모듈
```yaml
데이터 관리:
  - 문서 업로드 인터페이스
  - 벡터화 진행 상황 모니터링
  - 데이터셋 통계 대시보드
  - 라벨링 및 QA 도구

모델 관리:
  - Teacher/Student 모델 상태
  - 파인튜닝 진행 상황
  - 모델 성능 비교
  - A/B 테스트 설정

사용자 관리:
  - RBAC 권한 설정
  - 사용자 활동 로그
  - API 키 발급/관리
  - 접근 제어 정책

시스템 모니터링:
  - 실시간 메트릭 (CPU, Memory, GPU)
  - API 요청 통계
  - 에러율 및 레이턴시
  - 알림 설정
```

#### 기술 스택
```yaml
Frontend:
  - React 18 + TypeScript
  - State: Redux Toolkit + RTK Query
  - UI: TailwindCSS + HeadlessUI
  - Charts: Recharts, D3.js
  - Forms: React Hook Form + Zod

Build:
  - Vite (fast HMR)
  - ESBuild (transpiling)
  - PostCSS (CSS processing)

Testing:
  - Vitest (unit tests)
  - Playwright (E2E tests)
  - React Testing Library
```

### 사용자 포털

#### 권한 계층
```yaml
Super Admin:
  - 전체 시스템 제어
  - 모든 데이터 접근
  - 시스템 설정 변경
  - 사용자 관리

Internal (부서별 권한):
  인사:
    - 인사 문서 조회/검색
    - 직원 정보 관리
    - 급여/복지 데이터

  생산:
    - 생산 계획/실적
    - 품질 데이터
    - 설비 정보

  물류:
    - 재고 현황
    - 출하/입고 내역
    - 배송 추적

Client (고객):
  - 제품 정보 조회
  - 주문/배송 상태
  - 품질 이력 (제한적)
  - 견적 요청
```

#### 인터페이스 설계
```typescript
// User Interface
interface User {
  id: string;
  email: string;
  role: 'super_admin' | 'internal' | 'client';
  permissions: string[];
  department?: 'hr' | 'production' | 'logistics';
}

// Permission Check
function hasPermission(user: User, resource: string, action: string): boolean {
  const permission = `${resource}:${action}`;
  return user.permissions.includes(permission) ||
         user.permissions.includes(`${resource}:*`) ||
         user.permissions.includes('*:*');
}

// Example usage
if (hasPermission(user, 'product', 'read')) {
  // Show product data
}
```

---

## Layer 2: Orchestration Layer

### Teacher-Student LLM 구조

#### 모델 구성
```yaml
Teacher (Qwen 2.5-7B):
  backend: MLX (Apple Silicon 최적화)
  precision: FP16
  context_window: 32K tokens
  role:
    - 고품질 응답 생성
    - 지식 증류 데이터 생성
    - 복잡한 추론 작업

Student 1 (gemma-3-1B):
  backend: Transformers (CUDA/CPU)
  precision: INT8 (Quantized)
  context_window: 8K tokens
  role:
    - 실시간 서비스 (저지연)
    - 간단한 질의 응답
    - 엣지 배포용

Student 2 (Qwen 2.5-3B):
  backend: MLX
  precision: FP16
  context_window: 16K tokens
  role:
    - 추천/검색 작업
    - 중간 복잡도 작업
    - Teacher와 Student 1 사이 균형
```

#### 라우팅 전략
```python
class QueryRouter:
    """쿼리 복잡도 기반 모델 라우팅"""

    def route(self, query: str) -> str:
        complexity = self.estimate_complexity(query)

        if complexity < 0.3:
            return "student_1"  # gemma-3-1B
        elif complexity < 0.7:
            return "student_2"  # Qwen 2.5-3B
        else:
            return "teacher"    # Qwen 2.5-7B

    def estimate_complexity(self, query: str) -> float:
        """복잡도 추정 (0-1)"""
        factors = {
            'length': len(query.split()) / 100,  # 길이
            'entities': self.count_entities(query) / 10,  # 엔티티 수
            'reasoning': self.has_reasoning_keywords(query),  # 추론 키워드
            'multimodal': self.is_multimodal(query)  # 멀티모달 여부
        }

        # 가중 평균
        complexity = (
            0.2 * min(factors['length'], 1.0) +
            0.3 * min(factors['entities'], 1.0) +
            0.3 * (1.0 if factors['reasoning'] else 0.0) +
            0.2 * (1.0 if factors['multimodal'] else 0.0)
        )

        return complexity
```

### Prompt Chain / Agent Flow

#### 프롬프트 체인 설계
```yaml
체인 1: 제품 추천
  단계:
    1. Query Understanding:
       - 의도 파악 (검색/비교/추천)
       - 엔티티 추출 (용량, 색상, 재질)
       - 제약 조건 (가격, 재고)

    2. Information Retrieval:
       - 벡터 검색
       - 필터링
       - 랭킹

    3. Response Generation:
       - 제품 설명
       - 비교 테이블
       - 추천 이유

체인 2: 불량 분석
  단계:
    1. Multimodal Analysis:
       - 이미지 분석 (CLIP/BLIP-2)
       - 텍스트 설명 분석
       - 메타데이터 추출

    2. Pattern Matching:
       - 과거 불량 사례 검색
       - 유사도 비교
       - 원인 후보 추출

    3. Root Cause Analysis:
       - 원인 진단
       - 조치 방안 제시
       - 예방 가이드

체인 3: 문서 처리
  단계:
    1. Document Parsing:
       - 포맷 인식 (PDF, Excel, Image)
       - 구조 추출 (텍스트, 표, 이미지)
       - OCR (필요시)

    2. Information Extraction:
       - NER (제품코드, 날짜, 금액)
       - 관계 추출
       - 메타데이터 구성

    3. Embedding & Storage:
       - 청킹
       - 벡터화
       - Qdrant 저장
```

#### Agent Flow 구현
```python
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class AgentState:
    """에이전트 상태"""
    query: str
    context: Dict[str, Any]
    intermediate_results: List[Any]
    final_result: Any = None

class AgentPipeline:
    """에이전트 파이프라인"""

    def __init__(self, stages: List['AgentStage']):
        self.stages = stages

    async def execute(self, initial_state: AgentState) -> AgentState:
        """파이프라인 실행"""
        state = initial_state

        for stage in self.stages:
            try:
                state = await stage.process(state)

                # 조건부 종료
                if stage.should_terminate(state):
                    break

            except Exception as e:
                state = await stage.handle_error(state, e)

        return state

class AgentStage:
    """파이프라인 단계"""

    async def process(self, state: AgentState) -> AgentState:
        """단계 처리 (서브클래스에서 구현)"""
        raise NotImplementedError

    def should_terminate(self, state: AgentState) -> bool:
        """조기 종료 조건"""
        return False

    async def handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """에러 처리"""
        print(f"Error in {self.__class__.__name__}: {error}")
        return state

# 사용 예
class QueryUnderstandingStage(AgentStage):
    async def process(self, state: AgentState) -> AgentState:
        # 의도 파악
        intent = await self.detect_intent(state.query)
        state.context['intent'] = intent

        # 엔티티 추출
        entities = await self.extract_entities(state.query)
        state.context['entities'] = entities

        return state

class RetrievalStage(AgentStage):
    async def process(self, state: AgentState) -> AgentState:
        # 검색 실행
        results = await self.search(
            state.query,
            filters=state.context.get('entities', {})
        )

        state.intermediate_results.append(results)
        state.context['retrieved_docs'] = results

        return state

class GenerationStage(AgentStage):
    async def process(self, state: AgentState) -> AgentState:
        # 응답 생성
        response = await self.generate_response(
            query=state.query,
            context=state.context['retrieved_docs']
        )

        state.final_result = response
        return state

# 파이프라인 구성
pipeline = AgentPipeline([
    QueryUnderstandingStage(),
    RetrievalStage(),
    GenerationStage()
])

# 실행
result = await pipeline.execute(
    AgentState(query="50ml 빨간 용기 추천", context={}, intermediate_results=[])
)
```

### Knowledge Distillation Pipeline

#### 증류 프로세스
```python
import torch
import torch.nn.functional as F

class DistillationTrainer:
    """지식 증류 트레이너"""

    def __init__(
        self,
        teacher_model,
        student_model,
        temperature: float = 2.0,
        alpha: float = 0.3
    ):
        self.teacher = teacher_model
        self.student = student_model
        self.temperature = temperature
        self.alpha = alpha  # hard loss 가중치

    def distillation_loss(
        self,
        student_logits: torch.Tensor,
        teacher_logits: torch.Tensor,
        labels: torch.Tensor
    ) -> torch.Tensor:
        """증류 손실 계산"""

        # Soft loss (KL Divergence)
        soft_loss = F.kl_div(
            F.log_softmax(student_logits / self.temperature, dim=-1),
            F.softmax(teacher_logits / self.temperature, dim=-1),
            reduction='batchmean'
        ) * (self.temperature ** 2)

        # Hard loss (Cross Entropy)
        hard_loss = F.cross_entropy(student_logits, labels)

        # 가중 합
        total_loss = self.alpha * hard_loss + (1 - self.alpha) * soft_loss

        return total_loss

    async def generate_training_data(
        self,
        queries: List[str],
        batch_size: int = 8
    ) -> List[Dict]:
        """Teacher로부터 학습 데이터 생성"""

        training_data = []

        for i in range(0, len(queries), batch_size):
            batch = queries[i:i+batch_size]

            # Teacher 응답 생성
            teacher_responses = await self.teacher.batch_generate(
                batch,
                temperature=0.7,
                max_tokens=500
            )

            for query, response in zip(batch, teacher_responses):
                training_data.append({
                    'query': query,
                    'teacher_response': response,
                    'confidence': self.estimate_quality(response)
                })

        # 고품질 샘플만 필터링
        filtered_data = [
            d for d in training_data
            if d['confidence'] > 0.8
        ]

        return filtered_data
```

---

## Layer 3: RAG Retrieval Layer

### 데이터 수집 파이프라인

#### 직접 업로드
```python
from fastapi import UploadFile, FastAPI
import aiofiles

app = FastAPI()

@app.post("/upload")
async def upload_document(file: UploadFile):
    """비동기 파일 업로드"""

    # 파일 저장
    file_path = f"documents/{file.filename}"

    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    # 처리 큐에 추가
    await processing_queue.enqueue({
        'file_path': file_path,
        'mime_type': file.content_type,
        'uploaded_at': datetime.now()
    })

    return {"status": "queued", "file_id": file_path}
```

#### 웹 크롤링
```python
import asyncio
import aiohttp
from playwright.async_api import async_playwright

class WebCrawler:
    """비동기 웹 크롤러"""

    async def crawl_static(self, url: str) -> Dict:
        """정적 페이지 크롤링 (aiohttp)"""

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()

                # 파싱
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')

                return {
                    'url': url,
                    'title': soup.title.string if soup.title else '',
                    'text': soup.get_text(separator=' ', strip=True),
                    'links': [a['href'] for a in soup.find_all('a', href=True)]
                }

    async def crawl_dynamic(self, url: str) -> Dict:
        """동적 페이지 크롤링 (Playwright)"""

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto(url, wait_until='networkidle')

            # JavaScript 실행 대기
            await page.wait_for_load_state('domcontentloaded')

            # 데이터 추출
            title = await page.title()
            text = await page.inner_text('body')

            await browser.close()

            return {
                'url': url,
                'title': title,
                'text': text
            }
```

#### N8N 워크플로우 자동화
```yaml
workflow: "Product Data Sync"

triggers:
  - cron: "0 */6 * * *"  # 6시간마다
  - webhook: "/api/trigger/sync"

nodes:
  1. HTTP Request:
     method: GET
     url: https://api.example.com/products
     authentication: Bearer Token

  2. JSON Parse:
     extract:
       - id: $.products[*].id
       - name: $.products[*].name
       - specs: $.products[*].specifications

  3. Transform:
     mapping:
       product_code: "{{ $json.id }}"
       product_name: "{{ $json.name }}"
       embedding_text: "{{ $json.name }} {{ $json.specs }}"

  4. HTTP Request (FastAPI):
     method: POST
     url: http://172.28.0.7:8000/api/documents/batch
     body: "{{ $json }}"

  5. Success Notification:
     service: Slack
     channel: "#data-sync"
     message: "✅ {{ $json.count }} products synced"
```

### 전처리 및 임베딩

#### 문서 청킹
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_document(text: str, chunk_size: int = 512, overlap: int = 128):
    """재귀적 문서 청킹"""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len
    )

    chunks = splitter.split_text(text)

    return [
        {
            'text': chunk,
            'char_start': text.index(chunk),
            'char_end': text.index(chunk) + len(chunk),
            'chunk_index': idx
        }
        for idx, chunk in enumerate(chunks)
    ]
```

#### 벡터화 파이프라인
```python
class EmbeddingPipeline:
    """임베딩 파이프라인"""

    def __init__(self, model_name: str = 'gte-Qwen2-7B-instruct'):
        self.model = SentenceTransformer(model_name)

    async def process_document(self, document: Dict) -> List[Dict]:
        """문서 → 청크 → 임베딩 → Qdrant"""

        # 1. 청킹
        chunks = chunk_document(document['text'])

        # 2. 배치 임베딩
        texts = [c['text'] for c in chunks]
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True
        )

        # 3. Qdrant 포인트 생성
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            point = {
                'id': str(uuid.uuid4()),
                'vector': embedding.tolist(),
                'payload': {
                    'text': chunk['text'],
                    'document_id': document['id'],
                    'chunk_index': chunk['chunk_index'],
                    'metadata': document.get('metadata', {})
                }
            }
            points.append(point)

        # 4. Qdrant 저장
        await self.qdrant_client.upsert(
            collection_name='documents',
            points=points
        )

        return points
```

### 검색 및 생성

#### 검색 파이프라인
```python
class SearchPipeline:
    """다단계 검색 파이프라인"""

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """1. Query Understanding"""
        query_vector = self.embedding_model.encode([query])[0]

        """2. Multi-stage Retrieval"""
        # Stage 1: Fast approximate search (top 20)
        initial_results = await self.qdrant_client.search(
            collection_name='documents',
            query_vector=query_vector.tolist(),
            limit=20,
            query_filter=self._build_filter(filters)
        )

        # Stage 2: Re-ranking (top 5)
        documents = [r.payload['text'] for r in initial_results]
        reranked = self.reranker.rerank(query, documents, top_k=top_k)

        """3. Context Assembly"""
        context_docs = []
        for doc, score in reranked:
            context_docs.append({
                'text': doc,
                'score': score
            })

        return context_docs

    def _build_filter(self, filters: Optional[Dict]):
        """Qdrant 필터 생성"""
        if not filters:
            return None

        from qdrant_client.models import Filter, FieldCondition, MatchValue

        conditions = []

        for key, value in filters.items():
            conditions.append(
                FieldCondition(
                    key=f"metadata.{key}",
                    match=MatchValue(value=value)
                )
            )

        return Filter(must=conditions)
```

---

## 데이터 플로우 다이어그램

```
[사용자 질의]
     ↓
[Layer 2: Query Router] → Teacher / Student 선택
     ↓
[Layer 2: Prompt Chain] → 의도 파악 / 엔티티 추출
     ↓
[Layer 3: Embedding] → 쿼리 벡터화
     ↓
[Layer 3: Qdrant Search] → 벡터 검색 (Top-20)
     ↓
[Layer 3: Re-ranking] → 정밀 순위화 (Top-5)
     ↓
[Layer 2: LLM Generation] → 컨텍스트 + 쿼리 → 답변 생성
     ↓
[Layer 1: UI Response] → 사용자에게 응답
```

---

*Last Updated: 2025-10-18*
*Architecture Version: 1.0*
