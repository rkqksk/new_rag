"""
의도 기반 스마트 추천 엔진
제품 사용 목적을 분석하여 최적의 용기 추천
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
from collections import defaultdict


class IntentBasedRecommender:
    """사용 목적 기반 추천 시스템"""

    def __init__(self, data_root: str = "/Users/oypnus/Project/rag-enterprise/data/crawled_products_final"):
        self.data_root = Path(data_root)

        # 화장품 제품군별 최적 스펙 프로필
        self.product_profiles = {
            "클렌징오일": {
                "keywords": ["클렌징", "오일", "메이크업리무버", "딥클렌징"],
                "material_priority": ["PE"],
                "material_avoid": ["PET", "PETG"],
                "capacity_range": (100, 200),
                "neck_size": ["24파이", "28파이"],
                "viscosity": "high",
                "ph_range": (5.5, 7.0),
                "oil_content": "high",
                "description": "고점도 오일 기반 제형에 적합"
            },
            "토너": {
                "keywords": ["토너", "스킨", "화장수", "미스트토너"],
                "material_priority": ["PET", "PETG", "PE"],
                "material_avoid": [],
                "capacity_range": (150, 300),
                "neck_size": ["24파이", "28파이"],
                "viscosity": "low",
                "ph_range": (5.0, 7.0),
                "oil_content": "none",
                "description": "수분 기반 저점도 제형"
            },
            "세럼": {
                "keywords": ["세럼", "에센스", "앰플", "부스터"],
                "material_priority": ["PETG", "PET", "PE"],
                "material_avoid": [],
                "capacity_range": (30, 50),
                "neck_size": ["20파이"],
                "viscosity": "medium",
                "ph_range": (5.0, 7.0),
                "oil_content": "low",
                "description": "프리미엄 에센스류, 투명 용기 선호"
            },
            "로션": {
                "keywords": ["로션", "에멀젼", "밀크"],
                "material_priority": ["PE", "PET", "PETG"],
                "material_avoid": [],
                "capacity_range": (100, 150),
                "neck_size": ["24파이"],
                "viscosity": "medium",
                "ph_range": (5.5, 7.5),
                "oil_content": "medium",
                "description": "유수분 균형 제형"
            },
            "크림": {
                "keywords": ["크림", "수분크림", "영양크림"],
                "material_priority": ["PE", "PETG"],
                "material_avoid": [],
                "capacity_range": (50, 100),
                "neck_size": ["24파이", "28파이"],
                "viscosity": "high",
                "ph_range": (5.5, 7.5),
                "oil_content": "high",
                "description": "고점도 유분 함유 제형"
            },
            "바디워시": {
                "keywords": ["바디워시", "샤워젤", "바디클렌저"],
                "material_priority": ["PE"],
                "material_avoid": [],
                "capacity_range": (300, 500),
                "neck_size": ["28파이", "32파이", "43파이"],
                "viscosity": "high",
                "ph_range": (5.0, 7.0),
                "oil_content": "low",
                "description": "대용량 클렌징 제형"
            },
            "샴푸": {
                "keywords": ["샴푸", "트리트먼트", "헤어팩"],
                "material_priority": ["PE"],
                "material_avoid": [],
                "capacity_range": (250, 500),
                "neck_size": ["28파이", "32파이"],
                "viscosity": "medium",
                "ph_range": (5.0, 6.5),
                "oil_content": "low",
                "description": "대용량 헤어케어 제형"
            },
            "선크림": {
                "keywords": ["선크림", "자외선차단제", "선블록"],
                "material_priority": ["PE", "PETG"],
                "material_avoid": [],
                "capacity_range": (50, 100),
                "neck_size": ["20파이", "24파이"],
                "viscosity": "medium",
                "ph_range": (6.0, 7.5),
                "oil_content": "medium",
                "description": "UV 필터 함유, UV 차단 코팅 권장"
            },
            "핸드크림": {
                "keywords": ["핸드크림", "핸드로션"],
                "material_priority": ["PE", "PETG"],
                "material_avoid": [],
                "capacity_range": (30, 100),
                "neck_size": ["20파이", "24파이"],
                "viscosity": "high",
                "ph_range": (5.5, 7.5),
                "oil_content": "high",
                "description": "고보습 크림 제형"
            },
            "아이크림": {
                "keywords": ["아이크림", "아이세럼"],
                "material_priority": ["PETG", "PET"],
                "material_avoid": [],
                "capacity_range": (15, 30),
                "neck_size": ["18파이", "20파이"],
                "viscosity": "medium",
                "ph_range": (5.5, 7.0),
                "oil_content": "medium",
                "description": "소용량 프리미엄 제형"
            },
            "페이스오일": {
                "keywords": ["페이스오일", "페이셜오일", "뷰티오일"],
                "material_priority": ["PE", "PETG"],
                "material_avoid": ["PET"],
                "capacity_range": (30, 50),
                "neck_size": ["20파이"],
                "viscosity": "low",
                "ph_range": (5.0, 7.0),
                "oil_content": "very_high",
                "description": "순수 오일 제형, 드롭퍼 권장"
            },
            "미스트": {
                "keywords": ["미스트", "스프레이", "페이스미스트"],
                "material_priority": ["PET", "PETG", "PE"],
                "material_avoid": [],
                "capacity_range": (50, 150),
                "neck_size": ["20파이", "24파이"],
                "viscosity": "very_low",
                "ph_range": (5.0, 7.5),
                "oil_content": "none",
                "description": "미세 분사 가능한 미스트 전용"
            },
            "젤": {
                "keywords": ["수딩젤", "알로에젤", "진정젤"],
                "material_priority": ["PET", "PETG"],
                "material_avoid": [],
                "capacity_range": (100, 300),
                "neck_size": ["24파이", "28파이"],
                "viscosity": "medium",
                "ph_range": (5.0, 7.0),
                "oil_content": "none",
                "description": "투명 젤 제형"
            },
            "폼클렌저": {
                "keywords": ["폼클렌저", "거품클렌저", "페이셜폼"],
                "material_priority": ["PE"],
                "material_avoid": [],
                "capacity_range": (150, 250),
                "neck_size": ["43파이"],
                "viscosity": "low",
                "ph_range": (5.0, 7.0),
                "oil_content": "low",
                "description": "거품펌프 전용"
            },
            "바디로션": {
                "keywords": ["바디로션", "바디밀크", "보디로션"],
                "material_priority": ["PE"],
                "material_avoid": [],
                "capacity_range": (200, 500),
                "neck_size": ["28파이", "32파이"],
                "viscosity": "medium",
                "ph_range": (5.5, 7.5),
                "oil_content": "medium",
                "description": "대용량 보습 제형"
            }
        }

    def detect_product_type(self, query: str) -> Optional[str]:
        """
        쿼리에서 제품 유형 감지 (키워드 + 용량 기반)

        Args:
            query: 사용자 쿼리

        Returns:
            제품 유형 키 또는 None
        """
        query_lower = query.lower()

        # 1. 키워드 매칭 (우선순위 높음)
        for product_type, profile in self.product_profiles.items():
            for keyword in profile["keywords"]:
                if keyword in query_lower:
                    return product_type

        # 2. 용량 기반 감지 (키워드가 없을 때)
        import re
        # "미리", "ml", "mL" 모두 처리
        capacity_match = re.search(r'(\d+)\s*(?:미리|ml|mL)', query_lower)
        if capacity_match:
            capacity = int(capacity_match.group(1))

            # 용량 범위로 가장 적합한 제품군 찾기
            best_match = None
            best_score = -1

            for product_type, profile in self.product_profiles.items():
                cap_min, cap_max = profile["capacity_range"]
                center = (cap_min + cap_max) / 2
                range_size = cap_max - cap_min

                # 용량이 범위 내에 있는지 확인
                if cap_min <= capacity <= cap_max:
                    # 범위 내: 중심에 가까울수록 높은 점수
                    distance_from_center = abs(capacity - center)
                    score = 1000 - distance_from_center
                else:
                    # 범위 외: 범위 경계와의 거리 기반 (음수 점수)
                    if capacity < cap_min:
                        distance = cap_min - capacity
                    else:
                        distance = capacity - cap_max
                    score = -(distance + 1)

                if score > best_score:
                    best_score = score
                    best_match = product_type

            if best_match:
                return best_match

        return None

    def recommend(
        self,
        query: str,
        products: List[Dict],
        limit: int = 10
    ) -> List[Dict]:
        """
        의도 기반 제품 추천

        Args:
            query: 사용자 쿼리
            products: 검색된 제품 목록
            limit: 반환할 제품 수

        Returns:
            추천 제품 목록 (신뢰도 순)
        """
        # 제품 유형 감지
        product_type = self.detect_product_type(query)

        if not product_type:
            # 제품 유형 감지 실패 → 일반 정렬
            return products[:limit]

        profile = self.product_profiles[product_type]

        # 각 제품에 신뢰도 점수 계산
        scored_products = []
        for product in products:
            score = self._calculate_confidence(product, profile)
            reason = self._generate_reason(product, profile, product_type)

            scored_products.append({
                **product,
                "recommendation_score": score,
                "recommendation_reason": reason,
                "matched_profile": product_type,
                "profile_description": profile["description"]
            })

        # 신뢰도 순 정렬
        scored_products.sort(key=lambda x: x["recommendation_score"], reverse=True)

        return scored_products[:limit]

    def _calculate_confidence(self, product: Dict, profile: Dict) -> float:
        """
        제품의 프로필 적합도 점수 계산 (0.0 ~ 1.0)

        Args:
            product: 제품 데이터
            profile: 제품군 프로필

        Returns:
            신뢰도 점수
        """
        score = 0.0
        specs = product.get("specifications", {})

        # 1. 재질 매칭 (40점)
        material = specs.get("재질(원료)", "").upper()
        if material in [m.upper() for m in profile["material_priority"]]:
            # 우선순위에 따라 차등 점수
            priority_index = next(
                (i for i, m in enumerate(profile["material_priority"])
                 if m.upper() == material),
                len(profile["material_priority"])
            )
            score += 0.4 * (1 - priority_index / len(profile["material_priority"]))

        # 재질 회피 목록에 있으면 감점
        if material in [m.upper() for m in profile["material_avoid"]]:
            score -= 0.3

        # 2. 용량 매칭 (30점)
        capacity_str = specs.get("capacity", "")
        if capacity_str:
            import re
            match = re.search(r'(\d+)', capacity_str)
            if match:
                capacity = float(match.group(1))
                cap_min, cap_max = profile["capacity_range"]

                if cap_min <= capacity <= cap_max:
                    # 중앙값에 가까울수록 높은 점수
                    center = (cap_min + cap_max) / 2
                    distance_ratio = abs(capacity - center) / (cap_max - cap_min)
                    score += 0.3 * (1 - distance_ratio)

        # 3. 네크 사이즈 매칭 (20점)
        neck_size = specs.get("neck_size", "")
        if neck_size in profile["neck_size"]:
            score += 0.2

        # 4. 호환성 (10점)
        compat = product.get("compatibility_analysis", {})
        cap_count = compat.get("compatible_caps_pumps", {}).get("count", 0)
        score += 0.1 * min(cap_count / 30, 1.0)

        # 점수 범위 제한 (0.0 ~ 1.0)
        return max(0.0, min(1.0, score))

    def _generate_reason(
        self,
        product: Dict,
        profile: Dict,
        product_type: str
    ) -> str:
        """
        추천 이유 생성

        Args:
            product: 제품 데이터
            profile: 제품군 프로필
            product_type: 제품 유형

        Returns:
            추천 이유 문자열
        """
        reasons = []
        specs = product.get("specifications", {})

        # 제품 유형 매칭
        reasons.append(f"✅ {product_type} 제형에 최적화")

        # 재질 적합성
        material = specs.get("재질(원료)", "")
        if material.upper() in [m.upper() for m in profile["material_priority"]]:
            reasons.append(f"✅ {material} 재질 - {profile['description']}")

        # 용량 적합성
        capacity_str = specs.get("capacity", "")
        if capacity_str:
            cap_min, cap_max = profile["capacity_range"]
            reasons.append(f"✅ 용량 {capacity_str} ({cap_min}-{cap_max}ml 권장 범위)")

        # 호환성
        compat = product.get("compatibility_analysis", {})
        cap_count = compat.get("compatible_caps_pumps", {}).get("count", 0)
        if cap_count > 0:
            reasons.append(f"✅ 호환 Cap/Pump {cap_count}개")

        return " | ".join(reasons)

    def get_profile_description(self, product_type: str) -> Optional[str]:
        """
        제품군 프로필 설명 조회

        Args:
            product_type: 제품 유형

        Returns:
            프로필 설명
        """
        profile = self.product_profiles.get(product_type)
        if profile:
            return profile["description"]
        return None

    def get_all_profiles(self) -> Dict[str, Dict]:
        """모든 제품군 프로필 반환"""
        return self.product_profiles


# 싱글톤 인스턴스
_intent_recommender_instance = None


def get_intent_recommender() -> IntentBasedRecommender:
    """IntentBasedRecommender 싱글톤 반환"""
    global _intent_recommender_instance
    if _intent_recommender_instance is None:
        _intent_recommender_instance = IntentBasedRecommender()
    return _intent_recommender_instance
