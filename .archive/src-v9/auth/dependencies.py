"""
Authentication Dependencies
FastAPI dependencies for JWT authentication and authorization
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .jwt_utils import JWTUtils, get_user_from_token
from .models import CurrentUser, UserRole

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    Dependency to get current authenticated user from JWT token

    Args:
        credentials: HTTP Authorization credentials (Bearer token)

    Returns:
        CurrentUser object with id, email, role

    Raises:
        HTTPException: If token is invalid or missing

    Usage:
        @app.get("/protected")
        async def protected_route(current_user: CurrentUser = Depends(get_current_user)):
            return {"user": current_user.email}
    """
    token = credentials.credentials

    # Verify and decode token
    user_data = get_user_from_token(token)

    return CurrentUser(
        id=user_data["user_id"],
        email=user_data["email"],
        role=user_data["role"]
    )


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Dependency to get current active user

    This can be extended to check user status from database

    Args:
        current_user: Current authenticated user

    Returns:
        CurrentUser if active

    Raises:
        HTTPException: If user is inactive
    """
    # TODO: Add database check for user status
    # For now, just return the user
    return current_user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory for role-based access control

    Args:
        *allowed_roles: Roles that are allowed to access the endpoint

    Returns:
        Dependency function

    Usage:
        @app.get("/admin", dependencies=[Depends(require_role(UserRole.ADMIN))])
        async def admin_only():
            return {"message": "Admin access granted"}
    """
    async def role_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_user

    return role_checker


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[CurrentUser]:
    """
    Dependency to get current user if authenticated, None otherwise

    Useful for endpoints that work both with and without authentication

    Args:
        credentials: Optional HTTP Authorization credentials

    Returns:
        CurrentUser if authenticated, None otherwise

    Usage:
        @app.get("/public-or-private")
        async def flexible_route(user: Optional[CurrentUser] = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user.email}"}
            return {"message": "Hello anonymous user"}
    """
    if not credentials:
        return None

    try:
        user_data = get_user_from_token(credentials.credentials)
        return CurrentUser(
            id=user_data["user_id"],
            email=user_data["email"],
            role=user_data["role"]
        )
    except HTTPException:
        return None


# Convenience dependencies for common roles

async def require_admin(
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN))
) -> CurrentUser:
    """Require admin role"""
    return current_user


async def require_manager_or_admin(
    current_user: CurrentUser = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER))
) -> CurrentUser:
    """Require manager or admin role"""
    return current_user


async def require_authenticated(
    current_user: CurrentUser = Depends(get_current_active_user)
) -> CurrentUser:
    """Require any authenticated user"""
    return current_user
