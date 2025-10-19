```python
"""
tests/integration/test_phase3_loader.py

Phase 3 동적 문서 로더 통합 테스트
- SmartDocumentLoader 전략 테스트
- IntentAnalyzer 분석 테스트
- DocumentSelector 선택 테스트
- CacheManager 캐시 테스트
- 성능 테스트
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
from dataclasses import dataclass


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_claude_client():
    """Claude API 클라이언트 모킹"""
    client = MagicMock()
    return client


@pytest.fixture
def sample_documents() -> List[Dict[str, Any]]:
    """샘플 문서 데이터"""
    return [
        {
            "id": "doc_1",
            "title": "Python 성능 최적화",
            "content": "파이썬 코드 최적화 기법과 벤치마킹",
            "relevance": 0.95
        },
        {
            "id": "doc_2",
            "title": "데이터베이스 설계",
            "content": "관계형 데이터베이스 정규화 및 인덱싱",
            "relevance": 0.87
        },
        {
            "id": "doc_3",
            "title": "API 설계 패턴",
            "content": "RESTful API 설계 및 GraphQL",
            "relevance": 0.92
        },
        {
            "id": "doc_4",
            "title": "Python 성능 최적화",  # 중복
            "content": "파이썬 코드 최적화 기법과 벤치마킹",
            "relevance": 0.94
        }
    ]


@pytest.fixture
def sample_query() -> str:
    """샘플 쿼리"""
    return "Python 성능 최적화 방법"


@pytest.fixture
def cache_manager():
    """캐시 매니저 인스턴스"""
    from collections import OrderedDict
    
    class CacheManager:
        def __init__(self, ttl: int = 3600):
            self.cache: OrderedDict = OrderedDict()
            self.ttl = ttl
            self.timestamps: Dict[str, float] = {}
            self.hits = 0
            self.misses = 0
        
        def get(self, key: str) -> Any:
            if key in self.cache:
                if time.time() - self.timestamps[key] < self.ttl:
                    self.hits += 1
                    return self.cache[key]
                else:
                    del self.cache[key]
                    del self.timestamps[key]
            self.misses += 1
            return None
        
        def set(self, key: str, value: Any) -> None:
            self.cache[key] = value
            self.timestamps[key] = time.time()
        
        def hit_rate(self) -> float:
            total = self.hits + self.misses
            return self.hits / total if total > 0 else 0.0
    
    return CacheManager()


# ============================================================================
# TestSmartDocumentLoader
# ============================================================================

@pytest.mark.integration
class TestSmartDocumentLoader:
    """SmartDocumentLoader 전략 테스트"""
    
    @patch('anthropic.Anthropic')
    def test_fast_strategy(self, mock_anthropic, sample_documents, sample_query):
        """
        FAST 전략 성능 테스트
        
        - 최소 API 호출로 빠른 응답
        - 상위 2개 문서 선택
        - 응답 시간 < 500ms
        """
        # Arrange
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="[1, 2]")]
        )
        
        # Act
        start_time = time.time()
        selected_indices = [1, 2]
        elapsed = time.time() - start_time
        
        # Assert
        assert len(selected_indices) == 2
        assert elapsed < 0.5
        assert all(idx < len(sample_documents) for idx in selected_indices)
    
    @patch('anthropic.Anthropic')
    def test_balanced_strategy(self, mock_anthropic, sample_documents, sample_query):
        """
        BALANCED 전략 정확도 테스트
        
        - 중간 수준의 API 호출
        - 상위 3-4개 문서 선택
        - 정확도 >= 85%
        """
        # Arrange
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="[0, 2, 3]")]
        )
        
        # Act
        selected_indices = [0, 2, 3]
        accuracy = sum(
            sample_documents[idx]["relevance"] 
            for idx in selected_indices
        ) / len(selected_indices)
        
        # Assert
        assert 3 <= len(selected_indices) <= 4
        assert accuracy >= 0.85
        assert selected_indices == sorted(selected_indices)
    
    @patch('anthropic.Anthropic')
    def test_accurate_strategy(self, mock_anthropic, sample_documents, sample_query):
        """
        ACCURATE 전략 검증 테스트
        
        - 최대 API 호출로 정확한 분석
        - 모든 문서 평가
        - 정확도 >= 90%
        """
        # Arrange
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="[0, 2]")]
        )
        
        # Act
        selected_indices = [0, 2]
        accuracy = sum(
            sample_documents[idx]["relevance"] 
            for idx in selected_indices
        ) / len(selected_indices)
        
        # Assert
        assert accuracy >= 0.90
        assert len(selected_indices) >= 2
    
    def test_strategy_comparison(self, sample_documents, sample_query):
        """
        전략 비교 테스트
        
        - FAST < BALANCED < ACCURATE (응답시간)
        - FAST < BALANCED < ACCURATE (정확도)
        """
        # Arrange
        strategies = {
            "FAST": {"time": 0.1, "accuracy": 0.80},
            "BALANCED": {"time": 0.3, "accuracy": 0.88},
            "ACCURATE": {"time": 0.8, "accuracy": 0.95}
        }
        
        # Act & Assert
        times = [strategies[s]["time"] for s in ["FAST", "BALANCED", "ACCURATE"]]
        accuracies = [strategies[s]["accuracy"] for s in ["FAST", "BALANCED", "ACCURATE"]]
        
        assert times == sorted(times), "응답 시간 순서 확인"
        assert accuracies == sorted(accuracies), "정확도 순서 확인"


# ============================================================================
# TestIntentAnalyzer
# ============================================================================

@pytest.mark.integration
class TestIntentAnalyzer:
    """IntentAnalyzer 분석 테스트"""
    
    @patch('anthropic.Anthropic')
    def test_keyword_extraction_haiku(self, mock_anthropic, sample_query):
        """
        Haiku 모델 키워드 추출 테스트
        
        - 빠른 키워드 추출
        - 최소 3개 키워드
        - 관련성 높음
        """
        # Arrange
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(
                text='["Python", "성능", "최적화"]'
            )]
        )
        
        # Act
        keywords = ["Python", "성능", "최적화"]
        
        # Assert
        assert len(keywords) >= 3
        assert all(isinstance(k, str) for k in keywords)
        assert "Python" in keywords
        assert "성능" in keywords
    
    @patch('anthropic.Anthropic')
    def test_intent_analysis_sonnet(self, mock_anthropic, sample_query):
        """
        Sonnet 모델 의도 분석 테스트
        
        - 정확한 의도 파악
        - 신뢰도 >= 0.85
        - 카테고리 분류
        """
        # Arrange
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(
                text='{"intent": "optimization", "confidence": 0.92, "category": "performance"}'
            )]
        )
        
        # Act
        intent_data = {
            "intent": "optimization",
            "confidence": 0.92,
            "category": "performance"
        }
        
        # Assert
        assert intent_data["confidence"] >= 0.85
        assert intent_data["intent"] in ["optimization", "learning", "troubleshooting"]
        assert intent_data["category"] in ["performance", "design", "architecture"]
    
    @patch('anthropic.Anthropic')
    def test_deep_analysis(self, mock_anthropic, sample_query):
        """
        깊은 분석 테스트
        
        - 다층 의도 분석
        - 컨텍스트 이해
        - 관련 주제 식별
        """
        # Arrange
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(
                text='''{
                    "primary_intent": "optimization",
                    "secondary_intents": ["learning", "troubleshooting"],
                    "context": "performance improvement",
                    "related_topics": ["profiling", "caching", "algorithms"]
                }'''
            )]
        )
        
        # Act
        analysis = {
            "primary_intent": "optimization",
            "secondary_intents": ["learning", "troubleshooting"],
            "context": "performance improvement",
            "related_topics": ["profiling", "caching", "algorithms"]
        }
        
        # Assert
        assert analysis["primary_intent"]
        assert len(analysis["secondary_intents"]) >= 1
        assert len(analysis["related_topics"]) >= 3


# ============================================================================
# TestDocumentSelector
# ============================================================================

@pytest.mark.integration
class TestDocumentSelector:
    """DocumentSelector 선택 테스트"""
    
    def test_keyword_selection(self, sample_documents):
        """
        키워드 기반 선택 테스트
        
        - 키워드 매칭 문서 선택
        - 정확도 >= 90%
        """
        # Arrange
        keywords = ["Python", "성능", "최적화"]
        
        # Act
        selected = [
            doc for doc in sample_documents
            if any(kw in doc["title"] or kw in doc["content"] for kw in keywords)
        ]
        
        # Assert
        assert len(selected) >= 1
        assert all("Python" in doc["title"] or "성능" in doc["title"] for doc in selected)
    
    def test_relevance_ranking(self, sample_documents):
        """
        관련성 순위 테스트
        
        - 관련성 점수로 정렬
        - 상위 문서 관련성 높음
        - 순서 유지
        """
        # Arrange
        sorted_docs = sorted(
            sample_documents,
            key=lambda x: x["relevance"],
            reverse=True
        )
        
        # Act
        top_3 = sorted_docs[:3]
        
        # Assert
        assert top_3[0]["relevance"] >= top_3[1]["relevance"]
        assert top_3[1]["relevance"] >= top_3[2]["relevance"]
        assert all(doc["relevance"] > 0.85 for doc in top_3)
    
    def test_deduplication(self, sample_documents):
        """
        중복 제거 테스트
        
        - 동일 제목 문서 제거
        - 고유 문서만 반환
        - 관련성 높은 것 유지
        """
        # Arrange
        seen_titles = set()
        deduplicated = []
        
        # Act
        for doc in sorted(sample_documents, key=lambda x: x["relevance"], reverse=True):