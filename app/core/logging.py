"""
RAG Enterprise 구조화된 로깅 시스템

이 모듈은 structlog 기반의 엔터프라이즈급 로깅 시스템을 제공합니다.
민감 정보 자동 마스킹, 요청 컨텍스트 추적, 성능 메트릭 로깅을 지원합니다.

Example:
    >>> from app.core.logging import configure_logging, get_logger, RequestContext
    >>> configure_logging(log_level="INFO")
    >>> logger = get_logger(__name__)
    >>> with RequestContext(request_id="req-123", user_id="user-456"):
    ...     logger.info("user_login", username="john_doe")
"""

import asyncio
import contextvars
import functools
import json
import logging
import logging.handlers
import os
import re
import sys
import time
import traceback
import uuid
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import (
    Any, Callable, Dict, List, Optional, Pattern, Set, Tuple, TypeVar, Union
)

# Optional imports - graceful degradation if not available
try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False

try:
    from pythonjson_logger import jsonlogger
    HAS_PYTHONJSON = True
except ImportError:
    HAS_PYTHONJSON = False

# 타입 변수
T = TypeVar('T')
LoggerType = logging.Logger if not HAS_STRUCTLOG else structlog.PrintLogger

# 컨텍스트 변수 정의
_request_context: contextvars.ContextVar[Optional[Dict[str, Any]]] = (
    contextvars.ContextVar('request_context', default=None)
)
_performance_context: contextvars.ContextVar[Optional[Dict[str, Any]]] = (
    contextvars.ContextVar('performance_context', default=None)
)


@dataclass
class RequestContextData:
    """요청 컨텍스트 데이터 클래스.
    
    Attributes:
        request_id: 고유 요청 식별자
        user_id: 사용자 식별자
        session_id: 세션 식별자
        correlation_id: 상관 식별자 (분산 추적용)
        tenant_id: 테넌트 식별자 (멀티테넌시)
        metadata: 추가 메타데이터
    """
    request_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    tenant_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """데이터클래스를 딕셔너리로 변환.
        
        Returns:
            Dict[str, Any]: 변환된 딕셔너리
        """
        return asdict(self)


@dataclass
class PerformanceMetricsData:
    """성능 메트릭 데이터 클래스.
    
    Attributes:
        operation_name: 작업 이름
        start_time: 시작 시간 (Unix timestamp)
        end_time: 종료 시간 (Unix timestamp)
        duration_ms: 소요 시간 (밀리초)
        tokens_used: 사용된 토큰 수
        tokens_input: 입력 토큰 수
        tokens_output: 출력 토큰 수
        cache_hit: 캐시 히트 여부
        error: 에러 발생 여부
        metadata: 추가 메타데이터
    """
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    tokens_used: Optional[int] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    cache_hit: bool = False
    error: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """데이터클래스를 딕셔너리로 변환.
        
        Returns:
            Dict[str, Any]: 변환된 딕셔너리
        """
        return asdict(self)


class SensitiveDataFilter:
    """민감 정보 자동 마스킹 필터.
    
    API 키, 토큰, 비밀번호 등의 민감한 정보를 자동으로 감지하고 마스킹합니다.
    
    Attributes:
        patterns: 민감 정보 감지 패턴 딕셔너리
        mask_char: 마스킹 문자
        min_visible_chars: 최소 표시 문자 수
    """

    # 민감 정보 패턴 정의
    SENSITIVE_PATTERNS: Dict[str, Pattern[str]] = {
        'api_key': re.compile(
            r'(?:api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9\-_]{20,})["\']?',
            re.IGNORECASE
        ),
        'token': re.compile(
            r'(?:token|auth|bearer)\s*[:=]\s*["\']?([a-zA-Z0-9\-_.]{20,})["\']?',
            re.IGNORECASE
        ),
        'password': re.compile(
            r'(?:password|passwd|pwd)\s*[:=]\s*["\']?([^\s"\']{6,})["\']?',
            re.IGNORECASE
        ),
        'secret': re.compile(
            r'(?:secret|private[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9\-_]{20,})["\']?',
            re.IGNORECASE
        ),
        'aws_key': re.compile(r'AKIA[0-9A-Z]{16}'),
        'jwt': re.compile(r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'),
        'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
        'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    }

    # 마스킹할 키워드
    SENSITIVE_KEYS: Set[str] = {
        'password', 'passwd', 'pwd', 'secret', 'token', 'auth',
        'api_key', 'apikey', 'api-key', 'access_token', 'refresh_token',
        'private_key', 'private-key', 'bearer', 'authorization',
        'x-api-key', 'x-auth-token', 'credit_card', 'ssn',
        'aws_access_key_id', 'aws_secret_access_key',
    }

    def __init__(
        self,
        mask_char: str = '*',
        min_visible_chars: int = 3,
        patterns: Optional[Dict[str, Pattern[str]]] = None,
    ) -> None:
        """초기화.
        
        Args:
            mask_char: 마스킹에 사용할 문자 (기본값: '*')
            min_visible_chars: 최소 표시 문자 수 (기본값: 3)
            patterns: 커스텀 패턴 딕셔너리 (기본값: None)
        """
        self.mask_char = mask_char
        self.min_visible_chars = min_visible_chars
        self.patterns = patterns or self.SENSITIVE_PATTERNS

    def mask_value(self, value: str) -> str:
        """값을 마스킹.
        
        Args:
            value: 마스킹할 값
            
        Returns:
            str: 마스킹된 값
        """
        if not isinstance(value, str) or len(value) < 4:
            return value

        # 패턴 기반 마스킹
        for pattern in self.patterns.values():
            if pattern.search(value):
                return self._apply_mask(value)

        return value

    def _apply_mask(self, value: str) -> str:
        """마스킹 적용.
        
        Args:
            value: 마스킹할 값
            
        Returns:
            str: 마스킹된 값
        """
        if len(value) <= self.min_visible_chars:
            return self.mask_char * len(value)

        visible = self.min_visible_chars
        masked_count = len(value) - visible
        return value[:visible] + self.mask_char * masked_count

    def filter_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """딕셔너리의 민감 정보 필터링.
        
        Args:
            data: 필터링할 딕셔너리
            
        Returns:
            Dict[str, Any]: 필터링된 딕셔너리
        """
        if not isinstance(data, dict):
            return data

        filtered = {}
        for key, value in data.items():
            if self._is_sensitive_key(key):
                filtered[key] = self._mask_value_recursive(value)
            elif isinstance(value, dict):
                filtered[key] = self.filter_dict(value)
            elif isinstance(value, (list, tuple)):
                filtered[key] = [
                    self.filter_dict(item) if isinstance(item, dict)
                    else self._mask_value_recursive(item)
                    for item in value
                ]
            else:
                filtered[key] = value

        return filtered

    def _is_sensitive_key(self, key: str) -> bool:
        """키가 민감한 정보인지 확인.
        
        Args:
            key: 확인할 키
            
        Returns:
            bool: 민감한 정보 여부
        """
        return key.lower() in self.SENSITIVE_KEYS

    def _mask_value_recursive(self, value: Any) -> Any:
        """재귀적으로 값 마스킹.
        
        Args:
            value: 마스킹할 값
            
        Returns:
            Any: 마스킹된 값
        """
        if isinstance(value, str):
            return self.mask_value(value)
        elif isinstance(value, dict):
            return self.filter_dict(value)
        elif isinstance(value, (list, tuple)):
            return [self._mask_value_recursive(item) for item in value]
        return value


class RequestContext:
    """요청 컨텍스트 관리자.
    
    요청 생명주기 동안 요청 관련 정보를 추적합니다.
    
    Example:
        >>> with RequestContext(request_id="req-123", user_id="user-456"):
        ...     logger.info("processing_request")
    """

    def __init__(
        self,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """초기화.
        
        Args:
            request_id: 요청 ID (기본값: 자동 생성)
            user_id: 사용자 ID
            session_id: 세션 ID
            correlation_id: 상관 ID
            tenant_id: 테넌트 ID
            metadata: 추가 메타데이터
        """
        self.request_id = request_id or str(uuid.uuid4())
        self.user_id = user_id
        self.session_id = session_id
        self.correlation_id = correlation_id or self.request_id
        self.tenant_id = tenant_id
        self.metadata = metadata or {}
        self._token: Optional[contextvars.Token[Dict[str, Any]]] = None

    def __enter__(self) -> 'RequestContext':
        """컨텍스트 진입.
        
        Returns:
            RequestContext: 자신
        """
        context_data = RequestContextData(
            request_id=self.request_id,
            user_id=self.user_id,
            session_id=self.session_id,
            correlation_id=self.correlation_id,
            tenant_id=self.tenant_id,
            metadata=self.metadata,
        ).to_dict()

        self._token = _request_context.set(context_data)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """컨텍스트 종료.
        
        Args:
            exc_type: 예외 타입
            exc_val: 예외 값
            exc_tb: 예외 트레이스백
        """
        if self._token is not None:
            _request_context.reset(self._token)

    @asynccontextmanager
    async def async_context(self) -> Any:
        """비동기 컨텍스트 매니저.
        
        Yields:
            RequestContext: 자신
        """
        self.__enter__()
        try:
            yield self
        finally:
            self.__exit__(None, None, None)


class PerformanceMetrics:
    """성능 메트릭 추적 컨텍스트 매니저.
    
    작업의 성능 메트릭을 자동으로 추적하고 로깅합니다.
    
    Example:
        >>> with PerformanceMetrics("llm_inference") as metrics:
        ...     result = model.generate(prompt)
        ...     metrics.record_tokens(input=100, output=50)
    """

    def __init__(
        self,
        operation_name: str,
        logger: Optional[LoggerType] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """초기화.
        
        Args:
            operation_name: 작업 이름
            logger: 로거 인스턴스
            metadata: 추가 메타데이터
        """
        self.operation_name = operation_name
        self.logger = logger or get_logger(__name__)
        self.metadata = metadata or {}
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.tokens_input: Optional[int] = None
        self.tokens_output: Optional[int] = None
        self.cache_hit = False
        self.error = False
        self._token: Optional[contextvars.Token[Dict[str, Any]]] = None

    def __enter__(self) -> 'PerformanceMetrics':
        """컨텍스트 진입.
        
        Returns:
            PerformanceMetrics: 자신
        """
        metrics_data = PerformanceMetricsData(
            operation_name=self.operation_name,
            start_time=self.start_time,
        ).to_dict()

        self._token = _performance_context.set(metrics_data)
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Any,
    ) -> None:
        """컨텍스트 종료.
        
        Args:
            exc_type: 예외 타입
            exc_val: 예외 값
            exc_tb: 예외 트레이스백
        """
        self.end_time = time.time()
        self.error = exc_type is not None

        duration_ms = (self.end_time - self.start_time) * 1000

        metrics_data = {
            'operation_name': self.operation_name,
            'duration_ms': round(duration_ms, 2),
            'tokens_input': self.tokens_input,
            'tokens_output': self.tokens_output,
            'tokens_used': (
                (self.tokens_input or 0) + (self.tokens_output or 0)
                if self.tokens_input or self.tokens_output else None
            ),
            'cache_hit': self.cache_hit,
            'error': self.error,
            **self.metadata,
        }

        if exc_type is not None:
            self.logger.error(
                'performance_metrics',
                **metrics_data,
                exception=str(exc_val),
                traceback=traceback.format_exc(),
            )
        else:
            self.logger.info('performance_metrics', **metrics_data)

        if self._token is not None:
            _performance_context.reset(self._token)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


def configure_logging(log_level: str = "INFO") -> None:
    """Configure basic logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
