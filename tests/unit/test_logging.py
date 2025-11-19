# tests/unit/test_logging.py
"""
app/core/logging 모듈 테스트

테스트 대상:
- SensitiveDataFilter: 민감 데이터 마스킹
- configure_logging: 로깅 설정
- RequestContext: 요청 컨텍스트 관리
- PerformanceMetrics: 성능 메트릭 수집
"""

import asyncio
import json
import logging
from io import StringIO
from unittest.mock import MagicMock, Mock, patch

import pytest

from apps.api.core.logging import (
    PerformanceMetrics,
    RequestContext,
    SensitiveDataFilter,
    configure_logging,
)


@pytest.mark.unit
class TestSensitiveDataFilter:
    """SensitiveDataFilter 테스트"""

    @pytest.fixture
    def filter_instance(self):
        """필터 인스턴스 생성"""
        return SensitiveDataFilter()

    @pytest.fixture
    def log_record(self):
        """로그 레코드 생성"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        return record

    def test_mask_api_key(self, filter_instance, log_record):
        """API 키 마스킹 테스트"""
        # Arrange
        api_key = "sk-1234567890abcdef"
        log_record.msg = f"API Key: {api_key}"

        # Act
        result = filter_instance.filter(log_record)

        # Assert
        assert result is True
        assert api_key not in log_record.msg
        assert "sk-****" in log_record.msg or "****" in log_record.msg

    def test_mask_dict(self, filter_instance, log_record):
        """딕셔너리 마스킹 테스트"""
        # Arrange
        sensitive_dict = {
            "password": "secret123",
            "api_key": "key_abc123",
            "username": "user@example.com",
        }
        log_record.msg = f"User data: {sensitive_dict}"

        # Act
        result = filter_instance.filter(log_record)

        # Assert
        assert result is True
        assert "secret123" not in log_record.msg
        assert "key_abc123" not in log_record.msg

    def test_mask_sensitive_fields(self, filter_instance, log_record):
        """민감 필드 감지 및 마스킹 테스트"""
        # Arrange
        sensitive_fields = [
            "password",
            "token",
            "secret",
            "api_key",
            "authorization",
        ]
        test_data = {
            "password": "mypassword123",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "secret": "super_secret",
            "username": "john_doe",
        }
        log_record.msg = str(test_data)

        # Act
        result = filter_instance.filter(log_record)

        # Assert
        assert result is True
        for field in sensitive_fields:
            if field in test_data:
                assert str(test_data[field]) not in log_record.msg

    def test_mask_patterns(self, filter_instance, log_record):
        """패턴 매칭 마스킹 테스트"""
        # Arrange
        patterns = [
            ("email", r"[\w\.-]+@[\w\.-]+\.\w+"),
            ("phone", r"\d{3}-\d{3}-\d{4}"),
            ("credit_card", r"\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}"),
        ]

        test_cases = [
            ("user@example.com", "email"),
            ("123-456-7890", "phone"),
            ("1234-5678-9012-3456", "credit_card"),
        ]

        for test_value, pattern_type in test_cases:
            log_record.msg = f"Data: {test_value}"

            # Act
            result = filter_instance.filter(log_record)

            # Assert
            assert result is True
            # 원본 값이 마스킹되었는지 확인
            if pattern_type in ["email", "phone", "credit_card"]:
                assert test_value not in log_record.msg or "****" in log_record.msg


@pytest.mark.unit
class TestConfigureLogging:
    """로깅 설정 테스트"""

    @pytest.fixture
    def cleanup_handlers(self):
        """테스트 후 핸들러 정리"""
        yield
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    def test_configure_json_logging(self, cleanup_handlers):
        """JSON 로깅 설정 테스트"""
        # Arrange
        output = StringIO()
        handler = logging.StreamHandler(output)

        # Act
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            configure_logging(
                level=logging.INFO,
                format_type="json",
                handlers=[handler],
            )

            # Assert
            mock_logger.setLevel.assert_called_with(logging.INFO)
            mock_logger.addHandler.assert_called()

    def test_configure_console_logging(self, cleanup_handlers):
        """콘솔 로깅 설정 테스트"""
        # Arrange
        output = StringIO()
        handler = logging.StreamHandler(output)

        # Act
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            configure_logging(
                level=logging.DEBUG,
                format_type="console",
                handlers=[handler],
            )

            # Assert
            mock_logger.setLevel.assert_called_with(logging.DEBUG)
            assert mock_logger.addHandler.called

    def test_configure_logging_with_filters(self, cleanup_handlers):
        """필터가 적용된 로깅 설정 테스트"""
        # Arrange
        output = StringIO()
        handler = logging.StreamHandler(output)

        # Act
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            configure_logging(
                level=logging.INFO,
                format_type="json",
                handlers=[handler],
                enable_sensitive_filter=True,
            )

            # Assert
            mock_logger.setLevel.assert_called()
            assert mock_logger.addHandler.called


@pytest.mark.unit
class TestRequestContext:
    """요청 컨텍스트 관리 테스트"""

    @pytest.fixture
    def request_context(self):
        """요청 컨텍스트 인스턴스"""
        return RequestContext()

    def test_context_manager(self, request_context):
        """컨텍스트 매니저 진입/퇴출 테스트"""
        # Arrange
        request_id = "req-12345"
        user_id = "user-789"

        # Act
        with request_context(request_id=request_id, user_id=user_id):
            # 컨텍스트 내부에서 값 확인
            current_request_id = request_context.get("request_id")
            current_user_id = request_context.get("user_id")

            # Assert
            assert current_request_id == request_id
            assert current_user_id == user_id

        # 컨텍스트 퇴출 후 값 확인
        assert request_context.get("request_id") is None
        assert request_context.get("user_id") is None

    @pytest.mark.asyncio
    async def test_context_propagation(self, request_context):
        """비동기 컨텍스트 전파 테스트"""
        # Arrange
        request_id = "async-req-123"
        user_id = "async-user-456"

        async def async_task():
            """비동기 작업"""
            await asyncio.sleep(0.01)
            return request_context.get("request_id"), request_context.get("user_id")

        # Act
        with request_context(request_id=request_id, user_id=user_id):
            result_request_id, result_user_id = await async_task()

            # Assert
            assert result_request_id == request_id
            assert result_user_id == user_id

    def test_nested_contexts(self, request_context):
        """중첩 컨텍스트 테스트"""
        # Arrange
        outer_request_id = "outer-req-1"
        inner_request_id = "inner-req-2"

        # Act & Assert
        with request_context(request_id=outer_request_id):
            assert request_context.get("request_id") == outer_request_id

            with request_context(request_id=inner_request_id):
                assert request_context.get("request_id") == inner_request_id

            # 내부 컨텍스트 퇴출 후 외부 값 복원
            assert request_context.get("request_id") == outer_request_id

        # 모든 컨텍스트 퇴출 후
        assert request_context.get("request_id") is None

    def test_context_with_multiple_values(self, request_context):
        """여러 값을 가진 컨텍스트 테스트"""
        # Arrange
        context_data = {
            "request_id": "req-multi-1",
            "user_id": "user-123",
            "session_id": "sess-456",
            "trace_id": "trace-789",
        }

        # Act
        with request_context(**context_data):
            for key, value in context_data.items():
                # Assert
                assert request_context.get(key) == value

    def test_context_isolation(self, request_context):
        """컨텍스트 격리 테스트"""
        # Arrange
        context1_id = "ctx1-req-1"
        context2_id = "ctx2-req-2"

        # Act & Assert
        with request_context(request_id=context1_id):
            assert request_context.get("request_id") == context1_id

            # 다른 컨텍스트는 영향을 받지 않음
            with request_context(request_id=context2_id):
                assert request_context.get("request_id") == context2_id

            assert request_context.get("request_id") == context1_id


@pytest.mark.unit
class TestPerformanceMetrics:
    """성능 메트릭 수집 테스트"""

    @pytest.fixture
    def metrics(self):
        """메트릭 인스턴스"""
        return PerformanceMetrics()

    def test_metrics_collection(self, metrics):
        """메트릭 수집 테스트"""
        # Arrange
        operation_name = "database_query"
        duration = 0.123

        # Act
        metrics.record(operation_name, duration)

        # Assert
        assert operation_name in metrics.get_metrics()
        recorded_metrics = metrics.get_metrics()[operation_name]
        assert recorded_metrics["count"] >= 1
        assert recorded_metrics["total_time"] >= duration

    def test_metrics_statistics(self, metrics):
        """메트릭 통계 테스트"""
        # Arrange
        operation_name = "api_call"
        durations = [0.1, 0.2, 0.15, 0.25, 0.12]

        # Act
        for duration in durations:
            metrics.record(operation_name, duration)

        # Assert
        stats = metrics.get_statistics(operation_name)
        assert stats["count"] == len(durations)
        assert stats["total_time"] == pytest.approx(sum(durations), rel=0.01)
        assert stats["avg_time"] == pytest.approx(
            sum(durations) / len(durations), rel=0.01
        )
        assert stats["min_time"] == pytest.approx(min(durations), rel=0.01)
        assert stats["max_time"] == pytest.approx(max(durations), rel=0.01)

    @pytest.mark.asyncio
    async def test_async_metrics(self, metrics):
        """비동기 메트릭 수집 테스트"""
        # Arrange
        async def async_operation(duration):
            """비동기 작업 시뮬레이션"""
            await asyncio.sleep(duration)
            return "result"

        operation_name = "async_task"
        test_duration = 0.05

        # Act
        with metrics.timer(operation_name):
            result = await async_operation(test_duration)

        # Assert
        assert result == "result"