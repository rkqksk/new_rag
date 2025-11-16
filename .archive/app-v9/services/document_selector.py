# app/services/document_selector.py

```python
"""
Phase 3 문서 선택 엔진
키워드 기반 및 의도 기반 문서 선택, 순위 매김
"""

import asyncio
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import aioredis
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """문서 타입"""
    GUIDE = "guide"
    FAQ = "faq"
    API_DOC = "api_doc"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"
    EXAMPLE = "example"


class RelevanceLevel(Enum):
    """관련성 수준"""
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    IRRELEVANT = 0


@dataclass
class DocumentMetadata:
    """문서 메타데이터"""
    doc_id: str
    title: str
    content: str
    doc_type: DocumentType
    keywords: List[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    relevance_score: float = 0.0
    source_url: Optional[str] = None
    section: Optional[str] = None
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        data['doc_type'] = self.doc_type.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data


@dataclass
class SelectionResult:
    """선택 결과"""
    selected_docs: List[DocumentMetadata]
    total_candidates: int
    selection_method: str
    relevance_scores: Dict[str, float]
    processing_time_ms: float
    cache_hit: bool = False
    reasoning: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'selected_docs': [doc.to_dict() for doc in self.selected_docs],
            'total_candidates': self.total_candidates,
            'selection_method': self.selection_method,
            'relevance_scores': self.relevance_scores,
            'processing_time_ms': self.processing_time_ms,
            'cache_hit': self.cache_hit,
            'reasoning': self.reasoning
        }


class KeywordMatcher(ABC):
    """키워드 매칭 전략"""
    
    @abstractmethod
    def match(self, query_keywords: List[str], 
              doc_keywords: List[str]) -> float:
        """매칭 점수 계산"""
        pass


class ExactKeywordMatcher(KeywordMatcher):
    """정확한 키워드 매칭"""
    
    def match(self, query_keywords: List[str], 
              doc_keywords: List[str]) -> float:
        """정확한 매칭 점수"""
        if not query_keywords or not doc_keywords:
            return 0.0
        
        matches = len(set(query_keywords) & set(doc_keywords))
        return matches / len(query_keywords)


class FuzzyKeywordMatcher(KeywordMatcher):
    """퍼지 키워드 매칭"""
    
    def match(self, query_keywords: List[str], 
              doc_keywords: List[str]) -> float:
        """퍼지 매칭 점수"""
        if not query_keywords or not doc_keywords:
            return 0.0
        
        score = 0.0
        for q_kw in query_keywords:
            for d_kw in doc_keywords:
                # 부분 문자열 매칭
                if q_kw.lower() in d_kw.lower():
                    score += 0.5
                elif d_kw.lower() in q_kw.lower():
                    score += 0.3
        
        return min(score / len(query_keywords), 1.0)


class DocumentSelector:
    """문서 선택 엔진"""
    
    def __init__(self, 
                 redis_url: str = "redis://localhost",
                 cache_ttl: int = 3600,
                 max_candidates: int = 50,
                 top_k: int = 5):
        """
        초기화
        
        Args:
            redis_url: Redis URL
            cache_ttl: 캐시 TTL (초)
            max_candidates: 최대 후보 수
            top_k: 선택할 상위 문서 수
        """
        self.redis_url = redis_url
        self.cache_ttl = cache_ttl
        self.max_candidates = max_candidates
        self.top_k = top_k
        
        self.redis_client: Optional[aioredis.Redis] = None
        self.anthropic_client = Anthropic()
        
        self.exact_matcher = ExactKeywordMatcher()
        self.fuzzy_matcher = FuzzyKeywordMatcher()
        
        # 문서 저장소 (실제로는 DB에서 로드)
        self.document_store: Dict[str, DocumentMetadata] = {}
        
        # 키워드-문서 인덱스
        self.keyword_index: Dict[str, Set[str]] = {}
    
    async def initialize(self):
        """비동기 초기화"""
        try:
            self.redis_client = await aioredis.create_redis_pool(
                self.redis_url
            )
            logger.info("Redis 연결 성공")
        except Exception as e:
            logger.warning(f"Redis 연결 실패: {e}")
            self.redis_client = None
    
    async def close(self):
        """리소스 정리"""
        if self.redis_client:
            self.redis_client.close()
            await self.redis_client.wait_closed()
    
    def _build_keyword_index(self):
        """키워드 인덱스 구축"""
        self.keyword_index.clear()
        
        for doc_id, doc in self.document_store.items():
            for keyword in doc.keywords:
                if keyword not in self.keyword_index:
                    self.keyword_index[keyword] = set()
                self.keyword_index[keyword].add(doc_id)
    
    def _get_cache_key(self, query: str, method: str) -> str:
        """캐시 키 생성"""
        key_data = f"{query}:{method}"
        return f"doc_select:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[SelectionResult]:
        """캐시에서 조회"""
        if not self.redis_client:
            return None
        
        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                logger.debug(f"캐시 히트: {cache_key}")
                return self._deserialize_result(data)
        except Exception as e:
            logger.warning(f"캐시 조회 실패: {e}")
        
        return None
    
    async def _set_cache(self, cache_key: str, result: SelectionResult):
        """캐시에 저장"""
        if not self.redis_client:
            return
        
        try:
            data = result.to_dict()
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.warning(f"캐시 저장 실패: {e}")
    
    def _deserialize_result(self, data: Dict[str, Any]) -> SelectionResult:
        """결과 역직렬화"""
        docs = [
            DocumentMetadata(
                doc_id=doc['doc_id'],
                title=doc['title'],
                content=doc['content'],
                doc_type=DocumentType(doc['doc_type']),
                keywords=doc['keywords'],
                tags=doc['tags'],
                created_at=datetime.fromisoformat(doc['created_at']),
                updated_at=datetime.fromisoformat(doc['updated_at']),
                relevance_score=doc.get('relevance_score', 0.0),
                source_url=doc.get('source_url'),
                section=doc.get('section'),
                version=doc.get('version', '1.0')
            )
            for doc in data['selected_docs']
        ]
        
        return SelectionResult(
            selected_docs=docs,
            total_candidates=data['total_candidates'],
            selection_method=data['selection_method'],
            relevance_scores=data['relevance_scores'],
            processing_time_ms=data['processing_time_ms'],
            cache_hit=data.get('cache_hit', False),
            reasoning=data.get('reasoning')
        )
    
    def select_by_keywords(self, 
                          keywords: List[str],
                          doc_type: Optional[DocumentType] = None) -> List[str]:
        """
        키워드 기반 선택 (Haiku 빠름)
        
        Args:
            keywords: 검색 키워드
            doc_type: 문서 타입 필터
        
        Returns:
            선택된 문서 ID 리스트
        """
        if not keywords:
            return []
        
        # 키워드별 문서 수집
        candidate_docs: Dict[str, float] = {}
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # 정확한 매칭
            if keyword_lower in self.keyword_index:
                for doc_id in self.keyword_index[keyword_lower]:
                    candidate_docs[doc_id] = candidate_docs.get(doc_id, 0) + 1.0
            
            # 부분 매칭
            for idx_keyword, doc_ids in self.keyword_index.items():
                if keyword_lower in idx_keyword or idx_keyword in keyword_lower:
                    for doc_id in doc_ids:
                        candidate_docs[doc_id] = candidate_docs.get(doc_id, 0) + 0.5
        
        # 문서 타입 필터링
        if doc_type:
            candidate_docs = {
                doc_id: score
                for doc_id, score in candidate_docs.items()
                if self.document_store[doc_id].doc_type == doc_type
            }
        
        # 점수순 정렬
        sorted_docs = sorted(
            candidate_docs.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [doc_id for doc_id, _ in sorted_docs[:self.max_candidates]]
    
    def _calculate_relevance_score(self,
                                   doc: DocumentMetadata,
                                   query_keywords: List[str],
                                   query_tags: List[str]) -> float:
        """관련성 점수 계산"""
        score = 0.0
        
        # 키워드 매칭 (60%)
        exact_match = self.exact_matcher.match(query_keywords, doc.keywords)
        fuzzy_match = self.fuzzy_matcher.match(query_keywords, doc.keywords)
        keyword_score = (exact_match * 0.7 + fuzzy_match * 0.3) * 0.6
        score += keyword_score
        
        # 태그 매칭 (20%)
        tag_matches = len(set(query_tags) & set(doc.tags))
        tag_score = (tag_matches / len(query_tags)) * 0.2 if query_tags else 0
        score += tag_score
        
        # 최신성 (10%)
        days_old = (datetime.now() - doc.updated_at).days
        recency_score = max(0, 1 - (days_old / 365)) * 0.1
        score += recency_score
        
        # 문서 타입 가중치 (10%)
        type_weights = {
            DocumentType.GUIDE: 0.3,
            DocumentType.TUTORIAL: 0.25,
            DocumentType.API_DOC: 0.2,
            DocumentType.EXAMPLE: 0.15,
            DocumentType.FAQ: 0.1,
            DocumentType.REFERENCE: 0.05
        }
        type_score = type_weights.get(doc.doc_type, 0) * 0.1
        score += type_score
        
        return min(score, 1.0)
    
    def _generate_candidates(self,
                            query_keywords: List[str],
                            query_tags: List[str],
                            doc_type: Optional[DocumentType] = None) -> List[Tuple[str, float]]:
        """
        후보 생성 (다중 전략)
        
        Args:
            query_keywords: 쿼리 키워드
            query_tags: 쿼리 태그
            doc_type: 문서 타입 필터
        
        Returns:
            (문서ID, 점수) 튜플 리스트
        """
        candidates: Dict[str, float] = {}
        
        # 전략 1: 키워드 기반
        keyword_docs = self.select_by_keywords(query_keywords, doc_type)
        for doc_id in keyword_docs:
            candidates[doc_id] = 0.4
        
        # 전략 2: 태그 기반
        for doc_id, doc in self.document_store.items():
            if doc_type and doc.doc_type != doc_type:
                continue
            
            tag_matches = len(set(query_tags) & set(doc.tags))
            if tag_matches > 0:
                candidates[doc_id] = candidates.get(doc_id, 0) + 0.3
        
        # 전략 3: 콘텐츠 유사성 (간단한 버전)
        query_text = " ".join(query_keywords + query_tags).lower()
        for doc_id, doc in self.document_store.items():
            if doc_type and doc.doc_type != doc_type:
                continue
            
            doc_text = (doc.title + " " + doc.content).lower()
            word_overlap = len(set(query_text.split()) & set(doc_text.split()))
            if word_overlap > 0:
                candidates[doc_id] = candidates.get(doc_id, 0) + 0.3
        
        # 관련성 점수 계산
        scored_candidates = []
        for doc_id, base_score in candidates.items():
            doc = self.document_store[doc_id]
            relevance = self._calculate_relevance_score(
                doc, query_keywords, query_tags
            )
            final_score = base_score * 0.3 + relevance * 0.7
            scored_candidates.append((doc_id, final_score))
        
        # 점수순 정렬
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        return scored_candidates[:self.max_candidates]
    
    def _deduplicate_documents(self,
                              doc_ids: List[str]) -> List[str]:
        """중복 제거"""
        seen_titles: Set[str] = set()
        deduplicated = []
        
        for doc_id in doc_ids:
            doc = self.document_store[doc_id]
            title_lower = doc.title.lower()
            
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                deduplicated.append(doc_id)
        
        return deduplicated
    
    def _rank_candidates_sonnet(self,
                               candidates: List[Tuple[str, float]],
                               query: str,
                               intent: str) -> List[str]:
        """
        Sonnet으로 순위 매김 (고급)
        
        Args:
            candidates: 후보 (문서ID, 점수)
            query: 원본 쿼리
            intent: 사용자 의도
        
        Returns:
            순위 매겨진 문서 ID 리스트
        """
        if not candidates:
            return []
        
        # 상위 후보만 Sonnet으로 평가
        top_candidates = candidates[:min(10, len(candidates))]
        
        # 문서 정보 준비
        doc_info = []
        for doc_id, score in top_candidates:
            doc = self.document_store[doc_id]
            doc_info.append({
                'id': doc_id,
                'title':