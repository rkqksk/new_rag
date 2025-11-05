#!/usr/bin/env python3
"""
Query Enhancement System

Intelligent query processing to avoid false matches:
- Extract capacity, neck_size, material from query
- Generate smart Qdrant filters
- Validate results match query intent
- Fallback search if needed

Problem Examples:
- "50ml" should NOT match "50파이 튜브" (neck size 50 ≠ capacity 50ml)
- "20파이" should NOT match "20ml 병" (neck size 20 ≠ capacity 20ml)
- "PET 병" should only match material PET
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class QueryIntent:
    """
    Extracted intent from user query

    Attributes:
        capacity_value: Numeric capacity value (e.g., 50)
        capacity_unit: Unit (ml, cc, g)
        neck_size: Neck diameter in mm (e.g., 20)
        materials: List of materials (e.g., ["PET", "PP"])
        product_type: Product type keywords
        original_query: Original user query
        has_capacity: Whether capacity was detected
        has_neck_size: Whether neck size was detected
        has_material: Whether material was detected
    """
    capacity_value: Optional[float] = None
    capacity_unit: Optional[str] = None
    neck_size: Optional[int] = None
    materials: List[str] = None
    product_type: Optional[str] = None
    original_query: str = ""
    has_capacity: bool = False
    has_neck_size: bool = False
    has_material: bool = False

    def __post_init__(self):
        if self.materials is None:
            self.materials = []


class QueryAnalyzer:
    """
    Analyze user query and extract intent

    Detects:
    - Capacity: 50ml, 100cc, 30g
    - Neck size: 20파이, 24phi, neck 20
    - Materials: PET, PP, HDPE, etc.
    """

    def __init__(self):
        # Capacity patterns (ml, cc, g)
        self.capacity_patterns = [
            # Korean + numbers
            (r'(\d+(?:\.\d+)?)\s*ml', 'ml'),
            (r'(\d+(?:\.\d+)?)\s*밀리리터', 'ml'),
            (r'(\d+(?:\.\d+)?)\s*밀리', 'ml'),
            (r'(\d+(?:\.\d+)?)\s*cc', 'cc'),
            (r'(\d+(?:\.\d+)?)\s*시시', 'cc'),
            (r'(\d+(?:\.\d+)?)\s*g', 'g'),
            (r'(\d+(?:\.\d+)?)\s*그램', 'g'),
        ]

        # Neck size patterns (파이, phi, mm)
        self.neck_size_patterns = [
            r'(\d+)\s*파이',  # 20파이
            r'(\d+)\s*phi',   # 20phi
            r'(\d+)\s*Φ',     # 20Φ
            r'(\d+)\s*ø',     # 20ø
            r'neck\s*[×xXØø]?\s*(\d+)',  # neck 20, neck×20
        ]

        # Material keywords
        self.material_keywords = {
            'PET': ['PET', '페트', 'pet'],
            'PP': ['PP', '피피', 'pp', '폴리프로필렌'],
            'PE': ['PE', '피이', 'pe', '폴리에틸렌'],
            'HDPE': ['HDPE', '에이치디피이', 'hdpe'],
            'LDPE': ['LDPE', '엘디피이', 'ldpe'],
            'PS': ['PS', '피에스', 'ps', '폴리스티렌'],
            'PVC': ['PVC', '피브이씨', 'pvc'],
            'PETG': ['PETG', '피이티쥐', 'petg'],
            'PC': ['PC', '피씨', 'pc', '폴리카보네이트'],
            'ABS': ['ABS', '에이비에스', 'abs'],
            '기타': ['기타', 'OTHER', 'other'],
        }

        # Product type keywords with category-specific unit preferences
        self.product_types = {
            '병': {
                'keywords': ['병', 'bottle', '보틀'],
                'preferred_unit': 'ml',  # Bottles typically measured in ml
                'alternative_units': ['cc'],
                'uses_neck_size': False
            },
            '자': {
                'keywords': ['자', 'jar', '항아리'],
                'preferred_unit': 'g',  # Jars typically for creams/solids (weight)
                'alternative_units': ['ml', 'cc'],
                'uses_neck_size': False
            },
            '용기': {
                'keywords': ['용기', 'container', '컨테이너'],
                'preferred_unit': 'ml',  # General containers
                'alternative_units': ['g', 'cc'],
                'uses_neck_size': False
            },
            '펌프': {
                'keywords': ['펌프', 'pump'],
                'preferred_unit': '파이',  # Pumps measured by neck size
                'alternative_units': [],
                'uses_neck_size': True
            },
            '디스펜서': {
                'keywords': ['디스펜서', 'dispenser'],
                'preferred_unit': '파이',
                'alternative_units': [],
                'uses_neck_size': True
            },
            '캡': {
                'keywords': ['캡', 'cap', '뚜껑'],
                'preferred_unit': '파이',  # Caps measured by neck size
                'alternative_units': [],
                'uses_neck_size': True
            },
            '튜브': {
                'keywords': ['튜브', 'tube'],
                'preferred_unit': '파이',  # Tubes can have neck size
                'alternative_units': ['g', 'ml'],  # But also capacity
                'uses_neck_size': True
            },
            '스프레이': {
                'keywords': ['스프레이', 'spray'],
                'preferred_unit': '파이',
                'alternative_units': ['ml'],
                'uses_neck_size': True
            },
        }

    def analyze(self, query: str) -> QueryIntent:
        """
        Analyze query and extract intent with category-aware disambiguation

        Args:
            query: User query string

        Returns:
            QueryIntent with extracted information
        """
        intent = QueryIntent(original_query=query)

        # Normalize query
        query_lower = query.lower()

        # 1. Extract product type FIRST (needed for disambiguation)
        product_type = self._extract_product_type(query)
        if product_type:
            intent.product_type = product_type

        # 2. Disambiguate ambiguous numbers based on category
        disambiguated_query = self._disambiguate_numbers(query_lower, product_type)

        # 3. Extract capacity
        capacity = self._extract_capacity(disambiguated_query)
        if capacity:
            intent.capacity_value = capacity[0]
            intent.capacity_unit = capacity[1]
            intent.has_capacity = True

        # 4. Extract neck size
        neck_size = self._extract_neck_size(disambiguated_query)
        if neck_size:
            intent.neck_size = neck_size
            intent.has_neck_size = True

        # 5. Extract materials
        materials = self._extract_materials(query)
        if materials:
            intent.materials = materials
            intent.has_material = True

        return intent

    def _disambiguate_numbers(self, query: str, product_type: Optional[str]) -> str:
        """
        Disambiguate bare numbers based on product category

        Examples:
            "20 펌프" → "20파이 펌프" (pumps use neck size)
            "20 병" → "20ml 병" (bottles use capacity)
            "50 튜브" → ambiguous, don't change

        Args:
            query: User query
            product_type: Detected product type

        Returns:
            Query with disambiguated units
        """
        if not product_type or product_type not in self.product_types:
            return query

        category_info = self.product_types[product_type]
        preferred_unit = category_info['preferred_unit']

        # Pattern: bare number followed by product type keyword
        # e.g., "20 펌프", "50 병", "100 용기"
        pattern = r'(\d+)\s+(' + '|'.join(category_info['keywords']) + r')'

        def replacer(match):
            number = match.group(1)
            product_word = match.group(2)

            if preferred_unit == '파이':
                # Add 파이 for neck size categories
                return f"{number}파이 {product_word}"
            elif preferred_unit == 'ml':
                # Add ml for capacity categories
                return f"{number}ml {product_word}"
            elif preferred_unit == 'g':
                # Add g for weight categories
                return f"{number}g {product_word}"
            else:
                # No change if unsure
                return match.group(0)

        return re.sub(pattern, replacer, query, flags=re.IGNORECASE)

    def _extract_capacity(self, query: str) -> Optional[Tuple[float, str]]:
        """Extract capacity value and unit"""
        for pattern, unit in self.capacity_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    return (value, unit)
                except ValueError:
                    continue
        return None

    def _extract_neck_size(self, query: str) -> Optional[int]:
        """Extract neck size in mm"""
        for pattern in self.neck_size_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None

    def _extract_materials(self, query: str) -> List[str]:
        """Extract material keywords"""
        materials = []
        query_upper = query.upper()

        for material, keywords in self.material_keywords.items():
            for keyword in keywords:
                if keyword.upper() in query_upper:
                    materials.append(material)
                    break

        return materials

    def _extract_product_type(self, query: str) -> Optional[str]:
        """Extract product type"""
        for product_type, metadata in self.product_types.items():
            for keyword in metadata['keywords']:
                if keyword in query.lower():
                    return product_type
        return None


class SmartFilterGenerator:
    """
    Generate Qdrant filters from query intent

    Prevents false matches by using metadata filtering
    """

    def generate(self, intent: QueryIntent) -> Dict[str, Any]:
        """
        Generate Qdrant filter from intent

        Args:
            intent: QueryIntent object

        Returns:
            Dict with Qdrant filter conditions
        """
        must_conditions = []

        # 1. Capacity filter (if detected)
        if intent.has_capacity and intent.capacity_value is not None:
            # Range: ±5% tolerance
            tolerance = intent.capacity_value * 0.05
            must_conditions.append({
                'key': 'metadata.capacity_value',
                'range': {
                    'gte': intent.capacity_value - tolerance,
                    'lte': intent.capacity_value + tolerance
                }
            })

            # Unit match
            if intent.capacity_unit:
                must_conditions.append({
                    'key': 'metadata.capacity_unit',
                    'match': {'value': intent.capacity_unit}
                })

        # 2. Neck size filter (if detected)
        if intent.has_neck_size and intent.neck_size is not None:
            # Exact match (±1mm tolerance)
            must_conditions.append({
                'key': 'metadata.neck_size',
                'range': {
                    'gte': intent.neck_size - 1,
                    'lte': intent.neck_size + 1
                }
            })

        # 3. Material filter (if detected)
        if intent.has_material and intent.materials:
            must_conditions.append({
                'key': 'metadata.materials',
                'match': {'any': intent.materials}
            })

        # Build filter
        if must_conditions:
            return {'must': must_conditions}
        else:
            return {}


class ResultValidator:
    """
    Validate search results match query intent

    Checks if results actually satisfy the extracted intent
    """

    def validate(self, results: List[Dict[str, Any]], intent: QueryIntent) -> List[Dict[str, Any]]:
        """
        Filter results to match intent

        Args:
            results: Search results from Qdrant
            intent: QueryIntent object

        Returns:
            Filtered results that match intent
        """
        validated = []

        for result in results:
            metadata = result.get('metadata', {})

            # Check capacity match (if intent has capacity)
            if intent.has_capacity:
                if not self._validate_capacity(metadata, intent):
                    continue

            # Check neck size match (if intent has neck size)
            if intent.has_neck_size:
                if not self._validate_neck_size(metadata, intent):
                    continue

            # Check material match (if intent has material)
            if intent.has_material:
                if not self._validate_material(metadata, intent):
                    continue

            validated.append(result)

        return validated

    def _validate_capacity(self, metadata: Dict[str, Any], intent: QueryIntent) -> bool:
        """Check if metadata capacity matches intent"""
        capacity_value = metadata.get('capacity_value')
        capacity_unit = metadata.get('capacity_unit')

        if capacity_value is None:
            return False

        # Check unit match
        if intent.capacity_unit and capacity_unit != intent.capacity_unit:
            return False

        # Check value match (±10% tolerance)
        tolerance = intent.capacity_value * 0.10
        return abs(capacity_value - intent.capacity_value) <= tolerance

    def _validate_neck_size(self, metadata: Dict[str, Any], intent: QueryIntent) -> bool:
        """Check if metadata neck size matches intent"""
        neck_size = metadata.get('neck_size')

        if neck_size is None:
            return False

        # Exact match (±2mm tolerance)
        return abs(neck_size - intent.neck_size) <= 2

    def _validate_material(self, metadata: Dict[str, Any], intent: QueryIntent) -> bool:
        """Check if metadata material matches intent"""
        materials = metadata.get('materials', [])

        if not materials:
            return False

        # Check if any intent material is in product materials
        return any(mat in materials for mat in intent.materials)


class QueryEnhancer:
    """
    Complete query enhancement pipeline

    Usage:
        enhancer = QueryEnhancer()
        enhanced = enhancer.enhance_query("50ml PET 병")

        # enhanced = {
        #     'original_query': '50ml PET 병',
        #     'intent': QueryIntent(...),
        #     'filter': {'must': [...]},
        #     'refined_query': '50ml PET bottle capacity'
        # }
    """

    def __init__(self):
        self.analyzer = QueryAnalyzer()
        self.filter_generator = SmartFilterGenerator()
        self.validator = ResultValidator()

    def enhance_query(self, query: str) -> Dict[str, Any]:
        """
        Enhance user query with intent extraction and filtering

        Args:
            query: Original user query

        Returns:
            Dict with enhanced query information
        """
        # 1. Analyze query
        intent = self.analyzer.analyze(query)

        # 2. Generate filters
        filters = self.filter_generator.generate(intent)

        # 3. Refine query text (remove extracted info to avoid duplication)
        refined_query = self._refine_query_text(query, intent)

        return {
            'original_query': query,
            'intent': intent,
            'filter': filters,
            'refined_query': refined_query,
            'has_filters': len(filters) > 0
        }

    def validate_results(self, results: List[Dict[str, Any]], intent: QueryIntent) -> List[Dict[str, Any]]:
        """
        Validate and filter results

        Args:
            results: Search results
            intent: QueryIntent object

        Returns:
            Validated results
        """
        return self.validator.validate(results, intent)

    def _refine_query_text(self, query: str, intent: QueryIntent) -> str:
        """
        Remove extracted info from query to avoid duplication

        Example: "50ml PET 병" → "병" (capacity and material already in filter)
        """
        refined = query

        # Remove capacity mentions
        if intent.has_capacity:
            refined = re.sub(r'\d+(?:\.\d+)?\s*(?:ml|밀리|cc|시시|g|그램)', '', refined, flags=re.IGNORECASE)

        # Remove neck size mentions
        if intent.has_neck_size:
            refined = re.sub(r'\d+\s*(?:파이|phi|Φ|ø)', '', refined, flags=re.IGNORECASE)
            refined = re.sub(r'neck\s*[×xXØø]?\s*\d+', '', refined, flags=re.IGNORECASE)

        # Remove material mentions (keep in query for semantic search)
        # Materials are useful for vector search, so don't remove

        # Clean up extra spaces
        refined = ' '.join(refined.split())

        return refined if refined.strip() else query


def main():
    """Test query enhancer"""
    enhancer = QueryEnhancer()

    test_queries = [
        "50ml PET 병",
        "20파이 펌프",
        "100cc PP 용기",
        "24phi 스프레이",
        "HDPE 튜브 30g",
        "화장품 용기",  # No specific constraints
    ]

    print("="*80)
    print("QUERY ENHANCEMENT TEST")
    print("="*80)

    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        enhanced = enhancer.enhance_query(query)

        intent = enhanced['intent']
        print(f"   Intent:")
        if intent.has_capacity:
            print(f"      Capacity: {intent.capacity_value}{intent.capacity_unit}")
        if intent.has_neck_size:
            print(f"      Neck Size: {intent.neck_size}mm")
        if intent.has_material:
            print(f"      Materials: {', '.join(intent.materials)}")
        if intent.product_type:
            print(f"      Product Type: {intent.product_type}")

        print(f"   Refined Query: '{enhanced['refined_query']}'")
        print(f"   Has Filters: {enhanced['has_filters']}")
        if enhanced['has_filters']:
            print(f"   Filter: {enhanced['filter']}")


if __name__ == '__main__':
    main()
