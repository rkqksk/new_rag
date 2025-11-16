"""
Product Compatibility Matcher
Matches bottles with compatible caps/pumps based on neck size
"""

import re
from typing import Any, Dict, List, Optional


def extract_neck_size(spec: str) -> Optional[int]:
    """Extract neck size (Ø value) from product spec

    Examples:
        "23x53(mm)/Ø20" -> 20
        "내경 Ø24" -> 24
        "Ø28" -> 28
        "내경Ø43" -> 43

    Args:
        spec: Product specification string

    Returns:
        Neck size in mm, or None if not found
    """
    if not spec or not isinstance(spec, str):
        return None

    # Pattern: Ø followed by number (with or without space)
    # Handles: "Ø20", "Ø 20", "내경 Ø24", "내경Ø24"
    pattern = r"[Øø]\s*(\d+)"
    match = re.search(pattern, spec)

    if match:
        return int(match.group(1))

    return None


def get_product_category(product: Dict[str, Any]) -> str:
    """Get product category (Bottle, Jar, CapPump)

    Args:
        product: Product dictionary

    Returns:
        Category string: "Bottle", "Jar", "CapPump", "Other"
    """
    # Try product_name first
    name = product.get("product_name", "").lower()

    # Bottle indicators
    if any(word in name for word in ["브로우", "bottle", "용기"]):
        return "Bottle"

    # Jar indicators
    if any(word in name for word in ["크림", "jar", "사출"]):
        return "Jar"

    # Cap/Pump indicators
    if any(word in name for word in ["캡", "cap", "펌프", "pump"]):
        return "CapPump"

    # Try product code pattern
    code = product.get("product_code", "")
    if code:
        prefix = code[:2].upper()
        if prefix in ["BE", "BT", "BG", "BP", "BO"]:  # Bottle prefixes
            return "Bottle"
        elif prefix in ["JA", "JT", "JE", "JP"]:  # Jar prefixes
            return "Jar"
        elif prefix in ["CA", "CP", "EO", "FO", "IO", "LO"]:  # Cap/Pump prefixes
            return "CapPump"

    return "Other"


def get_recommended_dosage_for_capacity(capacity_ml: float) -> tuple:
    """Get recommended pump dosage range for bottle capacity

    Args:
        capacity_ml: Bottle capacity in ml

    Returns:
        (min_dosage, max_dosage) in cc
    """
    if capacity_ml <= 50:
        # Small bottles (30-50ml) → small dosage pumps
        return (0.1, 0.15)
    elif capacity_ml <= 100:
        # Medium-small bottles (50-100ml) → medium-small dosage pumps
        return (0.12, 0.2)
    elif capacity_ml <= 200:
        # Medium bottles (100-200ml) → medium dosage pumps
        return (0.2, 0.3)
    elif capacity_ml <= 500:
        # Large bottles (200-500ml) → large dosage pumps
        return (0.3, 0.5)
    else:
        # Extra large bottles (500ml+) → high dosage pumps
        return (0.5, 2.0)


def find_compatible_accessories(
    bottles: List[Dict[str, Any]], all_products: Dict[str, Any], limit: int = 10
) -> Dict[str, Any]:
    """Find compatible caps/pumps for given bottles, grouped by neck size

    Pump recommendations are sorted by dosage suitability based on bottle capacity:
    - Small bottles (30-50ml) → 0.1-0.15cc pumps (mist/spray)
    - Medium bottles (100-200ml) → 0.2-0.3cc pumps (essence/regular)
    - Large bottles (200-500ml) → 0.3-0.5cc pumps (lotion)
    - Extra large bottles (500ml+) → 0.5-2.0cc pumps (high-density)

    Args:
        bottles: List of bottle products from current context
        all_products: All available products dictionary
        limit: Maximum accessories per neck size

    Returns:
        {
            "groups": [
                {
                    "neck_size": 20,
                    "bottles": [...],  # Bottles with Ø20
                    "pumps": [...],    # Compatible Ø20 pumps (sorted by dosage suitability)
                    "caps": [...],     # Compatible Ø20 caps
                    "total_accessories": 15,
                    "recommended_dosage_range": (0.12, 0.2)  # Based on bottle capacity
                },
                {
                    "neck_size": 18,
                    "bottles": [...],  # Bottles with Ø18
                    "pumps": [...],    # Compatible Ø18 pumps (sorted by dosage suitability)
                    "caps": [...],     # Compatible Ø18 caps
                    "total_accessories": 8,
                    "recommended_dosage_range": (0.1, 0.15)
                }
            ],
            "summary": {
                "total_groups": 2,
                "neck_sizes": [20, 18],
                "total_bottles": 3,
                "total_accessories": 23
            }
        }
    """
    # Group bottles by neck size
    bottles_by_neck = {}
    for bottle in bottles:
        spec = bottle.get("spec", "")
        neck_size = extract_neck_size(spec)
        if neck_size:
            if neck_size not in bottles_by_neck:
                bottles_by_neck[neck_size] = []
            bottles_by_neck[neck_size].append(bottle)

    if not bottles_by_neck:
        return {
            "groups": [],
            "summary": {
                "total_groups": 0,
                "neck_sizes": [],
                "total_bottles": 0,
                "total_accessories": 0,
            },
        }

    # Find accessories for each neck size group
    groups = []
    total_accessories = 0

    for neck_size in sorted(bottles_by_neck.keys(), reverse=True):  # Largest first
        group_bottles = bottles_by_neck[neck_size]
        compatible_pumps = []
        compatible_caps = []

        # Calculate average bottle capacity for this group (for dosage recommendation)
        capacities = []
        for bottle in group_bottles:
            capacity_str = bottle.get("capacity", "")
            # Extract numeric capacity from "70ml", "100g" etc
            capacity_match = re.search(r"(\d+(?:\.\d+)?)", capacity_str)
            if capacity_match:
                capacities.append(float(capacity_match.group(1)))

        avg_capacity = sum(capacities) / len(capacities) if capacities else 100
        recommended_dosage_range = get_recommended_dosage_for_capacity(avg_capacity)

        # Find all accessories with matching neck size
        for product_id, product in all_products.items():
            category = get_product_category(product)

            if category != "CapPump":
                continue

            # Check if neck size matches
            spec = product.get("spec", "")
            product_neck_size = extract_neck_size(spec)

            if product_neck_size == neck_size:
                product_data = product.copy()
                product_data["product_id"] = product_id
                product_data["category"] = category
                product_data["neck_size"] = neck_size

                # Classify as pump or cap
                name = product.get("product_name", "").lower()
                if "펌프" in name or "pump" in name:
                    # Get pump dosage for suitability scoring
                    dosage = product.get("specifications", {}).get("dosage_value", 0)
                    product_data["dosage"] = dosage

                    # Calculate dosage suitability score (0-100)
                    # Perfect match: dosage within recommended range = 100
                    # Outside range: proportional penalty
                    min_dosage, max_dosage = recommended_dosage_range
                    if min_dosage <= dosage <= max_dosage:
                        product_data["dosage_suitability"] = 100
                    elif dosage < min_dosage:
                        # Too small: penalty based on difference
                        product_data["dosage_suitability"] = max(
                            0, 100 - (min_dosage - dosage) * 200
                        )
                    else:
                        # Too large: penalty based on difference
                        product_data["dosage_suitability"] = max(
                            0, 100 - (dosage - max_dosage) * 200
                        )

                    compatible_pumps.append(product_data)
                else:
                    compatible_caps.append(product_data)

        # Sort pumps by dosage suitability (best matches first)
        compatible_pumps.sort(key=lambda p: p.get("dosage_suitability", 0), reverse=True)

        group_total = len(compatible_pumps) + len(compatible_caps)
        total_accessories += group_total

        groups.append(
            {
                "neck_size": neck_size,
                "bottles": group_bottles,
                "pumps": compatible_pumps[:limit],
                "caps": compatible_caps[:limit],
                "total_pumps": len(compatible_pumps),
                "total_caps": len(compatible_caps),
                "total_accessories": group_total,
                "recommended_dosage_range": recommended_dosage_range,
                "avg_bottle_capacity": avg_capacity,
            }
        )

    return {
        "groups": groups,
        "summary": {
            "total_groups": len(groups),
            "neck_sizes": sorted(bottles_by_neck.keys(), reverse=True),
            "total_bottles": len(bottles),
            "total_accessories": total_accessories,
        },
    }


def format_accessory_recommendation(
    bottles: List[Dict[str, Any]], accessories: Dict[str, Any]
) -> str:
    """Format accessory recommendation message

    Args:
        bottles: Bottles from context
        accessories: Compatible accessories from find_compatible_accessories

    Returns:
        Formatted recommendation message
    """
    neck_sizes = accessories["neck_sizes"]

    if not neck_sizes:
        return "죄송합니다. 선택하신 용기의 neck size 정보를 찾을 수 없습니다."

    pumps = accessories["compatible_pumps"]
    caps = accessories["compatible_caps"]

    msg_parts = []
    msg_parts.append(f"선택하신 용기는 Ø{', Ø'.join(map(str, neck_sizes))} neck size입니다.")

    if pumps:
        msg_parts.append(f"\n\n호환 가능한 펌프 {len(pumps)}개:")
        for i, pump in enumerate(pumps[:5], 1):
            msg_parts.append(f"  {i}. {pump.get('product_name')} (Ø{pump.get('neck_size')})")

    if caps:
        msg_parts.append(f"\n\n호환 가능한 캡 {len(caps)}개:")
        for i, cap in enumerate(caps[:5], 1):
            msg_parts.append(f"  {i}. {cap.get('product_name')} (Ø{cap.get('neck_size')})")

    if not pumps and not caps:
        msg_parts.append("\n\n현재 호환 가능한 펌프/캡이 데이터베이스에 없습니다.")

    return "".join(msg_parts)
