"""
Product Search Service
Handles capacity extraction, product searching, and contextual filtering
"""
from typing import List, Dict, Any, Optional, Tuple
import re


def extract_capacity(query: str) -> Optional[Tuple[int, str]]:
    """Extract capacity value and unit from query

    Returns:
        tuple: (value, unit) where unit can be 'ml', 'g', or 'any' (for number-only queries)

    Examples:
        "50" → (50, 'any')      # Search both 50ml AND 50g
        "50ml" → (50, 'ml')     # Search 50ml ONLY
        "50미리" → (50, 'ml')    # Search 50ml ONLY
        "50g" → (50, 'g')       # Search 50g ONLY
    """
    # Pattern 1: Number with explicit unit (50ml, 50g, 50미리, etc.)
    ml_patterns = [
        r'(\d+)\s*(ml|ML)',
        r'(\d+)\s*(미리|밀리)',
    ]

    for pattern in ml_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            value = int(match.group(1))
            return (value, 'ml')

    # Check g/그램 patterns
    g_patterns = [
        r'(\d+)\s*(g|G)',
        r'(\d+)\s*그램',
    ]

    for pattern in g_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            value = int(match.group(1))
            return (value, 'g')

    # Pattern 2: Number only (50, 100, etc.) - search BOTH ml and g
    number_only_pattern = r'\b(\d+)\b'
    match = re.search(number_only_pattern, query)
    if match:
        value = int(match.group(1))
        return (value, 'any')

    return None


def is_contextual_query(query: str) -> bool:
    """Check if query references previous search results

    Keywords: 이중에, 여기서, 그중에서, 그 중, 이 중, 저기서, 거기서
    """
    context_keywords = [
        '이중에', '이 중에', '이중',
        '여기서', '여기에서',
        '그중에', '그 중에', '그중',
        '저기서', '저기에서',
        '거기서', '거기에서'
    ]
    query_lower = query.lower()
    return any(kw in query_lower for kw in context_keywords)


def filter_previous_results(query: str, previous_results: List[Dict[str, Any]], limit: int = 1000) -> List[Dict[str, Any]]:
    """Filter previous search results based on additional criteria

    Args:
        query: New query with filter criteria (e.g., "이중에 PETG만")
        previous_results: Previous search results
        limit: Maximum number of results

    Returns:
        Filtered results matching new criteria
    """
    query_lower = query.lower()

    # Extract filter criteria from query
    material_keywords = {
        'PETG': ['petg', '피이티지'],
        'HDPE': ['hdpe', 'high-density', '고밀도'],
        'PET': ['pet', '페트', '폴리에틸렌 테레프탈레이트', '피이티'],
        'PP': ['pp', '폴리프로필렌', 'polypropylene', '피피'],
        'PE': ['pe', '폴리에틸렌', 'polyethylene', '피이', 'ㅍㅇ']
    }

    # Check for material filter
    requested_material = None
    for material, keywords in material_keywords.items():
        if any(kw in query_lower for kw in keywords):
            requested_material = material
            break

    # Check for capacity filter
    capacity_match = extract_capacity(query)

    # Filter results
    filtered = []
    for product in previous_results:
        # Apply material filter
        if requested_material:
            product_material = product.get('material', '').upper()
            if product_material != requested_material:
                continue

        # Apply capacity filter
        if capacity_match:
            product_capacity_str = product.get('capacity', '')
            product_capacity_match = extract_capacity(product_capacity_str)

            if product_capacity_match:
                if capacity_match[1] == 'any':
                    if not (product_capacity_match[0] == capacity_match[0] and
                            product_capacity_match[1] in ['ml', 'g']):
                        continue
                else:
                    if not (product_capacity_match[0] == capacity_match[0] and
                            product_capacity_match[1] == capacity_match[1]):
                        continue
            else:
                continue

        filtered.append(product)

    return filtered[:limit]


def search_products(query: str, products: Dict[str, Any], limit: int = 1000) -> List[Dict[str, Any]]:
    """Search products with criteria matching AND keyword matching

    Priority order:
    1. Product code exact match (absolute - returns only 1 product)
    2. Exact criteria match WITH keyword match (e.g., "50ml 거품펌프")
    3. Keyword-only match (e.g., "거품" → matches "거품펌프", "거품용기")
    4. Exact criteria match without keyword (e.g., "50ml PET")
    5. Capacity match only (fallback)
    """
    query_lower = query.lower()
    query_upper = query.upper()

    # Priority 1: Product code exact match
    product_code_pattern = r'[A-Z]{2}\d{3,4}[-_][A-Z]\d{3}(?:\(\d+\))?'
    code_match = re.search(product_code_pattern, query_upper, re.IGNORECASE)

    if code_match:
        search_code = code_match.group(0).upper()
        for product_id, product in products.items():
            product_code = product.get('product_code', '').upper()
            if product_code == search_code:
                product_data = product.copy()
                product_data['product_id'] = product_id
                product_data['score'] = 100
                return [product_data]

    # Extract search criteria
    capacity_match = extract_capacity(query)

    # Material keywords (check longer keywords first)
    material_keywords = {
        'PETG': ['petg', '피이티지'],
        'HDPE': ['hdpe', 'high-density', '고밀도'],
        'PET': ['pet', '페트', '폴리에틸렌 테레프탈레이트', '피이티'],
        'PP': ['pp', '폴리프로필렌', 'polypropylene', '피피'],
        'PE': ['pe', '폴리에틸렌', 'polyethylene', '피이', 'ㅍㅇ']
    }

    requested_material = None
    for material, keywords in material_keywords.items():
        if any(kw in query_lower for kw in keywords):
            requested_material = material
            break

    # Product type keywords
    product_type_keywords = {
        'PUMP': ['펌프', 'pump', '분사', '스프레이'],
        'CAP': ['캡', 'cap', '뚜껑', '마개', '원터치'],
        'JAR': ['jar', '자', '항아리'],
        'BOTTLE': ['병', 'bottle', '보틀', '컨테이너'],
    }

    requested_product_type = None
    for product_type, keywords in product_type_keywords.items():
        if any(kw in query_lower for kw in keywords):
            requested_product_type = product_type
            break

    # Extract keywords from query
    query_keywords = query_lower

    # Remove capacity patterns
    if capacity_match:
        query_keywords = re.sub(r'\d+\s*(ml|g|미리|밀리|리터)', '', query_keywords)

    # Remove material keywords
    if requested_material:
        for mat_kws in material_keywords.values():
            for kw in mat_kws:
                query_keywords = query_keywords.replace(kw, '')

    # Extract meaningful keywords (2+ chars)
    keyword_tokens = [kw.strip() for kw in query_keywords.split() if len(kw.strip()) >= 2]
    generic_stopwords = ['제품', '상품', '아이템']
    keyword_tokens = [kw for kw in keyword_tokens if kw not in generic_stopwords]

    # Extract neck size
    requested_neck_size = None
    neck_patterns = [
        r'(\d+)\s*파이',
        r'Ø\s*(\d+)',
        r'내경\s*Ø?\s*(\d+)',
    ]

    for pattern in neck_patterns:
        neck_match = re.search(pattern, query, re.IGNORECASE)
        if neck_match:
            neck_value = neck_match.group(1)
            requested_neck_size = f"{neck_value}파이"
            break

    # Extract dosage
    requested_dosage = None
    dosage_patterns = [
        r'(\d+\.?\d*)\s*cc',
        r'토출량\s*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*씨씨',
    ]

    for pattern in dosage_patterns:
        dosage_match = re.search(pattern, query, re.IGNORECASE)
        if dosage_match:
            requested_dosage = float(dosage_match.group(1))
            break

    # Filter products
    exact_matches = []
    keyword_matches = []
    fallback_matches = []

    for product_id, product in products.items():
        product_data = product.copy()
        product_data['product_id'] = product_id

        product_name = product.get('product_name', '').lower()
        capacity_str = product.get('capacity', '')
        product_material = product.get('material', '').upper()
        product_category_type = product.get('category_type', '').upper()
        product_neck_size = product.get('neck_size', '')

        product_capacity_match = extract_capacity(capacity_str)

        # Check capacity match
        capacity_matches = False
        if capacity_match and product_capacity_match:
            if capacity_match[1] == 'any':
                if (product_capacity_match[0] == capacity_match[0] and
                    product_capacity_match[1] in ['ml', 'g']):
                    capacity_matches = True
            elif (product_capacity_match[0] == capacity_match[0] and
                  product_capacity_match[1] == capacity_match[1]):
                capacity_matches = True
        elif not capacity_match:
            capacity_matches = True

        # Check material match
        material_matches = False
        if requested_material:
            if product_material == requested_material:
                material_matches = True
        else:
            material_matches = True

        # Check product type match
        product_type_matches = False
        if requested_product_type:
            if product_category_type == requested_product_type:
                product_type_matches = True
        else:
            product_type_matches = True

        # Check neck size match
        neck_size_matches = False
        if requested_neck_size:
            if product_neck_size == requested_neck_size:
                neck_size_matches = True
        else:
            neck_size_matches = True

        # Check dosage match
        dosage_matches = False
        if requested_dosage:
            product_dosage = product.get('specifications', {}).get('dosage_value')
            if product_dosage and abs(product_dosage - requested_dosage) < 0.001:
                dosage_matches = True
        else:
            dosage_matches = True

        # Check keyword matching
        keyword_score = 0
        if keyword_tokens:
            for keyword in keyword_tokens:
                if keyword in product_name:
                    keyword_score += 2
                else:
                    keyword_parts = []
                    if len(keyword) >= 4:
                        mid = len(keyword) // 2
                        keyword_parts = [keyword[:mid], keyword[mid:]]
                    else:
                        keyword_parts = [keyword]

                    all_parts_match = True
                    for part in keyword_parts:
                        if len(part) >= 2 and part not in product_name:
                            all_parts_match = False
                            break

                    if all_parts_match and len(keyword_parts) > 1:
                        keyword_score += 1

        # Priority classification
        if keyword_score > 0 and capacity_matches and material_matches and product_type_matches and neck_size_matches and dosage_matches:
            product_data['score'] = 100 + keyword_score * 10
            exact_matches.append(product_data)
        elif keyword_score > 0 and not (capacity_match or requested_material or requested_product_type or requested_neck_size or requested_dosage):
            product_data['score'] = 90 + keyword_score * 5
            keyword_matches.append(product_data)
        elif capacity_matches and material_matches and product_type_matches and neck_size_matches and dosage_matches:
            product_data['score'] = 80
            exact_matches.append(product_data)
        elif capacity_matches and not requested_material and not requested_product_type and not requested_neck_size and not requested_dosage:
            product_data['score'] = 50
            fallback_matches.append(product_data)

    # Combine and sort
    all_matches = exact_matches + keyword_matches + fallback_matches

    if not all_matches:
        return []

    all_matches.sort(key=lambda x: x['score'], reverse=True)

    return all_matches[:limit]
