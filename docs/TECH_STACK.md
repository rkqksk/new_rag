# 🔧 RAG Enterprise 기술 스택 완전 가이드

## 임베딩 모델 상세

### 텍스트 임베딩

#### Primary: gte-Qwen2-7B-instruct
```yaml
모델 정보:
  developer: Alibaba DAMO Academy
  size: 7B parameters
  architecture: Qwen2 + GTE (General Text Embeddings)
  embedding_dim: 4096
  max_tokens: 8192

특징:
  - 다국어 지원 (한국어 우수)
  - 긴 문맥 처리 능력
  - 검색 태스크 특화
  - 고품질 의미 표현

사용 사례:
  - 제품 설명 임베딩
  - 기술 문서 임베딩
  - 고객 문의 벡터화

성능:
  - MTEB Score: 73.2
  - Korean KLUE: 82.5
  - Retrieval@10: 89.3

구현:
  from sentence_transformers import SentenceTransformer

  model = SentenceTransformer('Alibaba-NLP/gte-Qwen2-7B-instruct')
  embeddings = model.encode(texts, batch_size=32)
```

#### Fallback: multilingual-e5-large
```yaml
모델 정보:
  developer: Microsoft
  size: 560M parameters
  embedding_dim: 1024
  max_tokens: 512

특징:
  - 다국어 균형
  - 빠른 추론 속도
  - 안정적 성능

사용 시나리오:
  - gte-Qwen2 로딩 실패 시
  - 짧은 텍스트 처리
  - 리소스 제약 환경

구현:
  model = SentenceTransformer('intfloat/multilingual-e5-large')
  embeddings = model.encode(texts, normalize_embeddings=True)
```

#### Korean Specialized: KoE5-base
```yaml
모델 정보:
  developer: KLUE Team
  size: 178M parameters
  embedding_dim: 768
  max_tokens: 512

특징:
  - 한국어 특화 최적화
  - 경량 모델
  - 높은 한국어 정확도

사용 사례:
  - 한국어 전용 검색
  - 모바일/엣지 배포
  - 실시간 처리

구현:
  model = SentenceTransformer('nlpai-lab/KoE5-base')
```

### 이미지 임베딩

#### Primary: OpenCLIP-ViT-H-14
```yaml
모델 정보:
  architecture: Vision Transformer (ViT-H/14)
  size: 632M parameters
  embedding_dim: 1024
  resolution: 224x224 → 336x336 (adaptable)

특징:
  - CLIP 기반 멀티모달 학습
  - 텍스트-이미지 공동 임베딩 공간
  - 제로샷 분류 가능
  - 고품질 시각적 표현

사용 사례:
  - 제품 이미지 검색
  - 텍스트 → 이미지 검색
  - 이미지 유사도 비교

성능:
  - ImageNet Top-1: 84.5%
  - Zero-shot CIFAR-10: 97.8%
  - Retrieval R@5: 91.2%

구현:
  import open_clip

  model, _, preprocess = open_clip.create_model_and_transforms(
      'ViT-H-14', pretrained='laion2b_s32b_b79k'
  )

  # 이미지 임베딩
  image = preprocess(Image.open('product.jpg')).unsqueeze(0)
  image_features = model.encode_image(image)

  # 텍스트 임베딩 (멀티모달 검색)
  text = open_clip.tokenize(["red bottle 50ml"])
  text_features = model.encode_text(text)
```

#### Fallback: CLIP-ViT-L-14
```yaml
모델 정보:
  size: 428M parameters
  embedding_dim: 768
  resolution: 224x224

특징:
  - 경량 대안
  - 빠른 추론
  - 안정적 성능

구현:
  model, preprocess = clip.load("ViT-L/14", device="cuda")
```

### 임베딩 최적화 전략

#### 배치 처리
```python
def batch_embed(texts: List[str], batch_size: int = 32):
    """대용량 텍스트 배치 임베딩"""
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_emb = model.encode(batch, show_progress_bar=True)
        embeddings.append(batch_emb)
    return np.vstack(embeddings)
```

#### GPU 가속 (MLX/Metal)
```python
import mlx.core as mx

def mlx_encode(texts: List[str]):
    """MLX 기반 Apple Silicon 최적화"""
    # MLX array로 변환
    inputs = tokenizer(texts, return_tensors="mlx")

    # MLX 모델 추론
    with mx.stream(mx.gpu):
        outputs = model(**inputs)

    return outputs.last_hidden_state.mean(axis=1)
```

#### 캐싱 전략
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=10000)
def cached_embed(text: str) -> np.ndarray:
    """자주 사용되는 텍스트 임베딩 캐싱"""
    return model.encode([text])[0]

# Redis 캐싱
def redis_cached_embed(text: str) -> np.ndarray:
    key = f"emb:{hashlib.md5(text.encode()).hexdigest()}"
    cached = redis_client.get(key)

    if cached:
        return np.frombuffer(cached, dtype=np.float32)

    embedding = model.encode([text])[0]
    redis_client.setex(key, 86400, embedding.tobytes())  # 24시간
    return embedding
```

---

## 파서 에이전트 상세

### PDF 파싱

#### Docling: 구조화된 추출
```yaml
기능:
  - 텍스트, 표, 이미지 동시 추출
  - 문서 레이아웃 이해
  - 구조화된 JSON 출력

사용 사례:
  - 견적서, 거래명세서
  - 기술 문서
  - 보고서

구현:
  from docling import DocumentConverter

  converter = DocumentConverter()
  result = converter.convert("invoice.pdf")

  # 구조화된 데이터
  text = result.document.export_to_text()
  tables = result.document.tables
  images = result.document.images
```

#### TableTransformer: 표 구조 분석
```yaml
모델:
  - DETR 기반 객체 탐지
  - 표 경계 인식
  - 셀 관계 추출

구현:
  from transformers import TableTransformerForObjectDetection

  model = TableTransformerForObjectDetection.from_pretrained(
      "microsoft/table-transformer-detection"
  )

  # 표 탐지
  outputs = model(pixel_values)
  detected_tables = postprocess_table_detection(outputs)
```

#### Camelot/Tabula: 레거시 PDF
```python
import camelot

# Camelot (복잡한 표)
tables = camelot.read_pdf(
    'report.pdf',
    flavor='lattice',  # 'stream' for borderless
    pages='all'
)

for table in tables:
    df = table.df
    df.to_csv(f'table_{table.page}.csv')

# Tabula (간단한 표)
import tabula
dfs = tabula.read_pdf('invoice.pdf', pages='all', multiple_tables=True)
```

### Excel 파싱

#### Pandas: 데이터프레임 변환
```python
import pandas as pd

# 기본 읽기
df = pd.read_excel('products.xlsx', sheet_name='Sheet1')

# 복잡한 헤더 처리
df = pd.read_excel(
    'complex.xlsx',
    header=[0, 1],  # 멀티레벨 헤더
    skiprows=2,     # 메타데이터 스킵
    usecols='A:F'   # 특정 컬럼만
)

# 데이터 정제
df = df.dropna(subset=['product_code'])
df['price'] = df['price'].str.replace(',', '').astype(float)
```

#### SQLite: 구조화 저장
```python
import sqlite3

# DataFrame → SQLite
conn = sqlite3.connect('products.db')
df.to_sql('products', conn, if_exists='replace', index=False)

# 쿼리
query = "SELECT * FROM products WHERE category = 'Bottle'"
result = pd.read_sql_query(query, conn)
```

#### Text2SQL: 자연어 쿼리
```python
from transformers import pipeline

text2sql = pipeline(
    "text2text-generation",
    model="gaussalgo/T5-LM-Large-text2sql-spider"
)

# 자연어 → SQL
question = "50ml 용기 중 가격 낮은 순서로 5개"
sql = text2sql(f"question: {question} | schema: {schema}")[0]['generated_text']

# 실행
result = pd.read_sql_query(sql, conn)
```

### 이미지 처리

#### EasyOCR: 다국어 텍스트 추출
```python
import easyocr

# Reader 초기화
reader = easyocr.Reader(['ko', 'en', 'ch_sim'])

# OCR 실행
result = reader.readtext('product_label.jpg', detail=1)

for (bbox, text, confidence) in result:
    if confidence > 0.8:
        print(f"텍스트: {text}, 신뢰도: {confidence:.2f}")
```

#### OpenCV: 전처리 및 품질 개선
```python
import cv2
import numpy as np

def preprocess_image(image_path):
    """이미지 전처리 파이프라인"""
    img = cv2.imread(image_path)

    # 1. Grayscale 변환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. 노이즈 제거
    denoised = cv2.fastNlMeansDenoising(gray)

    # 3. 대비 향상 (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)

    # 4. 이진화 (Adaptive Threshold)
    binary = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    return binary
```

#### CLIP/BLIP-2: 시각적 특징 임베딩
```python
from transformers import Blip2Processor, Blip2ForConditionalGeneration

# BLIP-2 초기화
processor = Blip2Processor.from_pretrained("Salesforce/blip2-opt-2.7b")
model = Blip2ForConditionalGeneration.from_pretrained("Salesforce/blip2-opt-2.7b")

# 이미지 캡셔닝
from PIL import Image
image = Image.open("product.jpg")

inputs = processor(images=image, return_tensors="pt")
generated_ids = model.generate(**inputs, max_length=50)
caption = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

# Visual Question Answering
question = "이 제품의 색상은?"
inputs = processor(images=image, text=question, return_tensors="pt")
answer_ids = model.generate(**inputs)
answer = processor.decode(answer_ids[0], skip_special_tokens=True)
```

---

## 청킹 전략

### Semantic Chunking: 의미 단위 분할
```python
from langchain.text_splitter import SemanticChunker

def semantic_chunk(text: str, embedding_model):
    """의미적 유사도 기반 청킹"""
    splitter = SemanticChunker(
        embeddings=embedding_model,
        breakpoint_threshold_type="percentile",  # or "standard_deviation", "interquartile"
        breakpoint_threshold_amount=95
    )

    chunks = splitter.create_documents([text])
    return [chunk.page_content for chunk in chunks]

# 사용 예
from sentence_transformers import SentenceTransformer
embedding_model = SentenceTransformer('gte-Qwen2-7B-instruct')
chunks = semantic_chunk(document_text, embedding_model)
```

### Table-aware Chunking: 표 구조 보존
```python
def table_aware_chunk(html_content: str, max_chunk_size: int = 512):
    """표 구조를 보존하는 청킹"""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, 'html.parser')
    chunks = []

    # 표는 분리하지 않고 독립 청크로
    for table in soup.find_all('table'):
        table_text = table.get_text(separator=' ', strip=True)
        chunks.append({
            'type': 'table',
            'content': table_text,
            'html': str(table)
        })
        table.decompose()  # 처리 후 제거

    # 나머지 텍스트는 일반 청킹
    remaining_text = soup.get_text(separator=' ', strip=True)
    text_chunks = recursive_chunk(remaining_text, max_chunk_size)

    for chunk in text_chunks:
        chunks.append({
            'type': 'text',
            'content': chunk
        })

    return chunks
```

### Hierarchical Chunking: 문서 계층 유지
```python
def hierarchical_chunk(markdown_text: str):
    """마크다운 제목 기반 계층적 청킹"""
    import re

    # 제목 레벨별 파싱
    sections = []
    current_section = {'level': 0, 'title': 'root', 'content': [], 'children': []}
    stack = [current_section]

    for line in markdown_text.split('\n'):
        # 제목 감지 (# ~ ######)
        match = re.match(r'^(#{1,6})\s+(.+)$', line)

        if match:
            level = len(match.group(1))
            title = match.group(2)

            # 계층 조정
            while stack and stack[-1]['level'] >= level:
                stack.pop()

            new_section = {
                'level': level,
                'title': title,
                'content': [],
                'children': []
            }

            stack[-1]['children'].append(new_section)
            stack.append(new_section)
        else:
            # 현재 섹션에 내용 추가
            stack[-1]['content'].append(line)

    return current_section

# 청크 생성
def section_to_chunks(section, parent_context=""):
    """섹션을 컨텍스트 포함 청크로 변환"""
    chunks = []
    context = f"{parent_context} > {section['title']}" if parent_context else section['title']

    content = '\n'.join(section['content'])
    if content.strip():
        chunks.append({
            'context': context,
            'content': content,
            'level': section['level']
        })

    for child in section['children']:
        chunks.extend(section_to_chunks(child, context))

    return chunks
```

### Sliding Window: 컨텍스트 중첩
```python
def sliding_window_chunk(text: str, window_size: int = 512, overlap: int = 128):
    """슬라이딩 윈도우 청킹 (컨텍스트 보존)"""
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained('gpt2')
    tokens = tokenizer.encode(text)

    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + window_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens)

        chunks.append({
            'text': chunk_text,
            'start_idx': start,
            'end_idx': end
        })

        if end == len(tokens):
            break

        start += window_size - overlap  # 오버랩만큼 이동

    return chunks
```

---

## 검색 파이프라인

### 하이브리드 검색: Dense + Sparse

#### Dense Retrieval (벡터 검색)
```python
from qdrant_client import QdrantClient
from qdrant_client.models import SearchParams

client = QdrantClient(host="172.28.0.2", port=6333)

def dense_search(query: str, top_k: int = 10):
    """벡터 유사도 검색"""
    # 쿼리 임베딩
    query_vector = embedding_model.encode([query])[0].tolist()

    # Qdrant 검색
    results = client.search(
        collection_name="documents",
        query_vector=query_vector,
        limit=top_k,
        search_params=SearchParams(
            hnsw_ef=128,  # 정확도 vs 속도 트레이드오프
            exact=False   # Approximate search
        )
    )

    return [(hit.id, hit.score, hit.payload) for hit in results]
```

#### Sparse Retrieval (BM25 키워드 매칭)
```python
from rank_bm25 import BM25Okapi
import jieba  # 한국어: konlpy

class BM25Retriever:
    def __init__(self, documents: List[str]):
        # 토큰화
        self.tokenized_docs = [doc.split() for doc in documents]
        self.bm25 = BM25Okapi(self.tokenized_docs)
        self.documents = documents

    def search(self, query: str, top_k: int = 10):
        tokenized_query = query.split()
        scores = self.bm25.get_scores(tokenized_query)

        # Top-K 추출
        top_indices = np.argsort(scores)[::-1][:top_k]

        return [(idx, scores[idx], self.documents[idx])
                for idx in top_indices]
```

#### Hybrid Fusion
```python
def hybrid_search(query: str, top_k: int = 20, alpha: float = 0.7):
    """Dense + Sparse 하이브리드 검색"""
    # 각각 검색
    dense_results = dense_search(query, top_k=top_k)
    sparse_results = bm25_retriever.search(query, top_k=top_k)

    # 점수 정규화 (0-1 범위)
    def normalize_scores(results):
        scores = [score for _, score, _ in results]
        min_score, max_score = min(scores), max(scores)
        if max_score == min_score:
            return results

        normalized = []
        for doc_id, score, payload in results:
            norm_score = (score - min_score) / (max_score - min_score)
            normalized.append((doc_id, norm_score, payload))
        return normalized

    dense_norm = normalize_scores(dense_results)
    sparse_norm = normalize_scores(sparse_results)

    # Reciprocal Rank Fusion (RRF)
    from collections import defaultdict
    rrf_scores = defaultdict(float)
    k = 60  # RRF constant

    for rank, (doc_id, _, payload) in enumerate(dense_norm):
        rrf_scores[doc_id] += alpha / (k + rank + 1)

    for rank, (doc_id, _, payload) in enumerate(sparse_norm):
        rrf_scores[doc_id] += (1 - alpha) / (k + rank + 1)

    # 정렬 및 반환
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results[:top_k]
```

### Re-ranking: Cross-encoder

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class CrossEncoderReranker:
    def __init__(self, model_name='cross-encoder/ms-marco-MiniLM-L-6-v2'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.eval()

    def rerank(self, query: str, documents: List[str], top_k: int = 5):
        """Cross-encoder로 재순위화"""
        # 쿼리-문서 쌍 생성
        pairs = [[query, doc] for doc in documents]

        # 배치 인코딩
        inputs = self.tokenizer(
            pairs,
            padding=True,
            truncation=True,
            return_tensors='pt',
            max_length=512
        )

        # 스코어 계산
        with torch.no_grad():
            scores = self.model(**inputs).logits.squeeze().tolist()

        # 정렬
        doc_scores = list(zip(documents, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)

        return doc_scores[:top_k]

# 사용 예
reranker = CrossEncoderReranker()
initial_results = hybrid_search("50ml 빨간 용기", top_k=20)
documents = [payload['text'] for _, _, payload in initial_results]
reranked = reranker.rerank(query, documents, top_k=5)
```

---

## QA 에이전트

### Chain-of-Thought 추론

```python
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def chain_of_thought_qa(query: str, context: str):
    """CoT 프롬프트를 사용한 추론"""

    system_prompt = """당신은 제조업 전문 AI 어시스턴트입니다.
주어진 컨텍스트를 바탕으로 단계적으로 추론하여 답변하세요.

답변 형식:
1. **문제 이해**: 질문의 핵심 파악
2. **정보 추출**: 컨텍스트에서 관련 정보 찾기
3. **추론 과정**: 단계별 논리 전개
4. **최종 답변**: 명확하고 간결한 결론
5. **근거**: 답변의 출처 명시
"""

    user_prompt = f"""질문: {query}

컨텍스트:
{context}

위 형식에 따라 답변해주세요."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    return response.content[0].text
```

### Citation 자동 생성

```python
def generate_answer_with_citations(query: str, retrieved_docs: List[Dict]):
    """인용과 함께 답변 생성"""

    # 컨텍스트 구성 (출처 포함)
    context_parts = []
    for idx, doc in enumerate(retrieved_docs, 1):
        source = doc.get('source', 'Unknown')
        text = doc.get('text', '')
        context_parts.append(f"[{idx}] (출처: {source})\n{text}")

    context = "\n\n".join(context_parts)

    system_prompt = """답변 시 반드시 [숫자] 형식으로 출처를 표시하세요.
예: "제품 용량은 50ml입니다[1]. 색상은 빨간색입니다[2]."
"""

    response = chain_of_thought_qa(query, context)

    # 인용 추출
    import re
    citations = re.findall(r'\[(\d+)\]', response)
    cited_sources = [retrieved_docs[int(c)-1] for c in citations if int(c) <= len(retrieved_docs)]

    return {
        'answer': response,
        'citations': cited_sources,
        'citation_count': len(set(citations))
    }
```

### Confidence 스코어링

```python
def calculate_confidence(query: str, answer: str, retrieved_docs: List[Dict]) -> float:
    """답변 신뢰도 계산"""

    # 1. 검색 점수 (평균)
    retrieval_scores = [doc.get('score', 0) for doc in retrieved_docs]
    avg_retrieval_score = np.mean(retrieval_scores) if retrieval_scores else 0

    # 2. 답변 길이 (너무 짧거나 길면 감점)
    answer_length = len(answer.split())
    length_score = 1.0
    if answer_length < 10:
        length_score = 0.5
    elif answer_length > 500:
        length_score = 0.8

    # 3. 인용 비율
    import re
    citations = re.findall(r'\[(\d+)\]', answer)
    citation_ratio = len(set(citations)) / len(retrieved_docs) if retrieved_docs else 0

    # 4. 엔티티 매칭 (쿼리의 핵심 용어가 답변에 포함되는지)
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer(max_features=10)

    try:
        tfidf = vectorizer.fit_transform([query, answer])
        entity_overlap = (tfidf[0].toarray() * tfidf[1].toarray()).sum()
    except:
        entity_overlap = 0.5

    # 가중 평균
    confidence = (
        0.4 * avg_retrieval_score +
        0.2 * length_score +
        0.2 * citation_ratio +
        0.2 * entity_overlap
    )

    return min(max(confidence, 0.0), 1.0)  # 0-1 범위로 클리핑
```

### Fallback 답변 전략

```python
def qa_with_fallback(query: str):
    """Fallback 메커니즘이 있는 QA 시스템"""

    # 1차 시도: RAG
    try:
        retrieved_docs = hybrid_search(query, top_k=5)

        if not retrieved_docs:
            raise ValueError("No documents retrieved")

        answer_data = generate_answer_with_citations(query, retrieved_docs)
        confidence = calculate_confidence(query, answer_data['answer'], retrieved_docs)

        if confidence > 0.7:
            return {
                'answer': answer_data['answer'],
                'confidence': confidence,
                'method': 'RAG',
                'citations': answer_data['citations']
            }
    except Exception as e:
        print(f"RAG failed: {e}")

    # 2차 시도: 웹 검색
    try:
        from tavily import TavilyClient
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

        search_results = tavily.search(query, max_results=3)
        web_context = "\n\n".join([r['content'] for r in search_results['results']])

        answer = chain_of_thought_qa(query, web_context)

        return {
            'answer': answer,
            'confidence': 0.6,
            'method': 'Web Search',
            'sources': [r['url'] for r in search_results['results']]
        }
    except Exception as e:
        print(f"Web search failed: {e}")

    # 3차 시도: LLM 일반 지식
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"{query}\n\n참고: 제공된 문서에서 정보를 찾을 수 없어 일반적인 지식으로 답변합니다."
            }]
        )

        return {
            'answer': response.content[0].text,
            'confidence': 0.4,
            'method': 'General Knowledge',
            'warning': '제공된 문서에서 정보를 찾을 수 없습니다.'
        }
    except Exception as e:
        print(f"LLM failed: {e}")

    # 최종 Fallback
    return {
        'answer': "죄송합니다. 현재 답변을 생성할 수 없습니다. 나중에 다시 시도해주세요.",
        'confidence': 0.0,
        'method': 'Fallback',
        'error': True
    }
```

---

*Last Updated: 2025-10-18*
*Tech Stack Version: 1.0*
