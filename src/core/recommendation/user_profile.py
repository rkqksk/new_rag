"""
User Profile & Preference Extraction

Tracks user preferences from search and interaction history
"""

import re
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """
    User preference profile

    Tracks preferences extracted from:
    - Search queries
    - Clicked products
    - Viewed products
    - Bookmarked items
    """
    session_id: str

    # Preference weights (0.0 - 1.0)
    capacity_preferences: Dict[str, float] = field(default_factory=dict)  # {"50ml": 0.8, "100ml": 0.6}
    material_preferences: Dict[str, float] = field(default_factory=dict)  # {"PET": 0.9, "PP": 0.5}
    neck_preferences: Dict[str, float] = field(default_factory=dict)      # {"20파이": 0.7}
    category_preferences: Dict[str, float] = field(default_factory=dict)  # {"Bottle": 0.8, "Cap": 0.6}

    # Product history
    viewed_products: List[str] = field(default_factory=list)      # Product IDs
    clicked_products: List[str] = field(default_factory=list)     # Product IDs with clicks
    bookmarked_products: Set[str] = field(default_factory=set)    # Bookmarked IDs

    # Search history
    search_queries: List[Dict[str, Any]] = field(default_factory=list)  # [{query, timestamp, extracted_attrs}]

    # Compatibility tracking (for container-cap matching)
    compatible_pairs: Dict[str, List[str]] = field(default_factory=dict)  # {"container_id": ["cap_id1", "cap_id2"]}

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    interaction_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['bookmarked_products'] = list(self.bookmarked_products)
        data['created_at'] = self.created_at.isoformat()
        data['last_updated'] = self.last_updated.isoformat()
        for query in data['search_queries']:
            if isinstance(query.get('timestamp'), datetime):
                query['timestamp'] = query['timestamp'].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create from dictionary"""
        data['bookmarked_products'] = set(data.get('bookmarked_products', []))
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        for query in data.get('search_queries', []):
            if isinstance(query.get('timestamp'), str):
                query['timestamp'] = datetime.fromisoformat(query['timestamp'])
        return cls(**data)

    def get_top_preferences(self, attribute: str, top_k: int = 3) -> List[tuple]:
        """
        Get top K preferences for an attribute

        Args:
            attribute: 'capacity', 'material', 'neck', 'category'
            top_k: Number of top preferences to return

        Returns:
            List of (value, weight) tuples, sorted by weight descending
        """
        pref_dict = getattr(self, f"{attribute}_preferences", {})
        sorted_prefs = sorted(pref_dict.items(), key=lambda x: x[1], reverse=True)
        return sorted_prefs[:top_k]

    def get_preference_weight(self, attribute: str, value: str) -> float:
        """Get preference weight for a specific attribute value"""
        pref_dict = getattr(self, f"{attribute}_preferences", {})
        return pref_dict.get(value, 0.0)

    def has_strong_preference(self, attribute: str, threshold: float = 0.5) -> bool:
        """Check if user has strong preference for an attribute"""
        pref_dict = getattr(self, f"{attribute}_preferences", {})
        return any(weight >= threshold for weight in pref_dict.values())


class PreferenceExtractor:
    """
    Extract user preferences from interactions

    Features:
    - Parse search queries for attributes
    - Track clicked products and extract attributes
    - Apply time decay (recent preferences weighted higher)
    - Normalize preference weights
    """

    def __init__(
        self,
        decay_days: int = 7,
        click_weight: float = 1.0,
        view_weight: float = 0.5,
        search_weight: float = 0.3,
        bookmark_weight: float = 2.0
    ):
        """
        Initialize preference extractor

        Args:
            decay_days: Days for preference to decay to 50%
            click_weight: Weight for clicked products
            view_weight: Weight for viewed products
            search_weight: Weight for search queries
            bookmark_weight: Weight for bookmarked products
        """
        self.decay_days = decay_days
        self.click_weight = click_weight
        self.view_weight = view_weight
        self.search_weight = search_weight
        self.bookmark_weight = bookmark_weight

        # Attribute extraction patterns (Korean + English)
        self.capacity_patterns = [
            r'(\d+)\s*(ml|ML|미리|밀리)',
            r'(\d+)\s*(l|L|리터|리터)',
            r'(\d+)\s*(cc|CC)'
        ]

        self.material_patterns = [
            r'\b(PET|pet|페트|펫)\b',
            r'\b(PP|pp|폴리프로필렌)\b',
            r'\b(PE|pe|폴리에틸렌)\b',
            r'\b(PS|ps|폴리스티렌)\b',
            r'\b(PVC|pvc)\b',
            r'\b(유리|glass|Glass|GLASS)\b',
            r'\b(알루미늄|aluminum|Aluminum)\b'
        ]

        self.neck_patterns = [
            r'(\d+)\s*파이',
            r'(\d+)\s*mm\s*넥',
            r'(\d+)\s*mm\s*neck',
            r'neck\s*(\d+)',
            r'넥\s*(\d+)'
        ]

        self.category_keywords = {
            'Bottle': ['병', '보틀', 'bottle', '용기', 'container'],
            'Cap': ['캡', 'cap', '뚜껑', 'lid', '마개'],
            'Pump': ['펌프', 'pump', '디스펜서', 'dispenser'],
            'Jar': ['자', 'jar', '단지', '용기']
        }

        logger.info("✅ PreferenceExtractor initialized")

    def extract_from_query(self, query: str) -> Dict[str, List[str]]:
        """
        Extract attributes from search query

        Args:
            query: Search query string

        Returns:
            Dictionary of extracted attributes
        """
        extracted = {
            'capacity': [],
            'material': [],
            'neck': [],
            'category': []
        }

        # Extract capacity
        for pattern in self.capacity_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    value = match[0]
                    unit = match[1].lower()
                    if unit in ['l', '리터', 'liter']:
                        value = str(int(value) * 1000)  # Convert to ml
                    extracted['capacity'].append(f"{value}ml")

        # Extract material
        for pattern in self.material_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                material = match.upper() if len(match) <= 3 else match.capitalize()
                if material not in extracted['material']:
                    extracted['material'].append(material)

        # Extract neck size
        for pattern in self.neck_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                extracted['neck'].append(f"{match}파이")

        # Extract category
        query_lower = query.lower()
        for category, keywords in self.category_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                extracted['category'].append(category)

        return extracted

    def extract_from_product(self, product: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Extract attributes from product data

        Args:
            product: Product dictionary

        Returns:
            Dictionary of extracted attributes
        """
        extracted = {
            'capacity': [],
            'material': [],
            'neck': [],
            'category': []
        }

        # Extract from product fields
        if 'capacity' in product and product['capacity']:
            extracted['capacity'].append(product['capacity'])

        if 'material' in product and product['material']:
            material = product['material'].upper() if len(product['material']) <= 3 else product['material']
            extracted['material'].append(material)

        if 'neck' in product and product['neck']:
            extracted['neck'].append(product['neck'])

        if 'category' in product and product['category']:
            extracted['category'].append(product['category'])

        # Fallback: extract from product name/description
        text = f"{product.get('name', '')} {product.get('description', '')}"
        query_extracted = self.extract_from_query(text)

        for attr in ['capacity', 'material', 'neck', 'category']:
            for value in query_extracted[attr]:
                if value not in extracted[attr]:
                    extracted[attr].append(value)

        return extracted

    def update_profile_from_search(
        self,
        profile: UserProfile,
        query: str,
        timestamp: Optional[datetime] = None
    ):
        """
        Update user profile from search query

        Args:
            profile: User profile to update
            query: Search query
            timestamp: Optional timestamp (defaults to now)
        """
        timestamp = timestamp or datetime.now()

        # Extract attributes
        extracted = self.extract_from_query(query)

        # Record search
        profile.search_queries.append({
            'query': query,
            'timestamp': timestamp,
            'extracted_attrs': extracted
        })

        # Update preferences with time decay
        decay_factor = self._calculate_decay(timestamp)
        weight = self.search_weight * decay_factor

        self._update_preferences(profile, extracted, weight)

        profile.last_updated = datetime.now()
        profile.interaction_count += 1

        logger.debug(f"Updated profile from search: {query} (weight={weight:.2f})")

    def update_profile_from_view(
        self,
        profile: UserProfile,
        product_id: str,
        product: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ):
        """
        Update user profile from viewed product

        Args:
            profile: User profile to update
            product_id: Product ID
            product: Product data
            timestamp: Optional timestamp
        """
        timestamp = timestamp or datetime.now()

        # Record view
        if product_id not in profile.viewed_products:
            profile.viewed_products.append(product_id)

        # Extract attributes
        extracted = self.extract_from_product(product)

        # Update preferences
        decay_factor = self._calculate_decay(timestamp)
        weight = self.view_weight * decay_factor

        self._update_preferences(profile, extracted, weight)

        profile.last_updated = datetime.now()
        profile.interaction_count += 1

        logger.debug(f"Updated profile from view: {product_id} (weight={weight:.2f})")

    def update_profile_from_click(
        self,
        profile: UserProfile,
        product_id: str,
        product: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ):
        """
        Update user profile from clicked product

        Args:
            profile: User profile to update
            product_id: Product ID
            product: Product data
            timestamp: Optional timestamp
        """
        timestamp = timestamp or datetime.now()

        # Record click
        if product_id not in profile.clicked_products:
            profile.clicked_products.append(product_id)

        # Extract attributes
        extracted = self.extract_from_product(product)

        # Update preferences (clicks have higher weight)
        decay_factor = self._calculate_decay(timestamp)
        weight = self.click_weight * decay_factor

        self._update_preferences(profile, extracted, weight)

        profile.last_updated = datetime.now()
        profile.interaction_count += 1

        logger.debug(f"Updated profile from click: {product_id} (weight={weight:.2f})")

    def update_profile_from_bookmark(
        self,
        profile: UserProfile,
        product_id: str,
        product: Dict[str, Any]
    ):
        """
        Update user profile from bookmarked product

        Args:
            profile: User profile to update
            product_id: Product ID
            product: Product data
        """
        # Record bookmark
        profile.bookmarked_products.add(product_id)

        # Extract attributes
        extracted = self.extract_from_product(product)

        # Update preferences (bookmarks have highest weight, no decay)
        weight = self.bookmark_weight

        self._update_preferences(profile, extracted, weight)

        profile.last_updated = datetime.now()
        profile.interaction_count += 1

        logger.debug(f"Updated profile from bookmark: {product_id} (weight={weight:.2f})")

    def _update_preferences(
        self,
        profile: UserProfile,
        extracted: Dict[str, List[str]],
        weight: float
    ):
        """
        Update preference weights for extracted attributes

        Args:
            profile: User profile
            extracted: Extracted attributes
            weight: Weight to add
        """
        for attr_type in ['capacity', 'material', 'neck', 'category']:
            values = extracted.get(attr_type, [])
            pref_dict = getattr(profile, f"{attr_type}_preferences")

            for value in values:
                # Add weight (bounded to [0, 1])
                current = pref_dict.get(value, 0.0)
                pref_dict[value] = min(1.0, current + weight)

        # Normalize preferences
        self._normalize_preferences(profile)

    def _normalize_preferences(self, profile: UserProfile):
        """
        Normalize preference weights to [0, 1]

        Uses softmax-like normalization to maintain relative weights
        """
        for attr_type in ['capacity', 'material', 'neck', 'category']:
            pref_dict = getattr(profile, f"{attr_type}_preferences")

            if not pref_dict:
                continue

            # Get max weight
            max_weight = max(pref_dict.values())

            if max_weight > 0:
                # Normalize relative to max
                for key in pref_dict:
                    pref_dict[key] = pref_dict[key] / max_weight

    def _calculate_decay(self, timestamp: datetime) -> float:
        """
        Calculate time decay factor

        Args:
            timestamp: Event timestamp

        Returns:
            Decay factor (0.5 at decay_days, 1.0 for recent)
        """
        age_days = (datetime.now() - timestamp).days

        # Exponential decay: 0.5^(age_days / decay_days)
        decay = 0.5 ** (age_days / self.decay_days)

        return decay

    def get_profile_summary(self, profile: UserProfile) -> str:
        """
        Get human-readable profile summary

        Args:
            profile: User profile

        Returns:
            Summary string
        """
        lines = [
            f"👤 User Profile: {profile.session_id}",
            f"   Interactions: {profile.interaction_count}",
            f"   Created: {profile.created_at.strftime('%Y-%m-%d')}",
            ""
        ]

        # Top preferences
        for attr_type in ['capacity', 'material', 'neck', 'category']:
            top_prefs = profile.get_top_preferences(attr_type, top_k=3)
            if top_prefs:
                lines.append(f"   {attr_type.capitalize()}:")
                for value, weight in top_prefs:
                    lines.append(f"      • {value}: {weight:.2f}")

        # History
        lines.append(f"\n   📊 History:")
        lines.append(f"      • Searches: {len(profile.search_queries)}")
        lines.append(f"      • Viewed: {len(profile.viewed_products)}")
        lines.append(f"      • Clicked: {len(profile.clicked_products)}")
        lines.append(f"      • Bookmarked: {len(profile.bookmarked_products)}")

        return "\n".join(lines)


# Usage example
"""
# Initialize
extractor = PreferenceExtractor(decay_days=7)
profile = UserProfile(session_id="sess_123")

# User searches "50ml PET 병"
extractor.update_profile_from_search(profile, "50ml PET 병")
# → capacity_preferences: {"50ml": 0.3}
# → material_preferences: {"PET": 0.3}

# User clicks on product
product = {
    'id': 'prod_001',
    'name': '50ml PET 병',
    'capacity': '50ml',
    'material': 'PET',
    'neck': '20파이',
    'category': 'Bottle'
}
extractor.update_profile_from_click(profile, 'prod_001', product)
# → capacity_preferences: {"50ml": 1.0}  # Boosted by click
# → material_preferences: {"PET": 1.0}
# → neck_preferences: {"20파이": 1.0}

# Later: User searches "캡"
extractor.update_profile_from_search(profile, "캡")
# → category_preferences: {"Cap": 0.3}

# Profile now knows:
# - User prefers 50ml capacity
# - User prefers PET material
# - User has 20파이 neck products
# → Recommendation: Show 20파이 compatible caps!
"""
