"""
자연어 답변 생성기 (Natural Language Response Generator)
Natural Language Response Generator

목적: 검색 결과 → 자연어 답변 생성
전략: 템플릿 기반 + LLM 옵션
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from src.core.query_parser import ParsedQuery
from src.core.search_engine import SearchResult


@dataclass
class NaturalLanguageResponse:
    """자연어 응답"""

    answer: str  # 자연어 답변
    products: List[SearchResult]  # 추천 제품 리스트
    query_understanding: str  # 쿼리 이해 요약


class NaturalLanguageResponseGenerator:
    """자연어 답변 생성기"""

    def __init__(self, use_llm: bool = False):
        """
        초기화

        Args:
            use_llm: LLM 사용 여부 (현재는 템플릿 기반만 구현)
        """
        self.use_llm = use_llm

    def generate(
        self, parsed_query: ParsedQuery, search_results: List[SearchResult]
    ) -> NaturalLanguageResponse:
        """
        자연어 답변 생성

        Args:
            parsed_query: 파싱된 쿼리
            search_results: 검색 결과

        Returns:
            NaturalLanguageResponse: 자연어 응답
        """
        # Step 1: 쿼리 이해 요약
        query_understanding = self._summarize_query(parsed_query)

        # Step 2: 답변 생성
        if not search_results:
            answer = self._generate_no_results_message(parsed_query)
        else:
            answer = self._generate_results_message(parsed_query, search_results)

        return NaturalLanguageResponse(
            answer=answer, products=search_results, query_understanding=query_understanding
        )

    def _summarize_query(self, parsed_query: ParsedQuery) -> str:
        """쿼리 이해 요약"""
        parts = []

        for entity in parsed_query.entities:
            entity_type = entity.entity_type.value
            if entity_type == "category":
                parts.append(f"{entity.value} 제품")
            elif entity_type == "neck":
                parts.append(f"Neck {entity.value}")
            elif entity_type == "moq":
                parts.append(f"최소주문수량 {entity.value:,}개 이하")
            elif entity_type == "material":
                parts.append(f"{entity.value} 재질")
            elif entity_type == "capacity":
                parts.append(f"{entity.value} 용량")
            elif entity_type == "origin":
                parts.append(f"{entity.value}산")
            elif entity_type == "use_case":
                parts.append(f"{entity.value}용")
            else:
                parts.append(str(entity.value))

        if parts:
            return "검색 조건: " + ", ".join(parts)
        else:
            return f"검색어: {parsed_query.original_query}"

    def _generate_no_results_message(self, parsed_query: ParsedQuery) -> str:
        """결과 없음 메시지"""
        return (
            f"죄송합니다. '{parsed_query.original_query}' 조건에 맞는 제품을 찾지 못했습니다.\n\n"
            "다음과 같이 검색 조건을 완화해보시는 건 어떨까요?\n"
            "• 용량 범위를 넓히기\n"
            "• 재질 조건 제거\n"
            "• 최소 주문량 조건 완화"
        )

    def _generate_results_message(
        self, parsed_query: ParsedQuery, results: List[SearchResult]
    ) -> str:
        """검색 결과 메시지 생성"""
        intent = parsed_query.intent

        # Intent-based opening
        if intent == "recommend":
            opening = f"'{parsed_query.original_query}' 조건에 맞는 제품을 추천드립니다."
        elif intent == "search":
            opening = f"'{parsed_query.original_query}' 검색 결과입니다."
        elif intent == "compare":
            opening = "비교 가능한 제품들을 찾았습니다."
        else:
            opening = "다음 제품을 찾았습니다."

        # Build response
        lines = [opening, ""]

        for idx, result in enumerate(results, 1):
            lines.append(f"**{idx}. {result.product_name}** (매칭도: {result.score:.1%})")

            # Extract key info from metadata
            metadata = result.metadata
            details = []

            if "neck" in metadata:
                details.append(f"• Neck: {metadata['neck']}")

            if "moq" in metadata:
                moq_value = metadata["moq"]
                if isinstance(moq_value, (int, float)):
                    details.append(f"• 최소주문수량: {int(moq_value):,}개")

            if "material" in metadata:
                details.append(f"• 재질: {metadata['material']}")

            if "capacity_ml" in metadata:
                details.append(f"• 용량: {metadata['capacity_ml']}ml")

            if "origin" in metadata:
                details.append(f"• 원산지: {metadata['origin']}")

            if "manufacturer" in metadata:
                details.append(f"• 제조사: {metadata['manufacturer']}")

            if details:
                lines.extend(details)

            # Show matched chunks (why this product matched)
            if result.matched_chunks:
                matched_reasons = []
                for chunk in result.matched_chunks[:3]:  # Top 3 chunks
                    field_type = chunk.get("field_type", "")
                    chunk_text = chunk.get("chunk_text", "")
                    if field_type and chunk_text:
                        matched_reasons.append(f"  - {chunk_text}")

                if matched_reasons:
                    lines.append(f"• 매칭 이유:")
                    lines.extend(matched_reasons)

            lines.append("")  # Empty line between products

        # Add summary
        if len(results) > 3:
            lines.append(
                f"총 {len(results)}개 제품이 검색되었습니다. 상위 {min(3, len(results))}개만 표시했습니다."
            )

        return "\n".join(lines)


if __name__ == "__main__":
    # Test response generator
    from src.core.query_parser import QueryParser
    from src.core.search_engine import SearchEngine

    print("=" * 80)
    print("NATURAL LANGUAGE RESPONSE GENERATOR TEST")
    print("=" * 80)

    # Initialize
    query_parser = QueryParser()
    search_engine = SearchEngine()
    response_gen = NaturalLanguageResponseGenerator()

    test_query = "20파이 캡 5,000개 주문 가능한 제품 추천해줘"

    print(f"\nUser Query: {test_query}")
    print(f"{'─'*80}")

    # Step 1: Parse query
    parsed_query = query_parser.parse(test_query)
    print(f"\n[1] Query Parsing")
    print(f"    Entities: {len(parsed_query.entities)}")
    for entity in parsed_query.entities:
        print(f"      • {entity.entity_type.value}: {entity.value}")

    # Step 2: Search
    search_results = search_engine.search(test_query, top_k=3)
    print(f"\n[2] Search Results")
    print(f"    Found: {len(search_results)} products")

    # Step 3: Generate response
    response = response_gen.generate(parsed_query, search_results)

    print(f"\n[3] Natural Language Response")
    print(f"{'─'*80}")
    print(f"\n{response.query_understanding}")
    print(f"\n{response.answer}")
    print(f"\n{'─'*80}")

    # Test no results case
    print(f"\n\n{'='*80}")
    print("NO RESULTS TEST")
    print(f"{'='*80}")

    test_query_no_results = "존재하지 않는 제품"
    parsed_query_empty = query_parser.parse(test_query_no_results)
    response_empty = response_gen.generate(parsed_query_empty, [])

    print(f"\nUser Query: {test_query_no_results}")
    print(f"{'─'*80}")
    print(f"\n{response_empty.answer}")
