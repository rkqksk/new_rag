"""
동의어 관리자 (Synonym Manager)
자연어의 다양성을 처리하기 위한 동의어 및 패턴 정규화
"""

import re
from typing import Dict, List, Optional, Set, Tuple


class SynonymManager:
    """
    동의어 관리자

    핵심 기능:
    1. 제품 유형 동의어: "로션 펌프" = "펌프" = "로션펌프"
    2. 네크 사이즈 동의어: "24파이" = "24/410" = "24" = "24mm"
    3. 용량 동의어: "50미리" = "50ml" = "50mL" = "50 ml"
    4. 재질 동의어: "PET" = "피이티" = "pet"
    5. 속성 동의어: "투명" = "투명한" = "clear"
    """

    def __init__(self):
        # 제품 유형 동의어
        self.product_type_synonyms = {
            "bottle": ["병", "용기", "보틀", "브로우용기", "헤비브로우용기"],
            "pump": ["펌프", "펌프캡", "디스펜서", "로션펌프", "로션 펌프"],
            "cap": ["캡", "뚜껑", "마개", "커버"],
            "jar": ["자", "항아리", "저"],
            "spray": ["스프레이", "분사기", "미스트"],
            "tube": ["튜브", "튜브용기"],
        }

        # 네크 사이즈 동의어 (파이, mm, 숫자만)
        self.neck_size_patterns = [
            (r"(\d+)\s*파이", r"\1"),  # "24파이" → "24"
            (r"(\d+)\s*/\s*(\d+)", r"\1/\2"),  # "24/410" → "24/410"
            (r"(\d+)\s*mm", r"\1"),  # "24mm" → "24"
            (r"(\d+)파이", r"\1"),  # "24파이" → "24"
        ]

        # 표준 네크 사이즈 매핑
        self.standard_neck_sizes = {
            "20": ["20파이", "20/410", "20mm", "20"],
            "24": ["24파이", "24/410", "24mm", "24"],
            "28": ["28파이", "28/410", "28mm", "28"],
            "32": ["32파이", "32/410", "32mm", "32"],
            "38": ["38파이", "38/410", "38mm", "38"],
            "43": ["43파이", "43/410", "43mm", "43"],
            "45": ["45파이", "45/410", "45mm", "45"],
            "53": ["53파이", "53/410", "53mm", "53"],
            "58": ["58파이", "58/410", "58mm", "58"],
        }

        # 용량 패턴 (미리, ml, mL)
        self.capacity_patterns = [
            (r"(\d+)\s*미리", r"\1ml"),  # "50미리" → "50ml"
            (r"(\d+)\s*mL", r"\1ml"),  # "50mL" → "50ml"
            (r"(\d+)\s+ml", r"\1ml"),  # "50 ml" → "50ml"
        ]

        # 재질 동의어
        self.material_synonyms = {
            "PET": ["PET", "pet", "피이티", "PETG", "petg", "피이티지"],
            "HDPE": ["HDPE", "hdpe", "에이치디피이", "PE", "pe"],
            "PP": ["PP", "pp", "피피", "폴리프로필렌"],
            "PS": ["PS", "ps", "피에스", "폴리스티렌"],
            "PC": ["PC", "pc", "피씨", "폴리카보네이트"],
            "PLA": ["PLA", "pla", "피엘에이"],
            "ABS": ["ABS", "abs", "에이비에스"],
        }

        # 투명도 동의어
        self.transparency_synonyms = {
            "transparent": ["투명", "투명한", "clear", "transparent", "클리어"],
            "opaque": ["불투명", "불투명한", "opaque", "흐린", "불투명색"],
            "translucent": ["반투명", "반투명한", "translucent", "살짝 투명"],
        }

        # 색상 동의어
        self.color_synonyms = {
            "white": ["흰색", "화이트", "white", "백색"],
            "black": ["검은색", "블랙", "black", "흑색"],
            "blue": ["파란색", "블루", "blue", "청색"],
            "green": ["초록색", "녹색", "green"],
            "red": ["빨간색", "레드", "red", "적색"],
            "amber": ["호박색", "앰버", "amber", "갈색"],
        }

        # 조합 패턴 (제품 유형 + 속성)
        self.compound_patterns = [
            # "로션펌프" → "로션 펌프"
            (r"로션펌프", "로션 펌프"),
            (r"크림병", "크림 병"),
            (r"세럼병", "세럼 병"),
            (r"미스트펌프", "미스트 펌프"),
            (r"스프레이펌프", "스프레이 펌프"),
        ]

    def normalize_query(self, query: str) -> str:
        """
        쿼리 정규화

        Examples:
            "24파이 로션펌프" → "24 로션 펌프"
            "50미리 투명 PET병" → "50ml 투명 PET 병"
            "24파이만" → "24만"
        """
        normalized = query

        # 1. 조합 패턴 분리
        for pattern, replacement in self.compound_patterns:
            normalized = re.sub(pattern, replacement, normalized)

        # 2. 용량 정규화
        for pattern, replacement in self.capacity_patterns:
            normalized = re.sub(pattern, replacement, normalized)

        # 3. 네크 사이즈 정규화
        for pattern, replacement in self.neck_size_patterns:
            normalized = re.sub(pattern, replacement, normalized)

        return normalized

    def extract_neck_size(self, query: str) -> Optional[str]:
        """
        네크 사이즈 추출 및 표준화

        Examples:
            "24파이" → "24"
            "24/410" → "24/410"
            "24mm" → "24"
            "24펌프" → "24"  (제품 타입 앞의 숫자)
            "24" → "24"
        """
        # 1. 네크 사이즈 패턴 매칭
        for pattern, replacement in self.neck_size_patterns:
            match = re.search(pattern, query)
            if match:
                # 표준 네크 사이즈로 변환
                extracted = re.sub(pattern, replacement, match.group(0))

                # 숫자만 추출된 경우 표준 형식 찾기
                if extracted.isdigit():
                    for standard, variants in self.standard_neck_sizes.items():
                        if extracted == standard:
                            return standard

                return extracted

        # 2. "24펌프", "24캡" 같은 패턴 처리 (제품 타입 앞의 숫자)
        product_types = ["펌프", "캡", "뚜껑", "병", "용기", "보틀"]
        for product_type in product_types:
            pattern = r"(\d+)" + product_type
            match = re.search(pattern, query)
            if match:
                neck_num = match.group(1)
                # 표준 네크 사이즈인지 확인
                if neck_num in self.standard_neck_sizes:
                    return neck_num

        return None

    def extract_capacity(self, query: str) -> Optional[float]:
        """
        용량 추출

        Examples:
            "50미리" → 50.0
            "100ml" → 100.0
            "30 ml" → 30.0
        """
        # 용량 패턴 매칭
        patterns = [
            r"(\d+(?:\.\d+)?)\s*미리",
            r"(\d+(?:\.\d+)?)\s*ml",
            r"(\d+(?:\.\d+)?)\s*mL",
            r"(\d+(?:\.\d+)?)\s+ml",
        ]

        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return float(match.group(1))

        return None

    def extract_material(self, query: str) -> Optional[str]:
        """
        재질 추출 및 표준화

        Examples:
            "PET" → "PET"
            "피이티" → "PET"
            "hdpe" → "HDPE"
        """
        query_lower = query.lower()

        for standard, synonyms in self.material_synonyms.items():
            for synonym in synonyms:
                if synonym.lower() in query_lower:
                    return standard

        return None

    def extract_product_type(self, query: str) -> Optional[str]:
        """
        제품 유형 추출 및 표준화

        Examples:
            "로션 펌프" → "pump"
            "병" → "bottle"
            "캡" → "cap"
        """
        query_lower = query.lower()

        for standard, synonyms in self.product_type_synonyms.items():
            for synonym in synonyms:
                if synonym in query_lower:
                    return standard

        return None

    def extract_transparency(self, query: str) -> Optional[str]:
        """
        투명도 추출 및 표준화

        Examples:
            "투명" → "transparent"
            "clear" → "transparent"
            "불투명" → "opaque"
        """
        query_lower = query.lower()

        for standard, synonyms in self.transparency_synonyms.items():
            for synonym in synonyms:
                if synonym in query_lower:
                    return standard

        return None

    def extract_color(self, query: str) -> Optional[str]:
        """
        색상 추출 및 표준화

        Examples:
            "흰색" → "white"
            "블랙" → "black"
            "호박색" → "amber"
        """
        query_lower = query.lower()

        for standard, synonyms in self.color_synonyms.items():
            for synonym in synonyms:
                if synonym in query_lower:
                    return standard

        return None

    def expand_query(self, query: str) -> str:
        """
        쿼리 확장 (동의어 추가)

        Examples:
            "24파이 펌프" → "24 펌프 24파이 펌프 로션펌프 디스펜서"
        """
        normalized = self.normalize_query(query)
        tokens = normalized.split()

        expanded_tokens = set(tokens)

        # 각 토큰에 대해 동의어 추가
        for token in tokens:
            # 제품 유형 동의어
            for standard, synonyms in self.product_type_synonyms.items():
                if token in synonyms:
                    expanded_tokens.update(synonyms[:3])  # 상위 3개 동의어만

            # 재질 동의어
            for standard, synonyms in self.material_synonyms.items():
                if token.upper() in [s.upper() for s in synonyms]:
                    expanded_tokens.add(standard)

            # 투명도 동의어
            for standard, synonyms in self.transparency_synonyms.items():
                if token in synonyms:
                    expanded_tokens.update(synonyms[:2])

        return " ".join(expanded_tokens)

    def get_search_filters(self, query: str) -> Dict[str, any]:
        """
        쿼리에서 모든 필터 추출

        Examples:
            "24파이 50미리 투명 PET 로션펌프"
            →{
                'neck_size': '24',
                'capacity': 50.0,
                'transparency': 'transparent',
                'material': 'PET',
                'product_type': 'pump'
            }
        """
        filters = {}

        # 네크 사이즈
        neck_size = self.extract_neck_size(query)
        if neck_size:
            filters["neck_size"] = neck_size

        # 용량
        capacity = self.extract_capacity(query)
        if capacity:
            filters["capacity"] = capacity

        # 재질
        material = self.extract_material(query)
        if material:
            filters["material"] = material

        # 제품 유형
        product_type = self.extract_product_type(query)
        if product_type:
            filters["product_type"] = product_type

        # 투명도
        transparency = self.extract_transparency(query)
        if transparency:
            filters["transparency"] = transparency

        # 색상
        color = self.extract_color(query)
        if color:
            filters["color"] = color

        return filters


# 싱글톤 인스턴스
_synonym_manager_instance = None


def get_synonym_manager() -> SynonymManager:
    """싱글톤 동의어 관리자 반환"""
    global _synonym_manager_instance
    if _synonym_manager_instance is None:
        _synonym_manager_instance = SynonymManager()
    return _synonym_manager_instance
