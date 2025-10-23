"""
컨텍스트 인식 RAG 서비스
대화 컨텍스트를 활용한 지능형 검색
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.core.conversation_manager import ConversationManager
from src.core.intent_classifier import IntentClassifier, Intent
from src.core.reference_resolver import ReferenceResolver
from src.services.intent_recommender import get_intent_recommender


class ContextualRAG:
    """컨텍스트 기반 RAG 시스템"""

    def __init__(
        self,
        conv_manager: ConversationManager,
        intent_classifier: IntentClassifier,
        reference_resolver: ReferenceResolver,
        data_root: str = "/Users/oypnus/Project/rag-enterprise/data/crawled_products_final"
    ):
        """
        Args:
            conv_manager: 대화 관리자
            intent_classifier: 의도 분류기
            reference_resolver: 참조 해결기
            data_root: 제품 데이터 루트 경로
        """
        self.conv_manager = conv_manager
        self.intent_classifier = intent_classifier
        self.reference_resolver = reference_resolver
        self.data_root = Path(data_root)

        # 스마트 추천 엔진
        self.intent_recommender = get_intent_recommender()

        # 제품 데이터 캐시 (간단한 인메모리 캐시)
        self._product_cache: Dict[str, Dict] = {}

    async def query(
        self,
        session_id: str,
        user_query: str
    ) -> Dict[str, Any]:
        """
        컨텍스트 기반 쿼리 처리

        Args:
            session_id: 세션 ID
            user_query: 사용자 쿼리

        Returns:
            응답 딕셔너리
        """
        # 1. 세션 컨텍스트 로드
        context = self.conv_manager.get_context(session_id)
        if not context:
            # 세션이 없으면 생성
            session_id = self.conv_manager.create_session()
            context = self.conv_manager.get_context(session_id)

        # 2. 의도 분류
        intent_result = self.intent_classifier.classify_detailed(
            user_query, context
        )
        intent = Intent(intent_result["intent"])
        entities = intent_result["entities"]

        # 3. 참조 해결
        resolved, product_idx, product_list = \
            self.reference_resolver.resolve(user_query, context)

        if resolved and product_idx:
            # 참조된 제품 데이터 로드
            product_data = self._load_product(product_idx)

            if product_data:
                # 쿼리 확장
                expanded_query = self.reference_resolver.expand_query(
                    user_query, product_idx, product_data
                )
            else:
                expanded_query = user_query
        else:
            expanded_query = user_query

        # 4. 인텐트별 처리
        if intent == Intent.REFERENCE and resolved:
            # 참조 쿼리 - 참조된 제품에 대한 정보
            result = await self._handle_reference_query(
                expanded_query, product_idx, intent_result
            )
        elif intent == Intent.COMPATIBILITY:
            # 호환성 쿼리
            result = await self._handle_compatibility_query(
                expanded_query, entities, context, product_idx
            )
        elif intent == Intent.PRICE:
            # 가격 쿼리
            result = await self._handle_price_query(
                expanded_query, entities, context, product_idx
            )
        elif intent == Intent.COMPARE:
            # 비교 쿼리
            result = await self._handle_compare_query(
                expanded_query, entities, context
            )
        elif intent == Intent.FILTER:
            # 필터 쿼리
            result = await self._handle_filter_query(
                expanded_query, entities, context
            )
        else:
            # 기본 검색
            result = await self._handle_search_query(
                expanded_query, entities, context
            )

        # 5. 컨텍스트 업데이트
        if result.get("products"):
            product_idxs = [p["idx"] for p in result["products"][:5]]

            # 포커스 업데이트
            if product_idxs:
                self.conv_manager.update_focus(
                    session_id,
                    product_idxs[0],
                    product_idxs
                )

        # 6. 히스토리 추가
        self.conv_manager.add_to_history(
            session_id,
            user_query,
            intent.value,
            result.get("products", []),
            result.get("response")
        )

        # 7. 응답 구성
        response = {
            "session_id": session_id,
            "query": user_query,
            "intent": intent_result,
            "reference_resolved": resolved,
            "expanded_query": expanded_query if resolved else None,
            **result
        }

        return response

    async def _handle_reference_query(
        self,
        query: str,
        product_idx: str,
        intent_result: Dict
    ) -> Dict:
        """참조 쿼리 처리"""
        product = self._load_product(product_idx)

        if not product:
            return {
                "products": [],
                "response": f"제품 {product_idx}를 찾을 수 없습니다.",
                "total_count": 0
            }

        # 참조 쿼리 의도 파악
        entities = intent_result.get("entities", {})

        # 호환성 관련 키워드
        if any(kw in query for kw in ["호환", "맞는", "펌프", "캡"]):
            return await self._get_compatible_products(product)

        # 가격 관련 키워드
        if any(kw in query for kw in ["가격", "얼마", "비용"]):
            return self._get_product_price(product)

        # 상세 정보
        return self._get_product_detail(product)

    async def _handle_compatibility_query(
        self,
        query: str,
        entities: Dict,
        context: Dict,
        product_idx: Optional[str]
    ) -> Dict:
        """호환성 쿼리 처리"""
        if product_idx:
            product = self._load_product(product_idx)
            if product:
                return await self._get_compatible_products(product)

        return {
            "products": [],
            "response": "호환성을 확인할 제품을 먼저 선택해주세요.",
            "total_count": 0
        }

    async def _handle_price_query(
        self,
        query: str,
        entities: Dict,
        context: Dict,
        product_idx: Optional[str]
    ) -> Dict:
        """가격 쿼리 처리"""
        if product_idx:
            product = self._load_product(product_idx)
            if product:
                return self._get_product_price(product)

        # 가격 필터 적용하여 검색
        return await self._handle_search_query(query, entities, context)

    async def _handle_compare_query(
        self,
        query: str,
        entities: Dict,
        context: Dict
    ) -> Dict:
        """비교 쿼리 처리"""
        # 이전 제품 목록에서 비교
        previous_products = context.get("previous_products", [])[:5]

        products = []
        for idx in previous_products:
            product = self._load_product(idx)
            if product:
                products.append(product)

        return {
            "products": products,
            "response": f"{len(products)}개 제품을 비교할 수 있습니다.",
            "total_count": len(products),
            "comparison_mode": True
        }

    async def _handle_filter_query(
        self,
        query: str,
        entities: Dict,
        context: Dict
    ) -> Dict:
        """필터 쿼리 처리"""
        # 필터 추출 및 적용
        filters = self._extract_filters(entities, query)

        # 컨텍스트 필터 업데이트
        # (실제로는 session_id가 필요하지만 여기서는 생략)

        return await self._handle_search_query(query, entities, context, filters)

    async def _handle_search_query(
        self,
        query: str,
        entities: Dict,
        context: Dict,
        additional_filters: Dict = None
    ) -> Dict:
        """기본 검색 쿼리 처리 (스마트 추천 통합)"""
        # 1. 제품 유형 감지
        product_type = self.intent_recommender.detect_product_type(query)

        # 2. 정확한 용량값 추출 (예: "50미리" → 50)
        exact_capacity = self._extract_exact_capacity(query)

        # 3. 필터 구성
        filters = self._build_filters(entities, context, additional_filters)

        # 정확 용량이 있으면 우선 검색, 없으면 범위 검색
        if exact_capacity:
            filters["capacity_exact"] = exact_capacity
            search_mode = "exact"
        elif product_type:
            profile = self.intent_recommender.product_profiles.get(product_type, {})
            cap_min, cap_max = profile.get("capacity_range", (0, 10000))
            filters["capacity_min"] = cap_min
            filters["capacity_max"] = cap_max
            search_mode = "range"
        else:
            search_mode = "general"

        # 4. 파일 기반 검색으로 후보 제품 수집
        products = self._search_products(query, filters)

        # 5. 정확 용량 검색이었는데 결과가 없으면 범위 검색으로 폴백
        if search_mode == "exact" and not products and product_type:
            # 범위 검색으로 폴백
            profile = self.intent_recommender.product_profiles.get(product_type, {})
            cap_min, cap_max = profile.get("capacity_range", (0, 10000))

            # 범위 필터로 변경
            filters.pop("capacity_exact", None)
            filters["capacity_min"] = cap_min
            filters["capacity_max"] = cap_max

            products = self._search_products(query, filters)

            if products:
                response_msg = f"{exact_capacity}ml {product_type} 제품이 없습니다. 비슷한 용량 제품을 추천합니다."
            else:
                return {
                    "products": [],
                    "response": f"{exact_capacity}ml {product_type} 제품을 찾을 수 없습니다.",
                    "total_count": 0,
                    "matched_profile": product_type
                }
        elif not products:
            return {
                "products": [],
                "response": "검색 결과가 없습니다. 다른 조건으로 검색해보세요.",
                "total_count": 0,
                "matched_profile": product_type
            }
        else:
            response_msg = None

        # 6. 스마트 추천 엔진 적용
        if product_type:
            # 의도 기반 추천 적용
            recommended_products = self.intent_recommender.recommend(
                query=query,
                products=products,
                limit=10
            )

            if response_msg is None:
                if exact_capacity:
                    response_msg = f"{exact_capacity}ml {product_type} 제품을 추천합니다."
                else:
                    response_msg = f"{product_type} 제품을 추천합니다."
        else:
            # 추천 프로필 없으면 관련성 점수만 사용
            recommended_products = products[:10]
            response_msg = response_msg or self._generate_search_response(products, entities)

        return {
            "products": recommended_products,
            "response": response_msg,
            "total_count": len(products),
            "filters_applied": filters,
            "matched_profile": product_type,
            "recommendation_applied": product_type is not None,
            "exact_capacity": exact_capacity
        }

    def _search_products(
        self,
        query: str,
        filters: Dict
    ) -> List[Dict]:
        """제품 검색 (간단한 파일 기반 구현)"""
        # 모든 제품 파일 로드 (실제로는 DB 쿼리 또는 벡터 검색)
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

        # 관련성 점수로 정렬 (간단한 키워드 매칭)
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
        pricing = product.get("pricing", {})

        # 재질 필터
        if "material" in filters:
            material = specs.get("재질(원료)", "")
            if material.upper() != filters["material"].upper():
                return False

        # 용량 필터 - 정확 용량 우선
        if "capacity_exact" in filters:
            capacity_str = specs.get("capacity", "")
            if not capacity_str:
                # 용량 정보가 없으면 제외
                return False
            import re
            match = re.search(r'(\d+)', capacity_str)
            if match:
                capacity = float(match.group(1))
                if capacity != filters["capacity_exact"]:
                    return False
            else:
                return False
        elif "capacity_min" in filters or "capacity_max" in filters:
            capacity_str = specs.get("capacity", "")
            if capacity_str:
                import re
                match = re.search(r'(\d+)', capacity_str)
                if match:
                    capacity = float(match.group(1))
                    if "capacity_min" in filters and capacity < filters["capacity_min"]:
                        return False
                    if "capacity_max" in filters and capacity > filters["capacity_max"]:
                        return False

        # 네크 사이즈 필터
        if "neck_size" in filters:
            neck_size = specs.get("neck_size", "")
            if neck_size != filters["neck_size"]:
                return False

        # 가격 필터
        if "price_max" in filters:
            discount_price = pricing.get("discount_price") or pricing.get("regular_price", 9999)
            if discount_price > filters["price_max"]:
                return False

        return True

    def _build_filters(
        self,
        entities: Dict,
        context: Dict,
        additional_filters: Dict = None
    ) -> Dict:
        """필터 구성"""
        filters = {}

        # 엔티티에서 필터 추출
        if "material" in entities:
            filters["material"] = entities["material"]

        if "capacity" in entities:
            cap_value = entities["capacity"]["value"]
            # 정확한 용량보다는 범위로
            filters["capacity_min"] = cap_value * 0.8
            filters["capacity_max"] = cap_value * 1.2

        if "neck_size" in entities:
            filters["neck_size"] = entities["neck_size"]

        if "price_max" in entities:
            filters["price_max"] = entities["price_max"]

        if "price_min" in entities:
            filters["price_min"] = entities["price_min"]

        # 컨텍스트 필터 병합
        context_filters = context.get("filters", {})
        filters.update(context_filters)

        # 추가 필터 병합
        if additional_filters:
            filters.update(additional_filters)

        return filters

    def _extract_filters(self, entities: Dict, query: str) -> Dict:
        """쿼리에서 필터 추출"""
        filters = {}

        # 가격 관련
        if "저렴" in query or "싼" in query:
            filters["sort_by"] = "price_asc"

        if "비싼" in query or "고급" in query or "프리미엄" in query:
            filters["sort_by"] = "price_desc"

        # 투명도
        if "투명" in query:
            filters["transparency"] = "transparent"

        return filters

    async def _get_compatible_products(self, product: Dict) -> Dict:
        """호환 제품 조회"""
        compat_analysis = product.get("compatibility_analysis", {})
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
            "response": f"{product.get('product_name')}와 호환되는 Cap/Pump {len(compatible_products)}개를 찾았습니다.",
            "total_count": len(compatible_products),
            "compatibility_for": product.get("idx")
        }

    def _get_product_price(self, product: Dict) -> Dict:
        """제품 가격 정보"""
        pricing = product.get("pricing", {})

        regular_price = pricing.get("regular_price", "정보 없음")
        discount_price = pricing.get("discount_price", regular_price)

        response = f"{product.get('product_name')} 가격 정보:\n"
        response += f"- 정가: {regular_price}원\n"
        response += f"- 할인가: {discount_price}원"

        return {
            "products": [product],
            "response": response,
            "total_count": 1,
            "pricing": pricing
        }

    def _get_product_detail(self, product: Dict) -> Dict:
        """제품 상세 정보"""
        specs = product.get("specifications", {})
        compat = product.get("compatibility_analysis", {})

        response = f"📦 {product.get('product_name')}\n\n"
        response += f"제품 코드: {product.get('product_code', 'N/A')}\n"
        response += f"재질: {specs.get('재질(원료)', 'N/A')}\n"
        response += f"용량: {specs.get('capacity', 'N/A')}\n"
        response += f"네크 사이즈: {specs.get('neck_size', 'N/A')}\n\n"

        if compat:
            compat_count = compat.get("compatible_caps_pumps", {}).get("count", 0)
            response += f"호환 Cap/Pump: {compat_count}개"

        return {
            "products": [product],
            "response": response,
            "total_count": 1
        }

    def _generate_search_response(
        self,
        products: List[Dict],
        entities: Dict
    ) -> str:
        """검색 응답 메시지 생성"""
        count = len(products)

        # 엔티티 기반 설명
        conditions = []
        if "capacity" in entities:
            cap = entities["capacity"]
            conditions.append(f"{cap['value']}{cap['unit']}")

        if "material" in entities:
            conditions.append(entities["material"])

        if "product_type" in entities:
            conditions.append(entities["product_type"])

        if conditions:
            condition_text = " ".join(conditions)
            return f"{condition_text} 조건으로 {count}개 제품을 찾았습니다."
        else:
            return f"{count}개 제품을 찾았습니다."

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
            with open(file_path, 'r', encoding='utf-8') as f:
                product = json.load(f)

            # images 배열에 downloaded_images의 local_path 추가
            if "images" in product and "downloaded_images" in product:
                for i, img in enumerate(product["images"]):
                    if i < len(product["downloaded_images"]):
                        local_path = product["downloaded_images"][i].get("local_path")
                        if local_path:
                            # "data/" 제거 (백엔드에서 자동 추가됨)
                            clean_path = local_path.replace("data/", "", 1)
                            img["local_path"] = clean_path

            # product_code 추가 (specifications에서 추출)
            if not product.get("product_code"):
                specs = product.get("specifications", {})
                # 제품 코드를 여러 이름으로 찾기
                for key in ["제품코드", "제품 코드", "product_code"]:
                    if key in specs:
                        product["product_code"] = specs[key]
                        break

            return product
        except Exception as e:
            print(f"제품 로드 실패 {file_path}: {e}")
            return None

    def _extract_exact_capacity(self, query: str) -> Optional[float]:
        """쿼리에서 정확한 용량값 추출 (예: '50미리' → 50.0)"""
        import re
        # "미리", "ml", "mL" 패턴 찾기
        match = re.search(r'(\d+)\s*(?:미리|ml|mL)', query)
        if match:
            return float(match.group(1))
        return None

    def _find_nearby_capacities(self, exact_capacity: float, product_type: str) -> Optional[str]:
        """정확 용량이 없을 때 근처 용량 찾기"""
        profile = self.intent_recommender.product_profiles.get(product_type, {})
        if not profile:
            return None

        cap_min, cap_max = profile.get("capacity_range", (0, 10000))

        # 범위 내의 모든 제품 용량 수집
        all_capacities = set()
        for category in ["Bottle", "Cappump", "Pump", "Jar"]:
            category_path = self.data_root / category
            if not category_path.exists():
                continue

            for json_file in category_path.rglob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        product = json.load(f)
                    specs = product.get("specifications", {})
                    capacity_str = specs.get("capacity", "")
                    if capacity_str:
                        import re
                        match = re.search(r'(\d+)', capacity_str)
                        if match:
                            cap = float(match.group(1))
                            if cap_min <= cap <= cap_max:
                                all_capacities.add(cap)
                except Exception:
                    continue

        if not all_capacities:
            return None

        # 가장 가까운 2개 용량 찾기
        sorted_caps = sorted(all_capacities)
        nearby = []

        # 가장 가까운 값 찾기
        for cap in sorted_caps:
            if cap != exact_capacity:
                nearby.append(cap)
                if len(nearby) >= 2:
                    break

        if nearby:
            return ", ".join([f"{int(c)}" for c in nearby])
        return None

    def _search_nearby_products(
        self,
        query: str,
        nearby_capacities_str: str,
        filters: Dict,
        product_type: str
    ) -> List[Dict]:
        """근처 용량으로 제품 재검색"""
        products = []

        # 근처 용량들을 범위로 변환
        try:
            nearby_nums = [float(x.strip()) for x in nearby_capacities_str.split(",")]
            if nearby_nums:
                cap_min = min(nearby_nums) - 5
                cap_max = max(nearby_nums) + 5
        except (ValueError, AttributeError):
            return []

        # 근처 용량 범위로 검색
        search_filters = filters.copy()
        search_filters.pop("capacity_exact", None)
        search_filters["capacity_min"] = cap_min
        search_filters["capacity_max"] = cap_max

        return self._search_products(query, search_filters)
