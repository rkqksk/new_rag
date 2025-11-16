"""
인기도 스코어 계산 엔진
수집된 사용자 행동 데이터를 기반으로 제품 인기도 스코어 계산
"""

import asyncio
import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class PopularityCalculator:
    """
    인기도 스코어 계산 엔진

    핵심 기능:
    1. 가중치 기반 스코어 계산
    2. 시간 감쇠 적용 (최근 데이터 우선)
    3. 트렌드 부스트 (상승세 제품 가산점)
    4. 카테고리별 스코어 (재질/용도/용량별)
    5. 정규화 (0-100 스케일)
    """

    # 행동별 가중치
    WEIGHT_SAMPLE_REQUEST = 10.0  # 샘플 신청 (가장 강력한 구매 의도)
    WEIGHT_CLICK = 3.0  # 클릭
    WEIGHT_SEARCH = 1.0  # 검색 출현
    WEIGHT_CONVERSATION = 0.5  # 대화 언급

    # 시간 감쇠 파라미터
    DECAY_HALFLIFE_DAYS = 7  # 7일마다 절반으로 감소

    # 트렌드 계산
    TREND_BOOST_MAX = 1.5  # 최대 1.5배 부스트
    TREND_BOOST_MIN = 0.8  # 최소 0.8배 패널티

    def __init__(self, db_connection=None, backup_dir: str = "logs/analytics"):
        """
        Args:
            db_connection: 데이터베이스 연결 (PostgreSQL)
            backup_dir: DB 실패 시 백업 디렉토리
        """
        self.db = db_connection
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def time_decay_factor(self, days_ago: float) -> float:
        """
        시간 감쇠 계산

        최근 데이터에 더 높은 가중치 부여
        반감기 기반 지수 감쇠: factor = 0.5 ^ (days_ago / halflife)

        Args:
            days_ago: 며칠 전 데이터인지

        Returns:
            감쇠 계수 (0.0 ~ 1.0)

        Examples:
            - 오늘: 1.0
            - 7일 전: 0.5
            - 14일 전: 0.25
            - 30일 전: 0.088
        """
        return math.pow(0.5, days_ago / self.DECAY_HALFLIFE_DAYS)

    def trend_boost_factor(self, recent_7d_score: float, previous_7d_score: float) -> float:
        """
        트렌드 부스트 계산

        최근 7일 vs 이전 7-14일 비교하여 상승세 제품에 가산점

        Args:
            recent_7d_score: 최근 7일 스코어
            previous_7d_score: 이전 7-14일 스코어

        Returns:
            부스트 계수 (0.8 ~ 1.5)

        Examples:
            - 2배 증가: 1.5x (최대 부스트)
            - 1.5배 증가: 1.35x
            - 동일: 1.0x
            - 절반 감소: 0.85x
            - 대폭 감소: 0.8x (최소 패널티)
        """
        if previous_7d_score == 0:
            # 이전 데이터 없으면 중립
            return 1.0

        # 증가율 계산
        growth_rate = (recent_7d_score / previous_7d_score) - 1.0

        # 증가율을 부스트 계수로 변환 (-1.0 ~ +2.0 → 0.8 ~ 1.5)
        # growth_rate = +2.0 (3배 증가) → boost = 1.5
        # growth_rate = 0.0 (동일) → boost = 1.0
        # growth_rate = -0.5 (절반) → boost = 0.85
        # growth_rate = -1.0 (제로) → boost = 0.8

        if growth_rate >= 1.0:
            # 2배 이상 증가
            boost = self.TREND_BOOST_MAX
        elif growth_rate >= 0:
            # 증가세 (0% ~ 100%)
            boost = 1.0 + (growth_rate * 0.5)  # 0% → 1.0, 100% → 1.5
        else:
            # 감소세
            boost = max(self.TREND_BOOST_MIN, 1.0 + (growth_rate * 0.2))

        return boost

    def normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """
        스코어를 0-100 스케일로 정규화

        Args:
            scores: {product_idx: raw_score}

        Returns:
            {product_idx: normalized_score (0-100)}
        """
        if not scores:
            return {}

        max_score = max(scores.values())
        if max_score == 0:
            return {k: 0.0 for k in scores.keys()}

        return {product_idx: (score / max_score) * 100.0 for product_idx, score in scores.items()}

    async def calculate_product_scores(self, window_days: int = 30) -> Dict[str, Dict[str, Any]]:
        """
        제품별 인기도 스코어 계산

        Args:
            window_days: 집계 기간 (기본 30일)

        Returns:
            {
                product_idx: {
                    'total_score': float,
                    'normalized_score': float,
                    'sample_request_count': int,
                    'click_count': int,
                    'search_appearance_count': int,
                    'conversation_mention_count': int,
                    'recent_7d_score': float,
                    'previous_7d_score': float,
                    'trend_percentage': float,
                    'trend_boost': float,
                }
            }
        """
        now = datetime.now()
        window_start = now - timedelta(days=window_days)
        recent_7d_start = now - timedelta(days=7)
        previous_7d_start = now - timedelta(days=14)

        # 1. 데이터 수집 (최근 30일)
        sample_requests = await self._get_sample_requests(window_start, now)
        clicks = await self._get_clicks(window_start, now)
        searches = await self._get_search_appearances(window_start, now)
        conversations = await self._get_conversation_mentions(window_start, now)

        # 2. 트렌드 계산용 데이터 (최근 7일 vs 이전 7-14일)
        recent_7d_data = await self._get_recent_activity(recent_7d_start, now)
        previous_7d_data = await self._get_recent_activity(previous_7d_start, recent_7d_start)

        # 3. 제품별 스코어 계산
        product_scores = {}
        all_products = set(
            list(sample_requests.keys())
            + list(clicks.keys())
            + list(searches.keys())
            + list(conversations.keys())
        )

        for product_idx in all_products:
            # 각 행동별 카운트
            sample_count = len(sample_requests.get(product_idx, []))
            click_count = len(clicks.get(product_idx, []))
            search_count = searches.get(product_idx, 0)
            conversation_count = conversations.get(product_idx, 0)

            # 시간 감쇠 적용 스코어 계산
            sample_score = self._calculate_weighted_score(
                sample_requests.get(product_idx, []), self.WEIGHT_SAMPLE_REQUEST, now
            )
            click_score = self._calculate_weighted_score(
                clicks.get(product_idx, []), self.WEIGHT_CLICK, now
            )
            search_score = search_count * self.WEIGHT_SEARCH
            conversation_score = conversation_count * self.WEIGHT_CONVERSATION

            # 총 스코어 (시간 감쇠 적용)
            total_score = sample_score + click_score + search_score + conversation_score

            # 트렌드 계산
            recent_7d_score = recent_7d_data.get(product_idx, 0.0)
            previous_7d_score = previous_7d_data.get(product_idx, 0.0)
            trend_boost = self.trend_boost_factor(recent_7d_score, previous_7d_score)

            # 트렌드 적용
            total_score *= trend_boost

            # 트렌드 퍼센티지
            if previous_7d_score > 0:
                trend_percentage = ((recent_7d_score / previous_7d_score) - 1.0) * 100
            else:
                trend_percentage = 0.0

            product_scores[product_idx] = {
                "total_score": total_score,
                "normalized_score": 0.0,  # 나중에 정규화
                "sample_request_count": sample_count,
                "click_count": click_count,
                "search_appearance_count": search_count,
                "conversation_mention_count": conversation_count,
                "recent_7d_score": recent_7d_score,
                "previous_7d_score": previous_7d_score,
                "trend_percentage": trend_percentage,
                "trend_boost": trend_boost,
            }

        # 4. 정규화 (0-100)
        raw_scores = {k: v["total_score"] for k, v in product_scores.items()}
        normalized_scores = self.normalize_scores(raw_scores)

        for product_idx, normalized_score in normalized_scores.items():
            product_scores[product_idx]["normalized_score"] = normalized_score

        return product_scores

    def _calculate_weighted_score(
        self, events: List[Dict], base_weight: float, now: datetime
    ) -> float:
        """
        이벤트 리스트의 가중치 합계 계산 (시간 감쇠 적용)

        Args:
            events: 이벤트 리스트 [{'timestamp': datetime, ...}, ...]
            base_weight: 기본 가중치
            now: 현재 시간

        Returns:
            가중치 합계
        """
        total_score = 0.0

        for event in events:
            timestamp = event.get("timestamp", now)
            days_ago = (now - timestamp).total_seconds() / 86400
            decay = self.time_decay_factor(days_ago)
            total_score += base_weight * decay

        return total_score

    async def calculate_category_scores(
        self, product_scores: Dict[str, Dict[str, Any]], product_metadata: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        카테고리별 스코어 계산 (재질/용도/용량별)

        Args:
            product_scores: 제품별 스코어
            product_metadata: 제품 메타데이터 {product_idx: {material, capacity_ml, category, ...}}

        Returns:
            {
                product_idx: {
                    'score_by_material': {PET: 85.5, HDPE: 20.3, ...},
                    'score_by_use': {로션: 90.2, 크림: 45.1, ...},
                    'score_by_capacity': {50: 75.0, 100: 60.5, ...},
                    'score_by_category': {Bottle: 80.0, Pump: 70.0, ...}
                }
            }
        """
        # 1. 재질별 그룹화
        by_material = {}
        by_capacity = {}
        by_category = {}

        for product_idx, score_data in product_scores.items():
            metadata = product_metadata.get(product_idx, {})
            material = metadata.get("material", "Unknown")
            capacity = metadata.get("capacity_ml")
            category = metadata.get("category", "Unknown")

            # 재질별
            if material not in by_material:
                by_material[material] = {}
            by_material[material][product_idx] = score_data["normalized_score"]

            # 용량별
            if capacity:
                capacity_key = str(int(capacity))
                if capacity_key not in by_capacity:
                    by_capacity[capacity_key] = {}
                by_capacity[capacity_key][product_idx] = score_data["normalized_score"]

            # 카테고리별
            if category not in by_category:
                by_category[category] = {}
            by_category[category][product_idx] = score_data["normalized_score"]

        # 2. 각 카테고리 내에서 정규화
        for material, scores in by_material.items():
            by_material[material] = self.normalize_scores(scores)

        for capacity, scores in by_capacity.items():
            by_capacity[capacity] = self.normalize_scores(scores)

        for category, scores in by_category.items():
            by_category[category] = self.normalize_scores(scores)

        # 3. 제품별로 재구성
        category_scores = {}
        for product_idx in product_scores.keys():
            metadata = product_metadata.get(product_idx, {})
            material = metadata.get("material", "Unknown")
            capacity = metadata.get("capacity_ml")
            category = metadata.get("category", "Unknown")

            category_scores[product_idx] = {
                "score_by_material": {
                    material: by_material.get(material, {}).get(product_idx, 0.0)
                },
                "score_by_capacity": (
                    {
                        str(int(capacity)): by_capacity.get(str(int(capacity)), {}).get(
                            product_idx, 0.0
                        )
                    }
                    if capacity
                    else {}
                ),
                "score_by_category": {
                    category: by_category.get(category, {}).get(product_idx, 0.0)
                },
                "score_by_use": {},  # TODO: 용도별 스코어는 샘플 신청 데이터에서 추출
            }

        return category_scores

    async def update_popularity_table(
        self,
        product_scores: Dict[str, Dict[str, Any]],
        category_scores: Dict[str, Dict[str, Dict[str, float]]],
        product_metadata: Dict[str, Dict[str, Any]],
    ):
        """
        product_popularity 테이블 업데이트

        Args:
            product_scores: 제품별 스코어
            category_scores: 카테고리별 스코어
            product_metadata: 제품 메타데이터
        """
        now = datetime.now()
        window_start = now - timedelta(days=30)

        if self.db:
            try:
                await self._update_db(
                    product_scores, category_scores, product_metadata, window_start, now
                )
            except Exception as e:
                print(f"[PopularityCalculator] DB 업데이트 실패: {e}")
                await self._save_to_file(product_scores, category_scores)
        else:
            # DB 연결 없으면 파일로 저장
            await self._save_to_file(product_scores, category_scores)

    async def _update_db(
        self,
        product_scores: Dict,
        category_scores: Dict,
        product_metadata: Dict,
        window_start: datetime,
        window_end: datetime,
    ):
        """
        PostgreSQL DB 업데이트

        UPSERT (INSERT ... ON CONFLICT UPDATE) 사용
        """
        # TODO: 실제 DB 연결 구현
        print(f"[PopularityCalculator] Updating {len(product_scores)} products in DB")

        # for product_idx, scores in product_scores.items():
        #     metadata = product_metadata.get(product_idx, {})
        #     category = category_scores.get(product_idx, {})
        #
        #     await self.db.execute("""
        #         INSERT INTO product_popularity (
        #             product_idx, product_code, product_name, category, material, capacity_ml, neck_size,
        #             sample_request_count, click_count, search_appearance_count, conversation_mention_count,
        #             total_score, normalized_score,
        #             score_by_material, score_by_use, score_by_capacity, score_by_category,
        #             recent_7d_score, previous_7d_score, trend_percentage,
        #             data_window_start, data_window_end, last_updated
        #         ) VALUES (
        #             %(product_idx)s, %(product_code)s, %(product_name)s, %(category)s, %(material)s, %(capacity_ml)s, %(neck_size)s,
        #             %(sample_request_count)s, %(click_count)s, %(search_appearance_count)s, %(conversation_mention_count)s,
        #             %(total_score)s, %(normalized_score)s,
        #             %(score_by_material)s, %(score_by_use)s, %(score_by_capacity)s, %(score_by_category)s,
        #             %(recent_7d_score)s, %(previous_7d_score)s, %(trend_percentage)s,
        #             %(data_window_start)s, %(data_window_end)s, NOW()
        #         )
        #         ON CONFLICT (product_idx) DO UPDATE SET
        #             sample_request_count = EXCLUDED.sample_request_count,
        #             click_count = EXCLUDED.click_count,
        #             search_appearance_count = EXCLUDED.search_appearance_count,
        #             conversation_mention_count = EXCLUDED.conversation_mention_count,
        #             total_score = EXCLUDED.total_score,
        #             normalized_score = EXCLUDED.normalized_score,
        #             score_by_material = EXCLUDED.score_by_material,
        #             score_by_use = EXCLUDED.score_by_use,
        #             score_by_capacity = EXCLUDED.score_by_capacity,
        #             score_by_category = EXCLUDED.score_by_category,
        #             recent_7d_score = EXCLUDED.recent_7d_score,
        #             previous_7d_score = EXCLUDED.previous_7d_score,
        #             trend_percentage = EXCLUDED.trend_percentage,
        #             data_window_start = EXCLUDED.data_window_start,
        #             data_window_end = EXCLUDED.data_window_end,
        #             last_updated = NOW()
        #     """, {
        #         'product_idx': product_idx,
        #         'product_code': metadata.get('product_code'),
        #         'product_name': metadata.get('product_name'),
        #         'category': metadata.get('category'),
        #         'material': metadata.get('material'),
        #         'capacity_ml': metadata.get('capacity_ml'),
        #         'neck_size': metadata.get('neck_size'),
        #         'sample_request_count': scores['sample_request_count'],
        #         'click_count': scores['click_count'],
        #         'search_appearance_count': scores['search_appearance_count'],
        #         'conversation_mention_count': scores['conversation_mention_count'],
        #         'total_score': scores['total_score'],
        #         'normalized_score': scores['normalized_score'],
        #         'score_by_material': json.dumps(category['score_by_material']),
        #         'score_by_use': json.dumps(category['score_by_use']),
        #         'score_by_capacity': json.dumps(category['score_by_capacity']),
        #         'score_by_category': json.dumps(category['score_by_category']),
        #         'recent_7d_score': scores['recent_7d_score'],
        #         'previous_7d_score': scores['previous_7d_score'],
        #         'trend_percentage': scores['trend_percentage'],
        #         'data_window_start': window_start,
        #         'data_window_end': window_end,
        #     })

    async def _save_to_file(self, product_scores: Dict, category_scores: Dict):
        """파일로 백업 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"popularity_scores_{timestamp}.json"

        data = {
            "timestamp": timestamp,
            "product_scores": product_scores,
            "category_scores": category_scores,
        }

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        print(f"[PopularityCalculator] Saved scores to {backup_file}")

    # ============================================================
    # 데이터 조회 메서드 (DB 또는 BehaviorTracker 백업 파일)
    # ============================================================

    async def _get_sample_requests(self, start: datetime, end: datetime) -> Dict[str, List[Dict]]:
        """
        샘플 신청 데이터 조회

        Returns:
            {product_idx: [{'timestamp': datetime, ...}, ...]}
        """
        # TODO: 실제 DB 쿼리 구현
        # SELECT product_idx, requested_at FROM sample_requests
        # WHERE requested_at BETWEEN start AND end
        return {}

    async def _get_clicks(self, start: datetime, end: datetime) -> Dict[str, List[Dict]]:
        """
        클릭 데이터 조회

        Returns:
            {product_idx: [{'timestamp': datetime, ...}, ...]}
        """
        # TODO: 실제 DB 쿼리 구현
        return {}

    async def _get_search_appearances(self, start: datetime, end: datetime) -> Dict[str, int]:
        """
        검색 출현 데이터 조회

        Returns:
            {product_idx: appearance_count}
        """
        # TODO: 실제 DB 쿼리 구현
        return {}

    async def _get_conversation_mentions(self, start: datetime, end: datetime) -> Dict[str, int]:
        """
        대화 언급 데이터 조회

        Returns:
            {product_idx: mention_count}
        """
        # TODO: 실제 DB 쿼리 구현
        return {}

    async def _get_recent_activity(self, start: datetime, end: datetime) -> Dict[str, float]:
        """
        특정 기간의 활동 스코어 계산 (트렌드 분석용)

        Returns:
            {product_idx: activity_score}
        """
        # TODO: 실제 DB 쿼리 구현
        return {}


# 싱글톤 인스턴스
_calculator_instance = None


def get_popularity_calculator(db_connection=None) -> PopularityCalculator:
    """싱글톤 인기도 계산기 반환"""
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = PopularityCalculator(db_connection=db_connection)
    return _calculator_instance
