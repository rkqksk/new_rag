```python
"""
Phase 3 하이브리드 AI 문서 로더 핵심 모듈

이 모듈은 다양한 로딩 전략을 지원하는 스마트 문서 로더를 제공합니다.
캐싱, 성능 메트릭, 에러 처리를 포함한 엔터프라이즈급 구현입니다.

Author: AI Development Team
Version: 3.0.0
"""

import asyncio
import hashlib
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ============================================================================
# 커스텀 예외 정의
# ============================================================================

class SmartDocLoaderException(Exception):
    """스마트 문서 로더 기본 예외 클래스."""
    pass


class DocumentNotFoundError(SmartDocLoaderException):
    """문서를 찾을 수 없을 때 발생하는 예외."""
    pass


class InvalidLoadStrategyError(SmartDocLoaderException):
    """잘못된 로드 전략이 지정되었을 때 발생하는 예외."""
    pass


class CacheExpiredError(SmartDocLoaderException):
    """캐시가 만료되었을 때 발생하는 예외."""
    pass


class DocumentProcessingError(SmartDocLoaderException):
    """문서 처리 중 오류가 발생했을 때 발생하는 예외."""
    pass


# ============================================================================
# Enum 정의
# ============================================================================

class LoadStrategy(Enum):
    """문서 로딩 전략 열거형.
    
    Attributes:
        FAST: 빠른 로딩, 최소 검증 (응답 시간 우선)
        BALANCED: 균형잡힌 로딩, 중간 검증 (기본값)
        ACCURATE: 정확한 로딩, 완전 검증 (정확성 우선)
    """
    FAST = "fast"
    BALANCED = "balanced"
    ACCURATE = "accurate"


class DocumentFormat(Enum):
    """문서 형식 열거형."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


# ============================================================================
# Dataclass 정의
# ============================================================================

@dataclass
class PerformanceMetrics:
    """성능 메트릭 데이터 클래스.
    
    Attributes:
        load_time_ms: 로딩 소요 시간 (밀리초)
        parse_time_ms: 파싱 소요 시간 (밀리초)
        validation_time_ms: 검증 소요 시간 (밀리초)
        cache_hit: 캐시 히트 여부
        total_time_ms: 전체 소요 시간 (밀리초)
    """
    load_time_ms: float = 0.0
    parse_time_ms: float = 0.0
    validation_time_ms: float = 0.0
    cache_hit: bool = False
    total_time_ms: float = 0.0


@dataclass
class LoadRequest:
    """문서 로드 요청 데이터 클래스.
    
    Attributes:
        document_path: 문서 파일 경로
        strategy: 로딩 전략 (기본값: BALANCED)
        timeout_seconds: 타임아웃 시간 (초)
        use_cache: 캐시 사용 여부 (기본값: True)
        cache_ttl_minutes: 캐시 유효 시간 (분)
        metadata: 추가 메타데이터
    """
    document_path: str
    strategy: LoadStrategy = LoadStrategy.BALANCED
    timeout_seconds: float = 30.0
    use_cache: bool = True
    cache_ttl_minutes: int = 60
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """요청 유효성 검증."""
        if not self.document_path:
            raise ValueError("document_path는 필수 입력값입니다.")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds는 양수여야 합니다.")
        if self.cache_ttl_minutes < 0:
            raise ValueError("cache_ttl_minutes는 음수가 될 수 없습니다.")


@dataclass
class LoadResult:
    """문서 로드 결과 데이터 클래스.
    
    Attributes:
        success: 로딩 성공 여부
        content: 로드된 문서 내용
        document_format: 문서 형식
        document_size_bytes: 문서 크기 (바이트)
        metadata: 문서 메타데이터
        metrics: 성능 메트릭
        error_message: 에러 메시지 (실패 시)
        timestamp: 로드 시간
    """
    success: bool
    content: Optional[str] = None
    document_format: Optional[DocumentFormat] = None
    document_size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """결과를 딕셔너리로 변환.
        
        Returns:
            결과 딕셔너리
        """
        return {
            "success": self.success,
            "content_length": len(self.content) if self.content else 0,
            "document_format": self.document_format.value if self.document_format else None,
            "document_size_bytes": self.document_size_bytes,
            "metrics": {
                "load_time_ms": self.metrics.load_time_ms,
                "parse_time_ms": self.metrics.parse_time_ms,
                "validation_time_ms": self.metrics.validation_time_ms,
                "cache_hit": self.metrics.cache_hit,
                "total_time_ms": self.metrics.total_time_ms,
            },
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
        }


# ============================================================================
# 캐시 항목 클래스
# ============================================================================

@dataclass
class CacheEntry:
    """캐시 항목 데이터 클래스.
    
    Attributes:
        content: 캐시된 콘텐츠
        created_at: 생성 시간
        ttl_minutes: 유효 시간 (분)
        access_count: 접근 횟수
    """
    content: str
    created_at: datetime
    ttl_minutes: int
    access_count: int = 0

    def is_expired(self) -> bool:
        """캐시 만료 여부 확인.
        
        Returns:
            만료되었으면 True, 아니면 False
        """
        expiry_time = self.created_at + timedelta(minutes=self.ttl_minutes)
        return datetime.now() > expiry_time

    def increment_access(self) -> None:
        """접근 횟수 증가."""
        self.access_count += 1


# ============================================================================
# 로딩 전략 추상 클래스
# ============================================================================

class DocumentLoadingStrategy(ABC):
    """문서 로딩 전략 추상 기본 클래스."""

    @abstractmethod
    async def load(self, file_path: Path) -> Tuple[str, float]:
        """문서를 로드합니다.
        
        Args:
            file_path: 파일 경로
            
        Returns:
            (콘텐츠, 소요시간_ms) 튜플
            
        Raises:
            DocumentProcessingError: 처리 중 오류 발생
        """
        pass

    @abstractmethod
    async def validate(self, content: str) -> Tuple[bool, Optional[str]]:
        """콘텐츠를 검증합니다.
        
        Args:
            content: 검증할 콘텐츠
            
        Returns:
            (유효성, 에러메시지) 튜플
        """
        pass


class FastLoadingStrategy(DocumentLoadingStrategy):
    """빠른 로딩 전략 구현."""

    async def load(self, file_path: Path) -> Tuple[str, float]:
        """최소 검증으로 빠르게 로드합니다."""
        start_time = time.time()
        try:
            content = file_path.read_text(encoding="utf-8")
            elapsed_ms = (time.time() - start_time) * 1000
            return content, elapsed_ms
        except Exception as e:
            raise DocumentProcessingError(f"빠른 로딩 실패: {str(e)}")

    async def validate(self, content: str) -> Tuple[bool, Optional[str]]:
        """기본 검증만 수행합니다."""
        if not content:
            return False, "콘텐츠가 비어있습니다."
        return True, None


class BalancedLoadingStrategy(DocumentLoadingStrategy):
    """균형잡힌 로딩 전략 구현."""

    async def load(self, file_path: Path) -> Tuple[str, float]:
        """중간 수준의 검증으로 로드합니다."""
        start_time = time.time()
        try:
            content = file_path.read_text(encoding="utf-8")
            # 기본 정규화
            content = content.strip()
            elapsed_ms = (time.time() - start_time) * 1000
            return content, elapsed_ms
        except Exception as e:
            raise DocumentProcessingError(f"균형 로딩 실패: {str(e)}")

    async def validate(self, content: str) -> Tuple[bool, Optional[str]]:
        """중간 수준의 검증을 수행합니다."""
        if not content:
            return False, "콘텐츠가 비어있습니다."
        if len(content) < 10:
            return False, "콘텐츠가 너무 짧습니다."
        return True, None


class AccurateLoadingStrategy(DocumentLoadingStrategy):
    """정확한 로딩 전략 구현."""

    async def load(self, file_path: Path) -> Tuple[str, float]:
        """완전한 검증으로 정확하게 로드합니다."""
        start_time = time.time()
        try:
            # 다중 인코딩 시도
            content = None
            for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
                try:
                    content = file_path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                raise DocumentProcessingError("지원되는 인코딩으로 파일을 읽을 수 없습니다.")

            # 상세 정규화
            content = self._normalize_content(content)
            elapsed_ms = (time.time() - start_time) * 1000
            return content, elapsed_ms
        except Exception as e:
            raise DocumentProcessingError(f"정확한 로딩 실패: {str(e)}")

    async def validate(self, content: str) -> Tuple[bool, Optional[str]]:
        """완전한 검증을 수행합니다."""
        if not content:
            return False, "콘텐츠가 비어있습니다."
        if len(content) < 10:
            return False, "콘텐츠가 너무 짧습니다."
        if len(content) > 100_000_000:  # 100MB
            return False, "콘텐츠가 너무 큽니다."
        
        # 특수 문자 검증
        invalid_chars = ['\x00', '\x01', '\x02']
        for char in invalid_chars:
            if char in content:
                return False, f"유효하지 않은 문자 포함: {repr(char)}"
        
        return True, None

    @staticmethod
    def _normalize_content(content: str) -> str:
        """콘텐츠를 정규화합니다.
        
        Args:
            content: 정규화할 콘텐츠
            
        Returns:
            정규화된 콘텐츠
        """
        # 줄바꿈 정규화
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        # 연속된 공백 정규화
        lines = [line.rstrip() for line in content.split('\n')]
        return '\n'.join(lines).strip()


# ============================================================================
# 메인 스마트 문서 로더 클래스
# ============================================================================

class SmartDocumentLoader:
    """하이브리드 AI 문서 로더 메인 클래스.
    
    다양한 로딩 전략을 지원하며, 캐싱, 성능 메트릭, 에러 처리를 제공합니다.
    
    Attributes:
        _cache: 인메모리 캐시 저장소
        _strategies: 로딩 전략 매핑
        _logger: 로거 인스턴스
        _stats: 통계 정보
    """

    def __init__(self, max_cache_size: int = 1000) -> None:
        """스마트 문서 로더를 초기화합니다.
        
        Args:
            max_cache_size: 최대 캐시 크기 (기본값: 1000)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._max_cache_size = max_cache_size
        self._cache_keys_order: List[str] = []
        
        # 로딩 전략 초기화
        self._strategies: Dict[LoadStrategy, DocumentLoadingStrategy] = {
            LoadStrategy.FAST: FastLoadingStrategy(),
            LoadStrategy.BALANCED: BalancedLoadingStrategy(),
            LoadStrategy.ACCURATE: AccurateLoadingStrategy(),
        }
        
        # 로거 설정
        self._logger = self._setup_logger()
        
        # 통계 정보
        self._stats = {
            "total_loads