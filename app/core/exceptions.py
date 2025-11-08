"""Custom Exceptions with Context"""

import json
import traceback
from typing import Any, Dict, Optional


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
