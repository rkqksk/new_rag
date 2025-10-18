#!/usr/bin/env python3
"""
웹 크롤링 에이전트
엔터프라이즈 RAG 시스템의 데이터 수집 담당 에이전트

주요 기능:
- 다양한 사이트 크롤링 지원
- 스케줄링 및 자동 실행
- RAG 시스템과 자동 연동
- 실시간 진행 상황 모니터링
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# 데이터 모델
# ============================================================================

class CrawlConfig(BaseModel):
    """크롤링 설정"""
    site_name: str = Field(..., description="사이트 이름")
    site_url: str = Field(..., description="사이트 URL")
    output_dir: str = Field(default="data/crawled_products", description="출력 디렉토리")
    delay: int = Field(default=2, description="요청 간 지연 (초)")
    max_retries: int = Field(default=3, description="최대 재시도 횟수")
    enable_csv_report: bool = Field(default=True, description="CSV 리포트 생성 여부")

    # 브라우저 설정
    browser_type: str = Field(default="webkit", description="브라우저 타입: webkit (macOS) 또는 chromium (크로스 플랫폼)")
    use_playwright: bool = Field(default=False, description="Playwright 사용 여부 (False=Google DevTools MCP)")


class CrawlCategory(BaseModel):
    """카테고리 정보"""
    name: str
    url: str
    pages: int
    description: Optional[str] = None


class CrawlProgress(BaseModel):
    """크롤링 진행 상황"""
    category: str
    current_page: int
    total_pages: int
    products_collected: int
    products_crawled: int
    success_count: int
    error_count: int
    start_time: str
    elapsed_seconds: float

    @property
    def progress_percent(self) -> float:
        return (self.current_page / self.total_pages * 100) if self.total_pages > 0 else 0


class CrawlResult(BaseModel):
    """크롤링 결과"""
    site_name: str
    category: str
    total_products: int
    success: int
    error: int
    duration_seconds: float
    output_dir: str
    csv_report: Optional[str] = None


# ============================================================================
# 추상 크롤러 기반 클래스
# ============================================================================

class BaseCrawler(ABC):
    """모든 사이트 크롤러의 기반 클래스"""

    def __init__(self, config: CrawlConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    async def crawl_category(
        self,
        category: CrawlCategory,
        progress_callback: Optional[callable] = None
    ) -> CrawlResult:
        """카테고리 크롤링 (구현 필요)"""
        pass

    @abstractmethod
    async def crawl_product(self, url: str) -> Dict[str, Any]:
        """제품 페이지 크롤링 (구현 필요)"""
        pass

    def save_json(self, data: Dict[str, Any], filename: str) -> Path:
        """JSON 저장"""
        json_path = self.output_dir / filename

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return json_path


# ============================================================================
# 크롤링 에이전트
# ============================================================================

class CrawlingAgent:
    """
    웹 크롤링 에이전트

    기능:
    - 다중 사이트 크롤링 관리
    - 진행 상황 실시간 모니터링
    - RAG 시스템 자동 연동
    - 스케줄링 지원
    """

    def __init__(self):
        self.crawlers: Dict[str, BaseCrawler] = {}
        self.progress_callbacks: List[callable] = []

    def register_crawler(self, site_name: str, crawler: BaseCrawler):
        """크롤러 등록"""
        self.crawlers[site_name] = crawler
        logger.info(f"✓ 크롤러 등록: {site_name}")

    def add_progress_callback(self, callback: callable):
        """진행 상황 콜백 등록"""
        self.progress_callbacks.append(callback)

    async def crawl_site(
        self,
        site_name: str,
        categories: List[CrawlCategory]
    ) -> List[CrawlResult]:
        """
        사이트 전체 크롤링

        Args:
            site_name: 등록된 사이트 이름
            categories: 크롤링할 카테고리 목록

        Returns:
            각 카테고리의 크롤링 결과 목록
        """
        if site_name not in self.crawlers:
            raise ValueError(f"등록되지 않은 사이트: {site_name}")

        crawler = self.crawlers[site_name]
        results = []

        logger.info(f"\n{'='*80}")
        logger.info(f"사이트 크롤링 시작: {site_name}")
        logger.info(f"카테고리: {len(categories)}개")
        logger.info(f"{'='*80}\n")

        for category in categories:
            logger.info(f"\n[카테고리] {category.name}")
            logger.info(f"  URL: {category.url}")
            logger.info(f"  페이지: {category.pages}개")

            # 진행 상황 콜백
            def progress_callback(progress: CrawlProgress):
                for callback in self.progress_callbacks:
                    callback(progress)

            # 카테고리 크롤링 실행
            result = await crawler.crawl_category(
                category,
                progress_callback=progress_callback
            )

            results.append(result)

            logger.info(f"\n✅ {category.name} 완료: {result.success}/{result.total_products}")

        logger.info(f"\n{'='*80}")
        logger.info(f"사이트 크롤링 완료: {site_name}")
        logger.info(f"{'='*80}\n")

        return results

    async def crawl_and_ingest(
        self,
        site_name: str,
        categories: List[CrawlCategory],
        rag_system: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        크롤링 + RAG 시스템 자동 연동

        Args:
            site_name: 사이트 이름
            categories: 카테고리 목록
            rag_system: RAG 시스템 인스턴스 (선택)

        Returns:
            {
                'crawl_results': [...],
                'rag_ingestion': {...}
            }
        """
        # 1. 크롤링 실행
        crawl_results = await self.crawl_site(site_name, categories)

        # 2. RAG 시스템 연동
        rag_result = None
        if rag_system:
            logger.info("\n[RAG 연동] 크롤링 데이터를 RAG 시스템에 수집 중...")

            # 크롤링 결과 수집
            all_products = []
            for result in crawl_results:
                output_dir = Path(result.output_dir)
                json_files = list(output_dir.glob('idx_*.json'))

                for json_file in json_files:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        product_data = json.load(f)
                        all_products.append(product_data)

            # RAG 시스템에 수집
            rag_result = await rag_system.ingest_products(all_products)

            logger.info(f"✓ RAG 수집 완료: {len(all_products)}개 제품")

        return {
            'crawl_results': [r.dict() for r in crawl_results],
            'rag_ingestion': rag_result
        }

    def get_scheduler_job(
        self,
        site_name: str,
        categories: List[CrawlCategory],
        cron_expression: str = "0 2 * * *"  # 매일 새벽 2시
    ) -> Dict[str, Any]:
        """
        스케줄러 작업 설정 반환

        Args:
            site_name: 사이트 이름
            categories: 카테고리 목록
            cron_expression: Cron 표현식

        Returns:
            스케줄러 작업 설정 (APScheduler 또는 Celery용)
        """
        return {
            'job_id': f"crawl_{site_name}",
            'trigger': 'cron',
            'cron_expression': cron_expression,
            'func': self.crawl_site,
            'args': [site_name, categories],
            'description': f"{site_name} 정기 크롤링"
        }


# ============================================================================
# 청진코리아 크롤러 (통합)
# ============================================================================

class ChungjinCrawler(BaseCrawler):
    """청진코리아 전용 크롤러"""

    def __init__(self, config: CrawlConfig):
        super().__init__(config)

        # chungjin_crawler.py 통합
        from chungjin_crawler import ChungjinCrawler as OriginalCrawler
        self._crawler = OriginalCrawler(
            output_dir=str(self.output_dir),
            browser_type=config.browser_type,
            use_playwright=config.use_playwright
        )

    async def crawl_category(
        self,
        category: CrawlCategory,
        progress_callback: Optional[callable] = None
    ) -> CrawlResult:
        """카테고리 크롤링"""
        start_time = datetime.now()

        # 기존 크롤러 실행
        summary = await self._crawler.crawl_category(
            category_name=category.name,
            category_url=category.url,
            max_pages=category.pages,
            delay=self.config.delay
        )

        duration = (datetime.now() - start_time).total_seconds()

        # CSV 리포트 생성 (옵션)
        csv_report = None
        if self.config.enable_csv_report:
            from scripts.generate_crawl_report import generate_csv_report

            csv_path = self.output_dir / f"{category.name}_report.csv"
            generate_csv_report(
                crawled_dir=self.output_dir,
                output_csv=csv_path,
                category_name=category.name
            )
            csv_report = str(csv_path)

        return CrawlResult(
            site_name=self.config.site_name,
            category=category.name,
            total_products=summary['total_products'],
            success=summary['success'],
            error=summary['error'],
            duration_seconds=duration,
            output_dir=str(self.output_dir),
            csv_report=csv_report
        )

    async def crawl_product(self, url: str) -> Dict[str, Any]:
        """제품 페이지 크롤링"""
        return await self._crawler.crawl_product(url)


# ============================================================================
# 사용 예시
# ============================================================================

async def main():
    """크롤링 에이전트 사용 예시"""

    # 1. 에이전트 생성
    agent = CrawlingAgent()

    # 2. 진행 상황 모니터링 콜백
    def progress_monitor(progress: CrawlProgress):
        print(f"\r[{progress.category}] "
              f"{progress.progress_percent:.1f}% "
              f"({progress.current_page}/{progress.total_pages} 페이지) "
              f"- 제품: {progress.products_crawled}/{progress.products_collected}",
              end='')

    agent.add_progress_callback(progress_monitor)

    # 3. 크롤러 등록
    chungjin_config = CrawlConfig(
        site_name="청진코리아",
        site_url="http://chungjinkorea.com",
        output_dir="data/crawled_products",
        delay=2,
        enable_csv_report=True
    )

    chungjin_crawler = ChungjinCrawler(chungjin_config)
    agent.register_crawler("청진코리아", chungjin_crawler)

    # 4. 카테고리 정의
    categories = [
        CrawlCategory(
            name="Jar",
            url="http://chungjinkorea.com/kr/product/list.php?part_idx=2",
            pages=4,
            description="용기 카테고리"
        ),
        CrawlCategory(
            name="Cap&Pump",
            url="http://chungjinkorea.com/kr/product/list.php?part_idx=3",
            pages=14,
            description="캡 및 펌프 카테고리"
        ),
        CrawlCategory(
            name="Bottle",
            url="http://chungjinkorea.com/kr/product/list.php?part_idx=1",
            pages=68,
            description="병 카테고리"
        )
    ]

    # 5. 크롤링 실행
    results = await agent.crawl_site("청진코리아", categories)

    # 6. 결과 출력
    print("\n\n" + "="*80)
    print("크롤링 완료!")
    print("="*80)

    for result in results:
        print(f"\n{result.category}:")
        print(f"  총 제품: {result.total_products}개")
        print(f"  성공: {result.success}개")
        print(f"  실패: {result.error}개")
        print(f"  소요 시간: {result.duration_seconds:.1f}초")
        if result.csv_report:
            print(f"  CSV 리포트: {result.csv_report}")


if __name__ == '__main__':
    asyncio.run(main())
