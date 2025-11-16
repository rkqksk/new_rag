"""
Global Analytics System

Tracks all user searches and interactions for:
- Popular search keywords ranking
- Popular products ranking
- Search context patterns
- Trending queries
"""

import json
import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SearchEvent:
    """Single search event"""

    timestamp: datetime
    session_id: str
    query: str
    parsed_keywords: List[str]
    context: Dict[str, Any]  # Previous search context
    results_count: int


@dataclass
class ProductEvent:
    """Single product interaction event"""

    timestamp: datetime
    session_id: str
    product_id: str
    event_type: str  # 'view', 'click', 'bookmark'
    product_category: Optional[str] = None
    product_name: Optional[str] = None
    search_context: Optional[str] = None  # What query led to this


@dataclass
class KeywordStats:
    """Statistics for a keyword"""

    keyword: str
    search_count: int = 0
    total_results: int = 0
    unique_sessions: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    related_products: List[str] = field(default_factory=list)  # Product IDs
    co_occurring_keywords: Dict[str, int] = field(default_factory=dict)  # keyword -> count


@dataclass
class ProductStats:
    """Statistics for a product"""

    product_id: str
    view_count: int = 0
    click_count: int = 0
    bookmark_count: int = 0
    unique_sessions: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    search_keywords: Dict[str, int] = field(default_factory=dict)  # keyword -> count
    category: Optional[str] = None
    name: Optional[str] = None


@dataclass
class SearchContext:
    """Search context pattern"""

    pattern: str  # e.g., "bottle -> cap", "PET -> 20파이 -> cap"
    count: int = 0
    sessions: List[str] = field(default_factory=list)


class GlobalAnalytics:
    """
    Global Analytics System

    Tracks all searches and interactions across all users

    Features:
    - Keyword extraction and ranking
    - Product popularity tracking
    - Search context pattern detection
    - Trending queries
    - Database persistence
    """

    def __init__(self, database=None, redis_client=None):
        """
        Initialize global analytics

        Args:
            database: Optional database connection for persistence
            redis_client: Optional Redis client for caching
        """
        self.database = database
        self.redis_client = redis_client

        # In-memory storage (for fast access)
        self.keyword_stats: Dict[str, KeywordStats] = {}
        self.product_stats: Dict[str, ProductStats] = {}
        self.search_contexts: Dict[str, SearchContext] = {}

        # Event history (limited size)
        self.search_events: List[SearchEvent] = []
        self.product_events: List[ProductEvent] = []
        self.max_events = 10000  # Keep last 10k events in memory

        # Keyword extraction patterns
        self._init_extraction_patterns()

        logger.info("✅ GlobalAnalytics initialized")

    def _init_extraction_patterns(self):
        """Initialize keyword extraction patterns"""

        # Stop words (Korean + English)
        self.stop_words = {
            "을",
            "를",
            "이",
            "가",
            "은",
            "는",
            "의",
            "에",
            "로",
            "와",
            "과",
            "있는",
            "없는",
            "좋은",
            "나쁜",
            "주세요",
            "알려주세요",
            "찾아주세요",
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
        }

        # Meaningful keyword patterns
        self.keyword_patterns = [
            # Capacity
            (r"(\d+)\s*(ml|ML|미리|밀리)", "capacity"),
            (r"(\d+)\s*(l|L|리터)", "capacity"),
            # Neck size
            (r"(\d+)\s*파이", "neck"),
            (r"(\d+)\s*mm\s*(넥|neck)", "neck"),
            # Material
            (
                r"\b(PET|pet|페트|펫|PP|pp|PE|pe|PS|ps|PVC|pvc|유리|glass|초자|알루미늄|aluminum)\b",
                "material",
            ),
            # Category
            (
                r"\b(병|보틀|bottle|용기|container|캡|cap|뚜껑|펌프|pump|디스펜서|자|jar)\b",
                "category",
            ),
            # Supplier
            (r"\b(춘진|onehago|원하고|freemold|프리몰드|장업|jangup)\b", "supplier"),
            # Business terms
            (r"\b(MOQ|최소|가격|단가|견적|대량|도매)\b", "business"),
            # Shape/form
            (r"\b(원형|사각|타원|직사각|정사각|원통|각형)\b", "shape"),
            # Color
            (r"\b(투명|반투명|불투명|화이트|블랙|실버|골드|투명|색상)\b", "color"),
        ]

    def track_search(
        self,
        session_id: str,
        query: str,
        results_count: int,
        previous_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Track a search event

        Args:
            session_id: Session identifier
            query: Search query
            results_count: Number of results returned
            previous_context: Previous search context
        """
        timestamp = datetime.now()

        # Extract keywords
        keywords = self._extract_keywords(query)

        # Create search event
        event = SearchEvent(
            timestamp=timestamp,
            session_id=session_id,
            query=query,
            parsed_keywords=keywords,
            context=previous_context or {},
            results_count=results_count,
        )

        # Add to history
        self.search_events.append(event)
        if len(self.search_events) > self.max_events:
            self.search_events.pop(0)  # Remove oldest

        # Update keyword statistics
        for keyword in keywords:
            if keyword not in self.keyword_stats:
                self.keyword_stats[keyword] = KeywordStats(keyword=keyword, first_seen=timestamp)

            stats = self.keyword_stats[keyword]
            stats.search_count += 1
            stats.total_results += results_count
            stats.last_seen = timestamp

            # Track co-occurring keywords
            for other_keyword in keywords:
                if other_keyword != keyword:
                    stats.co_occurring_keywords[other_keyword] = (
                        stats.co_occurring_keywords.get(other_keyword, 0) + 1
                    )

        # Update search context pattern
        if previous_context and "last_query" in previous_context:
            pattern = f"{previous_context['last_query']} → {query}"
            if pattern not in self.search_contexts:
                self.search_contexts[pattern] = SearchContext(pattern=pattern)

            context = self.search_contexts[pattern]
            context.count += 1
            if session_id not in context.sessions:
                context.sessions.append(session_id)

        # Persist to database
        if self.database:
            self._persist_search_event(event)

        logger.debug(f"Tracked search: '{query}' -> {len(keywords)} keywords")

    def track_product_event(
        self,
        session_id: str,
        product_id: str,
        event_type: str,
        product: Optional[Dict[str, Any]] = None,
        search_context: Optional[str] = None,
    ):
        """
        Track a product interaction event

        Args:
            session_id: Session identifier
            product_id: Product ID
            event_type: 'view', 'click', 'bookmark'
            product: Optional product data
            search_context: Optional search query that led to this
        """
        timestamp = datetime.now()

        # Create product event
        event = ProductEvent(
            timestamp=timestamp,
            session_id=session_id,
            product_id=product_id,
            event_type=event_type,
            product_category=product.get("category") if product else None,
            product_name=product.get("name") if product else None,
            search_context=search_context,
        )

        # Add to history
        self.product_events.append(event)
        if len(self.product_events) > self.max_events:
            self.product_events.pop(0)

        # Update product statistics
        if product_id not in self.product_stats:
            self.product_stats[product_id] = ProductStats(
                product_id=product_id,
                first_seen=timestamp,
                category=product.get("category") if product else None,
                name=product.get("name") if product else None,
            )

        stats = self.product_stats[product_id]
        stats.last_seen = timestamp

        if event_type == "view":
            stats.view_count += 1
        elif event_type == "click":
            stats.click_count += 1
        elif event_type == "bookmark":
            stats.bookmark_count += 1

        # Track search keywords that led to this product
        if search_context:
            keywords = self._extract_keywords(search_context)
            for keyword in keywords:
                stats.search_keywords[keyword] = stats.search_keywords.get(keyword, 0) + 1

                # Update keyword -> product link
                if keyword in self.keyword_stats:
                    keyword_stats = self.keyword_stats[keyword]
                    if product_id not in keyword_stats.related_products:
                        keyword_stats.related_products.append(product_id)

        # Persist to database
        if self.database:
            self._persist_product_event(event)

        logger.debug(f"Tracked {event_type}: {product_id}")

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract meaningful keywords from query

        Args:
            query: Search query

        Returns:
            List of extracted keywords
        """
        keywords = []

        # Extract pattern-based keywords
        for pattern, keyword_type in self.keyword_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Join tuple elements
                    keyword = "".join(str(m) for m in match)
                else:
                    keyword = str(match)

                keyword = keyword.strip()
                if keyword and keyword.lower() not in self.stop_words:
                    keywords.append(keyword)

        # Extract individual words (fallback)
        words = re.findall(r"\b\w+\b", query)
        for word in words:
            word = word.strip()
            if (
                word
                and len(word) > 1
                and word.lower() not in self.stop_words
                and word not in keywords
            ):
                keywords.append(word)

        return keywords[:10]  # Limit to 10 keywords

    def get_top_keywords(
        self, limit: int = 20, time_window: Optional[timedelta] = None
    ) -> List[Tuple[str, int]]:
        """
        Get top keywords by search count

        Args:
            limit: Number of keywords to return
            time_window: Optional time window (e.g., last 7 days)

        Returns:
            List of (keyword, count) tuples
        """
        if time_window:
            cutoff = datetime.now() - time_window
            relevant_stats = {
                k: v for k, v in self.keyword_stats.items() if v.last_seen and v.last_seen > cutoff
            }
        else:
            relevant_stats = self.keyword_stats

        # Sort by search count
        sorted_keywords = sorted(
            relevant_stats.items(), key=lambda x: x[1].search_count, reverse=True
        )

        return [(k, v.search_count) for k, v in sorted_keywords[:limit]]

    def get_top_products(
        self, limit: int = 20, metric: str = "click", time_window: Optional[timedelta] = None
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Get top products by metric

        Args:
            limit: Number of products to return
            metric: 'view', 'click', 'bookmark'
            time_window: Optional time window

        Returns:
            List of (product_id, stats) tuples
        """
        if time_window:
            cutoff = datetime.now() - time_window
            relevant_stats = {
                k: v for k, v in self.product_stats.items() if v.last_seen and v.last_seen > cutoff
            }
        else:
            relevant_stats = self.product_stats

        # Sort by metric
        metric_map = {
            "view": lambda s: s.view_count,
            "click": lambda s: s.click_count,
            "bookmark": lambda s: s.bookmark_count,
        }

        sort_func = metric_map.get(metric, lambda s: s.click_count)

        sorted_products = sorted(
            relevant_stats.items(), key=lambda x: sort_func(x[1]), reverse=True
        )

        return [
            (
                product_id,
                {
                    "name": stats.name,
                    "category": stats.category,
                    "views": stats.view_count,
                    "clicks": stats.click_count,
                    "bookmarks": stats.bookmark_count,
                },
            )
            for product_id, stats in sorted_products[:limit]
        ]

    def get_trending_queries(
        self, time_window: timedelta = timedelta(days=7), limit: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Get trending search queries

        Args:
            time_window: Time window for trend calculation
            limit: Number of queries to return

        Returns:
            List of (query, trend_score) tuples
        """
        cutoff = datetime.now() - time_window
        recent_events = [e for e in self.search_events if e.timestamp > cutoff]

        if not recent_events:
            return []

        # Count queries
        query_counts = Counter([e.query for e in recent_events])

        # Calculate trend score (higher for recent queries)
        trend_scores = {}
        for query, count in query_counts.items():
            # Get most recent timestamp
            recent_timestamp = max(e.timestamp for e in recent_events if e.query == query)

            # Recency factor (0.0 - 1.0)
            hours_ago = (datetime.now() - recent_timestamp).total_seconds() / 3600
            recency = max(0, 1.0 - (hours_ago / (time_window.days * 24)))

            # Trend score = count * recency
            trend_scores[query] = count * (1 + recency)

        # Sort by trend score
        sorted_queries = sorted(trend_scores.items(), key=lambda x: x[1], reverse=True)

        return sorted_queries[:limit]

    def get_search_context_patterns(self, limit: int = 20) -> List[Tuple[str, int]]:
        """
        Get common search context patterns

        Args:
            limit: Number of patterns to return

        Returns:
            List of (pattern, count) tuples
        """
        sorted_patterns = sorted(
            self.search_contexts.items(), key=lambda x: x[1].count, reverse=True
        )

        return [(p, c.count) for p, c in sorted_patterns[:limit]]

    def get_related_keywords(self, keyword: str, limit: int = 5) -> List[str]:
        """
        Get keywords that co-occur with given keyword

        Args:
            keyword: Keyword to find relations for
            limit: Number of related keywords

        Returns:
            List of related keywords
        """
        if keyword not in self.keyword_stats:
            return []

        stats = self.keyword_stats[keyword]
        sorted_related = sorted(
            stats.co_occurring_keywords.items(), key=lambda x: x[1], reverse=True
        )

        return [k for k, _ in sorted_related[:limit]]

    def get_product_keywords(self, product_id: str) -> List[Tuple[str, int]]:
        """
        Get keywords used to search for a product

        Args:
            product_id: Product ID

        Returns:
            List of (keyword, count) tuples
        """
        if product_id not in self.product_stats:
            return []

        stats = self.product_stats[product_id]
        sorted_keywords = sorted(stats.search_keywords.items(), key=lambda x: x[1], reverse=True)

        return sorted_keywords

    def get_analytics_summary(self) -> Dict[str, Any]:
        """
        Get overall analytics summary

        Returns:
            Summary dictionary
        """
        return {
            "total_searches": len(self.search_events),
            "total_product_events": len(self.product_events),
            "unique_keywords": len(self.keyword_stats),
            "unique_products": len(self.product_stats),
            "search_contexts": len(self.search_contexts),
            "top_keywords": self.get_top_keywords(limit=10),
            "top_products": self.get_top_products(limit=10, metric="click"),
            "trending_queries": self.get_trending_queries(limit=5),
        }

    def _persist_search_event(self, event: SearchEvent):
        """Persist search event to database"""
        if not self.database:
            return

        try:
            # Insert into database
            # SQL: INSERT INTO search_events (timestamp, session_id, query, keywords, context, results_count)
            #      VALUES (?, ?, ?, ?, ?, ?)
            pass  # Implement based on your database

        except Exception as e:
            logger.error(f"Failed to persist search event: {e}")

    def _persist_product_event(self, event: ProductEvent):
        """Persist product event to database"""
        if not self.database:
            return

        try:
            # Insert into database
            # SQL: INSERT INTO product_events (timestamp, session_id, product_id, event_type, ...)
            #      VALUES (?, ?, ?, ?, ...)
            pass  # Implement based on your database

        except Exception as e:
            logger.error(f"Failed to persist product event: {e}")


# Usage example
"""
# Initialize
analytics = GlobalAnalytics(database=db, redis_client=redis)

# Track searches
analytics.track_search(
    session_id="user_001",
    query="50ml PET 병",
    results_count=15
)

analytics.track_search(
    session_id="user_001",
    query="20파이 캡",
    results_count=8,
    previous_context={'last_query': '50ml PET 병'}
)

# Track product interaction
analytics.track_product_event(
    session_id="user_001",
    product_id="prod_123",
    event_type="click",
    product={'name': '50ml PET 병', 'category': 'Bottle'},
    search_context="50ml PET 병"
)

# Get analytics
top_keywords = analytics.get_top_keywords(limit=10)
# [('50ml', 120), ('PET', 95), ('20파이', 80), ...]

top_products = analytics.get_top_products(limit=10, metric='click')
# [('prod_123', {'name': '...', 'clicks': 45}), ...]

trending = analytics.get_trending_queries(limit=5)
# [('유리병 MOQ', 8.5), ('20파이 펌프', 7.2), ...]

patterns = analytics.get_search_context_patterns(limit=10)
# [('50ml PET 병 → 20파이 캡', 25), ('병 → 캡', 18), ...]
"""
