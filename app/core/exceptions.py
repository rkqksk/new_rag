"""Custom Exceptions"""

class RAGEnterpriseException(Exception):
    """Base exception"""
    pass

class ServiceException(RAGEnterpriseException):
    """Service layer exception"""
    pass

class RepositoryException(RAGEnterpriseException):
    """Repository layer exception"""
    pass

class ValidationException(RAGEnterpriseException):
    """Validation exception"""
    pass
