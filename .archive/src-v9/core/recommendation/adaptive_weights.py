"""
Adaptive User-Specific Weights Learning

Automatically learns user's search focus and adjusts weights:
- Supplier-focused users: High weight on manufacturer/supplier
- Compatibility-focused users: High weight on neck size matching
- Material-focused users: High weight on material (glass, PET, PP)
- Price-focused users: High weight on MOQ/price
"""

import json
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class UserSearchFocus:
    """
    User's search focus profile

    Automatically learned from search patterns
    """

    session_id: str

    # Focus scores (0.0 - 1.0, higher = more focused)
    supplier_focus: float = 0.0  # Searches include supplier/manufacturer names
    compatibility_focus: float = 0.0  # Searches include neck size, capacity matching
    material_focus: float = 0.0  # Searches emphasize material (glass, PET, PP)
    price_focus: float = 0.0  # Searches include MOQ, price, business terms
    category_focus: float = 0.0  # Searches are category-specific (bottle, cap)
    specification_focus: float = 0.0  # Searches include detailed specs (dimensions, etc.)

    # Detected patterns
    frequent_suppliers: List[str] = field(default_factory=list)  # Top 3 suppliers
    frequent_materials: List[str] = field(default_factory=list)  # Top 3 materials
    frequent_categories: List[str] = field(default_factory=list)  # Top 3 categories

    # Statistics
    total_searches: int = 0
    searches_with_supplier: int = 0
    searches_with_compatibility: int = 0
    searches_with_material: int = 0
    searches_with_price: int = 0
    searches_with_category: int = 0
    searches_with_spec: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "supplier_focus": self.supplier_focus,
            "compatibility_focus": self.compatibility_focus,
            "material_focus": self.material_focus,
            "price_focus": self.price_focus,
            "category_focus": self.category_focus,
            "specification_focus": self.specification_focus,
            "frequent_suppliers": self.frequent_suppliers,
            "frequent_materials": self.frequent_materials,
            "frequent_categories": self.frequent_categories,
            "total_searches": self.total_searches,
            "searches_with_supplier": self.searches_with_supplier,
            "searches_with_compatibility": self.searches_with_compatibility,
            "searches_with_material": self.searches_with_material,
            "searches_with_price": self.searches_with_price,
            "searches_with_category": self.searches_with_category,
            "searches_with_spec": self.searches_with_spec,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserSearchFocus":
        """Create from dictionary"""
        return cls(**data)

    def get_dominant_focus(self) -> str:
        """Get user's dominant search focus"""
        focuses = {
            "supplier": self.supplier_focus,
            "compatibility": self.compatibility_focus,
            "material": self.material_focus,
            "price": self.price_focus,
            "category": self.category_focus,
            "specification": self.specification_focus,
        }

        if max(focuses.values()) < 0.3:
            return "general"  # No clear focus yet

        return max(focuses.items(), key=lambda x: x[1])[0]


class AdaptiveWeightsLearner:
    """
    Adaptive Weights Learning System

    Learns user's search focus and adjusts recommendation weights accordingly

    Features:
    - Pattern recognition from search queries
    - Automatic weight adjustment
    - Focus detection (supplier/compatibility/material/price)
    """

    def __init__(self):
        """Initialize adaptive weights learner"""

        # Supplier patterns (Korean manufacturers)
        self.supplier_patterns = [
            r"\b(춘진|onehago|원하고|프리몰드|freemold|장업|jangup)\b",
            r"\b(주)\s*\w+",  # 주식회사
            r"\b회사\b",
            r"\b제조\b",
            r"\b공급\b",
            r"\b업체\b",
        ]

        # Compatibility patterns (neck, capacity matching)
        self.compatibility_patterns = [
            r"(\d+)\s*파이",
            r"(\d+)\s*mm\s*(넥|neck)",
            r"호환",
            r"맞는",
            r"적합",
            r"와\s*함께",
            r"세트",
        ]

        # Material patterns
        self.material_patterns = [
            r"\b(PET|pet|페트|펫)\b",
            r"\b(PP|pp|폴리프로필렌)\b",
            r"\b(PE|pe|폴리에틸렌)\b",
            r"\b(PS|ps|폴리스티렌)\b",
            r"\b(PVC|pvc)\b",
            r"\b(유리|glass|Glass|GLASS|초자)\b",
            r"\b(알루미늄|aluminum)\b",
            r"\b(금속|metal)\b",
            r"\b재질\b",
            r"\b소재\b",
        ]

        # Price/business patterns
        self.price_patterns = [
            r"\bMOQ\b",
            r"\b최소\s*주문\b",
            r"\b가격\b",
            r"\b단가\b",
            r"\b견적\b",
            r"\b대량\b",
            r"\b도매\b",
            r"\b수량\b",
        ]

        # Category patterns
        self.category_patterns = {
            "Bottle": [r"\b(병|보틀|bottle|용기|container)\b"],
            "Cap": [r"\b(캡|cap|뚜껑|lid|마개)\b"],
            "Pump": [r"\b(펌프|pump|디스펜서|dispenser)\b"],
            "Jar": [r"\b(자|jar|단지)\b"],
        }

        # Specification patterns
        self.spec_patterns = [
            r"(\d+)\s*(ml|ML|미리|밀리)",
            r"(\d+)\s*(l|L|리터)",
            r"(\d+)\s*(mm|cm|m)",
            r"(\d+)\s*x\s*(\d+)",  # Dimensions
            r"직경",
            r"높이",
            r"두께",
            r"무게",
            r"사이즈",
        ]

        logger.info("✅ AdaptiveWeightsLearner initialized")

    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze search query for focus detection

        Args:
            query: Search query

        Returns:
            Analysis results
        """
        query_lower = query.lower()

        analysis = {
            "has_supplier": False,
            "has_compatibility": False,
            "has_material": False,
            "has_price": False,
            "has_category": False,
            "has_spec": False,
            "detected_suppliers": [],
            "detected_materials": [],
            "detected_categories": [],
            "detected_specs": [],
        }

        # Check supplier
        for pattern in self.supplier_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                analysis["has_supplier"] = True
                matches = re.findall(pattern, query, re.IGNORECASE)
                analysis["detected_suppliers"].extend(matches)

        # Check compatibility
        for pattern in self.compatibility_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                analysis["has_compatibility"] = True

        # Check material
        for pattern in self.material_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                analysis["has_material"] = True
                matches = re.findall(pattern, query, re.IGNORECASE)
                analysis["detected_materials"].extend(
                    [m.upper() if len(m) <= 3 else m for m in matches]
                )

        # Check price
        for pattern in self.price_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                analysis["has_price"] = True

        # Check category
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    analysis["has_category"] = True
                    analysis["detected_categories"].append(category)

        # Check specification
        for pattern in self.spec_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                analysis["has_spec"] = True
                matches = re.findall(pattern, query, re.IGNORECASE)
                analysis["detected_specs"].extend(matches)

        return analysis

    def update_focus(self, focus: UserSearchFocus, query: str):
        """
        Update user's search focus based on query

        Args:
            focus: User's search focus profile
            query: Search query
        """
        # Analyze query
        analysis = self.analyze_query(query)

        # Update counters
        focus.total_searches += 1

        if analysis["has_supplier"]:
            focus.searches_with_supplier += 1
            # Track frequent suppliers
            for supplier in analysis["detected_suppliers"]:
                if isinstance(supplier, tuple):
                    supplier = supplier[0]
                if supplier and supplier not in focus.frequent_suppliers:
                    focus.frequent_suppliers.append(supplier)

        if analysis["has_compatibility"]:
            focus.searches_with_compatibility += 1

        if analysis["has_material"]:
            focus.searches_with_material += 1
            # Track frequent materials
            for material in analysis["detected_materials"]:
                if isinstance(material, tuple):
                    material = material[0]
                if material and material not in focus.frequent_materials:
                    focus.frequent_materials.append(material)

        if analysis["has_price"]:
            focus.searches_with_price += 1

        if analysis["has_category"]:
            focus.searches_with_category += 1
            # Track frequent categories
            for category in analysis["detected_categories"]:
                if category not in focus.frequent_categories:
                    focus.frequent_categories.append(category)

        if analysis["has_spec"]:
            focus.searches_with_spec += 1

        # Calculate focus scores (normalized to [0, 1])
        if focus.total_searches > 0:
            focus.supplier_focus = focus.searches_with_supplier / focus.total_searches
            focus.compatibility_focus = focus.searches_with_compatibility / focus.total_searches
            focus.material_focus = focus.searches_with_material / focus.total_searches
            focus.price_focus = focus.searches_with_price / focus.total_searches
            focus.category_focus = focus.searches_with_category / focus.total_searches
            focus.specification_focus = focus.searches_with_spec / focus.total_searches

        # Limit frequent lists to top 3
        focus.frequent_suppliers = focus.frequent_suppliers[:3]
        focus.frequent_materials = focus.frequent_materials[:3]
        focus.frequent_categories = focus.frequent_categories[:3]

        logger.debug(f"Updated focus: dominant={focus.get_dominant_focus()}")

    def get_adaptive_weights(self, focus: UserSearchFocus) -> Dict[str, float]:
        """
        Get adaptive recommendation weights based on user's focus

        Args:
            focus: User's search focus profile

        Returns:
            Adaptive weights for recommendation
        """
        # Base weights (default)
        weights = {
            "capacity_importance": 1.0,
            "material_importance": 0.8,
            "neck_importance": 0.9,
            "category_importance": 0.7,
            "supplier_importance": 0.5,  # New
            "price_importance": 0.6,  # New
            "compatibility_boost": 0.2,
            "vector_score_weight": 0.6,
            "preference_score_weight": 0.4,
        }

        # Adjust based on user's dominant focus
        dominant = focus.get_dominant_focus()

        if dominant == "supplier":
            # Supplier-focused: boost supplier, reduce others
            weights["supplier_importance"] = 1.5
            weights["material_importance"] = 0.6
            weights["neck_importance"] = 0.7
            weights["preference_score_weight"] = 0.5  # More weight on preferences
            logger.debug("Supplier-focused weights applied")

        elif dominant == "compatibility":
            # Compatibility-focused: boost neck/capacity matching
            weights["neck_importance"] = 1.5
            weights["capacity_importance"] = 1.2
            weights["compatibility_boost"] = 0.4  # Double boost!
            weights["material_importance"] = 0.6
            logger.debug("Compatibility-focused weights applied")

        elif dominant == "material":
            # Material-focused: boost material importance
            weights["material_importance"] = 1.5
            weights["neck_importance"] = 0.7
            weights["category_importance"] = 0.6
            logger.debug("Material-focused weights applied")

        elif dominant == "price":
            # Price-focused: boost price/MOQ importance
            weights["price_importance"] = 1.5
            weights["supplier_importance"] = 1.0
            weights["material_importance"] = 0.6
            logger.debug("Price-focused weights applied")

        elif dominant == "category":
            # Category-focused: boost category matching
            weights["category_importance"] = 1.2
            weights["material_importance"] = 0.7
            logger.debug("Category-focused weights applied")

        elif dominant == "specification":
            # Specification-focused: boost all spec attributes
            weights["capacity_importance"] = 1.2
            weights["neck_importance"] = 1.1
            weights["material_importance"] = 1.0
            logger.debug("Specification-focused weights applied")

        else:
            # General/balanced
            logger.debug("Balanced weights applied (no clear focus)")

        return weights

    def get_focus_summary(self, focus: UserSearchFocus) -> str:
        """
        Get human-readable focus summary

        Args:
            focus: User's search focus profile

        Returns:
            Focus summary
        """
        dominant = focus.get_dominant_focus()

        lines = [
            f"🎯 User Search Focus: {dominant.upper()}",
            f"   Total Searches: {focus.total_searches}",
            "",
        ]

        # Focus scores
        lines.append("   Focus Scores:")
        lines.append(f"      • Supplier: {focus.supplier_focus:.2f}")
        lines.append(f"      • Compatibility: {focus.compatibility_focus:.2f}")
        lines.append(f"      • Material: {focus.material_focus:.2f}")
        lines.append(f"      • Price: {focus.price_focus:.2f}")
        lines.append(f"      • Category: {focus.category_focus:.2f}")
        lines.append(f"      • Specification: {focus.specification_focus:.2f}")

        # Frequent items
        if focus.frequent_suppliers:
            lines.append(f"\n   Frequent Suppliers: {', '.join(focus.frequent_suppliers)}")

        if focus.frequent_materials:
            lines.append(f"   Frequent Materials: {', '.join(focus.frequent_materials)}")

        if focus.frequent_categories:
            lines.append(f"   Frequent Categories: {', '.join(focus.frequent_categories)}")

        # Recommendation
        lines.append(f"\n   💡 Recommendation Strategy:")
        if dominant == "supplier":
            lines.append("      → Prioritize products from user's preferred suppliers")
        elif dominant == "compatibility":
            lines.append("      → Strongly filter by neck/capacity compatibility")
        elif dominant == "material":
            lines.append("      → Emphasize material matching (e.g., glass only)")
        elif dominant == "price":
            lines.append("      → Highlight MOQ and pricing information")
        elif dominant == "category":
            lines.append("      → Focus on specific product categories")
        elif dominant == "specification":
            lines.append("      → Match detailed specifications closely")
        else:
            lines.append("      → Use balanced recommendation approach")

        return "\n".join(lines)


# Usage example
"""
# Initialize
learner = AdaptiveWeightsLearner()
focus = UserSearchFocus(session_id="user_123")

# User searches "춘진 PET 병" (supplier-focused)
learner.update_focus(focus, "춘진 PET 병")

# User searches "춘진 유리병" (supplier + material)
learner.update_focus(focus, "춘진 유리병")

# User searches "춘진 가격" (supplier + price)
learner.update_focus(focus, "춘진 가격")

# Check focus
print(focus.get_dominant_focus())  # "supplier"
print(f"Supplier focus: {focus.supplier_focus:.2f}")  # 1.0 (3/3 searches)

# Get adaptive weights
weights = learner.get_adaptive_weights(focus)
# weights['supplier_importance'] = 1.5 (boosted!)
# weights['material_importance'] = 0.6 (reduced)

# Apply to recommendation
config = RecommendationConfig(**weights)
recommender = PersonalizedRecommender(config=config)
"""
