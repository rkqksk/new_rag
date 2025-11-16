"""
Shared domain models for RAG Enterprise v10.0.0

Common data models used across all applications.

Usage:
    from packages.core.models import Product, SearchResult

    product = Product(name="PET Bottle", code="PET-001")
    result = SearchResult(product=product, score=0.95)
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Product(BaseModel):
    """Product domain model."""

    id: Optional[int] = None
    code: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    material: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    """Search result with relevance score."""

    product: Product
    score: float = Field(ge=0.0, le=1.0, description="Similarity score (0-1)")
    highlights: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchQuery(BaseModel):
    """Search query parameters."""

    query: str = Field(min_length=1, description="Search query text")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results")
    filters: Optional[Dict[str, Any]] = None
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum score")


class User(BaseModel):
    """User domain model."""

    id: Optional[int] = None
    email: str
    name: Optional[str] = None
    role: str = "user"  # user, admin, etc.
    tenant_id: Optional[int] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Tenant(BaseModel):
    """Multi-tenant organization model."""

    id: Optional[int] = None
    name: str
    slug: str
    plan: str = "free"  # free, pro, enterprise
    max_users: int = 10
    max_products: int = 1000
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class APIResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel):
    """Paginated API response."""

    items: List[Any]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool = False


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = False
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


__all__ = [
    "Product",
    "SearchResult",
    "SearchQuery",
    "User",
    "Tenant",
    "APIResponse",
    "PaginatedResponse",
    "ErrorResponse",
]
