"""
Keycloak OAuth2/OIDC Integration (v7.0.0)
==========================================

Enterprise SSO with Keycloak.

Features:
- OAuth2/OIDC authentication
- Role-based access control (RBAC)
- Token validation
- User management
- Group/role synchronization

Version: v7.0.0
"""

import logging
import os
from typing import Any, Dict, Optional

try:
    from keycloak import KeycloakOpenID, KeycloakAdmin
    from keycloak.exceptions import KeycloakError

    KEYCLOAK_AVAILABLE = True
except ImportError:
    KEYCLOAK_AVAILABLE = False
    KeycloakOpenID = None
    KeycloakAdmin = None

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer

logger = logging.getLogger(__name__)


# ============================================================================
# Keycloak Client
# ============================================================================


class KeycloakClient:
    """
    Keycloak OAuth2/OIDC client

    Features:
    - User authentication
    - Token validation
    - Role/permission checking
    """

    def __init__(
        self,
        server_url: str = "http://localhost:8080",
        realm: str = "master",
        client_id: str = "rag-enterprise",
        client_secret: Optional[str] = None,
    ):
        """
        Initialize Keycloak client

        Args:
            server_url: Keycloak server URL
            realm: Realm name
            client_id: Client ID
            client_secret: Client secret (optional for public clients)
        """
        if not KEYCLOAK_AVAILABLE:
            logger.warning("python-keycloak not installed. OAuth2 disabled.")
            self.openid = None
            self.admin = None
            return

        self.server_url = server_url
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret

        try:
            # Initialize OpenID client
            self.openid = KeycloakOpenID(
                server_url=server_url,
                realm_name=realm,
                client_id=client_id,
                client_secret_key=client_secret,
            )

            # Initialize admin client (if credentials available)
            admin_username = os.getenv("KEYCLOAK_ADMIN_USERNAME")
            admin_password = os.getenv("KEYCLOAK_ADMIN_PASSWORD")

            if admin_username and admin_password:
                self.admin = KeycloakAdmin(
                    server_url=server_url,
                    username=admin_username,
                    password=admin_password,
                    realm_name=realm,
                )
                logger.info("✅ Keycloak admin client initialized")
            else:
                self.admin = None
                logger.info("✅ Keycloak OpenID client initialized (no admin)")

        except Exception as e:
            logger.error(f"Failed to initialize Keycloak: {e}")
            self.openid = None
            self.admin = None

    def get_token(self, username: str, password: str) -> Dict[str, Any]:
        """
        Get access token for user

        Args:
            username: Username
            password: Password

        Returns:
            Token response with access_token, refresh_token, etc.
        """
        if not self.openid:
            raise HTTPException(status_code=503, detail="Keycloak not available")

        try:
            token = self.openid.token(username=username, password=password)
            return token
        except KeycloakError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode access token

        Args:
            token: Access token

        Returns:
            Decoded token payload
        """
        if not self.openid:
            raise HTTPException(status_code=503, detail="Keycloak not available")

        try:
            # Verify token signature and expiration
            token_info = self.openid.decode_token(
                token,
                key=self.openid.public_key(),
                options={"verify_signature": True, "verify_aud": True, "verify_exp": True},
            )
            return token_info
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
            )

    def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Get user info from access token

        Args:
            token: Access token

        Returns:
            User information
        """
        if not self.openid:
            raise HTTPException(status_code=503, detail="Keycloak not available")

        try:
            user_info = self.openid.userinfo(token)
            return user_info
        except KeycloakError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to get user info: {str(e)}",
            )

    def has_role(self, token: str, role: str) -> bool:
        """
        Check if user has specific role

        Args:
            token: Access token
            role: Role name

        Returns:
            True if user has role
        """
        try:
            token_info = self.verify_token(token)
            roles = token_info.get("realm_access", {}).get("roles", [])
            return role in roles
        except Exception:
            return False

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token

        Args:
            refresh_token: Refresh token

        Returns:
            New token response
        """
        if not self.openid:
            raise HTTPException(status_code=503, detail="Keycloak not available")

        try:
            new_token = self.openid.refresh_token(refresh_token)
            return new_token
        except KeycloakError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token refresh failed: {str(e)}",
            )

    # Admin operations
    def create_user(self, username: str, email: str, password: str, enabled: bool = True) -> str:
        """Create new user (requires admin client)"""
        if not self.admin:
            raise HTTPException(status_code=503, detail="Admin operations not available")

        try:
            user_id = self.admin.create_user(
                {
                    "username": username,
                    "email": email,
                    "enabled": enabled,
                    "credentials": [{"type": "password", "value": password, "temporary": False}],
                }
            )
            logger.info(f"Created user: {username}")
            return user_id
        except KeycloakError as e:
            raise HTTPException(status_code=400, detail=f"User creation failed: {str(e)}")

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        if not self.admin:
            return None

        try:
            users = self.admin.get_users({"username": username})
            return users[0] if users else None
        except KeycloakError:
            return None


# ============================================================================
# FastAPI Dependencies
# ============================================================================

# OAuth2 scheme
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="/oauth2/authorize",
    tokenUrl="/oauth2/token",
)

# Singleton instance
_keycloak_client: Optional[KeycloakClient] = None


def get_keycloak_client() -> KeycloakClient:
    """Get or create Keycloak client singleton"""
    global _keycloak_client

    if _keycloak_client is None:
        server_url = os.getenv("KEYCLOAK_SERVER_URL", "http://localhost:8080")
        realm = os.getenv("KEYCLOAK_REALM", "master")
        client_id = os.getenv("KEYCLOAK_CLIENT_ID", "rag-enterprise")
        client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET")

        _keycloak_client = KeycloakClient(
            server_url=server_url,
            realm=realm,
            client_id=client_id,
            client_secret=client_secret,
        )

    return _keycloak_client


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    keycloak: KeycloakClient = Depends(get_keycloak_client),
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user

    Usage:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user": user}
    """
    user_info = keycloak.get_user_info(token)
    return user_info


def require_role(role: str):
    """
    FastAPI dependency to require specific role

    Usage:
        @app.get("/admin")
        async def admin_route(user: dict = Depends(require_role("admin"))):
            return {"message": "Admin access"}
    """

    async def role_checker(
        token: str = Depends(oauth2_scheme),
        keycloak: KeycloakClient = Depends(get_keycloak_client),
    ):
        if not keycloak.has_role(token, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return keycloak.get_user_info(token)

    return role_checker


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Initialize client
    client = KeycloakClient()

    # Login
    try:
        token_response = client.get_token("admin", "admin")
        access_token = token_response["access_token"]

        # Verify token
        token_info = client.verify_token(access_token)
        print(f"Token info: {token_info}")

        # Get user info
        user_info = client.get_user_info(access_token)
        print(f"User info: {user_info}")

        # Check role
        has_admin = client.has_role(access_token, "admin")
        print(f"Has admin role: {has_admin}")

    except Exception as e:
        print(f"Error: {e}")
