"""
API Key Handler for SaaS Authentication

Handles API key generation, validation, and management for programmatic access.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Security, Header
from fastapi.security import APIKeyHeader

from src.db.session import get_db
from src.models.saas_models import APIKey, Tenant


# Security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyManager:
    """
    Manage API keys for tenants

    Features:
    - Generate secure API keys
    - Validate and authenticate requests
    - Track usage
    - Revoke keys
    """

    @staticmethod
    def generate_api_key(
        tenant_id: str,
        name: str,
        expires_days: Optional[int] = None
    ) -> dict:
        """
        Generate new API key for tenant

        Args:
            tenant_id: Tenant UUID
            name: Friendly name for the key
            expires_days: Optional expiration in days

        Returns:
            dict with api_key (shown only once!) and metadata
        """
        from src.db.session import SessionLocal

        db = SessionLocal()

        try:
            # Generate secure random key
            # Format: tenant_<short_id>_<random_part>
            tenant_short_id = tenant_id[:8]
            random_part = secrets.token_urlsafe(32)
            api_key = f"tenant_{tenant_short_id}_{random_part}"

            # Hash for storage (NEVER store plaintext)
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            # Key prefix for display (first 12 chars)
            key_prefix = api_key[:12]

            # Calculate expiration
            expires_at = None
            if expires_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_days)

            # Create database record
            db_api_key = APIKey(
                tenant_id=tenant_id,
                name=name,
                key_hash=key_hash,
                key_prefix=key_prefix,
                scopes=["*"],  # Full access by default
                is_active=True,
                expires_at=expires_at,
                created_at=datetime.utcnow()
            )

            db.add(db_api_key)
            db.commit()
            db.refresh(db_api_key)

            return {
                "api_key": api_key,  # ⚠️ Only shown once!
                "key_id": str(db_api_key.id),
                "key_prefix": key_prefix,
                "name": name,
                "created_at": db_api_key.created_at.isoformat(),
                "expires_at": db_api_key.expires_at.isoformat() if db_api_key.expires_at else None
            }

        finally:
            db.close()

    @staticmethod
    def verify_api_key(api_key: str) -> tuple[str, str]:
        """
        Verify API key and return tenant_id and key_id

        Args:
            api_key: API key string

        Returns:
            (tenant_id, key_id)

        Raises:
            HTTPException: If key is invalid, expired, or revoked
        """
        from src.db.session import SessionLocal

        db = SessionLocal()

        try:
            # Hash the provided key
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            # Query database
            db_key = db.query(APIKey).filter(
                APIKey.key_hash == key_hash
            ).first()

            # Check if key exists
            if not db_key:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key"
                )

            # Check if key is active
            if not db_key.is_active:
                raise HTTPException(
                    status_code=401,
                    detail="API key has been revoked"
                )

            # Check if key is expired
            if db_key.is_expired:
                raise HTTPException(
                    status_code=401,
                    detail="API key has expired"
                )

            # Check tenant status
            tenant = db.query(Tenant).filter(Tenant.id == db_key.tenant_id).first()
            if not tenant or not tenant.is_active:
                raise HTTPException(
                    status_code=403,
                    detail="Tenant account is suspended"
                )

            # Update last used timestamp
            db_key.last_used_at = datetime.utcnow()
            db_key.total_requests += 1
            db.commit()

            return str(db_key.tenant_id), str(db_key.id)

        finally:
            db.close()

    @staticmethod
    def revoke_api_key(key_id: str, tenant_id: str) -> bool:
        """
        Revoke API key

        Args:
            key_id: API key UUID
            tenant_id: Tenant UUID (for authorization check)

        Returns:
            True if revoked successfully

        Raises:
            HTTPException: If key not found or unauthorized
        """
        from src.db.session import SessionLocal

        db = SessionLocal()

        try:
            db_key = db.query(APIKey).filter(
                APIKey.id == key_id,
                APIKey.tenant_id == tenant_id
            ).first()

            if not db_key:
                raise HTTPException(
                    status_code=404,
                    detail="API key not found"
                )

            db_key.is_active = False
            db.commit()

            return True

        finally:
            db.close()

    @staticmethod
    def list_api_keys(tenant_id: str):
        """
        List all API keys for tenant

        Args:
            tenant_id: Tenant UUID

        Returns:
            List of API key metadata (without actual keys)
        """
        from src.db.session import SessionLocal

        db = SessionLocal()

        try:
            keys = db.query(APIKey).filter(
                APIKey.tenant_id == tenant_id
            ).all()

            return [
                {
                    "id": str(k.id),
                    "name": k.name,
                    "key_prefix": k.key_prefix,
                    "scopes": k.scopes,
                    "is_active": k.is_active,
                    "total_requests": k.total_requests,
                    "created_at": k.created_at.isoformat(),
                    "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                    "expires_at": k.expires_at.isoformat() if k.expires_at else None
                }
                for k in keys
            ]

        finally:
            db.close()


# FastAPI dependency for API key authentication
async def get_current_tenant_from_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> str:
    """
    Extract tenant_id from API key header

    FastAPI dependency for API key authentication.

    Usage:
        @router.get("/protected")
        async def protected_route(tenant_id: str = Depends(get_current_tenant_from_api_key)):
            return {"tenant_id": tenant_id}

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    tenant_id, key_id = APIKeyManager.verify_api_key(api_key)
    return tenant_id


# Alternative: support both JWT and API key
async def get_current_tenant(
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None)
) -> str:
    """
    Extract tenant_id from either API key or JWT token

    Supports both authentication methods:
    - X-API-Key header (for programmatic access)
    - Authorization: Bearer <token> (for user access)

    Usage:
        @router.get("/flexible")
        async def flexible_route(tenant_id: str = Depends(get_current_tenant)):
            return {"tenant_id": tenant_id}

    Returns:
        tenant_id string

    Raises:
        HTTPException: If neither auth method is provided or both are invalid
    """
    # Try API key first
    if api_key:
        try:
            tenant_id, _ = APIKeyManager.verify_api_key(api_key)
            return tenant_id
        except HTTPException:
            pass  # Fall through to JWT

    # Try JWT token
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        try:
            from src.core.auth.jwt_handler import verify_token
            token_data = verify_token(token)
            return token_data.tenant_id
        except HTTPException:
            pass

    # Neither worked
    raise HTTPException(
        status_code=401,
        detail="Authentication required (API key or Bearer token)",
        headers={"WWW-Authenticate": "Bearer, ApiKey"}
    )
