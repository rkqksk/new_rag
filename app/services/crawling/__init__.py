"""
Advanced Crawling Services

Multi-strategy crawling with authentication, anti-bot evasion, and session management.
"""

from .auth_manager import AuthCredentials, AuthenticationManager, AuthType
from .dynamic_crawler import DynamicCrawler, PlaywrightConfig
from .evasion import AntiDetectionManager, EvasionStrategy
from .manual_auth import ManualAuthHandler, auto_or_manual_login, manual_login_once
from .multi_strategy_crawler import CrawlConfig, CrawlMethod, MultiStrategyCrawler
from .robots_handler import RobotsHandler, RobotsPolicy, bypass_robots, check_robots
from .session_manager import SessionManager
from .static_crawler import StaticCrawler

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
    "ManualAuthHandler",
    "manual_login_once",
    "auto_or_manual_login",
    "RobotsHandler",
    "RobotsPolicy",
    "check_robots",
    "bypass_robots",
]
