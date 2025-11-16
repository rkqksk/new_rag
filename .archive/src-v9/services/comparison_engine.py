"""
인터랙티브 제품 비교 엔진
실시간 필터링 및 스마트 추천
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ComparisonEngine:
    """제품 비교 엔진"""

    def __init__(
        self, data_root: str = "/Users/oypnus/Project/rag-enterprise/data/crawled_products_final"
    ):
        self.data_root = Path(data_root)

        # 비교 가능한 메트릭 정의
        self.comparison_metrics = {
            "재질": {"type": "categorical", "weight": 0.25},
            "용량": {"type": "numerical", "weight": 0.20},
            "네크사이즈": {"type": "categorical", "weight": 0.15},
            "가격": {"type": "numerical", "weight": 0.20},
            "호환성": {"type": "numerical", "weight": 0.15},
            "투명도": {"type": "categorical", "weight": 0.05},
        }

    def compare_products(self, product_idxs: List[str], metrics: List[str] = None) -> Dict:
        """
        여러 제품 비교

        Args:
            product_idxs: 비교할 제품 idx 목록
            metrics: 비교할 메트릭 목록 (None이면 전체)

        Returns:
            비교 결과
        """
        if not product_idxs:
            return {"error": "제품을 선택해주세요."}

        # 제품 로드
        products = []
        for idx in product_idxs:
            product = self._load_product(idx)
            if product:
                products.append(product)

        if not products:
            return {"error": "제품을 찾을 수 없습니다."}

        # 메트릭 선택
        if metrics is None:
            metrics = list(self.comparison_metrics.keys())

        # 비교 매트릭스 생성
        comparison_matrix = self._generate_comparison_matrix(products, metrics)

        # 하이라이트 추가
        highlighted_matrix = self._add_highlights(comparison_matrix, metrics)

        # 스마트 추천 생성
        recommendation = self._generate_smart_recommendation(products, highlighted_matrix)

        return {
            "products": products,
            "comparison_matrix": highlighted_matrix,
            "metrics": metrics,
            "product_count": len(products),
            "recommendation": recommendation,
        }

    def apply_filters(self, products: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """
        동적 필터 적용

        Args:
            products: 제품 목록
            filters: 필터 조건

        Returns:
            필터링된 제품 목록
        """
        filtered = []

        for product in products:
            if self._matches_filters(product, filters):
                filtered.append(product)

        return filtered

    def _generate_comparison_matrix(self, products: List[Dict], metrics: List[str]) -> List[Dict]:
        """비교 매트릭스 생성"""
        matrix = []

        for metric in metrics:
            row = {"metric": metric, "values": []}

            for product in products:
                value = self._extract_metric_value(product, metric)
                row["values"].append(
                    {
                        "product_idx": product.get("idx"),
                        "value": value,
                        "display": self._format_metric_value(value, metric),
                    }
                )

            matrix.append(row)

        return matrix

    def _extract_metric_value(self, product: Dict, metric: str) -> Any:
        """제품에서 메트릭 값 추출"""
        specs = product.get("specifications", {})
        pricing = product.get("pricing", {})
        compat = product.get("compatibility_analysis", {})

        if metric == "재질":
            return specs.get("재질(원료)", "N/A")

        elif metric == "용량":
            capacity_str = specs.get("capacity", "")
            if capacity_str:
                import re

                match = re.search(r"(\d+(?:\.\d+)?)", capacity_str)
                if match:
                    return float(match.group(1))
            return 0

        elif metric == "네크사이즈":
            return specs.get("neck_size", "N/A")

        elif metric == "가격":
            return pricing.get("discount_price") or pricing.get("regular_price", 0)

        elif metric == "호환성":
            return compat.get("compatible_caps_pumps", {}).get("count", 0)

        elif metric == "투명도":
            material = specs.get("재질(원료)", "").upper()
            if material in ["PET", "PETG"]:
                return "투명"
            elif material == "PE":
                return "불투명"
            else:
                return "N/A"

        return "N/A"

    def _format_metric_value(self, value: Any, metric: str) -> str:
        """메트릭 값 포맷팅"""
        if metric == "가격":
            return f"{value:,.0f}원" if value > 0 else "N/A"
        elif metric == "용량":
            return f"{value}ml" if value > 0 else "N/A"
        elif metric == "호환성":
            return f"{value}개"
        else:
            return str(value)

    def _add_highlights(self, matrix: List[Dict], metrics: List[str]) -> List[Dict]:
        """최고/최저값 하이라이트"""
        for row in matrix:
            metric = row["metric"]
            values = row["values"]

            metric_type = self.comparison_metrics.get(metric, {}).get("type", "categorical")

            if metric_type == "numerical":
                # 숫자형 메트릭
                numeric_values = [
                    v["value"]
                    for v in values
                    if isinstance(v["value"], (int, float)) and v["value"] > 0
                ]

                if numeric_values:
                    max_val = max(numeric_values)
                    min_val = min(numeric_values)

                    for v in values:
                        if v["value"] == max_val:
                            # 가격은 최저가 하이라이트, 나머지는 최고값 하이라이트
                            if metric == "가격":
                                pass  # 최고가는 하이라이트 안 함
                            else:
                                v["highlight"] = "best"
                                v["display"] += " ★최고"

                        elif v["value"] == min_val:
                            if metric == "가격":
                                v["highlight"] = "best"
                                v["display"] += " ★최저"
                            else:
                                pass  # 최저값은 하이라이트 안 함

        return matrix

    def _generate_smart_recommendation(
        self, products: List[Dict], comparison_matrix: List[Dict]
    ) -> str:
        """
        스마트 추천 생성

        Args:
            products: 제품 목록
            comparison_matrix: 비교 매트릭스

        Returns:
            추천 메시지
        """
        # 각 제품의 장점 파악
        strengths = defaultdict(list)

        for row in comparison_matrix:
            metric = row["metric"]

            for value in row["values"]:
                if value.get("highlight") == "best":
                    product_idx = value["product_idx"]
                    strengths[product_idx].append(metric)

        # 추천 메시지 생성
        recommendations = []

        for product in products:
            idx = product.get("idx")
            product_strengths = strengths.get(idx, [])

            if product_strengths:
                strength_text = ", ".join(product_strengths)
                recommendations.append(
                    f"**{product.get('product_name')}**: " f"{strength_text}에서 최고"
                )

        if recommendations:
            return "💡 추천:\n" + "\n".join(recommendations)
        else:
            return "💡 각 제품의 특성을 비교하여 선택하세요."

    def _matches_filters(self, product: Dict, filters: Dict) -> bool:
        """제품이 필터 조건을 만족하는지 확인"""
        for filter_key, filter_value in filters.items():
            if filter_value is None:
                continue

            metric_value = self._extract_metric_value(product, filter_key)

            # 필터 타입별 처리
            if filter_key == "재질":
                if isinstance(filter_value, list):
                    if metric_value.upper() not in [v.upper() for v in filter_value]:
                        return False
                else:
                    if metric_value.upper() != filter_value.upper():
                        return False

            elif filter_key == "투명도":
                if metric_value != filter_value:
                    return False

            elif filter_key == "가격":
                # 가격 범위 필터
                if isinstance(filter_value, dict):
                    min_price = filter_value.get("min", 0)
                    max_price = filter_value.get("max", 999999)
                    if not (min_price <= metric_value <= max_price):
                        return False
                elif isinstance(filter_value, (int, float)):
                    if metric_value > filter_value:
                        return False

            elif filter_key == "용량":
                # 용량 범위 필터
                if isinstance(filter_value, dict):
                    min_cap = filter_value.get("min", 0)
                    max_cap = filter_value.get("max", 999999)
                    if not (min_cap <= metric_value <= max_cap):
                        return False

            elif filter_key == "호환성":
                # 최소 호환성 필터
                if isinstance(filter_value, int):
                    if metric_value < filter_value:
                        return False

        return True

    def _load_product(self, idx: str) -> Optional[Dict]:
        """제품 데이터 로드"""
        for category in ["Bottle", "Cappump", "Pump", "Jar"]:
            for json_file in (self.data_root / category).rglob(f"idx_{idx}.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    continue

        return None


# defaultdict import
from collections import defaultdict

# 싱글톤 인스턴스
_comparison_engine_instance = None


def get_comparison_engine() -> ComparisonEngine:
    """ComparisonEngine 싱글톤 반환"""
    global _comparison_engine_instance
    if _comparison_engine_instance is None:
        _comparison_engine_instance = ComparisonEngine()
    return _comparison_engine_instance
