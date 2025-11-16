"""
Authentication API Routes
Login, register, token refresh, and user management endpoints
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from ...auth.models import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    TokenResponse,
    UserResponse,
    LoginResponse,
    UserRole,
    UserStatus,
    get_mock_user,
    MOCK_USERS
)
from ...auth.jwt_utils import JWTUtils, create_tokens_for_user
from ...auth.dependencies import get_current_user, require_admin, CurrentUser


class AuthRouter:
    """Authentication API Router"""

    def __init__(self):
        self.router = APIRouter(prefix="/auth", tags=["Authentication"])
        self.security = HTTPBearer()
        self._setup_routes()

    def _setup_routes(self):
        """Setup authentication routes"""

        # ================================================================
        # Public Routes (No authentication required)
        # ================================================================

        @self.router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
        async def register(request: RegisterRequest):
            """
            Register a new user

            **Request Body:**
            - email: User email (unique)
            - password: User password (min 8 characters)
            - name: User's full name
            - phone: Phone number (optional)
            - role: User role (default: worker)

            **Response:**
            - User information (without password)

            **Status Codes:**
            - 201: User created successfully
            - 400: Email already exists
            - 422: Validation error
            """
            # Check if email already exists
            if get_mock_user(request.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

            # Hash password
            password_hash = JWTUtils.hash_password(request.password)

            # Create user (in real app, save to database)
            user_id = f"user_{request.email.split('@')[0]}_{datetime.utcnow().timestamp()}"

            new_user = {
                "id": user_id,
                "email": request.email,
                "password_hash": password_hash,
                "name": request.name,
                "phone": request.phone,
                "role": request.role,
                "status": UserStatus.ACTIVE,
                "created_at": datetime.utcnow(),
                "last_login": None
            }

            # Store in mock database
            MOCK_USERS[request.email] = new_user

            return UserResponse(
                id=new_user["id"],
                email=new_user["email"],
                name=new_user["name"],
                phone=new_user["phone"],
                role=new_user["role"],
                status=new_user["status"],
                created_at=new_user["created_at"],
                last_login=new_user["last_login"]
            )

        @self.router.post("/login", response_model=LoginResponse)
        async def login(request: LoginRequest):
            """
            Authenticate user and return tokens

            **Request Body:**
            - email: User email
            - password: User password

            **Response:**
            - access_token: JWT access token (30 min expiry)
            - refresh_token: JWT refresh token (7 day expiry)
            - token_type: "bearer"
            - user: User information

            **Status Codes:**
            - 200: Login successful
            - 401: Invalid credentials
            - 422: Validation error

            **Example:**
            ```
            POST /auth/login
            {
                "email": "worker@example.com",
                "password": "password123"
            }
            ```
            """
            # Get user from database (mock)
            user = get_mock_user(request.email)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Verify password
            if not JWTUtils.verify_password(request.password, user["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Check if user is active
            if user["status"] != UserStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Account is {user['status']}"
                )

            # Update last login (in real app, update database)
            user["last_login"] = datetime.utcnow()

            # Create tokens
            tokens = create_tokens_for_user(
                user_id=user["id"],
                email=user["email"],
                role=user["role"]
            )

            return LoginResponse(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_type=tokens["token_type"],
                user=UserResponse(
                    id=user["id"],
                    email=user["email"],
                    name=user["name"],
                    phone=user["phone"],
                    role=user["role"],
                    status=user["status"],
                    created_at=user["created_at"],
                    last_login=user["last_login"]
                )
            )

        @self.router.post("/refresh", response_model=TokenResponse)
        async def refresh_token(request: RefreshTokenRequest):
            """
            Refresh access token using refresh token

            **Request Body:**
            - refresh_token: Valid refresh token

            **Response:**
            - New access_token
            - Same refresh_token (or new one in some implementations)
            - token_type: "bearer"

            **Status Codes:**
            - 200: Token refreshed successfully
            - 401: Invalid or expired refresh token
            """
            # Verify refresh token
            payload = JWTUtils.verify_token(request.refresh_token, token_type="refresh")
            user_id = payload.get("sub")

            # Get user (in real app, from database)
            user = None
            for u in MOCK_USERS.values():
                if u["id"] == user_id:
                    user = u
                    break

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )

            # Create new access token
            tokens = create_tokens_for_user(
                user_id=user["id"],
                email=user["email"],
                role=user["role"]
            )

            return TokenResponse(
                access_token=tokens["access_token"],
                refresh_token=request.refresh_token,  # Return same refresh token
                token_type="bearer",
                expires_in=1800
            )

        # ================================================================
        # Protected Routes (Authentication required)
        # ================================================================

        @self.router.get("/me", response_model=UserResponse)
        async def get_current_user_info(current_user: CurrentUser = Depends(get_current_user)):
            """
            Get current authenticated user information

            **Headers:**
            - Authorization: Bearer {access_token}

            **Response:**
            - User information

            **Status Codes:**
            - 200: Success
            - 401: Unauthorized (invalid or expired token)
            """
            # Get user from database
            user = None
            for u in MOCK_USERS.values():
                if u["id"] == current_user.id:
                    user = u
                    break

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            return UserResponse(
                id=user["id"],
                email=user["email"],
                name=user["name"],
                phone=user["phone"],
                role=user["role"],
                status=user["status"],
                created_at=user["created_at"],
                last_login=user["last_login"]
            )

        @self.router.post("/change-password")
        async def change_password(
            request: ChangePasswordRequest,
            current_user: CurrentUser = Depends(get_current_user)
        ):
            """
            Change user password

            **Headers:**
            - Authorization: Bearer {access_token}

            **Request Body:**
            - old_password: Current password
            - new_password: New password (min 8 characters)

            **Status Codes:**
            - 200: Password changed successfully
            - 400: Invalid old password
            - 401: Unauthorized
            """
            # Get user
            user = None
            for u in MOCK_USERS.values():
                if u["id"] == current_user.id:
                    user = u
                    break

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Verify old password
            if not JWTUtils.verify_password(request.old_password, user["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid old password"
                )

            # Hash new password
            new_password_hash = JWTUtils.hash_password(request.new_password)

            # Update password (in real app, update database)
            user["password_hash"] = new_password_hash

            return {"message": "Password changed successfully"}

        @self.router.post("/logout")
        async def logout(current_user: CurrentUser = Depends(get_current_user)):
            """
            Logout user (revoke tokens)

            In a real implementation, this would:
            1. Add the access token to a blacklist
            2. Revoke the associated refresh token in database

            **Headers:**
            - Authorization: Bearer {access_token}

            **Status Codes:**
            - 200: Logged out successfully
            - 401: Unauthorized
            """
            # TODO: Implement token blacklist or revocation
            # For now, just return success
            # Client should delete tokens from storage

            return {"message": "Logged out successfully"}

        # ================================================================
        # Admin Routes
        # ================================================================

        @self.router.get("/users", response_model=list[UserResponse])
        async def list_users(current_user: CurrentUser = Depends(require_admin)):
            """
            List all users (Admin only)

            **Headers:**
            - Authorization: Bearer {admin_access_token}

            **Response:**
            - List of all users

            **Status Codes:**
            - 200: Success
            - 401: Unauthorized
            - 403: Forbidden (not admin)
            """
            users = []
            for user in MOCK_USERS.values():
                users.append(UserResponse(
                    id=user["id"],
                    email=user["email"],
                    name=user["name"],
                    phone=user["phone"],
                    role=user["role"],
                    status=user["status"],
                    created_at=user["created_at"],
                    last_login=user["last_login"]
                ))

            return users


# Create router instance
def create_auth_router() -> APIRouter:
    """Factory function to create auth router"""
    return AuthRouter().router
