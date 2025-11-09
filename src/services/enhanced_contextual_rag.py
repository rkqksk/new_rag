"""
강화된 컨텍스트 인식 RAG 서비스
영업사원 수준의 대화 상태 머신 통합
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.analytics.behavior_tracker import get_behavior_tracker
from src.core.conversation_state import ConversationState, DialogueContext, StateTransition
from src.core.dialogue_router import DialogueRouter, IntentType, RoutingDecision
from src.core.enhanced_reference_resolver import EnhancedReferenceResolver
from src.core.filter_manager import FilterManager
from src.services.intent_recommender import get_intent_recommender
from src.services.popularity_ranker import get_popularity_ranker


class EnhancedContextualRAG:
    """
    강화된 컨텍스트 기반 RAG 시스템

    핵심 기능:
    1. 대화 상태 머신 - 10가지 대화 상태 관리
    2. 누적 필터링 - "50ml" → "PET만" → "투명만"
    3. 스마트 참조 해결 - "3번", "그거", "원산지 증명서"
    4. 의도 기반 라우팅 - 컨텍스트 기반 액션 결정
    """

    def __init__(
        self, data_root: str = "/Users/oypnus/Project/rag-enterprise/data/crawled_products_final"
    ):
        """
        Args:
            data_root: 제품 데이터 루트 경로
        """
        self.data_root = Path(data_root)

        # 대화 상태 관리
        self.sessions: Dict[str, DialogueContext] = {}
        self.filter_managers: Dict[str, FilterManager] = {}

        # 핵심 컴포넌트
        self.router = DialogueRouter()
        self.reference_resolver = EnhancedReferenceResolver()
        self.intent_recommender = get_intent_recommender()
        self.behavior_tracker = get_behavior_tracker()  # 행동 추적기
        self.popularity_ranker = get_popularity_ranker()  # 인기도 랭커

        # 제품 데이터 캐시
        self._product_cache: Dict[str, Dict] = {}

    async def query(
        self,
        session_id: str,
        user_query: str,
        user_id: str = "default_user",
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        컨텍스트 기반 쿼리 처리 (영업사원 수준)

        Args:
            session_id: 세션 ID
            user_query: 사용자 쿼리
            user_id: 사용자 ID
            ip_address: 사용자 IP 주소

        Returns:
            응답 딕셔너리
        """
        # 시작 시간 기록
        start_time = datetime.now()

        # 1. 세션 컨텍스트 로드 또는 생성
        context = self._get_or_create_context(session_id, user_id)
        filter_manager = self._get_or_create_filter_manager(session_id)

        # 2. 라우팅 결정
        routing = self.router.route(user_query, context, filter_manager)

        print(
            f"[ROUTER] Intent: {routing.intent}, Action: {routing.action}, State: {routing.next_state}"
        )

        # 3. 액션별 처리
        if routing.action == "search":
            result = await self._handle_search(routing, context, filter_manager)
        elif routing.action == "apply_filter":
            result = await self._handle_filter(routing, context, filter_manager)
        elif routing.action == "show_detail":
            result = await self._handle_detail(routing, context)
        elif routing.action == "show_document":
            result = await self._handle_document(routing, context)
        elif routing.action == "find_compatible":
            result = await self._handle_compatibility(routing, context)
        elif routing.action == "compare_products":
            result = await self._handle_compare(routing, context)
        elif routing.action == "greeting":
            result = self._handle_greeting(routing)
        elif routing.action == "reset":
            result = self._handle_reset(session_id, context, filter_manager)
        elif routing.action == "request_clarification":
            result = self._handle_clarification(routing)
        else:
            result = {"error": f"Unknown action: {routing.action}"}

        # 4. 상태 전환
        try:
            StateTransition.transition(
                context, routing.next_state, reason=f"{routing.intent}: {routing.action}"
            )
        except ValueError as e:
            print(f"[STATE] Invalid transition: {e}")

        # 5. 컨텍스트 업데이트
        self._update_context(context, user_query, routing, result)

        # 6. 세션 저장
        self.sessions[session_id] = context

        # 7. 응답 시간 계산
        response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # 8. 응답 구성
        response = {
            "session_id": session_id,
            "query": user_query,
            "intent": routing.intent.value,
            "action": routing.action,
            "state": context.current_state.value,
            "confidence": routing.confidence,
            "response_time_ms": response_time_ms,
            **result,
        }

        # 9. 행동 로그 기록 (비동기)
        asyncio.create_task(
            self._log_user_behavior(
                user_id,
                session_id,
                user_query,
                routing,
                result,
                context,
                response_time_ms,
                ip_address,
            )
        )

        return response

    async def _handle_search(
        self, routing: RoutingDecision, context: DialogueContext, filter_manager: FilterManager
    ) -> Dict:
        """새로운 검색 처리 (인기도 랭킹 통합)"""
        params = routing.parameters
        query = params["query"]
        filters = params.get("filters", {})

        # 1. 제품 검색
        products = self._search_products(query, filters)

        # 2. 스마트 추천 적용
        product_type = self.intent_recommender.detect_product_type(query)
        if product_type and products:
            products = self.intent_recommender.recommend(
                query=query, products=products, limit=50  # 더 많이 가져와서 재정렬
            )

        # 3. 인기도 기반 재정렬 (NEW)
        if products:
            # 검색 결과를 인기도 랭커 형식으로 변환
            search_results = []
            for i, product in enumerate(products):
                search_results.append(
                    {
                        "product_idx": product.get("idx"),
                        "relevance_score": 100 - (i * 1.5),  # 검색 순위 기반 관련성 스코어
                        "metadata": product,
                    }
                )

            # 인기도 랭킹 적용
            reranked = await self.popularity_ranker.rerank(
                search_results=search_results,
                relevance_weight=0.7,
                popularity_weight=0.3,
                context_filters=filters,
                boost_trending=True,
                protect_new_products=True,
            )

            # 재정렬된 제품 리스트로 변환
            products = [r["metadata"] for r in reranked]

        # 4. 검색 결과 캐싱
        if products:
            filter_manager.cache_results(products, filters)

        # 5. 응답 생성
        return {
            "products": products[:10],
            "response": f"{len(products)}개 제품을 찾았습니다.",
            "total_count": len(products),
            "filters_applied": filters,
            "product_type": product_type,
            "ranking_applied": "popularity",  # 인기도 랭킹 적용 표시
        }

    async def _handle_filter(
        self, routing: RoutingDecision, context: DialogueContext, filter_manager: FilterManager
    ) -> Dict:
        """누적 필터 처리 (인기도 랭킹 통합)"""
        params = routing.parameters
        new_filters = params["filters"]

        # 1. 캐시된 결과 사용
        cached_results = filter_manager.get_cached_results()
        if not cached_results:
            return {
                "products": [],
                "response": "필터를 적용할 이전 검색 결과가 없습니다.",
                "total_count": 0,
            }

        # 2. 누적 필터 적용
        filtered_products = filter_manager.apply_incremental_filter(new_filters, cached_results)

        # 3. 인기도 기반 재정렬 (NEW)
        if filtered_products:
            # 검색 결과를 인기도 랭커 형식으로 변환
            search_results = []
            for i, product in enumerate(filtered_products):
                search_results.append(
                    {
                        "product_idx": product.get("idx"),
                        "relevance_score": 100 - (i * 1.5),  # 기존 순위 기반 관련성
                        "metadata": product,
                    }
                )

            # 활성 필터를 컨텍스트로 사용하여 카테고리별 인기도 적용
            all_filters = filter_manager.active_filters
            reranked = await self.popularity_ranker.rerank(
                search_results=search_results,
                relevance_weight=0.6,  # 필터 적용 시 인기도 비중 증가
                popularity_weight=0.4,
                context_filters=all_filters,
                boost_trending=True,
                protect_new_products=True,
            )

            # 재정렬된 제품 리스트로 변환
            filtered_products = [r["metadata"] for r in reranked]

        # 4. 필터링된 결과 재캐싱
        all_filters = filter_manager.active_filters
        filter_manager.cache_results(filtered_products, all_filters)

        # 5. 응답 생성
        filter_desc = ", ".join([f"{k}={v}" for k, v in new_filters.items()])
        return {
            "products": filtered_products[:10],
            "response": f"{filter_desc} 조건으로 {len(filtered_products)}개 제품을 필터링했습니다.",
            "total_count": len(filtered_products),
            "filters_applied": all_filters,
            "ranking_applied": "popularity_with_context",  # 컨텍스트 기반 인기도 랭킹
        }

    async def _handle_detail(self, routing: RoutingDecision, context: DialogueContext) -> Dict:
        """상세 정보 처리"""
        product_idx = routing.parameters["product_idx"]
        product = self._load_product(product_idx)

        if not product:
            return {
                "products": [],
                "response": f"제품 {product_idx}를 찾을 수 없습니다.",
                "total_count": 0,
            }

        # 상세 정보 포맷팅
        specs = product.get("specifications", {})
        response = f"📦 {product.get('product_name')}\n\n"
        response += f"제품 코드: {product.get('product_code', 'N/A')}\n"
        response += f"재질: {specs.get('재질(원료)', 'N/A')}\n"
        response += f"용량: {specs.get('capacity', 'N/A')}\n"
        response += f"네크 사이즈: {specs.get('neck_size', 'N/A')}\n"

        return {
            "products": [product],
            "response": response,
            "total_count": 1,
            "product_detail": product,
        }

    async def _handle_document(self, routing: RoutingDecision, context: DialogueContext) -> Dict:
        """문서 요청 처리"""
        product_idx = routing.parameters["product_idx"]
        doc_type = routing.parameters["document_type"]

        product = self._load_product(product_idx)
        if not product:
            return {
                "products": [],
                "response": f"제품 {product_idx}를 찾을 수 없습니다.",
                "total_count": 0,
            }

        # 문서 타입별 처리
        doc_type_names = {
            "certificate_of_origin": "원산지 증명서",
            "specification": "스펙 시트",
            "catalog": "카탈로그",
            "drawing": "도면",
        }

        doc_name = doc_type_names.get(doc_type, "문서")

        # 실제로는 문서 파일 경로를 반환하거나 생성
        response = f"{product.get('product_name')}의 {doc_name}를 준비 중입니다."

        return {
            "products": [product],
            "response": response,
            "total_count": 1,
            "document_type": doc_type,
            "document_available": False,  # 실제 구현 시 문서 존재 여부 확인
        }

    async def _handle_compatibility(
        self, routing: RoutingDecision, context: DialogueContext
    ) -> Dict:
        """호환성 확인 처리"""
        base_product_idx = routing.parameters["base_product_idx"]
        compatible_type = routing.parameters.get("compatible_type")

        base_product = self._load_product(base_product_idx)
        if not base_product:
            return {
                "products": [],
                "response": f"제품 {base_product_idx}를 찾을 수 없습니다.",
                "total_count": 0,
            }

        # 호환 제품 조회
        compat_analysis = base_product.get("compatibility_analysis", {})
        compat_items = compat_analysis.get("compatible_caps_pumps", {}).get("items", [])

        # 호환 제품 상세 정보 로드
        compatible_products = []
        for item in compat_items[:10]:
            idx = item.get("idx")
            if idx:
                compat_product = self._load_product(idx)
                if compat_product:
                    compatible_products.append(compat_product)

        return {
            "products": compatible_products,
            "response": f"{base_product.get('product_name')}와 호환되는 제품 {len(compatible_products)}개를 찾았습니다.",
            "total_count": len(compatible_products),
            "compatibility_for": base_product_idx,
        }

    async def _handle_compare(self, routing: RoutingDecision, context: DialogueContext) -> Dict:
        """제품 비교 처리"""
        product_indices = routing.parameters["product_indices"]

        products = []
        for idx in product_indices:
            product = self._load_product(idx)
            if product:
                products.append(product)

        if len(products) < 2:
            return {
                "products": products,
                "response": "비교하려면 최소 2개 제품이 필요합니다.",
                "total_count": len(products),
            }

        return {
            "products": products,
            "response": f"{len(products)}개 제품을 비교합니다.",
            "total_count": len(products),
            "comparison_mode": True,
        }

    def _handle_greeting(self, routing: RoutingDecision) -> Dict:
        """인사 처리"""
        return {"products": [], "response": "안녕하세요! 무엇을 도와드릴까요?", "total_count": 0}

    def _handle_reset(
        self, session_id: str, context: DialogueContext, filter_manager: FilterManager
    ) -> Dict:
        """대화 초기화 처리"""
        # 필터 초기화
        filter_manager.reset_filters()

        # 컨텍스트 초기화 (세션 ID, 사용자 ID는 유지)
        context.last_query = ""
        context.last_search_results = []
        context.display_indices = {}
        context.active_filters = {}
        context.focused_product = None
        context.focused_product_name = None
        context.comparison_products = []

        return {
            "products": [],
            "response": "대화를 초기화했습니다. 무엇을 도와드릴까요?",
            "total_count": 0,
        }

    def _handle_clarification(self, routing: RoutingDecision) -> Dict:
        """명확화 요청 처리"""
        clarification_msg = routing.parameters.get("clarification_message", "무엇을 도와드릴까요?")

        return {
            "products": [],
            "response": clarification_msg,
            "total_count": 0,
            "requires_clarification": True,
        }

    def _search_products(self, query: str, filters: Dict) -> List[Dict]:
        """제품 검색 (간단한 파일 기반 구현)"""
        products = []

        # Bottle 디렉토리 검색
        for category in ["Bottle", "Cappump", "Pump", "Jar"]:
            category_path = self.data_root / category
            if not category_path.exists():
                continue

            for json_file in category_path.rglob("*.json"):
                try:
                    product = self._load_product_from_file(json_file)
                    if product and self._matches_filters(product, filters):
                        products.append(product)

                        # 성능을 위해 50개까지만 로드
                        if len(products) >= 50:
                            break
                except Exception:
                    continue

            if len(products) >= 50:
                break

        # 관련성 점수로 정렬
        scored_products = []
        for product in products:
            score = self._calculate_relevance(product, query)
            scored_products.append((score, product))

        scored_products.sort(key=lambda x: x[0], reverse=True)

        return [p[1] for p in scored_products]

    def _calculate_relevance(self, product: Dict, query: str) -> float:
        """관련성 점수 계산"""
        score = 0.0
        query_lower = query.lower()

        # 제품명 매칭
        product_name = product.get("product_name", "").lower()
        if query_lower in product_name:
            score += 2.0

        # 키워드 매칭
        for word in query_lower.split():
            if word in product_name:
                score += 0.5

        # 스펙 매칭
        specs = product.get("specifications", {})
        spec_text = json.dumps(specs, ensure_ascii=False).lower()
        if query_lower in spec_text:
            score += 1.0

        return score

    def _matches_filters(self, product: Dict, filters: Dict) -> bool:
        """제품이 필터 조건을 만족하는지 확인"""
        if not filters:
            return True

        specs = product.get("specifications", {})

        # 재질 필터
        if "material" in filters:
            material = specs.get("재질(원료)", "")
            if filters["material"].upper() not in material.upper():
                return False

        # 용량 필터
        if "capacity" in filters:
            capacity_str = specs.get("capacity", "")
            if capacity_str:
                import re

                match = re.search(r"(\d+)", capacity_str)
                if match:
                    capacity = float(match.group(1))
                    target = filters["capacity"]
                    # ±20% 범위
                    if not (target * 0.8 <= capacity <= target * 1.2):
                        return False

        # 네크 사이즈 필터
        if "neck_size" in filters:
            neck_size = specs.get("neck_size", "")
            if filters["neck_size"] not in neck_size:
                return False

        # 투명도 필터
        if "transparency" in filters:
            product_name = product.get("product_name", "").lower()
            if filters["transparency"] == "transparent":
                if "투명" not in product_name and "clear" not in product_name:
                    return False
            elif filters["transparency"] == "opaque":
                if "투명" in product_name or "clear" in product_name:
                    return False

        return True

    def _update_context(
        self, context: DialogueContext, query: str, routing: RoutingDecision, result: Dict
    ):
        """컨텍스트 업데이트"""
        # 쿼리 업데이트
        context.last_query = query

        # 검색 결과 업데이트
        products = result.get("products", [])
        if products:
            product_idxs = [p.get("idx") for p in products if p.get("idx")]
            context.last_search_results = product_idxs

            # 표시 인덱스 생성 (1번, 2번, 3번...)
            context.display_indices = {i + 1: idx for i, idx in enumerate(product_idxs[:10])}

            # 포커스 제품 업데이트
            if routing.action == "show_detail" and product_idxs:
                context.focused_product = product_idxs[0]
                context.focused_product_name = products[0].get("product_name")

        # 대화 히스토리 추가
        context.conversation_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "intent": routing.intent.value,
                "action": routing.action,
                "state": context.current_state.value,
                "product_count": len(products),
            }
        )

    def _get_or_create_context(self, session_id: str, user_id: str) -> DialogueContext:
        """세션 컨텍스트 로드 또는 생성"""
        if session_id in self.sessions:
            return self.sessions[session_id]

        # 새 컨텍스트 생성
        now = datetime.now().isoformat()
        context = DialogueContext(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_activity=now,
            current_state=ConversationState.GREETING,
        )

        self.sessions[session_id] = context
        return context

    def _get_or_create_filter_manager(self, session_id: str) -> FilterManager:
        """필터 매니저 로드 또는 생성"""
        if session_id in self.filter_managers:
            return self.filter_managers[session_id]

        filter_manager = FilterManager()
        self.filter_managers[session_id] = filter_manager
        return filter_manager

    def _load_product(self, idx: str) -> Optional[Dict]:
        """제품 데이터 로드 (캐시 사용)"""
        if idx in self._product_cache:
            return self._product_cache[idx]

        # 파일에서 로드
        for category in ["Bottle", "Cappump", "Pump", "Jar"]:
            for json_file in (self.data_root / category).rglob(f"idx_{idx}.json"):
                product = self._load_product_from_file(json_file)
                if product:
                    self._product_cache[idx] = product
                    return product

        return None

    def _load_product_from_file(self, file_path: Path) -> Optional[Dict]:
        """파일에서 제품 로드"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                product = json.load(f)

            # images 배열에 downloaded_images의 local_path 추가
            if "images" in product and "downloaded_images" in product:
                for i, img in enumerate(product["images"]):
                    if i < len(product["downloaded_images"]):
                        local_path = product["downloaded_images"][i].get("local_path")
                        if local_path:
                            clean_path = local_path.replace("data/", "", 1)
                            img["local_path"] = clean_path

            # product_code 추가
            if not product.get("product_code"):
                specs = product.get("specifications", {})
                for key in ["제품코드", "제품 코드", "product_code"]:
                    if key in specs:
                        product["product_code"] = specs[key]
                        break

            return product
        except Exception as e:
            print(f"제품 로드 실패 {file_path}: {e}")
            return None

    async def _log_user_behavior(
        self,
        user_id: str,
        session_id: str,
        user_query: str,
        routing: RoutingDecision,
        result: Dict,
        context: DialogueContext,
        response_time_ms: int,
        ip_address: Optional[str],
    ):
        """
        사용자 행동 로그 기록

        1. 대화 로그 (모든 쿼리)
        2. 검색 로그 (search, filter 액션)
        """
        try:
            # 1. 대화 로그 (항상 기록)
            products_shown = [p.get("idx") for p in result.get("products", []) if p.get("idx")]

            await self.behavior_tracker.track_conversation(
                user_id=user_id,
                session_id=session_id,
                user_message=user_query,
                bot_response=result.get("response", ""),
                intent=routing.intent.value,
                reference_type=routing.parameters.get("reference_type"),
                conversation_state=context.current_state.value,
                focused_product=context.focused_product,
                active_filters=context.active_filters,
                products_shown=products_shown,
                product_count=len(products_shown),
                action_taken=routing.action,
                response_time_ms=response_time_ms,
                ip_address=ip_address,
            )

            # 2. 검색 로그 (search, filter 액션만)
            if routing.action in ["search", "apply_filter"]:
                filters = routing.parameters.get("filters", {})
                normalized_query = routing.parameters.get("normalized_query", user_query)

                await self.behavior_tracker.track_search(
                    user_id=user_id,
                    session_id=session_id,
                    query=user_query,
                    normalized_query=normalized_query,
                    filters=filters,
                    result_count=result.get("total_count", 0),
                    result_product_indices=products_shown,
                    intent=routing.intent.value,
                    product_type=filters.get("product_type"),
                    response_time_ms=response_time_ms,
                    ip_address=ip_address,
                )

        except Exception as e:
            # 로그 기록 실패는 사용자 경험에 영향 주지 않음
            print(f"[EnhancedContextualRAG] 행동 로그 기록 실패: {e}")
