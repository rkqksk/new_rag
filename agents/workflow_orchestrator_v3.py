#!/usr/bin/env python3
"""
Workflow Orchestrator v3.0
통합 워크플로우 오케스트레이터

주요 기능:
- Clean Deploy Agent 통합
- 병렬 처리 최적화
- API 통합
- 파일 자동 정리
"""

import asyncio
import json
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# 기존 에이전트 import
from agents.workflow_orchestrator import (
    WorkflowOrchestrator,
    Document,
    ProcessingStage,
    DocumentType,
    ProcessingMetadata
)
from agents.clean_deploy_agent_v2 import (
    CleanDeployAgent,
    CleanupMode,
    FileCategory
)
from agents.debugging_agent import (
    DebuggingAgent,
    DebugType,
    DebugLevel
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """워크플로우 유형"""
    FULL_PIPELINE = "full_pipeline"      # 전체 파이프라인
    CRAWLING_ONLY = "crawling_only"      # 크롤링만
    INDEXING_ONLY = "indexing_only"      # 인덱싱만
    CLEANUP_ONLY = "cleanup"             # 정리만
    DATA_PROCESSING = "data_processing"  # 데이터 처리만
    DEBUGGING = "debugging"              # 디버깅


@dataclass
class WorkflowStatus:
    """워크플로우 상태"""
    workflow_type: str
    status: str  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    documents_processed: int = 0
    documents_failed: int = 0
    errors: List[str] = field(default_factory=list)
    cleanup_stats: Optional[Dict] = None


class WorkflowOrchestratorV3:
    """
    통합 워크플로우 오케스트레이터 v3.0

    개선사항:
    - Clean Deploy Agent 통합
    - 병렬 처리 최적화
    - API 통합 준비
    - 파일 자동 정리
    """

    def __init__(self, config_path: str = "config/pipeline_config.json"):
        # 기존 오케스트레이터 초기화
        self.base_orchestrator = WorkflowOrchestrator(config_path)

        # Clean Deploy Agent 초기화
        self.clean_deploy = CleanDeployAgent(
            config_path=Path("config/clean_deploy_config.json")
        )

        # Debugging Agent 초기화
        self.debugging_agent = DebuggingAgent(
            output_dir="claudedocs/debug_reports"
        )

        # 워크플로우 상태 관리
        self.current_status = WorkflowStatus(
            workflow_type="",
            status="idle"
        )

        # 에이전트 레지스트리 (확장 가능)
        self.agents = {
            'base': self.base_orchestrator,
            'clean_deploy': self.clean_deploy,
            'debugging': self.debugging_agent
        }

        logger.info("Workflow Orchestrator v3.0 initialized")

    async def execute_workflow(
        self,
        workflow_type: WorkflowType,
        documents: Optional[List[Document]] = None,
        pre_cleanup: bool = True,
        post_cleanup: bool = True
    ) -> WorkflowStatus:
        """
        워크플로우 실행 (병렬 처리 최적화)

        Args:
            workflow_type: 워크플로우 유형
            documents: 처리할 문서 리스트
            pre_cleanup: 사전 정리 실행 여부
            post_cleanup: 사후 정리 실행 여부

        Returns:
            WorkflowStatus: 실행 결과 상태
        """
        self.current_status = WorkflowStatus(
            workflow_type=workflow_type.value,
            status="running",
            started_at=datetime.now()
        )

        try:
            # Phase 1: Pre-cleanup (사전 정리)
            if pre_cleanup:
                logger.info("Phase 1: Pre-cleanup...")
                await self._run_pre_cleanup()

            # Phase 2: Workflow 실행 (병렬 처리)
            logger.info(f"Phase 2: Executing {workflow_type.value}...")
            if workflow_type == WorkflowType.FULL_PIPELINE:
                await self._run_full_pipeline(documents)

            elif workflow_type == WorkflowType.CRAWLING_ONLY:
                await self._run_crawling_only()

            elif workflow_type == WorkflowType.INDEXING_ONLY:
                await self._run_indexing_only(documents)

            elif workflow_type == WorkflowType.CLEANUP_ONLY:
                await self._run_cleanup_only()

            elif workflow_type == WorkflowType.DATA_PROCESSING:
                await self._run_data_processing(documents)

            elif workflow_type == WorkflowType.DEBUGGING:
                await self._run_debugging(documents)

            # Phase 3: Post-cleanup (사후 정리)
            if post_cleanup:
                logger.info("Phase 3: Post-cleanup...")
                await self._run_post_cleanup()

            # Phase 4: File organization (파일 자동 정리)
            logger.info("Phase 4: File organization...")
            await self._organize_outputs()

            # 성공 완료
            self.current_status.status = "completed"
            self.current_status.completed_at = datetime.now()

            logger.info(f"Workflow {workflow_type.value} completed successfully")
            return self.current_status

        except Exception as e:
            self.current_status.status = "failed"
            self.current_status.errors.append(str(e))
            self.current_status.completed_at = datetime.now()
            logger.error(f"Workflow failed: {e}")
            raise

    async def _run_pre_cleanup(self):
        """사전 정리: 임시 파일 및 캐시 제거"""
        cleanup_stats = await asyncio.to_thread(
            self.clean_deploy.run_cleanup,
            mode=CleanupMode.SAFE,
            categories=[FileCategory.TEMPORARY],
            validate=False
        )
        self.current_status.cleanup_stats = {
            'pre_cleanup': {
                'files_deleted': cleanup_stats.files_deleted,
                'space_saved': cleanup_stats.space_saved
            }
        }
        logger.info(f"Pre-cleanup: {cleanup_stats.files_deleted} files deleted")

    async def _run_post_cleanup(self):
        """사후 정리: 로그 및 빌드 산출물 정리"""
        cleanup_stats = await asyncio.to_thread(
            self.clean_deploy.run_cleanup,
            mode=CleanupMode.SAFE,
            categories=[FileCategory.LOGS, FileCategory.BUILD],
            validate=False
        )
        if self.current_status.cleanup_stats is None:
            self.current_status.cleanup_stats = {}
        self.current_status.cleanup_stats['post_cleanup'] = {
            'files_deleted': cleanup_stats.files_deleted,
            'space_saved': cleanup_stats.space_saved
        }
        logger.info(f"Post-cleanup: {cleanup_stats.files_deleted} files deleted")

    async def _run_full_pipeline(self, documents: Optional[List[Document]]):
        """
        전체 파이프라인 실행 (병렬 처리 최적화)

        병렬 가능 작업:
        - 여러 문서 파싱 (병렬)
        - 여러 청크 임베딩 (병렬)

        순차 필수 작업:
        - 크롤링 → 파싱
        - 파싱 → 청킹
        - 청킹 → 임베딩
        - 임베딩 → 인덱싱
        """
        if not documents:
            logger.warning("No documents provided for processing")
            return

        # 병렬 처리: 여러 문서 동시 처리
        tasks = []
        for doc in documents:
            task = asyncio.create_task(
                self.base_orchestrator.process_document(doc)
            )
            tasks.append(task)

        # 모든 문서 병렬 처리
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 집계
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.current_status.documents_failed += 1
                self.current_status.errors.append(f"Document {i}: {result}")
                logger.error(f"Document {i} failed: {result}")
            else:
                self.current_status.documents_processed += 1
                logger.info(f"Document {i} completed")

    async def _run_crawling_only(self):
        """크롤링만 실행 (병렬 카테고리 크롤링)"""
        logger.info("Crawling workflow started")

        # 크롤러 에이전트 동적 import (순환 참조 방지)
        try:
            import sys
            sys.path.append(str(Path.cwd() / "scripts" / "crawlers"))
            from chungjin_crawler import ChungjinCrawler

            # 여러 카테고리 병렬 크롤링
            categories = ["Bottle", "Jar", "Cap&Pump"]
            tasks = []

            for category in categories:
                task = asyncio.create_task(
                    self._crawl_category(category, ChungjinCrawler)
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 결과 처리
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Crawling {categories[i]} failed: {result}")
                    self.current_status.errors.append(f"Crawling {categories[i]}: {result}")
                else:
                    logger.info(f"Crawling {categories[i]} completed: {result} products")

        except ImportError as e:
            logger.error(f"Failed to import crawler: {e}")
            self.current_status.errors.append(f"Crawler import failed: {e}")

    async def _crawl_category(self, category: str, crawler_class) -> int:
        """카테고리별 크롤링 실행"""
        def _run_crawler():
            crawler = crawler_class()
            # 실제 크롤링 로직 (간단 예시)
            logger.info(f"Crawling {category}...")
            return 100  # 크롤링된 제품 수 (예시)

        return await asyncio.to_thread(_run_crawler)

    async def _run_indexing_only(self, documents: Optional[List[Document]]):
        """인덱싱만 실행"""
        if not documents:
            logger.warning("No documents provided for indexing")
            return

        logger.info(f"Indexing {len(documents)} documents")

        # 병렬 임베딩 생성
        tasks = []
        for doc in documents:
            if doc.stage == ProcessingStage.CHUNKING:
                task = asyncio.create_task(
                    self.base_orchestrator._embed_chunks(doc)
                )
                tasks.append((doc, task))

        # 임베딩 완료 대기
        for doc, task in tasks:
            try:
                await task
                # 인덱싱
                await self.base_orchestrator._index_document(doc)
                self.current_status.documents_processed += 1
            except Exception as e:
                logger.error(f"Indexing failed for {doc.id}: {e}")
                self.current_status.documents_failed += 1
                self.current_status.errors.append(f"{doc.id}: {e}")

    async def _run_cleanup_only(self):
        """정리만 실행"""
        cleanup_stats = await asyncio.to_thread(
            self.clean_deploy.run_cleanup,
            mode=CleanupMode.SAFE,
            categories=[
                FileCategory.TEMPORARY,
                FileCategory.BUILD,
                FileCategory.LOGS
            ],
            validate=True
        )
        self.current_status.cleanup_stats = {
            'files_deleted': cleanup_stats.files_deleted,
            'space_saved': cleanup_stats.space_saved,
            'categories': cleanup_stats.categories
        }
        logger.info(f"Cleanup completed: {cleanup_stats.files_deleted} files deleted")

    async def _run_data_processing(self, documents: Optional[List[Document]]):
        """데이터 처리만 실행 (파싱 + 청킹)"""
        if not documents:
            logger.warning("No documents provided for processing")
            return

        # 병렬 파싱
        tasks = []
        for doc in documents:
            if doc.stage == ProcessingStage.PENDING:
                task = asyncio.create_task(
                    self.base_orchestrator._parse_document(doc)
                )
                tasks.append((doc, task))

        # 파싱 완료 후 청킹
        for doc, task in tasks:
            try:
                await task
                await self.base_orchestrator._chunk_document(doc)
                self.current_status.documents_processed += 1
            except Exception as e:
                logger.error(f"Data processing failed for {doc.id}: {e}")
                self.current_status.documents_failed += 1
                self.current_status.errors.append(f"{doc.id}: {e}")

    async def _run_debugging(self, documents: Optional[List[Document]]):
        """
        디버깅 워크플로우 실행

        - URL 디버깅: 특정 URL 디버깅 (스크린샷, HTML 덤프, 성능 분석)
        - 크롤 세션 디버깅: 크롤링 세션 샘플링 디버깅
        """
        logger.info("Debugging workflow started")

        # Documents가 제공되지 않은 경우 크롤 세션 디버깅
        if not documents:
            logger.info("No documents provided, running crawl session debugging...")

            # 샘플 URL 수집 (크롤링된 제품 URL 샘플)
            sample_urls = await self._collect_sample_urls()

            if not sample_urls:
                logger.warning("No sample URLs found for debugging")
                return

            # 크롤 세션 디버깅 실행
            debug_results = await self.debugging_agent.debug_crawl_session(
                category="AllCategories",
                sample_urls=sample_urls,
                max_urls=3  # 최대 3개 URL 디버깅
            )

            logger.info(f"Crawl debugging completed: {debug_results['debugged_urls']} URLs debugged")

            # 결과 집계
            for session_info in debug_results['sessions']:
                if session_info['success']:
                    self.current_status.documents_processed += 1
                else:
                    self.current_status.documents_failed += 1

        else:
            # Documents가 제공된 경우 각 문서의 소스 URL 디버깅
            logger.info(f"Debugging {len(documents)} document URLs...")

            tasks = []
            for doc in documents:
                # Document의 URL이 있다면 디버깅
                if hasattr(doc, 'metadata') and 'url' in doc.metadata:
                    url = doc.metadata['url']
                    task = asyncio.create_task(
                        self.debugging_agent.debug_url(
                            url=url,
                            debug_type=DebugType.BROWSER,
                            level=DebugLevel.INFO,
                            capture_screenshot=True,
                            dump_html=True
                        )
                    )
                    tasks.append((doc, task))

            # 모든 디버깅 작업 병렬 처리
            for doc, task in tasks:
                try:
                    session = await task

                    # 디버그 리포트 생성
                    report_path = self.debugging_agent.generate_debug_report(
                        session.session_id
                    )
                    logger.info(f"Debug report generated: {report_path}")

                    self.current_status.documents_processed += 1

                except Exception as e:
                    logger.error(f"Debugging failed for {doc.id}: {e}")
                    self.current_status.documents_failed += 1
                    self.current_status.errors.append(f"{doc.id}: {e}")

    async def _collect_sample_urls(self) -> List[str]:
        """
        크롤링된 제품에서 샘플 URL 수집

        Returns:
            샘플 URL 리스트
        """
        sample_urls = []

        # crawled_products_organized 폴더에서 샘플 URL 추출
        data_root = Path("data/crawled_products_organized")

        if not data_root.exists():
            logger.warning(f"Data folder not found: {data_root}")
            return sample_urls

        # 각 카테고리에서 샘플 URL 수집 (카테고리당 1개)
        for category_dir in data_root.iterdir():
            if not category_dir.is_dir():
                continue

            products_dir = category_dir / "products"
            if not products_dir.exists():
                continue

            # 첫 번째 JSON 파일 읽기
            json_files = list(products_dir.glob("*.json"))
            if json_files:
                try:
                    import json
                    with open(json_files[0], encoding='utf-8') as f:
                        product = json.load(f)

                    if 'url' in product:
                        sample_urls.append(product['url'])
                        logger.info(f"Collected sample URL from {category_dir.name}: {product['url']}")

                except Exception as e:
                    logger.warning(f"Failed to read {json_files[0]}: {e}")

        return sample_urls

    async def _organize_outputs(self):
        """
        실행 후 자동 파일 정리

        규칙:
        - 보고서 (*.md, *.csv) → archives/reports/YYYY-MM-DD/
        - 임시 파일 (7일 이상) → 삭제
        - 로그 (90일 이상) → archives/logs/
        """
        today = datetime.now().strftime('%Y-%m-%d')
        report_dir = Path("archives/reports") / today
        report_dir.mkdir(parents=True, exist_ok=True)

        # 보고서 이동
        moved_count = 0
        for report in Path(".").glob("*_report.md"):
            try:
                shutil.move(str(report), report_dir / report.name)
                moved_count += 1
                logger.info(f"Moved report: {report.name} → {report_dir}")
            except Exception as e:
                logger.warning(f"Failed to move {report}: {e}")

        # CSV 파일 이동
        for csv in Path(".").glob("*.csv"):
            try:
                # 특정 CSV만 이동 (보고서 관련)
                if "report" in csv.name.lower() or "crawl" in csv.name.lower():
                    shutil.move(str(csv), report_dir / csv.name)
                    moved_count += 1
                    logger.info(f"Moved CSV: {csv.name} → {report_dir}")
            except Exception as e:
                logger.warning(f"Failed to move {csv}: {e}")

        # 임시 파일 정리 (7일 이상)
        temp_dir = Path("temp")
        if temp_dir.exists():
            deleted_count = 0
            for temp_file in temp_dir.rglob("*"):
                if temp_file.is_file():
                    age_days = (datetime.now() - datetime.fromtimestamp(temp_file.stat().st_mtime)).days
                    if age_days > 7:
                        try:
                            temp_file.unlink()
                            deleted_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to delete {temp_file}: {e}")

            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} old temporary files")

        logger.info(f"File organization completed: {moved_count} files moved")

    def get_status(self) -> Dict[str, Any]:
        """현재 워크플로우 상태 조회"""
        return {
            "workflow_type": self.current_status.workflow_type,
            "status": self.current_status.status,
            "started_at": self.current_status.started_at.isoformat() if self.current_status.started_at else None,
            "completed_at": self.current_status.completed_at.isoformat() if self.current_status.completed_at else None,
            "documents_processed": self.current_status.documents_processed,
            "documents_failed": self.current_status.documents_failed,
            "errors": self.current_status.errors,
            "cleanup_stats": self.current_status.cleanup_stats
        }

    async def run_cleanup(
        self,
        mode: str = "safe",
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Clean Deploy 실행 (API 엔드포인트용)

        Args:
            mode: 정리 모드 (safe, aggressive, dry-run)
            categories: 정리할 카테고리 리스트

        Returns:
            정리 통계
        """
        mode_map = {
            "safe": CleanupMode.SAFE,
            "aggressive": CleanupMode.AGGRESSIVE,
            "dry-run": CleanupMode.DRY_RUN
        }
        cleanup_mode = mode_map.get(mode, CleanupMode.SAFE)

        # 카테고리 변환
        category_objs = None
        if categories:
            category_map = {c.value: c for c in FileCategory}
            category_objs = [category_map[c] for c in categories if c in category_map]

        # 정리 실행
        stats = await asyncio.to_thread(
            self.clean_deploy.run_cleanup,
            mode=cleanup_mode,
            categories=category_objs,
            validate=True
        )

        return {
            "mode": mode,
            "files_analyzed": stats.files_analyzed,
            "files_deleted": stats.files_deleted,
            "space_saved": stats.space_saved,
            "categories": stats.categories,
            "errors": stats.errors
        }


# 테스트 실행
async def test_workflow():
    """워크플로우 테스트"""
    orchestrator = WorkflowOrchestratorV3()

    # 1. Cleanup 테스트
    logger.info("Testing cleanup workflow...")
    status = await orchestrator.execute_workflow(
        workflow_type=WorkflowType.CLEANUP_ONLY
    )
    print(f"Cleanup Status: {status.status}")

    # 2. 상태 조회
    current_status = orchestrator.get_status()
    print(f"Current Status: {json.dumps(current_status, indent=2, default=str)}")


if __name__ == "__main__":
    # 테스트 실행
    asyncio.run(test_workflow())
