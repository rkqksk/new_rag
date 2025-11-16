"""Custom Exceptions with Context"""

import json
import traceback
from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class RAGEnterpriseException(Exception):
    """Base exception with context"""

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        self.message = message
        self.context = context or {}
        self.original_exception = original_exception
        self.traceback_str = traceback.format_exc() if original_exception else None

        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/API response"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "original_error": str(self.original_exception) if self.original_exception else None,
            "traceback": self.traceback_str,
        }

    def __str__(self) -> str:
        parts = [f"{self.__class__.__name__}: {self.message}"]

        if self.context:
            parts.append(f"Context: {json.dumps(self.context, indent=2)}")

        if self.original_exception:
            parts.append(f"Original: {str(self.original_exception)}")

        return "\n".join(parts)


class ServiceException(RAGEnterpriseException):
    """Service layer exception"""

    pass


class RepositoryException(RAGEnterpriseException):
    """Repository layer exception"""

    pass


class ValidationException(RAGEnterpriseException):
    """Validation exception"""

    pass


class SearchException(ServiceException):
    """Search operation exception"""

    pass


class CacheException(RepositoryException):
    """Cache operation exception"""

    pass


class DatabaseException(RepositoryException):
    """Database operation exception"""

    pass


class VectorSearchException(RepositoryException):
    """Vector search exception"""

    pass


# ============================================================================
# HTTP Exception Helpers
# ============================================================================


def get_status_code_for_exception(exc: Exception) -> int:
    """Get HTTP status code for a given exception type.

    Args:
        exc: Exception instance

    Returns:
        int: HTTP status code
    """
    exception_status_map = {
        ValidationException: status.HTTP_400_BAD_REQUEST,
        SearchException: status.HTTP_500_INTERNAL_SERVER_ERROR,
        CacheException: status.HTTP_503_SERVICE_UNAVAILABLE,
        DatabaseException: status.HTTP_503_SERVICE_UNAVAILABLE,
        VectorSearchException: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ServiceException: status.HTTP_500_INTERNAL_SERVER_ERROR,
        RepositoryException: status.HTTP_503_SERVICE_UNAVAILABLE,
        RAGEnterpriseException: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    # Find the most specific exception class
    for exc_class, status_code in exception_status_map.items():
        if isinstance(exc, exc_class):
            return status_code

    return status.HTTP_500_INTERNAL_SERVER_ERROR


def create_http_exception(
    exc: RAGEnterpriseException,
    status_code: Optional[int] = None,
) -> HTTPException:
    """Create an HTTPException from a RAGEnterpriseException.

    Args:
        exc: RAGEnterpriseException instance
        status_code: Optional HTTP status code override

    Returns:
        HTTPException: FastAPI HTTPException
    """
    if status_code is None:
        status_code = get_status_code_for_exception(exc)

    return HTTPException(
        status_code=status_code,
        detail={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "context": exc.context,
        },
    )
