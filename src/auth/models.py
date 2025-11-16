"""
Authentication Models
User, Role, and Session models for authentication
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


# ========================================================================
# Enums
# ========================================================================

class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    MANAGER = "manager"
    WORKER = "worker"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


# ========================================================================
# Request Models
# ========================================================================

class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: UserRole = UserRole.WORKER


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Password change request"""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class ResetPasswordRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


# ========================================================================
# Response Models
# ========================================================================

class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds


class UserResponse(BaseModel):
    """User information response"""
    id: str
    email: str
    name: str
    phone: Optional[str] = None
    role: UserRole
    status: UserStatus
    created_at: datetime
    last_login: Optional[datetime] = None


class LoginResponse(BaseModel):
    """Login response with tokens and user info"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


# ========================================================================
# Database Models (for SQLAlchemy/PostgreSQL)
# ========================================================================

class User:
    """
    User database model

    This is a template for SQLAlchemy model.
    Actual implementation should extend Base and include proper column definitions.
    """
    __tablename__ = "users"

    # Fields:
    # id: UUID (primary key)
    # email: String (unique, indexed)
    # password_hash: String
    # name: String
    # phone: String (nullable)
    # role: Enum (admin, manager, worker, viewer)
    # status: Enum (active, inactive, suspended)
    # created_at: DateTime
    # updated_at: DateTime
    # last_login: DateTime (nullable)
    # avatar_url: String (nullable)
    # metadata: JSONB (nullable)

    def __repr__(self):
        return f"<User {self.email}>"


class RefreshToken:
    """
    Refresh token database model

    Stores refresh tokens for revocation capability
    """
    __tablename__ = "refresh_tokens"

    # Fields:
    # id: UUID (primary key)
    # user_id: UUID (foreign key to users)
    # token_hash: String (hashed refresh token)
    # expires_at: DateTime
    # created_at: DateTime
    # revoked: Boolean (default False)
    # revoked_at: DateTime (nullable)
    # device_info: String (nullable, e.g., "iPhone 14 Pro")
    # ip_address: String (nullable)

    def __repr__(self):
        return f"<RefreshToken {self.id}>"


class LoginHistory:
    """
    Login history tracking
    """
    __tablename__ = "login_history"

    # Fields:
    # id: UUID (primary key)
    # user_id: UUID (foreign key to users)
    # login_at: DateTime
    # ip_address: String
    # user_agent: String
    # device_info: String (nullable)
    # location: String (nullable)
    # success: Boolean

    def __repr__(self):
        return f"<LoginHistory {self.user_id} at {self.login_at}>"


# ========================================================================
# Utility Models
# ========================================================================

class CurrentUser(BaseModel):
    """Current authenticated user (extracted from JWT token)"""
    id: str
    email: str
    role: UserRole

    class Config:
        use_enum_values = True


class PermissionCheck(BaseModel):
    """Permission check result"""
    allowed: bool
    reason: Optional[str] = None


# ========================================================================
# Mock Data (for development/testing)
# ========================================================================

MOCK_USERS = {
    "admin@example.com": {
        "id": "user_admin_001",
        "email": "admin@example.com",
        "password_hash": "$2b$12$nA11165x3Henx.IrqQZzM.3Wj.c3lxdmwRBb5RpOrTqjej4MC8/m6",  # "password123"
        "name": "관리자",
        "phone": "010-0000-0000",
        "role": UserRole.ADMIN,
        "status": UserStatus.ACTIVE,
        "created_at": datetime(2024, 1, 1, 0, 0, 0),
        "last_login": None,
    },
    "worker@example.com": {
        "id": "user_worker_001",
        "email": "worker@example.com",
        "password_hash": "$2b$12$nA11165x3Henx.IrqQZzM.3Wj.c3lxdmwRBb5RpOrTqjej4MC8/m6",  # "password123"
        "name": "작업자",
        "phone": "010-1111-1111",
        "role": UserRole.WORKER,
        "status": UserStatus.ACTIVE,
        "created_at": datetime(2024, 1, 1, 0, 0, 0),
        "last_login": None,
    },
    "customer@example.com": {
        "id": "user_customer_001",
        "email": "customer@example.com",
        "password_hash": "$2b$12$nA11165x3Henx.IrqQZzM.3Wj.c3lxdmwRBb5RpOrTqjej4MC8/m6",  # "password123"
        "name": "고객",
        "phone": "010-2222-2222",
        "role": UserRole.VIEWER,  # Using VIEWER as customer role
        "status": UserStatus.ACTIVE,
        "created_at": datetime(2024, 1, 1, 0, 0, 0),
        "last_login": None,
    }
}


def get_mock_user(email: str) -> Optional[dict]:
    """Get mock user by email"""
    return MOCK_USERS.get(email)
