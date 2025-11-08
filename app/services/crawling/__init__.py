"""
Advanced Crawling Services

Multi-strategy crawling with authentication, anti-bot evasion, and session management.
"""

from .dynamic_crawler import DynamicCrawler, PlaywrightConfig
from .static_crawler import StaticCrawler
from .auth_manager import AuthenticationManager, AuthType, AuthCredentials
from .session_manager import SessionManager
from .evasion import AntiDetectionManager, EvasionStrategy
from .multi_strategy_crawler import MultiStrategyCrawler, CrawlMethod, CrawlConfig

__all__ = [
    "DynamicCrawler",
    "PlaywrightConfig",
    "StaticCrawler",
    "AuthenticationManager",
    "AuthType",
    "AuthCredentials",
    "SessionManager",
    "AntiDetectionManager",
    "EvasionStrategy",
    "MultiStrategyCrawler",
    "CrawlMethod",
    "CrawlConfig",
]
