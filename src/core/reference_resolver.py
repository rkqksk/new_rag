"""
참조 해결 시스템
대명사 및 위치 참조를 실제 제품으로 변환
"""

import re
from typing import Dict, List, Optional, Tuple


class ReferenceResolver:
    """대화에서 참조 표현을 실제 제품으로 해결"""

    def __init__(self):
        # 순서 참조 패턴
        self.ordinal_patterns = {
            r"첫\s*번째|첫번째|처음|제일\s*먼저": 0,
            r"두\s*번째|두번째": 1,
            r"세\s*번째|세번째": 2,
            r"네\s*번째|네번째": 3,
            r"다섯\s*번째|다섯번째": 4,
            r"마지막": -1
        }

        # 지시 대명사 패턴
        self.demonstrative_patterns = [
            r"그\s*거",
            r"이\s*거",
            r"저\s*거",
            r"그\s*제품",
            r"이\s*제품",
            r"저\s*제품"
        ]

        # 상대 위치 참조
        self.relative_patterns = {
            r"위\s*에|위쪽": -1,
            r"아래\s*에|아래쪽": 1,
            r"이전|전\s*에|앞\s*에": -1,
            r"다음|후\s*에|뒤\s*에": 1
        }

    def resolve(
        self,
        query: str,
        context: Dict
    ) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        """
        쿼리에서 참조 해결

        Args:
            query: 사용자 쿼리
            context: 대화 컨텍스트

        Returns:
            (resolved, product_idx, product_list)
            - resolved: 참조가 해결되었는지
            - product_idx: 해결된 제품 idx (단일)
            - product_list: 해결된 제품 목록 (복수)
        """
        # 1. 순서 참조 체크 ("첫 번째", "두 번째" 등)
        ordinal_result = self._resolve_ordinal(query, context)
        if ordinal_result[0]:
            return ordinal_result

        # 2. 지시 대명사 체크 ("그거", "이거" 등)
        demonstrative_result = self._resolve_demonstrative(query, context)
        if demonstrative_result[0]:
            return demonstrative_result

        # 3. 상대 위치 참조 체크 ("위에", "이전" 등)
        relative_result = self._resolve_relative(query, context)
        if relative_result[0]:
            return relative_result

        # 4. 암묵적 참조 (짧은 쿼리 + 포커스 있음)
        implicit_result = self._resolve_implicit(query, context)
        if implicit_result[0]:
            return implicit_result

        return False, None, None

    def _resolve_ordinal(
        self,
        query: str,
        context: Dict
    ) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        """순서 참조 해결"""
        previous_products = context.get("previous_products", [])

        if not previous_products:
            return False, None, None

        for pattern, index in self.ordinal_patterns.items():
            if re.search(pattern, query):
                try:
                    # 인덱스가 범위 내인지 확인
                    if index == -1:  # 마지막
                        product_idx = previous_products[-1]
                    elif 0 <= index < len(previous_products):
                        product_idx = previous_products[index]
                    else:
                        return False, None, None

                    return True, product_idx, [product_idx]

                except IndexError:
                    return False, None, None

        return False, None, None

    def _resolve_demonstrative(
        self,
        query: str,
        context: Dict
    ) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        """지시 대명사 참조 해결"""
        current_focus = context.get("current_focus")

        # 지시 대명사가 있는지 확인
        has_demonstrative = any(
            re.search(pattern, query)
            for pattern in self.demonstrative_patterns
        )

        if has_demonstrative and current_focus:
            return True, current_focus, [current_focus]

        return False, None, None

    def _resolve_relative(
        self,
        query: str,
        context: Dict
    ) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        """상대 위치 참조 해결"""
        current_focus = context.get("current_focus")
        previous_products = context.get("previous_products", [])

        if not current_focus or not previous_products:
            return False, None, None

        try:
            current_index = previous_products.index(current_focus)
        except ValueError:
            return False, None, None

        for pattern, offset in self.relative_patterns.items():
            if re.search(pattern, query):
                new_index = current_index + offset

                if 0 <= new_index < len(previous_products):
                    product_idx = previous_products[new_index]
                    return True, product_idx, [product_idx]

        return False, None, None

    def _resolve_implicit(
        self,
        query: str,
        context: Dict
    ) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        """암묵적 참조 해결 (짧은 질문 + 포커스)"""
        current_focus = context.get("current_focus")

        # 짧은 쿼리 (20자 이하) + 포커스 있음
        if len(query) <= 20 and current_focus:
            # 검색 키워드가 없는 경우만 (기존 제품에 대한 질문으로 간주)
            search_indicators = [
                "ml", "파이", "용기", "병", "PE", "PET", "PETG"
            ]

            has_search_term = any(ind in query for ind in search_indicators)

            if not has_search_term:
                return True, current_focus, [current_focus]

        return False, None, None

    def expand_query(
        self,
        query: str,
        product_idx: str,
        product_data: Dict
    ) -> str:
        """
        참조를 실제 제품 정보로 확장

        Args:
            query: 원본 쿼리
            product_idx: 해결된 제품 idx
            product_data: 제품 상세 데이터

        Returns:
            확장된 쿼리
        """
        product_name = product_data.get("product_name", "")
        product_code = product_data.get("product_code", "")

        # 기본 정보
        specs = product_data.get("specifications", {})
        material = specs.get("재질(원료)", "")
        capacity = specs.get("capacity", "")
        neck_size = specs.get("neck_size", "")

        # 참조 표현 제거
        expanded = query
        for pattern in self.demonstrative_patterns:
            expanded = re.sub(pattern, "", expanded)

        for pattern in self.ordinal_patterns.keys():
            expanded = re.sub(pattern, "", expanded)

        # 제품 정보 추가
        context_info = f"{product_name} ({product_code})"
        if material:
            context_info += f", {material}"
        if capacity:
            context_info += f", {capacity}"
        if neck_size:
            context_info += f", {neck_size}"

        expanded = f"{context_info} {expanded}".strip()

        return expanded

    def get_reference_type(self, query: str) -> Optional[str]:
        """
        쿼리의 참조 유형 파악

        Args:
            query: 사용자 쿼리

        Returns:
            참조 유형 ("ordinal", "demonstrative", "relative", None)
        """
        # 순서 참조
        for pattern in self.ordinal_patterns.keys():
            if re.search(pattern, query):
                return "ordinal"

        # 지시 대명사
        for pattern in self.demonstrative_patterns:
            if re.search(pattern, query):
                return "demonstrative"

        # 상대 위치
        for pattern in self.relative_patterns.keys():
            if re.search(pattern, query):
                return "relative"

        return None

    def needs_resolution(self, query: str) -> bool:
        """
        쿼리가 참조 해결이 필요한지 확인

        Args:
            query: 사용자 쿼리

        Returns:
            참조 해결 필요 여부
        """
        return self.get_reference_type(query) is not None


# 전역 인스턴스
_reference_resolver_instance = None


def get_reference_resolver() -> ReferenceResolver:
    """ReferenceResolver 싱글톤 인스턴스 반환"""
    global _reference_resolver_instance
    if _reference_resolver_instance is None:
        _reference_resolver_instance = ReferenceResolver()
    return _reference_resolver_instance
