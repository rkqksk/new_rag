"""
Authentication Manager

Handles various authentication methods for web crawling:
- HTTP Basic Authentication
- Form-based login with cookies
- OAuth 2.0 flow
- TOTP/2FA (AUTHORIZED USE ONLY)
- API Keys

⚠️  LEGAL NOTICE:
2FA bypass is ILLEGAL without explicit authorization!
Only use for:
- Your own accounts
- Company systems (IT automation)
- With written permission
- Service accounts

NEVER use for unauthorized access!
"""

import asyncio
import base64
import hashlib
import logging
import secrets
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional

import httpx
import pyotp
from requests_oauthlib import OAuth2Session

logger = logging.getLogger(__name__)


class AuthType(Enum):
    """Authentication method types"""

    BASIC = "basic"  # HTTP Basic Auth
    FORM = "form"  # Form-based login
    OAUTH = "oauth"  # OAuth 2.0
    TOTP = "totp"  # Time-based One-Time Password (2FA)
    API_KEY = "api_key"  # API Key authentication
    BEARER = "bearer"  # Bearer token


@dataclass
class AuthCredentials:
    """Authentication credentials"""

    # Basic / Form auth
    username: Optional[str] = None
    password: Optional[str] = None

    # TOTP (2FA) - AUTHORIZED USE ONLY
    totp_secret: Optional[str] = None

    # OAuth 2.0
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None
    auth_url: Optional[str] = None
    token_url: Optional[str] = None
    scope: Optional[str] = None

    # API Key
    api_key: Optional[str] = None
    api_key_header: str = "X-API-Key"

    # Bearer token
    bearer_token: Optional[str] = None

    # Custom headers
    extra_headers: Optional[Dict[str, str]] = None


class AuthenticationManager:
    """
    Authentication Manager for web crawling

    Example:
        >>> # Basic Auth
        >>> auth = AuthenticationManager()
        >>> creds = AuthCredentials(username="user", password="pass")
        >>> session = await auth.authenticate(AuthType.BASIC, creds)
        >>>
        >>> # TOTP (2FA) - Own accounts only!
        >>> creds = AuthCredentials(
        ...     username="user",
        ...     password="pass",
        ...     totp_secret="BASE32SECRET"
        ... )
        >>> session = await auth.authenticate(AuthType.TOTP, creds)
        >>>
        >>> # API Key (RECOMMENDED)
        >>> creds = AuthCredentials(api_key="your-api-key")
        >>> headers = auth.get_api_key_headers(creds)
    """

    def __init__(self):
        self._sessions: Dict[str, httpx.AsyncClient] = {}

    async def authenticate(
        self,
        auth_type: AuthType,
        credentials: AuthCredentials,
        login_url: Optional[str] = None,
        form_selectors: Optional[Dict[str, str]] = None,
    ) -> httpx.AsyncClient:
        """
        Authenticate and return session

        Args:
            auth_type: Authentication method
            credentials: Auth credentials
            login_url: Login page URL (for form auth)
            form_selectors: Form field selectors (for form auth)

        Returns:
            Authenticated HTTP client session
        """
        if auth_type == AuthType.BASIC:
            return await self._basic_auth(credentials)

        elif auth_type == AuthType.FORM:
            if not login_url:
                raise ValueError("login_url required for form authentication")
            return await self._form_auth(credentials, login_url, form_selectors)

        elif auth_type == AuthType.OAUTH:
            return await self._oauth_auth(credentials)

        elif auth_type == AuthType.TOTP:
            logger.warning("⚠️  TOTP 2FA - Ensure you have authorization!")
            if not login_url:
                raise ValueError("login_url required for TOTP authentication")
            return await self._totp_auth(credentials, login_url, form_selectors)

        elif auth_type == AuthType.API_KEY:
            return self._api_key_session(credentials)

        elif auth_type == AuthType.BEARER:
            return self._bearer_token_session(credentials)

        else:
            raise ValueError(f"Unsupported auth type: {auth_type}")

    async def _basic_auth(self, credentials: AuthCredentials) -> httpx.AsyncClient:
        """HTTP Basic Authentication"""
        if not credentials.username or not credentials.password:
            raise ValueError("Username and password required for basic auth")

        logger.info(f"Authenticating with Basic Auth (user: {credentials.username})")

        # Create auth tuple
        auth = (credentials.username, credentials.password)

        # Create session with auth
        client = httpx.AsyncClient(auth=auth)

        logger.info("Basic auth session created")
        return client

    async def _form_auth(
        self,
        credentials: AuthCredentials,
        login_url: str,
        form_selectors: Optional[Dict[str, str]] = None,
    ) -> httpx.AsyncClient:
        """
        Form-based login with cookies

        Args:
            credentials: Username + password
            login_url: Login page URL
            form_selectors: Form field names (username_field, password_field, submit_url)
        """
        if not credentials.username or not credentials.password:
            raise ValueError("Username and password required for form auth")

        logger.info(f"Authenticating with form login at {login_url}")

        # Default selectors
        selectors = form_selectors or {}
        username_field = selectors.get("username_field", "username")
        password_field = selectors.get("password_field", "password")
        submit_url = selectors.get("submit_url", login_url)

        # Create session
        client = httpx.AsyncClient()

        try:
            # Submit login form
            response = await client.post(
                submit_url,
                data={username_field: credentials.username, password_field: credentials.password},
                follow_redirects=True,
            )

            response.raise_for_status()

            # Check if login succeeded (basic check)
            if "login" in response.url.path.lower() and response.status_code == 200:
                logger.warning("Login might have failed (still on login page)")
            else:
                logger.info(f"Form login successful (redirected to: {response.url})")

            return client

        except Exception as e:
            logger.error(f"Form login failed: {e}")
            await client.aclose()
            raise

    async def _oauth_auth(self, credentials: AuthCredentials) -> httpx.AsyncClient:
        """
        OAuth 2.0 authentication

        Note: This is a simplified OAuth flow.
        Full implementation requires a web server for redirect callback.
        """
        if not all(
            [
                credentials.client_id,
                credentials.client_secret,
                credentials.redirect_uri,
                credentials.auth_url,
                credentials.token_url,
            ]
        ):
            raise ValueError(
                "OAuth requires: client_id, client_secret, redirect_uri, auth_url, token_url"
            )

        logger.info("Starting OAuth 2.0 flow")

        oauth = OAuth2Session(
            credentials.client_id, redirect_uri=credentials.redirect_uri, scope=credentials.scope
        )

        # Get authorization URL
        authorization_url, state = oauth.authorization_url(credentials.auth_url)

        logger.info(f"Authorization URL: {authorization_url}")
        logger.warning(
            "⚠️  OAuth flow requires manual authorization. Visit URL and get callback code."
        )

        # In a real implementation, you'd:
        # 1. Open authorization_url in browser
        # 2. User authorizes
        # 3. Capture redirect callback with code
        # 4. Exchange code for token

        # For now, return a placeholder
        # TODO: Implement full OAuth flow with callback server
        raise NotImplementedError(
            "Full OAuth flow requires a callback server. "
            "Please use API keys or implement a custom OAuth handler."
        )

    async def _totp_auth(
        self,
        credentials: AuthCredentials,
        login_url: str,
        form_selectors: Optional[Dict[str, str]] = None,
    ) -> httpx.AsyncClient:
        """
        TOTP (2FA) authentication

        ⚠️  LEGAL WARNING:
        Only use this for AUTHORIZED automation:
        - Your own accounts
        - Company systems with permission
        - Service accounts

        NEVER use for unauthorized access!
        """
        if not all([credentials.username, credentials.password, credentials.totp_secret]):
            raise ValueError("TOTP requires: username, password, totp_secret")

        logger.warning("⚠️  TOTP 2FA Authentication - Ensure you have authorization!")

        # Generate TOTP code
        totp = pyotp.TOTP(credentials.totp_secret)
        totp_code = totp.now()

        logger.info(f"Generated TOTP code: {totp_code} (valid for ~30 seconds)")

        # First, do normal login
        selectors = form_selectors or {}
        client = await self._form_auth(credentials, login_url, selectors)

        # Then submit TOTP code
        totp_url = selectors.get("totp_url", login_url)
        totp_field = selectors.get("totp_field", "totp_code")

        try:
            response = await client.post(
                totp_url, data={totp_field: totp_code}, follow_redirects=True
            )

            response.raise_for_status()

            logger.info("TOTP authentication successful")
            return client

        except Exception as e:
            logger.error(f"TOTP authentication failed: {e}")
            await client.aclose()
            raise

    def _api_key_session(self, credentials: AuthCredentials) -> httpx.AsyncClient:
        """
        API Key authentication (RECOMMENDED)

        This is the PREFERRED method - no scraping needed!
        """
        if not credentials.api_key:
            raise ValueError("API key required for API key auth")

        logger.info("Creating API key authenticated session")

        headers = {credentials.api_key_header: credentials.api_key}

        if credentials.extra_headers:
            headers.update(credentials.extra_headers)

        client = httpx.AsyncClient(headers=headers)

        logger.info("API key session created")
        return client

    def _bearer_token_session(self, credentials: AuthCredentials) -> httpx.AsyncClient:
        """Bearer token authentication"""
        if not credentials.bearer_token:
            raise ValueError("Bearer token required")

        logger.info("Creating bearer token authenticated session")

        headers = {"Authorization": f"Bearer {credentials.bearer_token}"}

        if credentials.extra_headers:
            headers.update(credentials.extra_headers)

        client = httpx.AsyncClient(headers=headers)

        logger.info("Bearer token session created")
        return client

    def get_api_key_headers(self, credentials: AuthCredentials) -> Dict[str, str]:
        """
        Get headers for API key authentication

        Args:
            credentials: Auth credentials with api_key

        Returns:
            Headers dictionary
        """
        if not credentials.api_key:
            raise ValueError("API key required")

        headers = {credentials.api_key_header: credentials.api_key}

        if credentials.extra_headers:
            headers.update(credentials.extra_headers)

        return headers

    @staticmethod
    def generate_totp_secret() -> str:
        """
        Generate a new TOTP secret

        Use this when setting up 2FA for your own account.
        Keep this secret secure!

        Returns:
            Base32-encoded TOTP secret
        """
        secret = pyotp.random_base32()
        logger.info(f"Generated TOTP secret: {secret}")
        logger.warning(
            "⚠️  Keep this secret secure! Store in environment variable or secrets manager."
        )
        return secret

    @staticmethod
    def get_totp_provisioning_uri(secret: str, name: str, issuer: str = "RAG-Enterprise") -> str:
        """
        Get TOTP provisioning URI for QR code

        Args:
            secret: TOTP secret
            name: Account name
            issuer: Service name

        Returns:
            otpauth:// URI for QR code generation
        """
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=name, issuer_name=issuer)
        return uri

    async def verify_authentication(
        self, client: httpx.AsyncClient, test_url: str, expected_status: int = 200
    ) -> bool:
        """
        Verify authentication is working

        Args:
            client: Authenticated client
            test_url: URL to test
            expected_status: Expected HTTP status

        Returns:
            True if authenticated, False otherwise
        """
        try:
            response = await client.get(test_url)
            authenticated = response.status_code == expected_status

            if authenticated:
                logger.info(f"Authentication verified: {test_url} returned {response.status_code}")
            else:
                logger.warning(
                    f"Authentication may have failed: {test_url} returned {response.status_code}"
                )

            return authenticated

        except Exception as e:
            logger.error(f"Error verifying authentication: {e}")
            return False


# Convenience functions
async def authenticate_basic(username: str, password: str) -> httpx.AsyncClient:
    """
    Quick basic authentication

    Example:
        >>> client = await authenticate_basic('user', 'pass')
        >>> response = await client.get('https://protected-site.com')
    """
    auth_manager = AuthenticationManager()
    credentials = AuthCredentials(username=username, password=password)
    return await auth_manager.authenticate(AuthType.BASIC, credentials)


async def authenticate_api_key(api_key: str, header_name: str = "X-API-Key") -> httpx.AsyncClient:
    """
    Quick API key authentication (RECOMMENDED)

    Example:
        >>> client = await authenticate_api_key('your-api-key')
        >>> response = await client.get('https://api.example.com/data')
    """
    auth_manager = AuthenticationManager()
    credentials = AuthCredentials(api_key=api_key, api_key_header=header_name)
    return await auth_manager.authenticate(AuthType.API_KEY, credentials)
