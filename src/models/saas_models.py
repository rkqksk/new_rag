"""
SaaS Models for Multi-Tenancy

SQLAlchemy models for tenant management and API key authentication.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.db.session import Base


class PlanTier(str, Enum):
    """Subscription tier enumeration."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant status enumeration."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class UserRole(str, Enum):
    """User role enumeration."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    READONLY = "readonly"


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration."""

    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"


# Plan limits configuration
PLAN_LIMITS = {
    PlanTier.FREE: {
        "max_api_calls": 1000,
        "max_storage_mb": 100,
        "max_users": 1,
        "max_projects": 3,
        "rate_limit_per_minute": 10,
    },
    PlanTier.PRO: {
        "max_api_calls": 100000,
        "max_storage_mb": 10000,  # 10GB
        "max_users": 10,
        "max_projects": 50,
        "rate_limit_per_minute": 100,
    },
    PlanTier.ENTERPRISE: {
        "max_api_calls": -1,  # Unlimited
        "max_storage_mb": -1,  # Unlimited
        "max_users": -1,  # Unlimited
        "max_projects": -1,  # Unlimited
        "rate_limit_per_minute": 1000,
    },
}


class Tenant(Base):
    """
    Tenant model for multi-tenancy support.

    Each tenant represents an organization/customer using the platform.
    """

    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    tier = Column(String(50), default="free", nullable=False)  # free, pro, enterprise

    # Resource limits
    max_api_calls = Column(Integer, default=1000, nullable=False)
    max_storage_mb = Column(Integer, default=100, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    api_keys = relationship("APIKey", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, tier={self.tier})>"


class APIKey(Base):
    """
    API Key model for programmatic authentication.

    Stores hashed API keys for secure authentication.
    """

    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # Friendly name for the key
    key_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 hash

    # Key metadata
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)

    # Expiration
    expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(id={self.id}, name={self.name}, tenant_id={self.tenant_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if the API key has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the API key is valid (active and not expired)."""
        return self.is_active and not self.is_expired


class User(Base):
    """
    User model for multi-tenant user management.

    Each user belongs to a tenant and has a role within that tenant.
    """

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Role and status
    role = Column(String(50), default=UserRole.MEMBER.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Last login tracking
    last_login_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class Invoice(Base):
    """
    Invoice model for billing tracking.

    Stores invoice information from payment providers (e.g., Stripe).
    """

    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)

    # Stripe integration
    stripe_invoice_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_customer_id = Column(String(255), nullable=True)

    # Invoice details
    amount = Column(Integer, nullable=False)  # Amount in cents
    currency = Column(String(3), default="usd", nullable=False)
    status = Column(String(50), default="draft", nullable=False)  # draft, open, paid, void, uncollectible

    # Billing period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Due date
    due_date = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)

    # Metadata
    description = Column(Text, nullable=True)
    invoice_pdf = Column(String(500), nullable=True)  # URL to PDF

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant")

    def __repr__(self):
        return f"<Invoice(id={self.id}, tenant_id={self.tenant_id}, amount={self.amount}, status={self.status})>"


class QuotaUsage(Base):
    """
    Quota usage tracking model.

    Tracks API calls, storage, and other resource usage against plan limits.
    """

    __tablename__ = "quota_usage"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)

    # Usage metrics
    api_calls_count = Column(Integer, default=0, nullable=False)
    storage_used_mb = Column(Integer, default=0, nullable=False)

    # Period tracking
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Last reset
    last_reset_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant")

    def __repr__(self):
        return f"<QuotaUsage(id={self.id}, tenant_id={self.tenant_id}, api_calls={self.api_calls_count})>"


class UsageLog(Base):
    """
    Detailed usage log for API calls and operations.

    Records individual API calls for analytics and debugging.
    """

    __tablename__ = "usage_logs"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    # Request details
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False)  # GET, POST, etc.
    status_code = Column(Integer, nullable=False)

    # Performance
    response_time_ms = Column(Integer, nullable=True)

    # Metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(String(500), nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User")

    def __repr__(self):
        return f"<UsageLog(id={self.id}, tenant_id={self.tenant_id}, endpoint={self.endpoint})>"
