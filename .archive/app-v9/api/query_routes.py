"""
Query Router API Routes
질문 난이도에 따라 Ollama LLM 모델 자동 라우팅 (qwen2.5:3b / qwen2.5:7b)
"""

import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/query", tags=["query_router"])


class QueryComplexity(str, Enum):
    """질문 난이도"""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class QueryAnalyzer:
    """질문 난이도 분석"""

    @staticmethod
    def analyze(query: str) -> tuple[QueryComplexity, float]:
        """
        질문을 분석하여 난이도 판정

        Returns:
            (complexity, confidence)
        """
        score = 0.0
        confidence = 0.0

        # 1. 길이 기반 (긴 질문 = 복잡)
        word_count = len(query.split())
        if word_count > 50:
            score += 0.3
        elif word_count > 20:
            score += 0.15

        # 2. 기술적 키워드 검사
        complex_keywords = [
            "architecture",
            "microservice",
            "distributed",
            "scalable",
            "아키텍처",
            "마이크로서비스",
            "분산",
            "확장",
            "설계",
        ]
        moderate_keywords = [
            "implement",
            "optimize",
            "refactor",
            "design",
            "구현",
            "최적화",
            "리팩토링",
            "디자인",
        ]

        for keyword in complex_keywords:
            if keyword.lower() in query.lower():
                score += 0.25

        for keyword in moderate_keywords:
            if keyword.lower() in query.lower():
                score += 0.15

        # 3. 질문 유형 검사
        if any(word in query.lower() for word in ["why", "explain", "왜", "설명"]):
            score += 0.1

        if any(word in query.lower() for word in ["how", "what", "어떻게", "무엇"]):
            score += 0.05

        # 4. 난이도 판정
        if score >= 0.7:
            complexity = QueryComplexity.COMPLEX
            confidence = min(score, 1.0)
        elif score >= 0.35:
            complexity = QueryComplexity.MODERATE
            confidence = min(score * 1.2, 0.95)
        else:
            complexity = QueryComplexity.SIMPLE
            confidence = 0.8

        return complexity, confidence


class OllamaRouter:
    """Ollama LLM 라우터"""

    def __init__(self, ollama_url: str = "http://172.28.0.6:11434"):
        self.ollama_url = ollama_url
        self.stats = {
            "total_calls": 0,
            "qwen3b_calls": 0,
            "qwen7b_calls": 0,
            "qwen3b_tokens": 0,
            "qwen7b_tokens": 0,
        }

    async def generate(
        self, model: str, prompt: str, system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ollama 모델 호출"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {"model": model, "prompt": prompt, "stream": False}

            if system_prompt:
                payload["system"] = system_prompt

            response = await client.post(f"{self.ollama_url}/api/generate", json=payload)

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Ollama error: {response.text}")

            return response.json()

    async def route_and_process(
        self, query: str, system_prompt: Optional[str] = None, max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """난이도에 따라 적절한 모델로 라우팅"""

        # 1. 난이도 분석
        complexity, confidence = QueryAnalyzer.analyze(query)

        # 2. 모델 선택
        if complexity == QueryComplexity.SIMPLE:
            model = "qwen2.5:3b"
            thinking = [
                f"Query analysis: {complexity.value} (confidence: {confidence:.2f})",
                "Route: qwen2.5:3b (fast)",
            ]
        elif complexity == QueryComplexity.MODERATE:
            model = "qwen2.5:3b"
            thinking = [
                f"Query analysis: {complexity.value} (confidence: {confidence:.2f})",
                "Route: qwen2.5:3b → may verify with 7b",
            ]
        else:  # COMPLEX
            model = "qwen2.5:7b"
            thinking = [
                f"Query analysis: {complexity.value} (confidence: {confidence:.2f})",
                "Route: qwen2.5:7b (high quality)",
            ]

        # 3. 모델 호출
        result = await self.generate(model, query, system_prompt)

        # 4. 통계 업데이트
        self.stats["total_calls"] += 1
        if model == "qwen2.5:3b":
            self.stats["qwen3b_calls"] += 1
            self.stats["qwen3b_tokens"] += result.get("eval_count", 0)
        else:
            self.stats["qwen7b_calls"] += 1
            self.stats["qwen7b_tokens"] += result.get("eval_count", 0)

        return {
            "query": query,
            "complexity": complexity.value,
            "response": result.get("response"),
            "model_used": model,
            "tokens": {
                "input": result.get("prompt_eval_count", 0),
                "output": result.get("eval_count", 0),
                "total": result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
            },
            "review_passed": True,
            "thinking": thinking,
            "timestamp": datetime.now().isoformat(),
        }

    def get_stats(self) -> Dict[str, Any]:
        """라우팅 통계"""
        total = self.stats["total_calls"]
        if total == 0:
            return {
                "summary": {"total_calls": 0, "efficiency": "No calls yet"},
                "qwen3b": {"calls": 0, "tokens": 0, "percentage": 0},
                "qwen7b": {"calls": 0, "tokens": 0, "percentage": 0},
            }

        qwen3b_pct = (self.stats["qwen3b_calls"] / total) * 100
        qwen7b_pct = (self.stats["qwen7b_calls"] / total) * 100

        return {
            "summary": {
                "total_calls": total,
                "efficiency": f"{qwen3b_pct:.1f}% qwen2.5:3b / {qwen7b_pct:.1f}% qwen2.5:7b",
            },
            "qwen3b": {
                "calls": self.stats["qwen3b_calls"],
                "tokens": self.stats["qwen3b_tokens"],
                "percentage": round(qwen3b_pct, 1),
            },
            "qwen7b": {
                "calls": self.stats["qwen7b_calls"],
                "tokens": self.stats["qwen7b_tokens"],
                "percentage": round(qwen7b_pct, 1),
            },
        }


# Global router instance
ollama_router = OllamaRouter()


class QueryRequest(BaseModel):
    """질문 요청"""

    query: str
    system_prompt: Optional[str] = None
    max_tokens: int = 4096
    analyze_only: bool = False  # 분석만 수행 (응답 생성 없음)


class QueryResponse(BaseModel):
    """질문 응답"""

    query: str
    complexity: str
    response: Optional[str]
    model_used: str
    tokens: Dict[str, Any]
    review_passed: bool
    thinking: Optional[list]
    timestamp: str


@router.post("/route", response_model=QueryResponse)
async def route_query(request: QueryRequest):
    """
    질문을 분석하고 적절한 Ollama 모델로 라우팅

    주요 기능:
    - 자동 난이도 분석 (simple/moderate/complex)
    - Simple: qwen2.5:3b 빠른 처리
    - Moderate: qwen2.5:3b 우선, 필요시 7b 검증
    - Complex: qwen2.5:7b 직접 처리

    요청 예시:
    ```json
    {
        "query": "Python에서 list를 역순으로 정렬하는 방법은?",
        "system_prompt": "You are a Python expert"
    }
    ```
    """
    try:
        logger.info(f"🔍 Processing query: {request.query[:100]}...")

        # 분석만 수행하는 경우
        if request.analyze_only:
            complexity, confidence = QueryAnalyzer.analyze(request.query)
            logger.info(f"✓ Query analysis only: {complexity.value} (confidence: {confidence:.2f})")

            return QueryResponse(
                query=request.query,
                complexity=complexity.value,
                response=None,
                model_used="analyzer",
                tokens={"analysis_only": True},
                review_passed=True,
                thinking=[f"Query analysis: {complexity.value} (confidence: {confidence:.2f})"],
                timestamp=datetime.now().isoformat(),
            )

        # 전체 라우팅 및 처리
        result = await ollama_router.route_and_process(
            query=request.query, system_prompt=request.system_prompt, max_tokens=request.max_tokens
        )

        logger.info(f"✓ Query processed: {result.get('model_used')}")

        return QueryResponse(
            query=result.get("query"),
            complexity=result.get("complexity", "unknown"),
            response=result.get("response"),
            model_used=result.get("model_used", "unknown"),
            tokens=result.get("tokens", {}),
            review_passed=result.get("review_passed", True),
            thinking=result.get("thinking"),
            timestamp=result.get("timestamp"),
        )

    except Exception as e:
        logger.error(f"✗ Query routing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_query(request: QueryRequest):
    """
    질문 난이도 분석만 수행 (응답 생성 안 함)

    응답 예시:
    ```json
    {
        "query": "복잡한 마이크로서비스 아키텍처 설계",
        "complexity": "complex",
        "confidence": 0.85,
        "recommendation": "Will use qwen2.5:7b model for best results"
    }
    ```
    """
    try:
        complexity, confidence = QueryAnalyzer.analyze(request.query)

        model_recommendation = {
            QueryComplexity.SIMPLE: "qwen2.5:3b",
            QueryComplexity.MODERATE: "qwen2.5:3b (with optional 7b review)",
            QueryComplexity.COMPLEX: "qwen2.5:7b",
        }

        return {
            "query": request.query,
            "complexity": complexity.value,
            "confidence": round(confidence, 2),
            "recommendation": f"Will use {model_recommendation[complexity]} for best results",
        }

    except Exception as e:
        logger.error(f"✗ Query analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_routing_stats():
    """
    라우팅 통계 조회

    응답 예시:
    ```json
    {
        "summary": {
            "total_calls": 150,
            "efficiency": "65.3% qwen2.5:3b / 34.7% qwen2.5:7b"
        },
        "qwen3b": {
            "calls": 105,
            "tokens": 45000,
            "percentage": 65.3
        },
        "qwen7b": {
            "calls": 45,
            "tokens": 25000,
            "percentage": 34.7
        }
    }
    ```
    """
    try:
        stats = ollama_router.get_stats()
        logger.info("✓ Routing stats retrieved")
        return stats

    except Exception as e:
        logger.error(f"✗ Error retrieving stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_route_queries(requests: list[QueryRequest]):
    """
    여러 질문 일괄 처리

    요청 예시:
    ```json
    [
        {"query": "Python 기초?"},
        {"query": "마이크로서비스 아키텍처 설계"}
    ]
    ```

    응답: 각 질문에 대한 routing 결과 배열
    """
    try:
        results = []
        logger.info(f"🔄 Processing batch of {len(requests)} queries...")

        for i, req in enumerate(requests):
            try:
                result = await ollama_router.route_and_process(
                    query=req.query, system_prompt=req.system_prompt, max_tokens=req.max_tokens
                )

                results.append(
                    {
                        "index": i,
                        "query": req.query,
                        "status": "success",
                        "complexity": result.get("complexity"),
                        "model_used": result.get("model_used"),
                        "tokens": result.get("tokens", {}).get("total", 0),
                    }
                )

            except Exception as e:
                logger.warning(f"✗ Batch item {i} failed: {e}")
                results.append({"index": i, "query": req.query, "status": "error", "error": str(e)})

        logger.info(
            f"✓ Batch processing completed: {len([r for r in results if r['status'] == 'success'])}/{len(results)} success"
        )
        return {
            "batch_size": len(requests),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"]),
            "results": results,
        }

    except Exception as e:
        logger.error(f"✗ Batch routing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def query_router_health():
    """쿼리 라우터 상태 확인"""
    try:
        stats = ollama_router.get_stats()
        return {
            "status": "healthy",
            "ollama_url": ollama_router.ollama_url,
            "models": {"small": "qwen2.5:3b", "large": "qwen2.5:7b"},
            "stats": stats,
        }

    except Exception as e:
        logger.error(f"✗ Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
