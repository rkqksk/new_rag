---
name: rag-vector-search  
description: Qdrant 벡터 데이터베이스를 사용한 고급 의미 검색 스킬. 하이브리드 검색, 리랭킹, 메타데이터 필터링을 지원합니다.
license: MIT
allowed-tools:
  - python
  - bash
metadata:
  version: "2.0.0"
  category: "search"
  author: "RAG Enterprise Team"
  requires: ["qdrant-client", "sentence-transformers"]
---

# RAG Vector Search Skill

Qdrant를 활용한 고급 벡터 검색 기능을 제공합니다. 이 스킬은 의미 기반 검색, 하이브리드 검색, 그리고 지능형 리랭킹을 지원합니다.

## 활성화 조건

다음 키워드나 작업에서 자동 활성화:
- "벡터 검색", "유사도 검색", "의미 검색"
- "Qdrant에서 검색", "관련 문서 찾기"
- "RAG 검색 수행", "컨텍스트 검색"

## 핵심 기능

### 1. 벡터 검색 엔진

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, Range
from sentence_transformers import SentenceTransformer
import numpy as np

class VectorSearchEngine:
    def __init__(self, collection_name: str = "documents"):
        self.client = QdrantClient(url="http://localhost:6333")
        self.collection = collection_name
        self.encoder = SentenceTransformer('gte-Qwen2-7B-instruct')
        
    def search(self, query: str, top_k: int = 10, filters: dict = None):
        """의미 기반 벡터 검색"""
        
        # 쿼리 임베딩 생성
        query_vector = self.encoder.encode(query)
        
        # 필터 구성
        search_filters = self._build_filters(filters) if filters else None
        
        # 검색 실행
        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k * 2,  # 리랭킹을 위해 더 많이 가져옴
            query_filter=search_filters,
            with_payload=True,
            with_vectors=False
        )
        
        # 후처리 및 리랭킹
        return self._rerank_results(query, results, top_k)
```

### 2. 하이브리드 검색

벡터 검색과 키워드 검색을 결합:

```python
def hybrid_search(self, query: str, top_k: int = 10, alpha: float = 0.7):
    """벡터 검색과 BM25 키워드 검색 결합"""
    
    # 벡터 검색
    vector_results = self.vector_search(query, top_k * 2)
    
    # 키워드 검색 (BM25)
    keyword_results = self.keyword_search(query, top_k * 2)
    
    # 점수 정규화 및 결합
    combined = self._combine_scores(
        vector_results, 
        keyword_results, 
        alpha=alpha  # alpha: 벡터 검색 가중치
    )
    
    # 최종 정렬
    combined.sort(key=lambda x: x['score'], reverse=True)
    return combined[:top_k]

def keyword_search(self, query: str, top_k: int):
    """BM25 기반 키워드 검색"""
    
    # Qdrant의 텍스트 필드 검색
    results = self.client.scroll(
        collection_name=self.collection,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="text",
                    match={"text": query}
                )
            ]
        ),
        limit=top_k,
        with_payload=True
    )
    
    return results[0]  # 첫 번째 배치 반환
```

### 3. 고급 필터링

메타데이터 기반 정밀 필터링:

```python
def _build_filters(self, filters: dict):
    """복잡한 필터 조건 구성"""
    
    conditions = []
    
    # 날짜 범위 필터
    if 'date_range' in filters:
        conditions.append(
            FieldCondition(
                key="metadata.created_at",
                range=Range(
                    gte=filters['date_range']['start'],
                    lte=filters['date_range']['end']
                )
            )
        )
    
    # 문서 타입 필터
    if 'doc_types' in filters:
        conditions.append(
            FieldCondition(
                key="metadata.doc_type",
                match={"any": filters['doc_types']}
            )
        )
    
    # 태그 필터
    if 'tags' in filters:
        for tag in filters['tags']:
            conditions.append(
                FieldCondition(
                    key="metadata.tags",
                    match={"value": tag}
                )
            )
    
    return Filter(must=conditions) if conditions else None
```

### 4. 리랭킹 전략

Cross-encoder를 사용한 정밀 리랭킹:

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

class Reranker:
    def __init__(self):
        self.model_name = 'BAAI/bge-reranker-v2-m3'
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.model.eval()
    
    def rerank(self, query: str, documents: list, top_k: int = 10):
        """Cross-encoder 기반 리랭킹"""
        
        pairs = [[query, doc['text']] for doc in documents]
        
        with torch.no_grad():
            inputs = self.tokenizer(
                pairs,
                padding=True,
                truncation=True,
                return_tensors='pt',
                max_length=512
            )
            scores = self.model(**inputs).logits.squeeze(-1)
        
        # 점수에 따라 정렬
        sorted_indices = torch.argsort(scores, descending=True)
        
        # 상위 K개 반환
        reranked = [documents[i] for i in sorted_indices[:top_k]]
        for i, doc in enumerate(reranked):
            doc['rerank_score'] = float(scores[sorted_indices[i]])
        
        return reranked
```

### 5. 쿼리 확장

쿼리 이해도 향상을 위한 확장:

```python
def expand_query(self, query: str) -> list:
    """쿼리 확장 및 동의어 처리"""
    
    expanded_queries = [query]  # 원본 쿼리
    
    # 동의어 확장
    synonyms = self.get_synonyms(query)
    expanded_queries.extend(synonyms[:3])
    
    # 하이퍼님/하이포님 추가
    hypernyms = self.get_hypernyms(query)
    if hypernyms:
        expanded_queries.append(hypernyms[0])
    
    # 쿼리 리프레이징
    rephrased = self.rephrase_query(query)
    if rephrased != query:
        expanded_queries.append(rephrased)
    
    return expanded_queries

def multi_query_search(self, query: str, top_k: int = 10):
    """확장된 쿼리로 다중 검색"""
    
    expanded = self.expand_query(query)
    all_results = []
    
    for q in expanded:
        results = self.search(q, top_k=top_k//2)
        all_results.extend(results)
    
    # 중복 제거 및 점수 집계
    return self.aggregate_results(all_results, top_k)
```

## 검색 최적화

### 캐싱 전략

```python
from functools import lru_cache
import hashlib

class SearchCache:
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
    
    def get_cache_key(self, query: str, filters: dict = None):
        """쿼리와 필터로 캐시 키 생성"""
        key_str = f"{query}_{str(sorted(filters.items()) if filters else '')}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    @lru_cache(maxsize=128)
    def cached_search(self, query_hash: str):
        """캐시된 검색 결과 반환"""
        return self.cache.get(query_hash)
```

### 배치 검색

```python
async def batch_search(self, queries: list, top_k: int = 10):
    """여러 쿼리 동시 처리"""
    
    import asyncio
    
    tasks = [
        self.async_search(q, top_k) 
        for q in queries
    ]
    
    results = await asyncio.gather(*tasks)
    return dict(zip(queries, results))
```

## 검색 품질 평가

### 관련성 점수 계산

```python
def calculate_relevance_score(self, query: str, result: dict) -> float:
    """검색 결과의 관련성 점수 계산"""
    
    scores = {
        'vector_similarity': result.get('score', 0),
        'keyword_match': self.calculate_keyword_overlap(query, result['text']),
        'metadata_boost': self.calculate_metadata_boost(result['metadata']),
        'recency': self.calculate_recency_score(result['metadata'].get('created_at'))
    }
    
    # 가중 평균
    weights = {'vector_similarity': 0.4, 'keyword_match': 0.3, 
               'metadata_boost': 0.2, 'recency': 0.1}
    
    total_score = sum(scores[k] * weights[k] for k in scores)
    return total_score
```

## 사용 예제

### 기본 검색
```python
engine = VectorSearchEngine()
results = engine.search("50ml 용기 제품", top_k=5)
```

### 필터링된 검색
```python
results = engine.search(
    "플라스틱 용기",
    top_k=10,
    filters={
        'doc_types': ['product_spec', 'catalog'],
        'date_range': {
            'start': '2024-01-01',
            'end': '2024-12-31'
        }
    }
)
```

### 하이브리드 검색
```python
results = engine.hybrid_search(
    "내열성 용기",
    top_k=10,
    alpha=0.6  # 60% 벡터, 40% 키워드
)
```

## 성능 메트릭

검색 품질 모니터링:

```python
def evaluate_search_quality(self, test_queries: list, ground_truth: dict):
    """검색 품질 평가"""
    
    metrics = {
        'precision_at_k': [],
        'recall_at_k': [],
        'mrr': [],  # Mean Reciprocal Rank
        'ndcg': []  # Normalized Discounted Cumulative Gain
    }
    
    for query in test_queries:
        results = self.search(query, top_k=10)
        relevant = ground_truth.get(query, [])
        
        metrics['precision_at_k'].append(
            self.precision_at_k(results, relevant, k=5)
        )
        metrics['recall_at_k'].append(
            self.recall_at_k(results, relevant, k=10)
        )
        metrics['mrr'].append(
            self.mean_reciprocal_rank(results, relevant)
        )
        metrics['ndcg'].append(
            self.ndcg_at_k(results, relevant, k=10)
        )
    
    # 평균 계산
    return {k: np.mean(v) for k, v in metrics.items()}
```

## 추가 리소스

상세 가이드와 도구:
- `resources/search-tuning.md` - 검색 파라미터 튜닝 가이드
- `scripts/evaluate.py` - 검색 품질 평가 스크립트
- `scripts/index-optimizer.py` - 인덱스 최적화 도구
