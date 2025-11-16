"""
협업 필터링 기반 추천 시스템
사용자 행동을 추적하여 선호도 학습
"""

import json
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class UserInteractionTracker:
    """사용자 인터랙션 추적"""

    def __init__(self, redis_client=None):
        """
        Args:
            redis_client: Redis 클라이언트 (선택사항)
        """
        self.redis_client = redis_client
        # Redis 없을 경우 메모리 저장
        self._memory_store: Dict[str, List[Dict]] = defaultdict(list)

    def track(self, user_id: str, product_idx: str, action: str, metadata: Dict = None) -> bool:
        """
        사용자 인터랙션 추적

        Args:
            user_id: 사용자 ID
            product_idx: 제품 idx
            action: 행동 유형 (view, click, select, purchase)
            metadata: 추가 메타데이터

        Returns:
            성공 여부
        """
        interaction = {
            "user_id": user_id,
            "product_idx": product_idx,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "weight": self._get_action_weight(action),
            "metadata": metadata or {},
        }

        # Redis 저장 시도
        if self.redis_client:
            try:
                key = f"user_interactions:{user_id}"
                self.redis_client.lpush(key, json.dumps(interaction))
                # 최근 100개만 유지
                self.redis_client.ltrim(key, 0, 99)
                return True
            except Exception as e:
                print(f"Redis 저장 실패: {e}")

        # 메모리 저장 (폴백)
        self._memory_store[user_id].append(interaction)
        # 최근 100개만 유지
        if len(self._memory_store[user_id]) > 100:
            self._memory_store[user_id] = self._memory_store[user_id][-100:]

        return True

    def get_interactions(self, user_id: str, limit: int = 50) -> List[Dict]:
        """
        사용자의 최근 인터랙션 조회

        Args:
            user_id: 사용자 ID
            limit: 최대 개수

        Returns:
            인터랙션 목록
        """
        # Redis 조회 시도
        if self.redis_client:
            try:
                key = f"user_interactions:{user_id}"
                interactions_json = self.redis_client.lrange(key, 0, limit - 1)
                return [json.loads(i) for i in interactions_json]
            except Exception:
                pass

        # 메모리 조회 (폴백)
        return self._memory_store.get(user_id, [])[:limit]

    def _get_action_weight(self, action: str) -> float:
        """행동별 가중치"""
        weights = {
            "view": 0.1,
            "click": 0.3,
            "select": 0.7,
            "purchase": 1.0,
            "add_to_cart": 0.8,
            "favorite": 0.9,
        }
        return weights.get(action, 0.1)


class CollaborativeRecommender:
    """협업 필터링 추천 시스템"""

    def __init__(
        self,
        interaction_tracker: UserInteractionTracker,
        data_root: str = "/Users/oypnus/Project/rag-enterprise/data/crawled_products_final",
    ):
        """
        Args:
            interaction_tracker: 인터랙션 추적기
            data_root: 데이터 루트 경로
        """
        self.tracker = interaction_tracker
        self.data_root = data_root
        self._user_profiles: Dict[str, Dict] = {}

    def build_user_profile(self, user_id: str) -> Dict:
        """
        사용자 선호도 프로필 구축

        Args:
            user_id: 사용자 ID

        Returns:
            사용자 프로필
        """
        # 캐시 확인
        if user_id in self._user_profiles:
            return self._user_profiles[user_id]

        # 인터랙션 조회
        interactions = self.tracker.get_interactions(user_id)

        if not interactions:
            return self._cold_start_profile()

        # 프로필 초기화
        profile = {
            "user_id": user_id,
            "material_preference": defaultdict(float),
            "capacity_preference": defaultdict(float),
            "neck_size_preference": defaultdict(float),
            "category_preference": defaultdict(float),
            "price_sensitivity": 0.0,
            "total_interactions": len(interactions),
            "last_updated": datetime.now().isoformat(),
        }

        # 인터랙션 분석
        for interaction in interactions:
            weight = interaction["weight"]
            product_idx = interaction["product_idx"]

            # 제품 정보 로드 (간단한 구현)
            product = self._load_product(product_idx)
            if not product:
                continue

            specs = product.get("specifications", {})

            # 재질 선호도
            material = specs.get("재질(원료)", "")
            if material:
                profile["material_preference"][material.upper()] += weight

            # 용량 선호도 (범위로)
            capacity_str = specs.get("capacity", "")
            if capacity_str:
                import re

                match = re.search(r"(\d+)", capacity_str)
                if match:
                    capacity = float(match.group(1))
                    cap_range = self._get_capacity_range(capacity)
                    profile["capacity_preference"][cap_range] += weight

            # 네크 사이즈 선호도
            neck_size = specs.get("neck_size", "")
            if neck_size:
                profile["neck_size_preference"][neck_size] += weight

            # 카테고리 선호도
            category = product.get("category_label", "")
            if category:
                profile["category_preference"][category] += weight

            # 가격 민감도 (저가 제품 선호도)
            pricing = product.get("pricing", {})
            price = pricing.get("discount_price") or pricing.get("regular_price", 0)
            if price > 0:
                # 저가 제품일수록 가격 민감도 증가
                if price < 200:
                    profile["price_sensitivity"] += weight * 0.5

        # 정규화 (선호도를 0-1 범위로)
        total_weight = sum(i["weight"] for i in interactions)
        if total_weight > 0:
            for key in [
                "material_preference",
                "capacity_preference",
                "neck_size_preference",
                "category_preference",
            ]:
                for item in profile[key]:
                    profile[key][item] /= total_weight

            profile["price_sensitivity"] /= total_weight

        # 캐시 저장
        self._user_profiles[user_id] = profile

        return profile

    def recommend_for_user(self, user_id: str, products: List[Dict], limit: int = 10) -> List[Dict]:
        """
        사용자 맞춤 추천

        Args:
            user_id: 사용자 ID
            products: 제품 목록
            limit: 반환할 제품 수

        Returns:
            추천 제품 목록
        """
        # 사용자 프로필 조회
        profile = self.build_user_profile(user_id)

        if not profile or profile["total_interactions"] == 0:
            # Cold start → 인기 제품 반환
            return products[:limit]

        # 각 제품에 개인화 점수 계산
        scored_products = []
        for product in products:
            score = self._calculate_personalization_score(product, profile)

            scored_products.append(
                {
                    **product,
                    "personalization_score": score,
                    "personalization_reason": self._generate_personalization_reason(
                        product, profile
                    ),
                }
            )

        # 개인화 점수 순 정렬
        scored_products.sort(key=lambda x: x["personalization_score"], reverse=True)

        # 다양성 보장 (같은 재질만 추천하지 않도록)
        diverse_results = self._ensure_diversity(scored_products, limit)

        return diverse_results

    def _calculate_personalization_score(self, product: Dict, profile: Dict) -> float:
        """
        제품의 개인화 점수 계산

        Args:
            product: 제품 데이터
            profile: 사용자 프로필

        Returns:
            개인화 점수 (0.0 ~ 1.0)
        """
        score = 0.0
        specs = product.get("specifications", {})

        # 재질 선호도 (40%)
        material = specs.get("재질(원료)", "").upper()
        material_pref = profile["material_preference"].get(material, 0)
        score += 0.4 * material_pref

        # 용량 선호도 (30%)
        capacity_str = specs.get("capacity", "")
        if capacity_str:
            import re

            match = re.search(r"(\d+)", capacity_str)
            if match:
                capacity = float(match.group(1))
                cap_range = self._get_capacity_range(capacity)
                cap_pref = profile["capacity_preference"].get(cap_range, 0)
                score += 0.3 * cap_pref

        # 네크 사이즈 선호도 (20%)
        neck_size = specs.get("neck_size", "")
        neck_pref = profile["neck_size_preference"].get(neck_size, 0)
        score += 0.2 * neck_pref

        # 가격 민감도 반영 (10%)
        pricing = product.get("pricing", {})
        price = pricing.get("discount_price") or pricing.get("regular_price", 300)
        if profile["price_sensitivity"] > 0.5:  # 가격 민감
            if price < 200:
                score += 0.1
        else:  # 프리미엄 선호
            if price > 200:
                score += 0.1

        return min(1.0, score)

    def _generate_personalization_reason(self, product: Dict, profile: Dict) -> str:
        """개인화 추천 이유 생성"""
        reasons = []
        specs = product.get("specifications", {})

        # 재질 선호도
        material = specs.get("재질(원료)", "").upper()
        material_pref = profile["material_preference"].get(material, 0)
        if material_pref > 0.3:
            reasons.append(f"💚 선호 재질 ({material})")

        # 용량 선호도
        capacity_str = specs.get("capacity", "")
        if capacity_str:
            import re

            match = re.search(r"(\d+)", capacity_str)
            if match:
                capacity = float(match.group(1))
                cap_range = self._get_capacity_range(capacity)
                cap_pref = profile["capacity_preference"].get(cap_range, 0)
                if cap_pref > 0.3:
                    reasons.append(f"💚 선호 용량 범위 ({cap_range})")

        # 네크 사이즈 선호도
        neck_size = specs.get("neck_size", "")
        neck_pref = profile["neck_size_preference"].get(neck_size, 0)
        if neck_pref > 0.3:
            reasons.append(f"💚 선호 네크 사이즈 ({neck_size})")

        if not reasons:
            reasons.append("💡 새로운 옵션")

        return " | ".join(reasons)

    def _ensure_diversity(self, products: List[Dict], limit: int) -> List[Dict]:
        """
        다양성 보장 (같은 재질/용량만 추천하지 않도록)

        Args:
            products: 정렬된 제품 목록
            limit: 반환할 제품 수

        Returns:
            다양성이 보장된 제품 목록
        """
        diverse = []
        seen_materials = set()
        seen_capacities = set()

        for product in products:
            if len(diverse) >= limit:
                break

            specs = product.get("specifications", {})
            material = specs.get("재질(원료)", "").upper()
            capacity_str = specs.get("capacity", "")

            # 재질 다양성 체크 (최대 40% 같은 재질)
            material_count = sum(
                1
                for p in diverse
                if p.get("specifications", {}).get("재질(원료)", "").upper() == material
            )

            if material_count >= limit * 0.4:
                continue

            # 용량 다양성 체크
            if capacity_str:
                import re

                match = re.search(r"(\d+)", capacity_str)
                if match:
                    capacity = float(match.group(1))
                    cap_range = self._get_capacity_range(capacity)

                    capacity_count = sum(
                        1
                        for p in diverse
                        if self._get_capacity_range(
                            float(
                                re.search(
                                    r"(\d+)",
                                    p.get("specifications", {}).get("capacity", "0") or "0",
                                ).group(1)
                                if re.search(
                                    r"(\d+)",
                                    p.get("specifications", {}).get("capacity", "0") or "0",
                                )
                                else "0"
                            )
                        )
                        == cap_range
                    )

                    if capacity_count >= limit * 0.4:
                        continue

            diverse.append(product)

        return diverse

    def _get_capacity_range(self, capacity: float) -> str:
        """용량을 범위로 변환"""
        if capacity < 30:
            return "10-30ml"
        elif capacity < 50:
            return "30-50ml"
        elif capacity < 100:
            return "50-100ml"
        elif capacity < 150:
            return "100-150ml"
        elif capacity < 300:
            return "150-300ml"
        else:
            return "300ml+"

    def _cold_start_profile(self) -> Dict:
        """Cold start 사용자의 기본 프로필"""
        return {
            "user_id": "cold_start",
            "material_preference": {},
            "capacity_preference": {},
            "neck_size_preference": {},
            "category_preference": {},
            "price_sensitivity": 0.5,
            "total_interactions": 0,
            "last_updated": datetime.now().isoformat(),
        }

    def _load_product(self, idx: str) -> Optional[Dict]:
        """제품 데이터 로드 (간단한 구현)"""
        # 실제로는 DB 또는 캐시에서 로드
        import json
        from pathlib import Path

        for category in ["Bottle", "Cappump", "Pump", "Jar"]:
            for json_file in (Path(self.data_root) / category).rglob(f"idx_{idx}.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    continue

        return None


# 전역 인스턴스
_collaborative_recommender_instance = None


def get_collaborative_recommender(redis_client=None) -> CollaborativeRecommender:
    """CollaborativeRecommender 싱글톤 반환"""
    global _collaborative_recommender_instance
    if _collaborative_recommender_instance is None:
        tracker = UserInteractionTracker(redis_client)
        _collaborative_recommender_instance = CollaborativeRecommender(tracker)
    return _collaborative_recommender_instance
