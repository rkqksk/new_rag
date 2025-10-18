"""
Query Router API Routes
질문 난이도에 따라 Haiku/Sonnet 자동 라우팅
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import sys
import os

# Query Router import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from mcp_servers.query_router import TeacherStudentOrchestrator, QueryAnalyzer, QueryComplexity

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/query",
    tags=["query_router"]
)

# Global orchestrator instance
orchestrator = TeacherStudentOrchestrator()


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
    질문을 분석하고 적절한 모델로 라우팅

    주요 기능:
    - 자동 난이도 분석 (simple/moderate/complex)
    - Simple: Haiku 빠른 처리
    - Moderate: Haiku → Sonnet 검증
    - Complex: Sonnet 직접 처리
    
    요청 예시:
    ```json
    {
        "query": "Python에서 list를 역순으로 정렬하는 방법은?",
        "system_prompt": "You are a Python expert"
    }
    ```
    
    응답 예시:
    ```json
    {
        "query": "Python에서 list를 역순으로 정렬하는 방법은?",
        "complexity": "simple",
        "response": "Python에서 list를 역순으로 정렬하는 방법...",
        "model_used": "claude-haiku-4-5-20251001",
        "tokens": {
            "input": 15,
            "output": 120,
            "total": 135
        },
        "review_passed": true,
        "thinking": ["Query analysis: simple (confidence: 0.95)", "Route: Haiku (fast path)"]
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
                thinking=[f"Query analysis: {complexity.value} (confidence: {confidence:.2f})"]
            )

        # 전체 라우팅 및 처리
        result = await orchestrator.route_and_process(
            query=request.query,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens
        )

        logger.info(f"✓ Query processed: {result.get('model_used')}")

        return QueryResponse(
            query=result.get("query"),
            complexity=result.get("complexity", "unknown"),
            response=result.get("response"),
            model_used=result.get("model_used", "unknown"),
            tokens=result.get("tokens", {}),
            review_passed=result.get("review_passed", True),
            thinking=result.get("thinking")
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
        "recommendation": "Will use Sonnet model for best results"
    }
    ```
    """
    try:
        complexity, confidence = QueryAnalyzer.analyze(request.query)

        return {
            "query": request.query,
            "complexity": complexity.value,
            "confidence": round(confidence, 2),
            "recommendation": f"Will use {('Haiku' if complexity == QueryComplexity.SIMPLE else 'Haiku+Sonnet review' if complexity == QueryComplexity.MODERATE else 'Sonnet')} model for best results"
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
            "teacher_reviews": 45,
            "corrections_made": 8,
            "efficiency": "65.3% Haiku / 34.7% Sonnet"
        },
        "haiku": {
            "calls": 105,
            "tokens": 45000,
            "percentage": 65.3
        },
        "sonnet": {
            "calls": 45,
            "tokens": 25000,
            "percentage": 34.7
        }
    }
    ```
    """
    try:
        stats = orchestrator.get_stats()
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
                result = await orchestrator.route_and_process(
                    query=req.query,
                    system_prompt=req.system_prompt,
                    max_tokens=req.max_tokens
                )

                results.append({
                    "index": i,
                    "query": req.query,
                    "status": "success",
                    "complexity": result.get("complexity"),
                    "model_used": result.get("model_used"),
                    "tokens": result.get("tokens", {}).get("total", 0)
                })

            except Exception as e:
                logger.warning(f"✗ Batch item {i} failed: {e}")
                results.append({
                    "index": i,
                    "query": req.query,
                    "status": "error",
                    "error": str(e)
                })

        logger.info(f"✓ Batch processing completed: {len([r for r in results if r['status'] == 'success'])}/{len(results)} success")
        return {
            "batch_size": len(requests),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"]),
            "results": results
        }

    except Exception as e:
        logger.error(f"✗ Batch routing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def query_router_health():
    """쿼리 라우터 상태 확인"""
    try:
        stats = orchestrator.get_stats()
        return {
            "status": "healthy",
            "models": {
                "haiku": "claude-haiku-4-5-20251001",
                "sonnet": "claude-3-5-sonnet-20241022"
            },
            "stats": stats
        }

    except Exception as e:
        logger.error(f"✗ Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# 추가: Complexity enum을 QueryComplexity로 import하기
from mcp_servers.query_router import QueryComplexity
