"""
Anti-Bot Evasion Manager

Techniques to avoid bot detection:
- User-Agent rotation
- Proxy rotation
- Human-like delays
- Header randomization
- TLS fingerprint masking

Note: Use responsibly and respect robots.txt!
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class EvasionStrategy(Enum):
    """Anti-detection strategies"""

    USER_AGENT_ROTATION = "user_agent"
    PROXY_ROTATION = "proxy"
    HEADER_RANDOMIZATION = "headers"
    HUMAN_DELAYS = "delays"
    REFERRER_SPOOFING = "referrer"
    ALL = "all"


@dataclass
class EvasionConfig:
    """Anti-detection configuration"""

    # User-agent rotation
    rotate_user_agent: bool = True
    custom_user_agents: Optional[List[str]] = None

    # Proxy rotation
    use_proxies: bool = False
    proxy_list: Optional[List[str]] = None
    proxy_rotation_interval: int = 10  # Rotate every N requests

    # Request delays
    min_delay: float = 1.0  # Minimum delay between requests (seconds)
    max_delay: float = 3.0  # Maximum delay between requests (seconds)
    randomize_delay: bool = True

    # Header randomization
    randomize_headers: bool = True

    # Referrer
    spoof_referrer: bool = False
    referrer_list: Optional[List[str]] = None


class AntiDetectionManager:
    """
    Anti-bot detection manager

    Features:
    - User-agent rotation
    - Proxy rotation
    - Human-like delays
    - Header randomization
    - Referrer spoofing

    Example:
        >>> config = EvasionConfig(
        ...     rotate_user_agent=True,
        ...     min_delay=2.0,
        ...     max_delay=5.0
        ... )
        >>> manager = AntiDetectionManager(config)
        >>>
        >>> # Get headers for request
        >>> headers = manager.get_headers()
        >>>
        >>> # Apply human delay
        >>> await manager.human_delay()
        >>>
        >>> # Get proxy
        >>> proxy = manager.get_proxy()
    """

    # Common user agents (desktop browsers)
    DEFAULT_USER_AGENTS = [
        # Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]

    # Common referrers
    DEFAULT_REFERRERS = [
        "https://www.google.com/",
        "https://www.bing.com/",
        "https://www.yahoo.com/",
        "https://duckduckgo.com/",
        "https://www.reddit.com/",
        "https://twitter.com/",
    ]

    def __init__(self, config: Optional[EvasionConfig] = None):
        self.config = config or EvasionConfig()

        # User agents
        if self.config.custom_user_agents:
            self.user_agents = self.config.custom_user_agents
        else:
            self.user_agents = self.DEFAULT_USER_AGENTS

        # Proxies
        self.proxies = self.config.proxy_list or []
        self._proxy_index = 0
        self._request_count = 0

        # Referrers
        if self.config.referrer_list:
            self.referrers = self.config.referrer_list
        else:
            self.referrers = self.DEFAULT_REFERRERS

        logger.info(
            f"Anti-detection manager initialized (strategies: {self._get_active_strategies()})"
        )

    def _get_active_strategies(self) -> List[str]:
        """Get list of active evasion strategies"""
        strategies = []

        if self.config.rotate_user_agent:
            strategies.append("user-agent-rotation")

        if self.config.use_proxies and self.proxies:
            strategies.append("proxy-rotation")

        if self.config.randomize_headers:
            strategies.append("header-randomization")

        if self.config.min_delay > 0:
            strategies.append("human-delays")

        if self.config.spoof_referrer:
            strategies.append("referrer-spoofing")

        return strategies

    def get_random_user_agent(self) -> str:
        """Get random user agent"""
        return random.choice(self.user_agents)

    def get_headers(
        self, url: Optional[str] = None, extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Get request headers with anti-detection

        Args:
            url: Target URL (for referrer spoofing)
            extra_headers: Additional headers to include

        Returns:
            Headers dictionary
        """
        headers = {}

        # User-Agent
        if self.config.rotate_user_agent:
            headers["User-Agent"] = self.get_random_user_agent()
        else:
            headers["User-Agent"] = self.DEFAULT_USER_AGENTS[0]

        # Common headers to appear human
        if self.config.randomize_headers:
            headers.update(
                {
                    "Accept": random.choice(
                        [
                            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                        ]
                    ),
                    "Accept-Language": random.choice(
                        [
                            "en-US,en;q=0.9",
                            "en-US,en;q=0.5",
                            "en-GB,en;q=0.9",
                            "en-US,en;q=0.9,ko;q=0.8",
                        ]
                    ),
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": str(random.choice([1, 1, 1, 0])),  # Do Not Track (mostly 1)
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                }
            )
        else:
            headers.update(
                {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                }
            )

        # Referrer
        if self.config.spoof_referrer:
            if url:
                # Use same domain as referrer sometimes
                parsed = urlparse(url)
                if random.random() < 0.3:  # 30% chance to use same domain
                    headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"
                else:
                    headers["Referer"] = random.choice(self.referrers)
            else:
                headers["Referer"] = random.choice(self.referrers)

        # Extra headers
        if extra_headers:
            headers.update(extra_headers)

        return headers

    def get_proxy(self) -> Optional[str]:
        """
        Get proxy for request

        Returns:
            Proxy URL or None
        """
        if not self.config.use_proxies or not self.proxies:
            return None

        # Rotate proxy every N requests
        if self._request_count % self.config.proxy_rotation_interval == 0:
            self._proxy_index = (self._proxy_index + 1) % len(self.proxies)

        self._request_count += 1

        proxy = self.proxies[self._proxy_index]
        logger.debug(f"Using proxy {self._proxy_index + 1}/{len(self.proxies)}: {proxy}")

        return proxy

    async def human_delay(self, extra_delay: float = 0.0):
        """
        Apply human-like delay

        Args:
            extra_delay: Additional delay to add (seconds)
        """
        if self.config.randomize_delay:
            delay = random.uniform(self.config.min_delay, self.config.max_delay)
        else:
            delay = self.config.min_delay

        delay += extra_delay

        if delay > 0:
            logger.debug(f"Applying human delay: {delay:.2f}s")
            await asyncio.sleep(delay)

    def add_proxy(self, proxy: str):
        """
        Add proxy to rotation list

        Args:
            proxy: Proxy URL (e.g., 'http://proxy.com:8080')
        """
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            logger.info(f"Added proxy: {proxy} (total: {len(self.proxies)})")

    def remove_proxy(self, proxy: str):
        """
        Remove proxy from rotation list

        Args:
            proxy: Proxy URL
        """
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            logger.info(f"Removed proxy: {proxy} (remaining: {len(self.proxies)})")

    def add_user_agent(self, user_agent: str):
        """
        Add user agent to rotation list

        Args:
            user_agent: User agent string
        """
        if user_agent not in self.user_agents:
            self.user_agents.append(user_agent)
            logger.info(f"Added user agent (total: {len(self.user_agents)})")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get evasion manager statistics

        Returns:
            Statistics dictionary
        """
        return {
            "request_count": self._request_count,
            "user_agents_count": len(self.user_agents),
            "proxies_count": len(self.proxies),
            "current_proxy_index": self._proxy_index if self.proxies else None,
            "active_strategies": self._get_active_strategies(),
            "config": {
                "rotate_user_agent": self.config.rotate_user_agent,
                "use_proxies": self.config.use_proxies,
                "min_delay": self.config.min_delay,
                "max_delay": self.config.max_delay,
                "randomize_delay": self.config.randomize_delay,
                "spoof_referrer": self.config.spoof_referrer,
            },
        }


class RateLimiter:
    """
    Rate limiter to avoid overwhelming servers

    Example:
        >>> limiter = RateLimiter(max_requests=10, time_window=60)
        >>> await limiter.acquire()  # Wait if rate limit exceeded
    """

    def __init__(self, max_requests: int = 10, time_window: float = 60.0):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self._requests: List[float] = []

    async def acquire(self):
        """Wait until rate limit allows request"""
        now = time.time()

        # Remove old requests outside time window
        self._requests = [ts for ts in self._requests if now - ts < self.time_window]

        # Check if at limit
        if len(self._requests) >= self.max_requests:
            # Wait until oldest request expires
            oldest = self._requests[0]
            wait_time = self.time_window - (now - oldest)

            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

                # Clean up again
                now = time.time()
                self._requests = [ts for ts in self._requests if now - ts < self.time_window]

        # Record this request
        self._requests.append(time.time())

    def get_current_rate(self) -> float:
        """Get current requests per second"""
        now = time.time()
        recent = [ts for ts in self._requests if now - ts < self.time_window]
        return len(recent) / self.time_window if recent else 0.0


# Convenience functions
def get_random_headers(url: Optional[str] = None) -> Dict[str, str]:
    """
    Quick function to get randomized headers

    Example:
        >>> headers = get_random_headers()
        >>> response = requests.get(url, headers=headers)
    """
    manager = AntiDetectionManager(
        EvasionConfig(rotate_user_agent=True, randomize_headers=True, spoof_referrer=True)
    )

    return manager.get_headers(url=url)


async def with_rate_limit(max_requests: int = 10, time_window: float = 60.0):
    """
    Decorator for rate limiting

    Example:
        >>> limiter = await with_rate_limit(max_requests=5, time_window=10)
        >>> await limiter.acquire()
        >>> # Make request
    """
    return RateLimiter(max_requests=max_requests, time_window=time_window)
