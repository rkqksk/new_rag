"""
Pydantic schemas for API request/response validation.

This module consolidates all API schemas from across the application
to provide a single source of truth for request/response models.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# QA Schemas
# ============================================================================

class QARequest(BaseModel):
    """Q&A request schema.

    Attributes:
        question: User question
        collection: Qdrant collection name
        top_k: Number of results to return
        return_all: Return all results (no filtering)
        min_integrity_score: Minimum integrity score filter
        customer_id: Optional customer identifier
    """
    question: str = Field(..., min_length=1, max_length=1000, description="User question")
    collection: str = Field(default="products_all", description="Collection name")
    top_k: int = Field(default=3, ge=1, le=50, description="Number of results")
    return_all: bool = Field(default=False, description="Return all results")
    min_integrity_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Min integrity")
    customer_id: Optional[str] = Field(None, description="Customer ID")

    @field_validator("question")
    @classmethod
    def sanitize_question(cls, v: str) -> str:
        """Remove HTML tags and dangerous content from question."""
        # Remove HTML tags
        v = re.sub(r'<[^>]+>', '', v)
        # Remove script tags content
        v = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', v, flags=re.IGNORECASE)

        # Check for dangerous prompt injection patterns - REJECT if found
        dangerous_patterns = [
            (r'ignore\s+previous\s+instructions', '허용되지 않는 패턴: ignore previous instructions'),
            (r'forget\s+everything', '허용되지 않는 패턴: forget everything'),
            (r'system\s*:\s*you\s+are', '허용되지 않는 패턴: system role override'),
            (r'assistant\s*:\s*i\s+will', '허용되지 않는 패턴: assistant role override'),
            (r'ignore\s+instructions', '허용되지 않는 패턴: ignore instructions'),
            (r'hacker\s+mode', '허용되지 않는 패턴: hacker mode'),
            (r'jailbreak', '허용되지 않는 패턴: jailbreak'),
        ]
        for pattern, error_msg in dangerous_patterns:
            if re.search(pattern, v, flags=re.IGNORECASE):
                raise ValueError(error_msg)

        return v.strip()

    @field_validator("collection")
    @classmethod
    def validate_collection_name(cls, v: str) -> str:
        """Validate collection name format (alphanumeric, underscore, hyphen only)."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Collection name must contain only letters, numbers, underscores, and hyphens')
        return v


class QAResponse(BaseModel):
    """Q&A response schema.

    Attributes:
        question: Original user question
        answer: Generated answer
        related_products: List of related products
        confidence: Response confidence score
        qa_id: Unique QA identifier
        timestamp: Response timestamp
    """
    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="Generated answer")
    related_products: List[Dict[str, Any]] = Field(default_factory=list, description="Related products")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    qa_id: str = Field(..., description="QA identifier")
    timestamp: str = Field(..., description="Timestamp")


# ============================================================================
# Consultation Schemas
# ============================================================================

class ConsultationRequest(BaseModel):
    """Consultation request schema for product recommendations.

    Attributes:
        requirements: Product requirements description
        quantity: Required quantity
        budget: Budget range
        customer_email: Customer email address
    """
    requirements: str = Field(..., min_length=1, max_length=1000, description="Product requirements")
    quantity: int = Field(..., ge=1, description="Required quantity")
    budget: str = Field(..., description="Budget range")
    customer_email: str = Field(..., description="Customer email")

    @field_validator("customer_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation."""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v


class ConsultationResponse(BaseModel):
    """Consultation response schema.

    Attributes:
        recommendations: List of recommended products
        consultation_text: Consultation text/advice
        next_steps: List of suggested next steps
        consultation_id: Unique consultation identifier
        timestamp: Response timestamp
    """
    recommendations: List[Dict[str, Any]] = Field(..., description="Product recommendations")
    consultation_text: str = Field(..., description="Consultation advice")
    next_steps: List[str] = Field(..., description="Next steps")
    consultation_id: str = Field(..., description="Consultation ID")
    timestamp: str = Field(..., description="Timestamp")


# ============================================================================
# Product Schemas
# ============================================================================

class ProductSearchRequest(BaseModel):
    """Product search request schema.

    Attributes:
        query: Search query
        limit: Maximum number of results
    """
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    limit: Optional[int] = Field(default=10, ge=1, le=100, description="Result limit")

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, v: str) -> str:
        """Sanitize search query."""
        # Remove HTML tags
        v = re.sub(r'<[^>]+>', '', v)
        return v.strip()


class InquiryRequest(BaseModel):
    """Product inquiry request schema."""
    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    product_code: str = Field(..., description="Product code")
    company_name: str = Field(..., description="Company name")
    contact_name: str = Field(..., description="Contact name")
    contact_phone: str = Field(..., description="Contact phone")
    contact_email: str = Field(..., description="Contact email")
    quantity: Optional[str] = Field(None, description="Quantity")
    message: Optional[str] = Field(None, description="Message")
    timestamp: str = Field(..., description="Timestamp")


class SampleRequest(BaseModel):
    """Product sample request schema."""
    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    product_code: str = Field(..., description="Product code")
    company_name: str = Field(..., description="Company name")
    contact_name: str = Field(..., description="Contact name")
    contact_phone: str = Field(..., description="Contact phone")
    contact_email: str = Field(..., description="Contact email")
    quantity: Optional[str] = Field(None, description="Sample quantity")
    delivery_address: Optional[str] = Field(None, description="Delivery address")
    message: Optional[str] = Field(None, description="Additional message")
    timestamp: str = Field(..., description="Timestamp")


class QASearchRequest(BaseModel):
    """QA search request schema."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    limit: Optional[int] = Field(default=5, ge=1, le=100, description="Result limit")


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response schema.

    Attributes:
        error: Error type/code
        message: Human-readable error message
        error_id: Optional error identifier
        timestamp: Error timestamp
    """
    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Error message")
    error_id: Optional[str] = Field(None, description="Error identifier")
    timestamp: str = Field(..., description="Timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid request parameters",
                "error_id": "err_12345",
                "timestamp": "2025-11-08T08:00:00Z"
            }
        }


# ============================================================================
# Export all schemas
# ============================================================================

# Import health schemas for re-export
from app.api.routes.health import HealthCheckResponse

__all__ = [
    # QA Schemas
    "QARequest",
    "QAResponse",
    # Consultation Schemas
    "ConsultationRequest",
    "ConsultationResponse",
    # Product Schemas
    "ProductSearchRequest",
    "InquiryRequest",
    "QASearchRequest",
    # Error Schemas
    "ErrorResponse",
    # Health Schemas (re-exported for backward compatibility)
    "HealthCheckResponse",
]
