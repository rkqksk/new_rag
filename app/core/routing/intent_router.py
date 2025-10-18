"""
MCP Intent Router - 사용자 질의 의도 자동 감지 및 MCP 도구 라우팅

Purpose:
    사용자 메시지를 분석하여 최적의 MCP 도구를 자동으로 선택하고 실행

Available MCP Servers:
    - filesystem: 파일/디렉토리 작업
    - claude_haiku: 경량 LLM 작업
    - qdrant: 벡터 검색
    - ollama: 로컬 LLM (qwen2.5:7b)
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class Intent(Enum):
    """사용자 질의 의도 분류"""
    FILE_OPERATION = "file_operation"
    VECTOR_SEARCH = "vector_search"
    SIMPLE_QUERY = "simple_query"
    COMPLEX_ANALYSIS = "complex_analysis"
    UNKNOWN = "unknown"


@dataclass
class IntentResult:
    """의도 분석 결과"""
    intent: Intent
    confidence: float
    mcp_tool: Optional[str]
    fallback_tools: List[str]
    params: Dict


class IntentDetector:
    """사용자 질의 의도 감지기"""

    def __init__(self):
        # 의도별 키워드 패턴
        self.patterns = {
            Intent.FILE_OPERATION: {
                "keywords": [
                    "파일", "file", "폴더", "folder", "directory",
                    "보여줘", "show", "list", "읽어", "read", "찾아", "find"
                ],
                "patterns": [
                    r"(.+)\s+(폴더|디렉토리|directory).+(있|보여|list)",
                    r"(파일|file).+(읽|read|show|open)",
                    r"(찾|find|search).+(파일|file)"
                ],
                "mcp_tool": "filesystem",
                "confidence_boost": 0.2
            },
            Intent.VECTOR_SEARCH: {
                "keywords": [
                    "검색", "search", "찾아줘", "유사한", "similar",
                    "문서", "document", "관련", "related"
                ],
                "patterns": [
                    r"(.+)\s+(검색|search|찾아)",
                    r"(유사한|similar).+(문서|document)",
                    r"(.+)\s+관련.+(정보|문서)"
                ],
                "mcp_tool": "qdrant",
                "confidence_boost": 0.15
            },
            Intent.SIMPLE_QUERY: {
                "keywords": [
                    "뭐야", "what", "간단히", "짧게", "요약",
                    "설명", "explain", "의미"
                ],
                "patterns": [
                    r"^\w+\s+(뭐야|이란|is|means)",
                    r"^(간단히|짧게|요약).+",
                    r"(.+)\s+(설명|explain)"
                ],
                "mcp_tool": "ollama",  # 로컬 LLM
                "confidence_boost": 0.1
            },
            Intent.COMPLEX_ANALYSIS: {
                "keywords": [
                    "분석", "analyze", "왜", "why", "설계", "design",
                    "아키텍처", "architecture", "최적화", "optimize"
                ],
                "patterns": [
                    r"(왜|why).+",
                    r"(분석|analyze).+",
                    r"(설계|design|아키텍처|architecture)"
                ],
                "mcp_tool": "claude_haiku",
                "confidence_boost": 0.25
            }
        }

    def detect(self, query: str) -> IntentResult:
        """
        질의 의도 감지

        Args:
            query: 사용자 질의 문자열

        Returns:
            IntentResult: 감지된 의도 및 관련 정보
        """
        query_lower = query.lower()
        intent_scores = {}

        # 각 Intent에 대한 점수 계산
        for intent, config in self.patterns.items():
            score = self._calculate_score(query_lower, config)
            intent_scores[intent] = score

        # 가장 높은 점수의 Intent 선택
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[best_intent]

        # Confidence가 너무 낮으면 UNKNOWN
        if confidence < 0.3:
            best_intent = Intent.UNKNOWN

        # MCP 도구 및 Fallback 결정
        if best_intent == Intent.UNKNOWN:
            mcp_tool = None
            fallback_tools = ["ollama", "claude_haiku"]
        else:
            config = self.patterns[best_intent]
            mcp_tool = config["mcp_tool"]
            fallback_tools = self._get_fallback_tools(best_intent)

        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            mcp_tool=mcp_tool,
            fallback_tools=fallback_tools,
            params=self._extract_params(query, best_intent)
        )

    def _calculate_score(self, query: str, config: Dict) -> float:
        """
        의도별 점수 계산

        Args:
            query: 사용자 질의 (소문자)
            config: 의도 설정 정보

        Returns:
            float: 0-1 사이의 신뢰도 점수
        """
        score = 0.0

        # 키워드 매칭 (40%)
        keyword_matches = sum(1 for kw in config["keywords"] if kw in query)
        keyword_score = min(keyword_matches / 3, 1.0) * 0.4
        score += keyword_score

        # 패턴 매칭 (30%)
        pattern_match = any(re.search(pattern, query) for pattern in config["patterns"])
        pattern_score = 1.0 if pattern_match else 0.0
        score += pattern_score * 0.3

        # Confidence Boost (30%)
        if keyword_matches > 0 or pattern_match:
            score += config["confidence_boost"]

        return min(score, 1.0)

    def _get_fallback_tools(self, intent: Intent) -> List[str]:
        """
        의도별 Fallback MCP 도구 목록

        Args:
            intent: 감지된 의도

        Returns:
            List[str]: Fallback 도구 목록
        """
        fallback_map = {
            Intent.FILE_OPERATION: ["ollama"],
            Intent.VECTOR_SEARCH: ["filesystem", "ollama"],
            Intent.SIMPLE_QUERY: ["claude_haiku"],
            Intent.COMPLEX_ANALYSIS: ["ollama"]
        }
        return fallback_map.get(intent, ["ollama"])

    def _extract_params(self, query: str, intent: Intent) -> Dict:
        """
        질의에서 파라미터 추출

        Args:
            query: 사용자 질의
            intent: 감지된 의도

        Returns:
            Dict: 추출된 파라미터
        """
        params = {"query": query}

        # FILE_OPERATION: 경로 추출
        if intent == Intent.FILE_OPERATION:
            path_match = re.search(r'([/\w]+/[\w/]+)', query)
            if path_match:
                params["path"] = path_match.group(1)
            else:
                # 폴더명 추출
                folder_match = re.search(r'([\w_-]+)\s+(폴더|folder|디렉토리|directory)', query)
                if folder_match:
                    params["folder"] = folder_match.group(1)

        # VECTOR_SEARCH: 검색어 추출
        elif intent == Intent.VECTOR_SEARCH:
            search_match = re.search(r'(.+)\s+(검색|찾아|search)', query)
            if search_match:
                params["search_term"] = search_match.group(1).strip()

        return params


class MCPRouter:
    """MCP 도구 실행 라우터"""

    def __init__(self):
        self.intent_detector = IntentDetector()
        self.mcp_available = {
            "filesystem": True,
            "qdrant": True,
            "ollama": True,
            "claude_haiku": True
        }

    def route(self, query: str) -> Tuple[str, IntentResult]:
        """
        질의를 분석하여 적절한 MCP 도구로 라우팅

        Args:
            query: 사용자 질의

        Returns:
            Tuple[str, IntentResult]: (실행할 MCP 도구명, 의도 분석 결과)
        """
        # 1. 의도 감지
        intent_result = self.intent_detector.detect(query)

        # 2. MCP 도구 가용성 확인
        selected_tool = intent_result.mcp_tool

        if selected_tool and not self.mcp_available.get(selected_tool, False):
            # Primary 도구 사용 불가 → Fallback
            for fallback in intent_result.fallback_tools:
                if self.mcp_available.get(fallback, False):
                    selected_tool = fallback
                    break

        # 3. 최종 도구 선택 (기본값: ollama)
        if not selected_tool:
            selected_tool = "ollama"

        return selected_tool, intent_result

    def set_mcp_availability(self, mcp_name: str, available: bool):
        """
        MCP 도구 가용성 설정 (Health Check 용도)

        Args:
            mcp_name: MCP 도구명
            available: 사용 가능 여부
        """
        self.mcp_available[mcp_name] = available


# 전역 라우터 인스턴스
intent_router = MCPRouter()


if __name__ == "__main__":
    # 테스트
    test_queries = [
        "vault 폴더에 있는 파일들 개수는?",
        "RAG 시스템 설계 문서 검색해줘",
        "Python 리스트 컴프리헨션 뭐야?",
        "전체 시스템 성능 분석해줘"
    ]

    router = MCPRouter()

    for query in test_queries:
        tool, result = router.route(query)
        print(f"\n질의: {query}")
        print(f"→ Intent: {result.intent.value}")
        print(f"→ Confidence: {result.confidence:.2f}")
        print(f"→ MCP Tool: {tool}")
        print(f"→ Params: {result.params}")
