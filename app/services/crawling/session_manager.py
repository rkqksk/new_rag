"""
Session Manager

Manages authenticated sessions with cookie persistence and validation.

Features:
- Cookie persistence (save/load)
- Session validation
- Automatic session refresh
- Session reuse (avoid repeated logins)
- Multiple session storage
"""

import asyncio
import logging
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class SessionInfo:
    """Session metadata"""

    name: str
    created_at: datetime
    last_used: datetime
    last_validated: Optional[datetime] = None
    valid: bool = True
    validation_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionManager:
    """
    Session Manager for crawling

    Manages authenticated sessions with persistence.

    Example:
        >>> manager = SessionManager()
        >>>
        >>> # Save session
        >>> client = await authenticate_basic('user', 'pass')
        >>> manager.save_session('my-portal', client)
        >>>
        >>> # Load session later
        >>> client = manager.load_session('my-portal')
        >>> if client:
        >>>     # Session exists, verify it's still valid
        >>>     if await manager.verify_session(client, 'https://portal.com/dashboard'):
        >>>         # Use session
        >>>         response = await client.get('https://portal.com/data')
        >>>     else:
        >>>         # Session expired, re-login
        >>>         client = await authenticate_basic('user', 'pass')
        >>>         manager.save_session('my-portal', client)
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize session manager

        Args:
            storage_dir: Directory to store session data (default: .sessions/)
        """
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path.home() / ".rag-enterprise" / "sessions"

        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory session info
        self._session_info: Dict[str, SessionInfo] = {}

        logger.info(f"Session manager initialized (storage: {self.storage_dir})")

    def _get_session_path(self, name: str) -> Path:
        """Get file path for session"""
        # Sanitize session name
        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_"))
        return self.storage_dir / f"{safe_name}.session"

    def _get_info_path(self, name: str) -> Path:
        """Get file path for session info"""
        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_"))
        return self.storage_dir / f"{safe_name}.info"

    def save_session(
        self,
        name: str,
        client: httpx.AsyncClient,
        validation_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Save session cookies to disk

        Args:
            name: Session name (unique identifier)
            client: HTTP client with cookies
            validation_url: URL to check if session is still valid
            metadata: Additional metadata to store
        """
        session_path = self._get_session_path(name)
        info_path = self._get_info_path(name)

        try:
            # Save cookies
            with open(session_path, "wb") as f:
                pickle.dump(client.cookies, f)

            # Save session info
            info = SessionInfo(
                name=name,
                created_at=datetime.now(),
                last_used=datetime.now(),
                last_validated=datetime.now(),
                valid=True,
                validation_url=validation_url,
                metadata=metadata or {},
            )

            with open(info_path, "wb") as f:
                pickle.dump(info, f)

            self._session_info[name] = info

            logger.info(f"Session saved: {name}")

        except Exception as e:
            logger.error(f"Error saving session {name}: {e}")
            raise

    def load_session(self, name: str) -> Optional[httpx.AsyncClient]:
        """
        Load session from disk

        Args:
            name: Session name

        Returns:
            HTTP client with loaded cookies, or None if not found
        """
        session_path = self._get_session_path(name)
        info_path = self._get_info_path(name)

        if not session_path.exists():
            logger.debug(f"Session not found: {name}")
            return None

        try:
            # Load cookies
            with open(session_path, "rb") as f:
                cookies = pickle.load(f)

            # Load session info
            if info_path.exists():
                with open(info_path, "rb") as f:
                    info = pickle.load(f)
                    info.last_used = datetime.now()
                    self._session_info[name] = info

                    # Save updated last_used
                    with open(info_path, "wb") as f:
                        pickle.dump(info, f)

            # Create client with loaded cookies
            client = httpx.AsyncClient(cookies=cookies)

            logger.info(f"Session loaded: {name}")
            return client

        except Exception as e:
            logger.error(f"Error loading session {name}: {e}")
            return None

    async def verify_session(
        self, client: httpx.AsyncClient, validation_url: str, expected_status: int = 200
    ) -> bool:
        """
        Verify session is still valid

        Args:
            client: HTTP client with session
            validation_url: URL to test
            expected_status: Expected HTTP status for valid session

        Returns:
            True if session is valid, False otherwise
        """
        try:
            response = await client.get(validation_url, follow_redirects=False)

            # Check for redirect to login page
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("location", "")
                if "login" in location.lower():
                    logger.warning(f"Session expired (redirected to login)")
                    return False

            # Check status code
            valid = response.status_code == expected_status

            if valid:
                logger.info(f"Session valid: {validation_url} returned {response.status_code}")
            else:
                logger.warning(f"Session invalid: {validation_url} returned {response.status_code}")

            return valid

        except Exception as e:
            logger.error(f"Error verifying session: {e}")
            return False

    async def get_or_create_session(
        self,
        name: str,
        validation_url: str,
        login_func: Callable[[], httpx.AsyncClient],
        max_age_hours: int = 24,
        force_refresh: bool = False,
    ) -> httpx.AsyncClient:
        """
        Get existing session or create new one

        Smart session management:
        1. Load session from disk
        2. Verify it's still valid
        3. If invalid or too old, re-login
        4. Save and return session

        Args:
            name: Session name
            validation_url: URL to verify session
            login_func: Async function to create new session (should return httpx.AsyncClient)
            max_age_hours: Maximum session age in hours
            force_refresh: Force new login even if session exists

        Returns:
            Valid HTTP client session

        Example:
            >>> async def login():
            >>>     return await authenticate_basic('user', 'pass')
            >>>
            >>> client = await manager.get_or_create_session(
            >>>     name='my-portal',
            >>>     validation_url='https://portal.com/dashboard',
            >>>     login_func=login
            >>> )
        """
        if not force_refresh:
            # Try to load existing session
            client = self.load_session(name)

            if client:
                # Check session age
                info = self._session_info.get(name)
                if info:
                    age = datetime.now() - info.created_at
                    if age > timedelta(hours=max_age_hours):
                        logger.info(
                            f"Session {name} too old ({age.total_seconds() / 3600:.1f} hours), refreshing"
                        )
                        await client.aclose()
                        client = None

                # Verify session is still valid
                if client and await self.verify_session(client, validation_url):
                    logger.info(f"Using existing session: {name}")
                    return client
                elif client:
                    logger.info(f"Session {name} invalid, creating new session")
                    await client.aclose()

        # Create new session
        logger.info(f"Creating new session: {name}")
        client = await login_func()

        # Verify new session works
        if not await self.verify_session(client, validation_url):
            raise Exception(f"New session for {name} is invalid!")

        # Save session
        self.save_session(name, client, validation_url=validation_url)

        return client

    def delete_session(self, name: str):
        """
        Delete stored session

        Args:
            name: Session name
        """
        session_path = self._get_session_path(name)
        info_path = self._get_info_path(name)

        if session_path.exists():
            session_path.unlink()
            logger.info(f"Deleted session file: {name}")

        if info_path.exists():
            info_path.unlink()
            logger.info(f"Deleted session info: {name}")

        if name in self._session_info:
            del self._session_info[name]

    def list_sessions(self) -> Dict[str, SessionInfo]:
        """
        List all stored sessions

        Returns:
            Dictionary of session name -> SessionInfo
        """
        sessions = {}

        for session_file in self.storage_dir.glob("*.info"):
            try:
                with open(session_file, "rb") as f:
                    info = pickle.load(f)
                    sessions[info.name] = info
            except Exception as e:
                logger.error(f"Error loading session info {session_file}: {e}")

        return sessions

    def cleanup_old_sessions(self, max_age_days: int = 30):
        """
        Delete sessions older than max_age_days

        Args:
            max_age_days: Maximum age in days
        """
        cutoff = datetime.now() - timedelta(days=max_age_days)

        sessions = self.list_sessions()

        for name, info in sessions.items():
            if info.last_used < cutoff:
                logger.info(f"Deleting old session: {name} (last used: {info.last_used})")
                self.delete_session(name)

    async def refresh_session(
        self,
        name: str,
        login_func: Callable[[], httpx.AsyncClient],
        validation_url: Optional[str] = None,
    ) -> httpx.AsyncClient:
        """
        Force refresh a session

        Args:
            name: Session name
            login_func: Function to create new session
            validation_url: URL to verify new session

        Returns:
            New session client
        """
        # Delete old session
        self.delete_session(name)

        # Create new session
        client = await login_func()

        # Verify if validation_url provided
        if validation_url:
            if not await self.verify_session(client, validation_url):
                raise Exception(f"New session for {name} is invalid!")

        # Save session
        self.save_session(name, client, validation_url=validation_url)

        logger.info(f"Session refreshed: {name}")
        return client

    def get_session_info(self, name: str) -> Optional[SessionInfo]:
        """
        Get session metadata

        Args:
            name: Session name

        Returns:
            SessionInfo or None
        """
        # Check in-memory first
        if name in self._session_info:
            return self._session_info[name]

        # Load from disk
        info_path = self._get_info_path(name)
        if not info_path.exists():
            return None

        try:
            with open(info_path, "rb") as f:
                info = pickle.load(f)
                self._session_info[name] = info
                return info
        except Exception as e:
            logger.error(f"Error loading session info {name}: {e}")
            return None


# Convenience functions
async def with_session(
    name: str,
    validation_url: str,
    login_func: Callable[[], httpx.AsyncClient],
    operation: Callable[[httpx.AsyncClient], Any],
    manager: Optional[SessionManager] = None,
) -> Any:
    """
    Execute operation with managed session

    Automatically handles session loading, validation, and refresh.

    Args:
        name: Session name
        validation_url: URL to verify session
        login_func: Function to create new session
        operation: Async function to execute with session
        manager: Session manager (creates new if None)

    Returns:
        Result of operation()

    Example:
        >>> async def login():
        >>>     return await authenticate_basic('user', 'pass')
        >>>
        >>> async def fetch_data(client):
        >>>     response = await client.get('https://portal.com/data')
        >>>     return response.json()
        >>>
        >>> data = await with_session(
        >>>     name='my-portal',
        >>>     validation_url='https://portal.com/dashboard',
        >>>     login_func=login,
        >>>     operation=fetch_data
        >>> )
    """
    if manager is None:
        manager = SessionManager()

    client = await manager.get_or_create_session(
        name=name, validation_url=validation_url, login_func=login_func
    )

    try:
        return await operation(client)
    finally:
        # Don't close - session manager owns the client
        pass
