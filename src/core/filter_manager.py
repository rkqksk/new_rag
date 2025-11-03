"""
누적 필터링 관리자 (Cumulative Filter Manager)
영업사원처럼 이전 검색 결과를 기억하고 점진적으로 필터링
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from copy import deepcopy
import re


@dataclass
class FilterOperation:
    """필터 연산"""
    operation_type: str  # "add", "remove", "replace", "reset"
    filter_key: str
    filter_value: Any
    timestamp: str


class FilterManager:
    """
    누적 필터링 관리자

    핵심 기능:
    1. 필터 누적: "50ml" → "PET만" → "투명만"
    2. 필터 히스토리: 되돌리기 가능
    3. 결과 캐싱: 이전 검색 결과 재사용
    """

    def __init__(self):
        self.active_filters: Dict[str, Any] = {}
        self.filter_history: List[FilterOperation] = []
        self.cached_results: Optional[List[Dict]] = None
        self.cached_filters: Optional[Dict] = None

    def add_filter(
        self,
        filter_key: str,
        filter_value: Any,
        replace: bool = False
    ) -> Dict[str, Any]:
        """
        필터 추가 (누적)

        Args:
            filter_key: 필터 키 (capacity, material, neck_size, etc.)
            filter_value: 필터 값
            replace: True면 덮어쓰기, False면 추가

        Returns:
            업데이트된 필터 딕셔너리
        """
        from datetime import datetime

        operation_type = "replace" if replace else "add"

        # 필터 추가/업데이트
        if replace or filter_key not in self.active_filters:
            self.active_filters[filter_key] = filter_value
        else:
            # 누적 처리 (리스트로 변환)
            existing = self.active_filters[filter_key]
            if not isinstance(existing, list):
                existing = [existing]
            if isinstance(filter_value, list):
                existing.extend(filter_value)
            else:
                existing.append(filter_value)
            self.active_filters[filter_key] = existing

        # 히스토리 기록
        self.filter_history.append(FilterOperation(
            operation_type=operation_type,
            filter_key=filter_key,
            filter_value=filter_value,
            timestamp=datetime.now().isoformat()
        ))

        return deepcopy(self.active_filters)

    def remove_filter(self, filter_key: str) -> Dict[str, Any]:
        """필터 제거"""
        from datetime import datetime

        if filter_key in self.active_filters:
            removed_value = self.active_filters.pop(filter_key)

            self.filter_history.append(FilterOperation(
                operation_type="remove",
                filter_key=filter_key,
                filter_value=removed_value,
                timestamp=datetime.now().isoformat()
            ))

        return deepcopy(self.active_filters)

    def reset_filters(self) -> Dict[str, Any]:
        """모든 필터 초기화"""
        from datetime import datetime

        self.active_filters = {}
        self.cached_results = None
        self.cached_filters = None

        self.filter_history.append(FilterOperation(
            operation_type="reset",
            filter_key="all",
            filter_value=None,
            timestamp=datetime.now().isoformat()
        ))

        return {}

    def apply_incremental_filter(
        self,
        new_filter: Dict[str, Any],
        cached_results: List[Dict]
    ) -> List[Dict]:
        """
        이전 결과에 점진적 필터 적용

        핵심 로직:
        1. 이전 검색 결과가 있으면 그것을 기준으로 필터링
        2. 새로운 검색을 하지 않고 클라이언트 사이드 필터링

        Example:
            "50ml" → [100개 결과]
            "PET만" → [100개 중 PET만 필터링] → [30개]
            "투명만" → [30개 중 투명만 필터링] → [10개]
        """
        if not cached_results:
            return []

        filtered = cached_results

        # 각 필터 적용
        for key, value in new_filter.items():
            filtered = self._apply_single_filter(filtered, key, value)

        return filtered

    def _apply_single_filter(
        self,
        products: List[Dict],
        filter_key: str,
        filter_value: Any
    ) -> List[Dict]:
        """단일 필터 적용"""

        if filter_key == "capacity":
            return self._filter_by_capacity(products, filter_value)
        elif filter_key == "capacity_exact":
            return self._filter_by_exact_capacity(products, filter_value)
        elif filter_key == "material":
            return self._filter_by_material(products, filter_value)
        elif filter_key == "neck_size":
            return self._filter_by_neck_size(products, filter_value)
        elif filter_key == "price_max":
            return self._filter_by_price_max(products, filter_value)
        elif filter_key == "transparency":
            return self._filter_by_transparency(products, filter_value)
        elif filter_key == "category":
            return self._filter_by_category(products, filter_value)
        else:
            # 알 수 없는 필터 - 무시
            return products

    def _filter_by_capacity(self, products: List[Dict], capacity_value: float) -> List[Dict]:
        """용량 필터 (범위: ±20%)"""
        filtered = []
        min_cap = capacity_value * 0.8
        max_cap = capacity_value * 1.2

        for product in products:
            specs = product.get("specifications", {})
            capacity_str = specs.get("capacity", "")

            # 용량 추출
            match = re.search(r'(\d+(?:\.\d+)?)\s*ml', capacity_str.lower())
            if match:
                cap = float(match.group(1))
                if min_cap <= cap <= max_cap:
                    filtered.append(product)

        return filtered

    def _filter_by_exact_capacity(self, products: List[Dict], capacity_value: float) -> List[Dict]:
        """정확한 용량 필터"""
        filtered = []

        for product in products:
            specs = product.get("specifications", {})
            capacity_str = specs.get("capacity", "")

            match = re.search(r'(\d+(?:\.\d+)?)\s*ml', capacity_str.lower())
            if match:
                cap = float(match.group(1))
                if cap == capacity_value:
                    filtered.append(product)

        return filtered

    def _filter_by_material(self, products: List[Dict], material: str) -> List[Dict]:
        """재질 필터"""
        filtered = []
        material_upper = material.upper()

        for product in products:
            specs = product.get("specifications", {})
            product_material = specs.get("재질(원료)", "").upper()

            if material_upper in product_material:
                filtered.append(product)

        return filtered

    def _filter_by_neck_size(self, products: List[Dict], neck_size: str) -> List[Dict]:
        """네크 사이즈 필터"""
        filtered = []

        for product in products:
            specs = product.get("specifications", {})
            product_neck = specs.get("neck_size", "")

            if neck_size in product_neck:
                filtered.append(product)

        return filtered

    def _filter_by_price_max(self, products: List[Dict], max_price: float) -> List[Dict]:
        """최대 가격 필터"""
        filtered = []

        for product in products:
            pricing = product.get("pricing", {})
            price = pricing.get("discount_price") or pricing.get("regular_price", float('inf'))

            if isinstance(price, (int, float)) and price <= max_price:
                filtered.append(product)

        return filtered

    def _filter_by_transparency(self, products: List[Dict], transparency: str) -> List[Dict]:
        """투명도 필터"""
        filtered = []

        for product in products:
            product_name = product.get("product_name", "").lower()

            if transparency == "transparent":
                # "투명", "clear" 키워드 포함
                if "투명" in product_name or "clear" in product_name:
                    filtered.append(product)
            elif transparency == "opaque":
                # "불투명", "opaque" 키워드 포함 또는 투명 키워드 없음
                if "불투명" in product_name or "opaque" in product_name:
                    filtered.append(product)
                elif "투명" not in product_name and "clear" not in product_name:
                    filtered.append(product)

        return filtered

    def _filter_by_category(self, products: List[Dict], category: str) -> List[Dict]:
        """카테고리 필터"""
        filtered = []
        category_lower = category.lower()

        for product in products:
            product_category = product.get("category", "").lower()
            if category_lower in product_category:
                filtered.append(product)

        return filtered

    def cache_results(self, results: List[Dict], filters: Dict[str, Any]):
        """검색 결과 캐싱"""
        self.cached_results = deepcopy(results)
        self.cached_filters = deepcopy(filters)

    def get_cached_results(self) -> Optional[List[Dict]]:
        """캐시된 결과 반환"""
        return self.cached_results

    def should_use_cache(self, new_filters: Dict[str, Any]) -> bool:
        """
        캐시 사용 여부 판단

        조건:
        1. 캐시된 결과가 있음
        2. 새 필터가 이전 필터의 확장/추가인 경우
        """
        if not self.cached_results or not self.cached_filters:
            return False

        # 새 필터가 이전 필터를 포함하는지 확인
        for key, value in self.cached_filters.items():
            if key not in new_filters:
                # 이전 필터가 제거됨 → 캐시 사용 불가
                return False
            if new_filters[key] != value:
                # 필터 값이 변경됨 → 캐시 사용 불가 (추가는 OK)
                return False

        # 새 필터가 추가만 된 경우 → 캐시 사용 가능
        return True

    def get_filter_summary(self) -> Dict[str, Any]:
        """현재 필터 상태 요약"""
        return {
            "active_filters": deepcopy(self.active_filters),
            "filter_count": len(self.active_filters),
            "has_cache": self.cached_results is not None,
            "cached_result_count": len(self.cached_results) if self.cached_results else 0,
            "history_length": len(self.filter_history)
        }
