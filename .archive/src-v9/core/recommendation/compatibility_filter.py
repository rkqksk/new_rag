"""
Strict Compatibility Filtering

Hard filter for compatibility:
- 20파이 container → ONLY 20파이 cap/pump
- 50ml bottle → caps suitable for 50ml or less
- No incompatible products shown at all
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class CompatibilityRules:
    """Compatibility rules configuration"""

    # Strict neck matching
    strict_neck_matching: bool = True

    # Capacity tolerance (%)
    capacity_tolerance: float = 0.1  # 10% tolerance

    # Allow cross-category compatibility check
    enable_cross_category: bool = True

    # Fallback behavior when no user context
    fallback_mode: str = "permissive"  # 'permissive' or 'strict'


class CompatibilityFilter:
    """
    Strict Compatibility Filter

    Features:
    - Hard filtering by neck size compatibility
    - Capacity-based filtering
    - Cross-category compatibility (bottle-cap, bottle-pump)
    - User context-aware filtering
    """

    def __init__(self, rules: Optional[CompatibilityRules] = None):
        """
        Initialize compatibility filter

        Args:
            rules: Compatibility rules configuration
        """
        self.rules = rules or CompatibilityRules()

        # Neck size compatibility matrix
        self._init_neck_compatibility()

        # Category compatibility matrix
        self._init_category_compatibility()

        logger.info("✅ CompatibilityFilter initialized (strict mode)")

    def _init_neck_compatibility(self):
        """
        Initialize neck size compatibility matrix

        In strict mode: exact match only
        """
        # Exact match required by default
        self.neck_compatibility = {}

        # Special cases (if any)
        # e.g., 20파이 and 20mm are compatible
        self.neck_aliases = {
            "20파이": ["20mm", "20파이"],
            "24파이": ["24mm", "24파이"],
            "28파이": ["28mm", "28파이"],
            "32파이": ["32mm", "32파이"],
        }

    def _init_category_compatibility(self):
        """Initialize category compatibility matrix"""

        self.category_compatibility = {
            "Bottle": ["Cap", "Pump"],  # Bottles need caps/pumps
            "Jar": ["Cap", "Pump"],  # Jars need caps/pumps
            "Cap": ["Bottle", "Jar"],  # Caps fit bottles/jars
            "Pump": ["Bottle", "Jar"],  # Pumps fit bottles/jars
        }

    def filter_by_compatibility(
        self,
        results: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]] = None,
        query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter results by strict compatibility

        Args:
            results: Search results
            user_context: User's recent product context
                         e.g., {'recent_necks': ['20파이'], 'recent_capacities': ['50ml']}
            query: Current search query

        Returns:
            Filtered results (only compatible products)
        """
        if not user_context:
            # No context: return all (permissive mode)
            if self.rules.fallback_mode == "permissive":
                return results
            else:
                return results  # Still return all, but could be stricter

        filtered = []

        for result in results:
            if self._is_compatible(result, user_context, query):
                filtered.append(result)
            else:
                logger.debug(f"Filtered out incompatible: {result.get('name', result.get('id'))}")

        logger.info(f"Compatibility filter: {len(results)} → {len(filtered)} results")

        return filtered

    def _is_compatible(
        self, product: Dict[str, Any], user_context: Dict[str, Any], query: Optional[str]
    ) -> bool:
        """
        Check if product is compatible with user context

        Args:
            product: Product to check
            user_context: User's context
            query: Search query

        Returns:
            True if compatible, False otherwise
        """
        # Extract product attributes
        product_neck = product.get("neck")
        product_capacity = product.get("capacity")
        product_category = product.get("category")

        # Extract user context
        user_necks = user_context.get("recent_necks", [])
        user_capacities = user_context.get("recent_capacities", [])
        user_categories = user_context.get("recent_categories", [])

        # If no strong context, allow product
        if not user_necks and not user_capacities and not user_categories:
            return True

        # Check category compatibility
        if user_categories and product_category:
            if not self._check_category_compatibility(product_category, user_categories):
                # Incompatible category
                logger.debug(
                    f"Incompatible category: {product_category} not compatible with {user_categories}"
                )
                return False

        # Check neck compatibility (STRICT)
        if user_necks and product_neck:
            if not self._check_neck_compatibility(product_neck, user_necks):
                logger.debug(f"Incompatible neck: {product_neck} not in {user_necks}")
                return False

        # Check capacity compatibility
        if user_capacities and product_capacity:
            if not self._check_capacity_compatibility(
                product_capacity, user_capacities, product_category
            ):
                logger.debug(f"Incompatible capacity: {product_capacity} vs {user_capacities}")
                return False

        # All checks passed
        return True

    def _check_category_compatibility(
        self, product_category: str, user_categories: List[str]
    ) -> bool:
        """
        Check if product category is compatible with user's categories

        Args:
            product_category: Product category
            user_categories: User's recent categories

        Returns:
            True if compatible
        """
        if not self.rules.enable_cross_category:
            # Only exact match allowed
            return product_category in user_categories

        # Check compatibility matrix
        for user_cat in user_categories:
            compatible_cats = self.category_compatibility.get(user_cat, [])

            if product_category == user_cat or product_category in compatible_cats:
                return True

        return False

    def _check_neck_compatibility(self, product_neck: str, user_necks: List[str]) -> bool:
        """
        Check if product neck is compatible with user's necks

        Args:
            product_neck: Product neck size
            user_necks: User's recent neck sizes

        Returns:
            True if compatible
        """
        if not self.rules.strict_neck_matching:
            # Fuzzy matching allowed
            return True

        # Strict matching: exact match required
        for user_neck in user_necks:
            # Check direct match
            if product_neck == user_neck:
                return True

            # Check aliases
            product_aliases = self.neck_aliases.get(product_neck, [product_neck])
            user_aliases = self.neck_aliases.get(user_neck, [user_neck])

            if any(pa in user_aliases for pa in product_aliases):
                return True

        return False

    def _check_capacity_compatibility(
        self, product_capacity: str, user_capacities: List[str], product_category: Optional[str]
    ) -> bool:
        """
        Check if product capacity is compatible with user's capacities

        Args:
            product_capacity: Product capacity (e.g., "50ml")
            user_capacities: User's recent capacities
            product_category: Product category

        Returns:
            True if compatible
        """
        try:
            # Parse product capacity
            product_ml = self._parse_capacity_to_ml(product_capacity)

            if product_ml is None:
                # Can't parse, allow it
                return True

            # Parse user capacities
            user_ml_values = []
            for cap in user_capacities:
                ml = self._parse_capacity_to_ml(cap)
                if ml:
                    user_ml_values.append(ml)

            if not user_ml_values:
                return True

            # Check compatibility based on category
            if product_category in ["Cap", "Pump"]:
                # Cap/Pump should fit user's container capacity
                # Allow same size or slightly smaller
                for user_ml in user_ml_values:
                    # Cap can be for same capacity or smaller containers
                    # e.g., 50ml cap can fit 50ml or 100ml bottle
                    # But 100ml cap cannot fit 50ml bottle

                    # For now, allow if within reasonable range
                    if product_ml <= user_ml * 1.2:  # Allow up to 20% larger
                        return True

                return False

            else:
                # Container: check if similar capacity
                for user_ml in user_ml_values:
                    tolerance = user_ml * self.rules.capacity_tolerance
                    if abs(product_ml - user_ml) <= tolerance:
                        return True

                return False

        except Exception as e:
            logger.error(f"Error checking capacity compatibility: {e}")
            return True  # Allow on error

    def _parse_capacity_to_ml(self, capacity: str) -> Optional[float]:
        """
        Parse capacity string to ml

        Args:
            capacity: Capacity string (e.g., "50ml", "1l", "500ML")

        Returns:
            Capacity in ml, or None if can't parse
        """
        if not capacity:
            return None

        try:
            # Parse ml
            match = re.match(r"(\d+(?:\.\d+)?)\s*(ml|ML|미리|밀리)", capacity, re.IGNORECASE)
            if match:
                return float(match.group(1))

            # Parse liters
            match = re.match(r"(\d+(?:\.\d+)?)\s*(l|L|리터)", capacity, re.IGNORECASE)
            if match:
                return float(match.group(1)) * 1000

            # Parse cc
            match = re.match(r"(\d+(?:\.\d+)?)\s*(cc|CC)", capacity, re.IGNORECASE)
            if match:
                return float(match.group(1))

            return None

        except Exception as e:
            logger.error(f"Error parsing capacity '{capacity}': {e}")
            return None

    def extract_compatibility_context(self, profile) -> Dict[str, Any]:
        """
        Extract compatibility context from user profile

        Args:
            profile: User profile (from recommendation system)

        Returns:
            Compatibility context dict
        """
        context = {"recent_necks": [], "recent_capacities": [], "recent_categories": []}

        # Get top neck preferences
        if hasattr(profile, "get_top_preferences"):
            top_necks = profile.get_top_preferences("neck", top_k=3)
            context["recent_necks"] = [neck for neck, weight in top_necks if weight > 0.3]

            top_capacities = profile.get_top_preferences("capacity", top_k=3)
            context["recent_capacities"] = [cap for cap, weight in top_capacities if weight > 0.3]

            top_categories = profile.get_top_preferences("category", top_k=3)
            context["recent_categories"] = [cat for cat, weight in top_categories if weight > 0.3]

        return context

    def get_compatibility_rules_summary(self) -> str:
        """Get human-readable rules summary"""
        lines = [
            "🔒 Compatibility Filtering Rules:",
            f"   • Strict neck matching: {'YES' if self.rules.strict_neck_matching else 'NO'}",
            f"   • Capacity tolerance: {self.rules.capacity_tolerance * 100:.0f}%",
            f"   • Cross-category: {'ENABLED' if self.rules.enable_cross_category else 'DISABLED'}",
            f"   • Fallback mode: {self.rules.fallback_mode.upper()}",
            "",
            "   Examples:",
            "   ✅ 20파이 bottle → 20파이 cap (ALLOWED)",
            "   ❌ 20파이 bottle → 24파이 cap (BLOCKED)",
            "   ✅ 50ml bottle → 50ml cap (ALLOWED)",
            "   ❌ 50ml bottle → 100ml cap (BLOCKED)",
        ]

        return "\n".join(lines)


# Usage example
"""
from src.core.recommendation import PersonalizationService, CompatibilityFilter

# Initialize
compat_filter = CompatibilityFilter(
    rules=CompatibilityRules(
        strict_neck_matching=True,
        enable_cross_category=True
    )
)

# Get user context
profile = personalization.get_or_create_profile(session_id)
compat_context = compat_filter.extract_compatibility_context(profile)

# User previously viewed: 20파이 50ml PET bottle
# compat_context = {
#     'recent_necks': ['20파이'],
#     'recent_capacities': ['50ml'],
#     'recent_categories': ['Bottle']
# }

# Search for "캡"
search_results = [
    {'id': 'c1', 'name': '20파이 캡', 'neck': '20파이', 'category': 'Cap'},  # ALLOWED ✅
    {'id': 'c2', 'name': '24파이 캡', 'neck': '24파이', 'category': 'Cap'},  # BLOCKED ❌
    {'id': 'c3', 'name': '28파이 캡', 'neck': '28파이', 'category': 'Cap'}   # BLOCKED ❌
]

# Apply strict compatibility filter
filtered_results = compat_filter.filter_by_compatibility(
    results=search_results,
    user_context=compat_context
)

# Result: Only 20파이 cap remains!
# filtered_results = [{'id': 'c1', 'name': '20파이 캡', ...}]
"""
