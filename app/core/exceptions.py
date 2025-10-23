"""
Custom exceptions for RAG Enterprise system
Provides structured error handling across the application
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException


class RAGEnterpriseException(Exception):
    """Base exception for all RAG Enterprise errors"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class VectorDBException(RAGEnterpriseException):
    """Exceptions related to vector database operations"""
    pass


class QdrantConnectionError(VectorDBException):
    """Failed to connect to Qdrant"""
    pass


class QdrantOperationError(VectorDBException):
    """Qdrant operation failed"""
    pass


class EmbeddingException(RAGEnterpriseException):
    """Exceptions related to embedding generation"""
    pass


class ModelLoadError(EmbeddingException):
    """Failed to load embedding model"""
    pass


class EmbeddingGenerationError(EmbeddingException):
    """Failed to generate embeddings"""
    pass


class LLMException(RAGEnterpriseException):
    """Exceptions related to LLM operations"""
    pass


class OllamaConnectionError(LLMException):
    """Failed to connect to Ollama"""
    pass


class LLMGenerationError(LLMException):
    """Failed to generate LLM response"""
    pass


class DataIngestionException(RAGEnterpriseException):
    """Exceptions related to data ingestion"""
    pass


class FileParsingError(DataIngestionException):
    """Failed to parse file"""
    pass


class UnsupportedFileFormatError(DataIngestionException):
    """File format not supported"""
    pass


class ValidationException(RAGEnterpriseException):
    """Exceptions related to data validation"""
    pass


class ConfigurationException(RAGEnterpriseException):
    """Exceptions related to configuration"""
    pass


class MissingConfigError(ConfigurationException):
    """Required configuration is missing"""
    pass


def create_http_exception(
    exception: RAGEnterpriseException,
    status_code: int = 500
) -> HTTPException:
    """
    Convert RAGEnterpriseException to HTTPException

    Args:
        exception: The RAG Enterprise exception
        status_code: HTTP status code (default: 500)

    Returns:
        HTTPException with structured error details
    """
    return HTTPException(
        status_code=status_code,
        detail={
            "error": exception.error_code,
            "message": exception.message,
            "details": exception.details
        }
    )


# Error code mapping for HTTP status codes
ERROR_STATUS_MAPPING = {
    "QdrantConnectionError": 503,  # Service Unavailable
    "QdrantOperationError": 500,   # Internal Server Error
    "ModelLoadError": 503,         # Service Unavailable
    "EmbeddingGenerationError": 500,  # Internal Server Error
    "OllamaConnectionError": 503,  # Service Unavailable
    "LLMGenerationError": 500,     # Internal Server Error
    "FileParsingError": 400,       # Bad Request
    "UnsupportedFileFormatError": 415,  # Unsupported Media Type
    "ValidationException": 422,    # Unprocessable Entity
    "MissingConfigError": 500,     # Internal Server Error
}


def get_status_code_for_exception(exception: RAGEnterpriseException) -> int:
    """
    Get appropriate HTTP status code for an exception

    Args:
        exception: The RAG Enterprise exception

    Returns:
        HTTP status code
    """
    return ERROR_STATUS_MAPPING.get(exception.error_code, 500)