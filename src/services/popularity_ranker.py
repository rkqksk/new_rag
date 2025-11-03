"""
인기도 기반 검색 결과 재정렬

검색 관련성 스코어 + 인기도 스코어를 결합하여 최종 랭킹 생성
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json
from pathlib import Path


class PopularityRanker:
    """
    인기도 기반 검색 결과 재정렬기

    핵심 기능:
    1. 하이브리드 랭킹: 관련성 + 인기도
    2. 카테고리별 인기도 적용 (재질/용량/용도별)
    3. 동적 가중치 조정
    4. 신제품 부스트 (cold start 문제 해결)
    """

    # 기본 가중치
    DEFAULT_RELEVANCE_WEIGHT = 0.7      # 관련성 70%
    DEFAULT_POPULARITY_WEIGHT = 0.3     # 인기도 30%

    # 신제품 보호 기간 (일)
    NEW_PRODUCT_GRACE_PERIOD = 14

    def __init__(self, db_connection=None, cache_dir: str = "cache/popularity"):
        """
        Args:
            db_connection: 데이터베이스 연결 (PostgreSQL)
            cache_dir: 인기도 스코어 캐시 디렉토리
        """
        self.db = db_connection
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 인기도 스코어 캐시 (메모리)
        self.popularity_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamp: Optional[datetime] = None
        self.cache_ttl_minutes = 60  # 1시간 캐시

    async def load_popularity_scores(self, force_refresh: bool = False):
        """
        인기도 스코어 로드 (DB → 캐시)

        Args:
            force_refresh: 강제 새로고침 여부
        """
        # 캐시 유효성 확인
        if not force_refresh and self.cache_timestamp:
            elapsed = (datetime.now() - self.cache_timestamp).total_seconds() / 60
            if elapsed < self.cache_ttl_minutes:
                return  # 캐시 유효

        # DB에서 로드
        if self.db:
            try:
                self.popularity_cache = await self._load_from_db()
                self.cache_timestamp = datetime.now()
                return
            except Exception as e:
                print(f"[PopularityRanker] DB 로드 실패: {e}")

        # DB 실패 시 파일에서 로드
        await self._load_from_file()
        self.cache_timestamp = datetime.now()

    async def _load_from_db(self) -> Dict[str, Dict[str, Any]]:
        """
        DB에서 인기도 스코어 로드

        Returns:
            {
                product_idx: {
                    'normalized_score': float,
                    'score_by_material': {PET: 85.5, ...},
                    'score_by_capacity': {50: 75.0, ...},
                    'score_by_use': {로션: 90.2, ...},
                    'trend_percentage': float,
                }
            }
        """
        # TODO: 실제 DB 쿼리 구현
        # SELECT
        #     product_idx,
        #     normalized_score,
        #     score_by_material,
        #     score_by_capacity,
        #     score_by_use,
        #     trend_percentage
        # FROM product_popularity
        # WHERE last_updated >= NOW() - INTERVAL '1 day'

        print("[PopularityRanker] Loading popularity scores from DB")
        return {}

    async def _load_from_file(self):
        """파일에서 인기도 스코어 로드 (백업)"""
        # 최신 파일 찾기
        score_files = sorted(
            self.cache_dir.parent.parent.glob("logs/analytics/popularity_scores_*.json"),
            reverse=True
        )

        if not score_files:
            print("[PopularityRanker] No popularity score files found")
            return

        latest_file = score_files[0]
        print(f"[PopularityRanker] Loading from {latest_file}")

        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.popularity_cache = data.get('product_scores', {})

    def get_popularity_score(
        self,
        product_idx: str,
        context_filters: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        제품의 인기도 스코어 조회

        Args:
            product_idx: 제품 idx
            context_filters: 컨텍스트 필터 {material, capacity_ml, intended_use}

        Returns:
            인기도 스코어 (0-100)
        """
        if product_idx not in self.popularity_cache:
            return 0.0

        scores = self.popularity_cache[product_idx]

        # 1. 기본 스코어
        base_score = scores.get('normalized_score', 0.0)

        # 2. 컨텍스트 기반 부스트
        if context_filters:
            context_score = self._get_context_score(scores, context_filters)
            # 컨텍스트 스코어가 있으면 가중 평균
            if context_score > 0:
                return base_score * 0.6 + context_score * 0.4

        return base_score

    def _get_context_score(
        self,
        scores: Dict[str, Any],
        context_filters: Dict[str, Any]
    ) -> float:
        """
        컨텍스트 기반 스코어 계산

        사용자가 특정 재질/용량을 찾고 있을 때,
        해당 카테고리에서의 인기도를 반영

        Args:
            scores: 제품 스코어 데이터
            context_filters: {material, capacity_ml, intended_use}

        Returns:
            컨텍스트 스코어 (0-100)
        """
        context_scores = []

        # 재질별 스코어
        if 'material' in context_filters:
            material = context_filters['material']
            score_by_material = scores.get('score_by_material', {})
            if isinstance(score_by_material, dict) and material in score_by_material:
                context_scores.append(score_by_material[material])

        # 용량별 스코어
        if 'capacity_ml' in context_filters:
            capacity = str(int(context_filters['capacity_ml']))
            score_by_capacity = scores.get('score_by_capacity', {})
            if isinstance(score_by_capacity, dict) and capacity in score_by_capacity:
                context_scores.append(score_by_capacity[capacity])

        # 용도별 스코어
        if 'intended_use' in context_filters:
            use = context_filters['intended_use']
            score_by_use = scores.get('score_by_use', {})
            if isinstance(score_by_use, dict) and use in score_by_use:
                context_scores.append(score_by_use[use])

        # 평균 반환
        return sum(context_scores) / len(context_scores) if context_scores else 0.0

    async def rerank(
        self,
        search_results: List[Dict[str, Any]],
        relevance_weight: float = DEFAULT_RELEVANCE_WEIGHT,
        popularity_weight: float = DEFAULT_POPULARITY_WEIGHT,
        context_filters: Optional[Dict[str, Any]] = None,
        boost_trending: bool = True,
        protect_new_products: bool = True
    ) -> List[Dict[str, Any]]:
        """
        검색 결과 재정렬

        Args:
            search_results: 검색 결과 리스트
                [{'product_idx': str, 'relevance_score': float, 'metadata': {...}}, ...]
            relevance_weight: 관련성 가중치 (0.0 ~ 1.0)
            popularity_weight: 인기도 가중치 (0.0 ~ 1.0)
            context_filters: 컨텍스트 필터 (재질/용량/용도)
            boost_trending: 트렌드 상승 제품 부스트 여부
            protect_new_products: 신제품 보호 여부

        Returns:
            재정렬된 검색 결과 (final_score 추가)
        """
        # 가중치 정규화
        total_weight = relevance_weight + popularity_weight
        if total_weight > 0:
            relevance_weight /= total_weight
            popularity_weight /= total_weight

        # 인기도 스코어 로드
        await self.load_popularity_scores()

        # 스코어 계산
        for result in search_results:
            product_idx = result.get('product_idx')
            relevance_score = result.get('relevance_score', 0.0)

            # 인기도 스코어
            popularity_score = self.get_popularity_score(product_idx, context_filters)

            # 신제품 보호
            if protect_new_products:
                is_new = self._is_new_product(result.get('metadata', {}))
                if is_new and popularity_score < 20:
                    # 신제품은 최소 20점 보장
                    popularity_score = 20.0

            # 트렌드 부스트
            trend_boost = 1.0
            if boost_trending and product_idx in self.popularity_cache:
                trend_percentage = self.popularity_cache[product_idx].get('trend_percentage', 0.0)
                if trend_percentage > 30:  # 30% 이상 상승
                    trend_boost = 1.1  # 10% 부스트
                elif trend_percentage > 50:  # 50% 이상 상승
                    trend_boost = 1.2  # 20% 부스트

            # 최종 스코어
            final_score = (
                relevance_score * relevance_weight +
                popularity_score * popularity_weight
            ) * trend_boost

            # 결과에 추가
            result['popularity_score'] = popularity_score
            result['trend_boost'] = trend_boost
            result['final_score'] = final_score

        # 정렬
        search_results.sort(key=lambda x: x['final_score'], reverse=True)

        return search_results

    def _is_new_product(self, metadata: Dict[str, Any]) -> bool:
        """
        신제품 여부 확인

        Args:
            metadata: 제품 메타데이터

        Returns:
            신제품 여부
        """
        # 등록일 확인
        created_at = metadata.get('created_at')
        if not created_at:
            return False

        # 문자열이면 datetime으로 변환
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                return False

        # 보호 기간 내 제품
        days_since_creation = (datetime.now() - created_at).days
        return days_since_creation <= self.NEW_PRODUCT_GRACE_PERIOD

    async def get_popular_products(
        self,
        top_k: int = 10,
        category_filter: Optional[str] = None,
        material_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        인기 제품 조회 (검색 없이)

        Args:
            top_k: 반환할 제품 수
            category_filter: 카테고리 필터 (Bottle, Pump, Cap, etc.)
            material_filter: 재질 필터 (PET, HDPE, PP, etc.)

        Returns:
            인기 제품 리스트 (스코어 순)
        """
        await self.load_popularity_scores()

        # 필터 적용
        filtered = []
        for product_idx, scores in self.popularity_cache.items():
            # TODO: 제품 메타데이터에서 category, material 가져오기
            # 지금은 단순히 스코어만 사용
            filtered.append({
                'product_idx': product_idx,
                'popularity_score': scores.get('normalized_score', 0.0),
                'trend_percentage': scores.get('trend_percentage', 0.0),
            })

        # 정렬
        filtered.sort(key=lambda x: x['popularity_score'], reverse=True)

        return filtered[:top_k]

    async def explain_ranking(
        self,
        product_idx: str,
        relevance_score: float,
        context_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        랭킹 설명 (디버깅용)

        Args:
            product_idx: 제품 idx
            relevance_score: 관련성 스코어
            context_filters: 컨텍스트 필터

        Returns:
            {
                'product_idx': str,
                'relevance_score': float,
                'popularity_score': float,
                'context_boost': float,
                'trend_boost': float,
                'final_score': float,
                'explanation': str
            }
        """
        await self.load_popularity_scores()

        popularity_score = self.get_popularity_score(product_idx, context_filters)

        # 트렌드 부스트
        trend_boost = 1.0
        trend_percentage = 0.0
        if product_idx in self.popularity_cache:
            trend_percentage = self.popularity_cache[product_idx].get('trend_percentage', 0.0)
            if trend_percentage > 30:
                trend_boost = 1.1
            elif trend_percentage > 50:
                trend_boost = 1.2

        # 최종 스코어
        final_score = (
            relevance_score * self.DEFAULT_RELEVANCE_WEIGHT +
            popularity_score * self.DEFAULT_POPULARITY_WEIGHT
        ) * trend_boost

        # 설명 생성
        explanation_parts = [
            f"관련성 스코어: {relevance_score:.2f} (가중치 {self.DEFAULT_RELEVANCE_WEIGHT})",
            f"인기도 스코어: {popularity_score:.2f} (가중치 {self.DEFAULT_POPULARITY_WEIGHT})",
        ]

        if trend_boost > 1.0:
            explanation_parts.append(f"트렌드 부스트: {trend_boost}x (상승률 {trend_percentage:+.1f}%)")

        if context_filters:
            explanation_parts.append(f"컨텍스트 필터 적용: {context_filters}")

        explanation = " | ".join(explanation_parts)
        explanation += f" → 최종: {final_score:.2f}"

        return {
            'product_idx': product_idx,
            'relevance_score': relevance_score,
            'popularity_score': popularity_score,
            'context_boost': 0.0,  # TODO: 계산
            'trend_boost': trend_boost,
            'final_score': final_score,
            'explanation': explanation
        }


# 싱글톤 인스턴스
_ranker_instance = None


def get_popularity_ranker(db_connection=None) -> PopularityRanker:
    """싱글톤 인기도 랭커 반환"""
    global _ranker_instance
    if _ranker_instance is None:
        _ranker_instance = PopularityRanker(db_connection=db_connection)
    return _ranker_instance
