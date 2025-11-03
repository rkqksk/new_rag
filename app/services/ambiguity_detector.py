"""
Ambiguity Detection Service
Detects ambiguous searches and generates clarifying suggestions
"""
from typing import List, Dict, Any
from collections import Counter
import re


def detect_ambiguity(query: str, results: List[Dict[str, Any]], criteria: Dict[str, Any]) -> Dict[str, Any]:
    """Detect if search is ambiguous and needs clarification

    Returns:
        {
            "is_ambiguous": bool,
            "reason": str,
            "suggestions": List[Dict],
            "threshold": int
        }
    """
    from app.services.product_search import extract_capacity
    
    AMBIGUITY_THRESHOLD = 20

    # Check if query has minimal criteria
    capacity_from_query = extract_capacity(query)
    has_capacity = criteria.get('capacity') is not None or capacity_from_query is not None
    has_material = criteria.get('material') is not None
    has_product_type = criteria.get('product_type') is not None
    has_neck_size = criteria.get('neck_size') is not None

    minimal_criteria = not (has_capacity or has_material or has_product_type or has_neck_size)

    # If minimal criteria AND too many results, it's ambiguous
    if minimal_criteria and len(results) > AMBIGUITY_THRESHOLD:
        suggestions = generate_clarifying_suggestions(results)

        return {
            "is_ambiguous": True,
            "reason": "too_many_results_minimal_criteria",
            "suggestions": suggestions,
            "threshold": AMBIGUITY_THRESHOLD,
            "result_count": len(results)
        }

    return {
        "is_ambiguous": False,
        "reason": None,
        "suggestions": [],
        "threshold": AMBIGUITY_THRESHOLD,
        "result_count": len(results)
    }


def generate_clarifying_suggestions(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate clarifying question suggestions based on result diversity"""
    suggestions = []

    # 1. Category type distribution
    category_types = [r.get('category_type') for r in results if r.get('category_type')]
    type_counts = Counter(category_types)

    if len(type_counts) > 1:
        type_labels = {
            'BOTTLE': '용기/병',
            'JAR': '자용기',
            'CAP': '캡/뚜껑',
            'PUMP': '펌프'
        }

        type_options = []
        for cat_type, count in type_counts.most_common():
            type_options.append({
                'value': cat_type,
                'label': type_labels.get(cat_type, cat_type),
                'count': count
            })

        suggestions.append({
            'type': 'category_type',
            'question': '어떤 제품 타입을 찾으시나요?',
            'priority': 1,
            'options': type_options
        })

    # 2. Capacity distribution
    capacities = []
    for r in results:
        cap_str = r.get('capacity', '')
        if cap_str and ('ml' in cap_str.lower() or 'g' in cap_str.lower()):
            match = re.search(r'(\d+)', cap_str)
            if match:
                capacities.append(int(match.group(1)))

    if capacities:
        capacity_ranges = {
            '50ml 이하': (0, 50),
            '50-100ml': (50, 100),
            '100-300ml': (100, 300),
            '300-500ml': (300, 500),
            '500ml 이상': (500, 10000)
        }

        range_counts = {}
        for cap in capacities:
            for range_name, (min_val, max_val) in capacity_ranges.items():
                if min_val < cap <= max_val:
                    range_counts[range_name] = range_counts.get(range_name, 0) + 1
                    break

        if range_counts:
            capacity_options = [
                {'value': range_name, 'label': range_name, 'count': count}
                for range_name, count in sorted(range_counts.items(), key=lambda x: x[1], reverse=True)
            ]

            suggestions.append({
                'type': 'capacity_range',
                'question': '예상 용량 범위가 어떻게 되시나요?',
                'priority': 2,
                'options': capacity_options
            })

    # 3. Material distribution
    materials = [r.get('material') for r in results if r.get('material')]
    material_counts = Counter(materials)

    if len(material_counts) > 1:
        material_options = [
            {'value': material, 'label': material, 'count': count}
            for material, count in material_counts.most_common()
        ]

        suggestions.append({
            'type': 'material',
            'question': '재질 선호도가 있으신가요?',
            'priority': 3,
            'options': material_options
        })

    # Sort by priority
    suggestions.sort(key=lambda x: x['priority'])

    return suggestions
