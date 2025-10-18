"""
Workflow API Routes
워크플로우 오케스트레이션 API 엔드포인트
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

from agents.workflow_orchestrator_v3 import (
    WorkflowOrchestratorV3,
    WorkflowType
)

# 라우터 초기화
router = APIRouter(
    prefix="/api/v1/workflow",
    tags=["workflow"]
)

# Workflow Orchestrator 인스턴스 (싱글톤)
orchestrator = WorkflowOrchestratorV3()


# Request/Response 모델
class WorkflowTypeEnum(str, Enum):
    """워크플로우 유형"""
    FULL_PIPELINE = "full_pipeline"
    CRAWLING_ONLY = "crawling_only"
    INDEXING_ONLY = "indexing_only"
    CLEANUP_ONLY = "cleanup"
    DATA_PROCESSING = "data_processing"


class ExecuteWorkflowRequest(BaseModel):
    """워크플로우 실행 요청"""
    workflow_type: WorkflowTypeEnum = Field(
        ...,
        description="워크플로우 유형"
    )
    pre_cleanup: bool = Field(
        default=True,
        description="사전 정리 실행 여부"
    )
    post_cleanup: bool = Field(
        default=True,
        description="사후 정리 실행 여부"
    )


class CleanupRequest(BaseModel):
    """정리 요청"""
    mode: str = Field(
        default="safe",
        description="정리 모드 (safe, aggressive, dry-run)"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="정리할 카테고리 (생략 시 기본 카테고리 사용)"
    )


class WorkflowStatusResponse(BaseModel):
    """워크플로우 상태 응답"""
    workflow_type: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    documents_processed: int = 0
    documents_failed: int = 0
    errors: List[str] = []
    cleanup_stats: Optional[Dict[str, Any]] = None


class ExecuteWorkflowResponse(BaseModel):
    """워크플로우 실행 응답"""
    status: str
    workflow_type: str
    message: str


class CleanupResponse(BaseModel):
    """정리 응답"""
    status: str
    mode: str
    files_analyzed: int
    files_deleted: int
    space_saved: int
    categories: Dict[str, int]
    errors: List[str] = []


# API 엔드포인트
@router.post("/execute", response_model=ExecuteWorkflowResponse)
async def execute_workflow(
    request: ExecuteWorkflowRequest,
    background_tasks: BackgroundTasks
):
    """
    워크플로우 실행

    **워크플로우 유형**:
    - `full_pipeline`: 전체 파이프라인 (크롤링 → 파싱 → 청킹 → 임베딩 → 인덱싱)
    - `crawling_only`: 크롤링만 실행
    - `indexing_only`: 인덱싱만 실행 (기존 문서)
    - `cleanup`: 정리만 실행
    - `data_processing`: 데이터 처리만 (파싱 + 청킹)

    **옵션**:
    - `pre_cleanup`: 실행 전 임시 파일 정리
    - `post_cleanup`: 실행 후 로그 정리

    **반환**:
    - 워크플로우가 백그라운드에서 시작되고, 즉시 응답 반환
    - 진행 상황은 `/api/v1/workflow/status` 엔드포인트로 조회
    """
    try:
        # 워크플로우 타입 변환
        workflow_type = WorkflowType(request.workflow_type.value)

        # 백그라운드 태스크로 실행
        background_tasks.add_task(
            orchestrator.execute_workflow,
            workflow_type=workflow_type,
            documents=None,  # 향후 확장: 문서 리스트 전달
            pre_cleanup=request.pre_cleanup,
            post_cleanup=request.post_cleanup
        )

        return ExecuteWorkflowResponse(
            status="started",
            workflow_type=request.workflow_type.value,
            message=f"Workflow {request.workflow_type.value} started in background"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start workflow: {str(e)}"
        )


@router.post("/cleanup", response_model=CleanupResponse)
async def run_cleanup(request: CleanupRequest):
    """
    Clean Deploy 실행

    **모드**:
    - `safe`: 안전 모드 (백업 후 삭제)
    - `aggressive`: 공격적 모드 (즉시 삭제, 백업 없음)
    - `dry-run`: 드라이 런 (시뮬레이션만)

    **카테고리**:
    - `temporary`: 임시 파일 (__pycache__, *.pyc, *.tmp)
    - `build`: 빌드 산출물 (dist/, build/, *.egg-info)
    - `logs`: 로그 파일 (logs/, *.log)
    - `development`: 개발 전용 파일 (dev/, test_*.py)
    - `documentation`: 문서 (claudedocs/)
    - 생략 시: temporary, build 기본 정리

    **반환**:
    - 정리 통계 및 결과
    """
    try:
        stats = await orchestrator.run_cleanup(
            mode=request.mode,
            categories=request.categories
        )

        return CleanupResponse(
            status="completed",
            mode=stats["mode"],
            files_analyzed=stats["files_analyzed"],
            files_deleted=stats["files_deleted"],
            space_saved=stats["space_saved"],
            categories=stats["categories"],
            errors=stats.get("errors", [])
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.get("/status", response_model=WorkflowStatusResponse)
async def get_workflow_status():
    """
    현재 워크플로우 상태 조회

    **반환**:
    - 워크플로우 유형
    - 실행 상태 (idle, running, completed, failed)
    - 시작/완료 시각
    - 처리된 문서 수
    - 실패한 문서 수
    - 오류 목록
    - 정리 통계
    """
    try:
        status = orchestrator.get_status()

        return WorkflowStatusResponse(
            workflow_type=status["workflow_type"],
            status=status["status"],
            started_at=status["started_at"],
            completed_at=status["completed_at"],
            documents_processed=status["documents_processed"],
            documents_failed=status["documents_failed"],
            errors=status["errors"],
            cleanup_stats=status["cleanup_stats"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Workflow Orchestrator 헬스체크

    **반환**:
    - 오케스트레이터 상태
    - 사용 가능한 에이전트 목록
    """
    try:
        agents_status = {
            agent_name: "available"
            for agent_name in orchestrator.agents.keys()
        }

        return {
            "status": "healthy",
            "orchestrator": "WorkflowOrchestratorV3",
            "agents": agents_status,
            "current_workflow": orchestrator.current_status.workflow_type or "idle"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


# 확장 엔드포인트 (향후 추가)
@router.get("/workflows")
async def list_workflows():
    """
    사용 가능한 워크플로우 목록 조회

    **반환**:
    - 워크플로우 유형 리스트
    - 각 워크플로우 설명
    """
    workflows = [
        {
            "type": "full_pipeline",
            "description": "전체 파이프라인 (크롤링 → 파싱 → 청킹 → 임베딩 → 인덱싱)",
            "estimated_time": "10-30분"
        },
        {
            "type": "crawling_only",
            "description": "웹 크롤링만 실행",
            "estimated_time": "5-10분"
        },
        {
            "type": "indexing_only",
            "description": "기존 문서 인덱싱만 실행",
            "estimated_time": "5-15분"
        },
        {
            "type": "cleanup",
            "description": "프로젝트 정리 (임시 파일, 로그, 캐시)",
            "estimated_time": "1-2분"
        },
        {
            "type": "data_processing",
            "description": "데이터 처리 (파싱 + 청킹)",
            "estimated_time": "5-10분"
        }
    ]

    return {
        "total": len(workflows),
        "workflows": workflows
    }


@router.get("/categories")
async def list_cleanup_categories():
    """
    정리 가능한 파일 카테고리 목록

    **반환**:
    - 카테고리 목록
    - 각 카테고리 설명
    """
    categories = [
        {
            "name": "temporary",
            "description": "임시 파일 (__pycache__, *.pyc, *.tmp, .DS_Store)"
        },
        {
            "name": "build",
            "description": "빌드 산출물 (dist/, build/, *.egg-info, venv/)"
        },
        {
            "name": "logs",
            "description": "로그 파일 (logs/, *.log)"
        },
        {
            "name": "development",
            "description": "개발 전용 파일 (dev/, experiments/, test_*.py)"
        },
        {
            "name": "documentation",
            "description": "Claude 생성 문서 (claudedocs/)"
        },
        {
            "name": "data",
            "description": "데이터 파일 (data/, documents/, uploads/)"
        },
        {
            "name": "archives",
            "description": "아카이브 (archives/, backups/, *.tar.gz)"
        }
    ]

    return {
        "total": len(categories),
        "categories": categories
    }
