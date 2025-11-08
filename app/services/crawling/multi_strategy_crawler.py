"""
Multi-Strategy Crawler

Intelligent crawler that auto-selects the best crawling method:
- Static (BeautifulSoup) - Fast for simple HTML
- Dynamic (Playwright) - JavaScript rendering
- API - Direct API access (recommended)

Features:
- Auto-detection of site type
- Fallback strategy if primary fails
- Integrated authentication
- Anti-bot evasion
- Session management
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from urllib.parse import urlparse

from .static_crawler import StaticCrawler, StaticCrawlerConfig
from .dynamic_crawler import DynamicCrawler, PlaywrightConfig
from .auth_manager import AuthenticationManager, AuthType, AuthCredentials
from .session_manager import SessionManager
from .evasion import AntiDetectionManager, EvasionConfig, RateLimiter

logger = logging.getLogger(__name__)


class CrawlMethod(Enum):
    """Crawling method"""
    AUTO = "auto"  # Auto-detect
    STATIC = "static"  # BeautifulSoup
    DYNAMIC = "dynamic"  # Playwright
    API = "api"  # Direct API


@dataclass
class CrawlConfig:
    """Comprehensive crawl configuration"""

    # Method selection
    method: CrawlMethod = CrawlMethod.AUTO
    fallback_enabled: bool = True  # Fallback to dynamic if static fails

    # Static crawler config
    static_config: Optional[StaticCrawlerConfig] = None

    # Dynamic crawler config
    dynamic_config: Optional[PlaywrightConfig] = None

    # Authentication
    auth_type: Optional[AuthType] = None
    auth_credentials: Optional[AuthCredentials] = None

    # Anti-detection
    evasion_config: Optional[EvasionConfig] = None
    use_evasion: bool = True

    # Rate limiting
    rate_limit_requests: int = 10
    rate_limit_window: float = 60.0

    # Session management
    session_name: Optional[str] = None
    validation_url: Optional[str] = None

    # Timeouts
    timeout: int = 30

    # Retry
    max_retries: int = 3
    retry_delay: float = 2.0


class MultiStrategyCrawler:
    """
    Intelligent multi-strategy web crawler

    Automatically selects the best crawling method and handles:
    - Method auto-detection
    - Authentication
    - Anti-bot evasion
    - Session management
    - Rate limiting
    - Fallback strategies

    Example:
        >>> crawler = MultiStrategyCrawler()
        >>>
        >>> # Auto-detect method
        >>> result = await crawler.crawl('https://react-app.com')
        >>>
        >>> # Force specific method
        >>> result = await crawler.crawl(
        ...     'https://api.example.com/data',
        ...     method=CrawlMethod.STATIC
        ... )
        >>>
        >>> # With authentication
        >>> config = CrawlConfig(
        ...     auth_type=AuthType.API_KEY,
        ...     auth_credentials=AuthCredentials(api_key='your-key')
        ... )
        >>> crawler = MultiStrategyCrawler(config)
        >>> result = await crawler.crawl('https://api.example.com/protected')
    """

    # JavaScript framework indicators
    JS_FRAMEWORK_INDICATORS = [
        'react', 'vue', 'angular', 'ember', 'backbone',
        'next.js', 'nuxt', 'gatsby', 'svelte'
    ]

    # API endpoint indicators
    API_INDICATORS = [
        '/api/', '/v1/', '/v2/', '/v3/',
        '/graphql', '/rest/', '/json'
    ]

    def __init__(self, config: Optional[CrawlConfig] = None):
        self.config = config or CrawlConfig()

        # Initialize components
        self.static_crawler = StaticCrawler(
            self.config.static_config or StaticCrawlerConfig()
        )

        # Dynamic crawler initialized on demand (resource-intensive)
        self._dynamic_crawler: Optional[DynamicCrawler] = None

        # Auth manager
        self.auth_manager = AuthenticationManager()

        # Session manager
        self.session_manager = SessionManager()

        # Anti-detection
        if self.config.use_evasion:
            self.evasion_manager = AntiDetectionManager(
                self.config.evasion_config or EvasionConfig()
            )
        else:
            self.evasion_manager = None

        # Rate limiter
        self.rate_limiter = RateLimiter(
            max_requests=self.config.rate_limit_requests,
            time_window=self.config.rate_limit_window
        )

        # Statistics
        self.stats = {
            'total_requests': 0,
            'static_requests': 0,
            'dynamic_requests': 0,
            'api_requests': 0,
            'failed_requests': 0,
            'fallbacks': 0
        }

        logger.info("Multi-strategy crawler initialized")

    @property
    def dynamic_crawler(self) -> DynamicCrawler:
        """Lazy-load dynamic crawler"""
        if self._dynamic_crawler is None:
            self._dynamic_crawler = DynamicCrawler(
                self.config.dynamic_config or PlaywrightConfig()
            )
        return self._dynamic_crawler

    async def detect_method(self, url: str) -> CrawlMethod:
        """
        Auto-detect best crawling method

        Args:
            url: Target URL

        Returns:
            Recommended crawling method
        """
        url_lower = url.lower()
        parsed = urlparse(url)

        # Check for API endpoints
        if any(indicator in url_lower for indicator in self.API_INDICATORS):
            logger.info(f"Detected API endpoint: {url}")
            return CrawlMethod.STATIC  # Use static for API (no rendering needed)

        # Check for JavaScript frameworks in URL
        if any(framework in url_lower for framework in self.JS_FRAMEWORK_INDICATORS):
            logger.info(f"Detected JavaScript framework in URL: {url}")
            return CrawlMethod.DYNAMIC

        # Try a quick static fetch to check for JS frameworks
        try:
            result = await self.static_crawler.crawl(url, parse_html=False)
            content = result['text'].lower()

            # Check for JavaScript framework signatures in HTML
            js_indicators = [
                'data-react', 'ng-app', 'v-app', 'data-vue',
                'react.js', 'vue.js', 'angular.js',
                '__NEXT_DATA__', '__NUXT__'
            ]

            if any(indicator in content for indicator in js_indicators):
                logger.info(f"Detected JavaScript framework in HTML: {url}")
                return CrawlMethod.DYNAMIC

            # Check if content is mostly empty (likely needs JS)
            text_content = result['content'].get_text(strip=True) if result.get('content') else ''
            if len(text_content) < 100:
                logger.info(f"Little content detected, likely requires JS: {url}")
                return CrawlMethod.DYNAMIC

            # Static HTML should work
            logger.info(f"Static HTML detected: {url}")
            return CrawlMethod.STATIC

        except Exception as e:
            logger.warning(f"Error detecting method for {url}: {e}")
            # Default to static (faster)
            return CrawlMethod.STATIC

    async def crawl(
        self,
        url: str,
        method: Optional[CrawlMethod] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Crawl a URL with auto-detection

        Args:
            url: Target URL
            method: Crawling method (None for auto-detect)
            **kwargs: Additional arguments for crawlers

        Returns:
            Crawl result dictionary
        """
        # Rate limiting
        await self.rate_limiter.acquire()

        # Stats
        self.stats['total_requests'] += 1

        # Determine method
        if method is None or method == CrawlMethod.AUTO:
            method = await self.detect_method(url)

        logger.info(f"Crawling {url} with method: {method.value}")

        # Apply evasion
        if self.evasion_manager:
            await self.evasion_manager.human_delay()

        # Crawl with selected method
        try:
            if method == CrawlMethod.STATIC:
                result = await self._crawl_static(url, **kwargs)
                self.stats['static_requests'] += 1

            elif method == CrawlMethod.DYNAMIC:
                result = await self._crawl_dynamic(url, **kwargs)
                self.stats['dynamic_requests'] += 1

            elif method == CrawlMethod.API:
                result = await self._crawl_api(url, **kwargs)
                self.stats['api_requests'] += 1

            else:
                raise ValueError(f"Unknown crawl method: {method}")

            # Add metadata
            result['crawl_method'] = method.value
            result['crawl_config'] = {
                'evasion_enabled': self.config.use_evasion,
                'auth_enabled': self.config.auth_type is not None,
                'session_enabled': self.config.session_name is not None
            }

            return result

        except Exception as e:
            logger.error(f"Error crawling {url} with {method.value}: {e}")

            # Fallback to dynamic if static failed
            if self.config.fallback_enabled and method == CrawlMethod.STATIC:
                logger.info(f"Falling back to dynamic crawling for {url}")
                self.stats['fallbacks'] += 1

                try:
                    result = await self._crawl_dynamic(url, **kwargs)
                    result['crawl_method'] = 'dynamic_fallback'
                    self.stats['dynamic_requests'] += 1
                    return result
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")

            self.stats['failed_requests'] += 1
            raise

    async def _crawl_static(self, url: str, **kwargs) -> Dict[str, Any]:
        """Crawl with static method"""

        # Apply evasion headers
        if self.evasion_manager:
            # Note: Static crawler handles headers internally, but we can pass extra_headers
            pass

        return await self.static_crawler.crawl(url, **kwargs)

    async def _crawl_dynamic(self, url: str, **kwargs) -> Dict[str, Any]:
        """Crawl with dynamic method"""
        return await self.dynamic_crawler.crawl(url, **kwargs)

    async def _crawl_api(self, url: str, **kwargs) -> Dict[str, Any]:
        """Crawl API endpoint"""
        # For API, use static crawler but with API-specific settings
        return await self.static_crawler.crawl(url, parse_html=False, **kwargs)

    async def crawl_multiple(
        self,
        urls: List[str],
        method: Optional[CrawlMethod] = None,
        concurrent_limit: int = 3,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Crawl multiple URLs

        Args:
            urls: List of URLs
            method: Crawling method (None for auto-detect per URL)
            concurrent_limit: Maximum concurrent requests
            **kwargs: Additional arguments

        Returns:
            List of crawl results
        """
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def crawl_with_semaphore(url: str) -> Dict[str, Any]:
            async with semaphore:
                try:
                    return await self.crawl(url, method=method, **kwargs)
                except Exception as e:
                    logger.error(f"Error crawling {url}: {e}")
                    return {
                        'url': url,
                        'error': str(e),
                        'content': None,
                        'crawl_method': 'failed'
                    }

        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks)

        return results

    async def crawl_with_auth(
        self,
        url: str,
        auth_type: AuthType,
        credentials: AuthCredentials,
        login_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Crawl with authentication

        Args:
            url: Target URL
            auth_type: Authentication type
            credentials: Auth credentials
            login_url: Login page URL (for form auth)
            **kwargs: Additional arguments

        Returns:
            Crawl result
        """
        logger.info(f"Crawling with authentication: {auth_type.value}")

        # Authenticate
        session = await self.auth_manager.authenticate(
            auth_type=auth_type,
            credentials=credentials,
            login_url=login_url
        )

        # TODO: Integrate authenticated session with crawlers
        # For now, just log that auth happened

        return await self.crawl(url, **kwargs)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get crawler statistics

        Returns:
            Statistics dictionary
        """
        stats = dict(self.stats)

        if self.evasion_manager:
            stats['evasion'] = self.evasion_manager.get_stats()

        stats['rate_limit'] = {
            'current_rate': self.rate_limiter.get_current_rate(),
            'max_requests': self.config.rate_limit_requests,
            'time_window': self.config.rate_limit_window
        }

        return stats

    async def close(self):
        """Cleanup resources"""
        if self._dynamic_crawler:
            await self._dynamic_crawler.close()

        logger.info("Multi-strategy crawler closed")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Convenience functions
async def crawl_smart(url: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function for smart crawling with auto-detection

    Example:
        >>> result = await crawl_smart('https://react-app.com')
        >>> print(result['title'])
    """
    async with MultiStrategyCrawler() as crawler:
        return await crawler.crawl(url, **kwargs)


async def crawl_with_config(
    url: str,
    config: CrawlConfig,
    **kwargs
) -> Dict[str, Any]:
    """
    Crawl with custom configuration

    Example:
        >>> config = CrawlConfig(
        ...     method=CrawlMethod.DYNAMIC,
        ...     use_evasion=True
        ... )
        >>> result = await crawl_with_config('https://example.com', config)
    """
    async with MultiStrategyCrawler(config) as crawler:
        return await crawler.crawl(url, **kwargs)
