"""
JWT Token Handler for SaaS Authentication

Handles JWT token creation, validation, and user authentication.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


class TokenData(BaseModel):
    """JWT token payload"""

    user_id: str
    tenant_id: str
    email: str
    role: str
    exp: datetime


class TokenResponse(BaseModel):
    """Token response model"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: str, tenant_id: str, email: str, role: str, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token

    Args:
        user_id: User UUID
        tenant_id: Tenant UUID
        email: User email
        role: User role (admin, member, viewer, billing)
        expires_delta: Optional custom expiration

    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verify and decode JWT token

    Args:
        token: JWT token string

    Returns:
        TokenData with user information

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        email: str = payload.get("email")
        role: str = payload.get("role")
        exp = datetime.fromtimestamp(payload.get("exp"))

        if user_id is None or tenant_id is None:
            raise credentials_exception

        token_data = TokenData(
            user_id=user_id, tenant_id=tenant_id, email=email, role=role, exp=exp
        )

        return token_data

    except JWTError:
        raise credentials_exception


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> TokenData:
    """
    Extract current user from JWT token

    Dependency for FastAPI routes requiring authentication.

    Usage:
        @router.get("/protected")
        async def protected_route(current_user: TokenData = Depends(get_current_user_from_token)):
            return {"user_id": current_user.user_id}
    """
    token = credentials.credentials
    return verify_token(token)


def create_token_response(user_id: str, tenant_id: str, email: str, role: str) -> TokenResponse:
    """
    Create complete token response with metadata

    Args:
        user_id: User UUID
        tenant_id: Tenant UUID
        email: User email
        role: User role

    Returns:
        TokenResponse with token and metadata
    """
    access_token = create_access_token(user_id=user_id, tenant_id=tenant_id, email=email, role=role)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
    )


# Password validation
def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength

    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit

    Returns:
        (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    return True, ""
