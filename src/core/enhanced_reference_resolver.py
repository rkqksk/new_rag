"""
강화된 참조 해결 시스템 (Enhanced Reference Resolver)
숫자, 대명사, 문서 요청까지 모두 처리하는 영업사원 수준
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from src.core.conversation_state import DialogueContext, ConversationState


class EnhancedReferenceResolver:
    """
    강화된 참조 해결기

    처리 가능한 참조 유형:
    1. 숫자 참조: "3번", "3번째", "세 번째"
    2. 순서 참조: "첫 번째", "마지막", "다음"
    3. 대명사 참조: "그거", "이거", "저거"
    4. 문서 참조: "원산지 증명서", "스펙 시트", "카탈로그"
    5. 암묵적 참조: "펌프 보여줘" (포커스 제품 기준)
    """

    def __init__(self):
        # 숫자 패턴 (1번, 2번째, 첫 번째, etc.)
        self.number_patterns = [
            (r'(\d+)\s*번(?:째)?', 'direct_number'),      # "3번", "3번째"
            (r'([일이삼사오육칠팔구십])\s*번(?:째)?', 'korean_number'),  # "삼번째"
            (r'첫\s*번째|첫번째|처음', 'ordinal_first'),
            (r'두\s*번째|두번째', 'ordinal_second'),
            (r'세\s*번째|세번째', 'ordinal_third'),
            (r'네\s*번째|네번째', 'ordinal_fourth'),
            (r'다섯\s*번째|다섯번째', 'ordinal_fifth'),
            (r'마지막', 'ordinal_last')
        ]

        # 한글 숫자 매핑
        self.korean_number_map = {
            '일': 1, '이': 2, '삼': 3, '사': 4, '오': 5,
            '육': 6, '칠': 7, '팔': 8, '구': 9, '십': 10
        }

        # 순서 매핑
        self.ordinal_map = {
            'ordinal_first': 1,
            'ordinal_second': 2,
            'ordinal_third': 3,
            'ordinal_fourth': 4,
            'ordinal_fifth': 5,
            'ordinal_last': -1
        }

        # 대명사 패턴
        self.demonstrative_patterns = [
            r'그\s*거',
            r'이\s*거',
            r'저\s*거',
            r'그\s*제품',
            r'이\s*제품',
            r'저\s*제품',
            r'위\s*에\s*거',
            r'아래\s*거'
        ]

        # 문서 타입 키워드
        self.document_keywords = {
            '원산지': 'certificate_of_origin',
            '원산지증명서': 'certificate_of_origin',
            '증명서': 'certificate',
            '스펙': 'specification',
            '스펙시트': 'specification',
            '사양서': 'specification',
            '카탈로그': 'catalog',
            '자료': 'document',
            '문서': 'document',
            '도면': 'drawing',
            '설계도': 'drawing'
        }

    def resolve(
        self,
        query: str,
        context: DialogueContext
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        참조 해결

        Returns:
            (resolved, product_idx, reference_type, document_type)
            - resolved: 참조가 해결되었는지
            - product_idx: 해결된 제품 idx
            - reference_type: 참조 유형 (number, demonstrative, implicit, document)
            - document_type: 문서 타입 (원산지증명서, 스펙 등)
        """

        # 1. 숫자 참조 체크
        number_result = self._resolve_number_reference(query, context)
        if number_result[0]:
            return number_result + ('number', None)

        # 2. 문서 참조 체크
        document_result = self._resolve_document_reference(query, context)
        if document_result[0]:
            doc_type = document_result[2]
            return (True, document_result[1], 'document', doc_type)

        # 3. 대명사 참조 체크
        demonstrative_result = self._resolve_demonstrative(query, context)
        if demonstrative_result[0]:
            return demonstrative_result + ('demonstrative', None)

        # 4. 암묵적 참조 체크
        implicit_result = self._resolve_implicit(query, context)
        if implicit_result[0]:
            return implicit_result + ('implicit', None)

        return False, None, None, None

    def _resolve_number_reference(
        self,
        query: str,
        context: DialogueContext
    ) -> Tuple[bool, Optional[str]]:
        """숫자 참조 해결"""

        if not context.display_indices:
            return False, None

        for pattern, pattern_type in self.number_patterns:
            match = re.search(pattern, query)
            if match:
                # 직접 숫자 ("3번")
                if pattern_type == 'direct_number':
                    num = int(match.group(1))
                    if num in context.display_indices:
                        return True, context.display_indices[num]

                # 한글 숫자 ("삼번")
                elif pattern_type == 'korean_number':
                    korean_num = match.group(1)
                    num = self.korean_number_map.get(korean_num)
                    if num and num in context.display_indices:
                        return True, context.display_indices[num]

                # 순서 ("첫 번째", "마지막")
                elif pattern_type in self.ordinal_map:
                    ordinal_num = self.ordinal_map[pattern_type]

                    if ordinal_num == -1:  # 마지막
                        if context.last_search_results:
                            last_idx = context.last_search_results[-1]
                            return True, last_idx
                    elif ordinal_num in context.display_indices:
                        return True, context.display_indices[ordinal_num]

        return False, None

    def _resolve_document_reference(
        self,
        query: str,
        context: DialogueContext
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        문서 참조 해결

        "원산지 증명서 보여줘" → 현재 포커스 제품의 원산지 증명서
        "3번 스펙 시트" → 3번 제품의 스펙 시트
        """

        # 문서 키워드 감지
        doc_type = None
        for keyword, dtype in self.document_keywords.items():
            if keyword in query:
                doc_type = dtype
                break

        if not doc_type:
            return False, None, None

        # 숫자 참조와 함께 사용된 경우
        number_ref = self._resolve_number_reference(query, context)
        if number_ref[0]:
            return True, number_ref[1], doc_type

        # 포커스 제품이 있는 경우
        if context.focused_product:
            return True, context.focused_product, doc_type

        # 마지막 검색 결과의 첫 제품
        if context.last_search_results:
            first_product = context.last_search_results[0]
            return True, first_product, doc_type

        return False, None, None

    def _resolve_demonstrative(
        self,
        query: str,
        context: DialogueContext
    ) -> Tuple[bool, Optional[str]]:
        """대명사 참조 해결 ("그거", "이거")"""

        for pattern in self.demonstrative_patterns:
            if re.search(pattern, query):
                # 포커스 제품이 있으면 그것 반환
                if context.focused_product:
                    return True, context.focused_product

                # 없으면 마지막 검색 결과의 첫 제품
                if context.last_search_results:
                    return True, context.last_search_results[0]

                return False, None

        return False, None

    def _resolve_implicit(
        self,
        query: str,
        context: DialogueContext
    ) -> Tuple[bool, Optional[str]]:
        """
        암묵적 참조 해결

        조건:
        1. 짧은 쿼리 (<10자)
        2. 포커스 제품이 있음
        3. 호환성/추가정보 키워드 포함

        예: "펌프 보여줘" (현재 보틀에 맞는 펌프)
        """

        # 호환성/추가정보 키워드
        implicit_keywords = ['펌프', '캡', '뚜껑', '호환', '맞는', '색상', '가격']

        # 짧은 쿼리 & 키워드 포함 & 포커스 있음
        if (len(query) < 15 and
            any(kw in query for kw in implicit_keywords) and
            context.focused_product):
            return True, context.focused_product

        return False, None

    def expand_query_with_context(
        self,
        query: str,
        product_idx: str,
        product_data: Dict[str, Any]
    ) -> str:
        """
        참조된 제품 정보로 쿼리 확장

        "3번이랑 맞는 캡" → "PET-050 50ml 병에 맞는 캡 (네크: 28/410)"
        """

        product_name = product_data.get("product_name", "")
        specs = product_data.get("specifications", {})

        capacity = specs.get("capacity", "")
        material = specs.get("재질(원료)", "")
        neck_size = specs.get("neck_size", "")

        # 핵심 정보 추출
        context_parts = []
        if product_name:
            context_parts.append(product_name)
        if capacity:
            context_parts.append(f"{capacity}")
        if material:
            context_parts.append(f"{material} 재질")
        if neck_size:
            context_parts.append(f"네크 {neck_size}")

        context_str = ", ".join(context_parts)

        # 쿼리 확장
        expanded = f"{query} (기준 제품: {context_str})"

        return expanded

    def get_clarification_question(
        self,
        query: str,
        context: DialogueContext
    ) -> Optional[str]:
        """
        명확화 질문 생성

        예: "증명서 보여줘" → "어떤 제품의 증명서를 확인하시겠어요?"
        """

        # 문서 요청이지만 참조가 명확하지 않음
        if any(kw in query for kw in self.document_keywords.keys()):
            if not context.focused_product and not context.last_search_results:
                return "어떤 제품의 문서를 확인하시겠어요? 먼저 제품을 검색해주세요."

        # 숫자 참조가 있지만 범위 밖
        for pattern, _ in self.number_patterns:
            match = re.search(pattern, query)
            if match:
                if not context.display_indices:
                    return "현재 표시된 제품이 없습니다. 먼저 제품을 검색해주세요."

        return None
