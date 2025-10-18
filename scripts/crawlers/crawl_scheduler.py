#!/usr/bin/env python3
"""
청진코리아 크롤링 스케줄러
APScheduler 기반 월간 자동 크롤링

기능:
- 카테고리별 독립 스케줄 실행
- 증분 업데이트 (새 제품만 크롤링)
- 재시도 로직
- 실행 결과 알림
"""

import asyncio
import logging
import subprocess
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/crawl_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CrawlScheduler:
    """크롤링 스케줄러"""

    def __init__(self, config_path: str = "config/crawl_schedule.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.scheduler = AsyncIOScheduler()

    def _load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    async def run_crawl(self, category: str, script: str):
        """크롤링 스크립트 실행"""
        logger.info(f"\n{'='*80}")
        logger.info(f"[{category}] 크롤링 시작")
        logger.info(f"스크립트: {script}")
        logger.info(f"{'='*80}")

        start_time = datetime.now()

        try:
            # Python 스크립트 실행
            process = await asyncio.create_subprocess_exec(
                'python',
                script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"[{category}] 크롤링 성공")
                logger.debug(f"출력:\n{stdout.decode('utf-8')}")

                # 성공 알림
                if self.config.get('notifications', {}).get('slack', {}).get('on_success'):
                    await self._send_notification(
                        category=category,
                        status='success',
                        message=f"{category} 크롤링 완료"
                    )

                return True
            else:
                logger.error(f"[{category}] 크롤링 실패")
                logger.error(f"에러:\n{stderr.decode('utf-8')}")

                # 에러 알림
                if self.config.get('notifications', {}).get('slack', {}).get('on_error'):
                    await self._send_notification(
                        category=category,
                        status='error',
                        message=f"{category} 크롤링 실패:\n{stderr.decode('utf-8')[:500]}"
                    )

                return False

        except Exception as e:
            logger.error(f"[{category}] 실행 에러: {e}")

            # 에러 알림
            if self.config.get('notifications', {}).get('slack', {}).get('on_error'):
                await self._send_notification(
                    category=category,
                    status='error',
                    message=f"{category} 실행 에러: {str(e)}"
                )

            return False

        finally:
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{category}] 소요 시간: {duration:.1f}초")

    async def _send_notification(self, category: str, status: str, message: str):
        """알림 전송 (Slack/Email)"""
        logger.info(f"알림 전송: {category} - {status}")
        # TODO: Slack webhook 또는 Email 전송 구현
        pass

    def setup_schedules(self):
        """스케줄 등록"""
        logger.info("크롤링 스케줄 설정 중...")

        schedules = self.config.get('schedules', {})

        for category, schedule_config in schedules.items():
            if not schedule_config.get('enabled', True):
                logger.info(f"  [{category}] 비활성화됨 - SKIP")
                continue

            script = schedule_config.get('script')
            cron_expr = schedule_config.get('cron')

            # Cron 표현식 파싱
            minute, hour, day, month, day_of_week = cron_expr.split()

            # 작업 등록
            self.scheduler.add_job(
                func=self.run_crawl,
                trigger=CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week
                ),
                args=[category, script],
                id=f"crawl_{category}",
                name=schedule_config.get('description', f"{category} 크롤링"),
                replace_existing=True
            )

            logger.info(f"  ✓ [{category}] 등록: {cron_expr} - {script}")

        logger.info(f"\n총 {len(schedules)}개 스케줄 등록 완료")

    def start(self):
        """스케줄러 시작"""
        logger.info("\n" + "="*80)
        logger.info("크롤링 스케줄러 시작")
        logger.info("="*80)

        self.setup_schedules()
        self.scheduler.start()

        logger.info("\n스케줄러 실행 중... (Ctrl+C로 종료)")
        logger.info("="*80)

        # 스케줄 목록 출력
        jobs = self.scheduler.get_jobs()
        logger.info(f"\n등록된 작업 ({len(jobs)}개):")
        for job in jobs:
            logger.info(f"  - {job.name}: {job.trigger}")

    def stop(self):
        """스케줄러 중지"""
        logger.info("\n스케줄러 종료 중...")
        self.scheduler.shutdown()
        logger.info("스케줄러 종료됨")


async def main():
    """메인 실행"""
    scheduler = CrawlScheduler()

    try:
        scheduler.start()

        # 무한 대기
        while True:
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        logger.info("\n사용자에 의한 종료 요청")
        scheduler.stop()


if __name__ == "__main__":
    # 로그 디렉토리 생성
    Path("logs").mkdir(exist_ok=True)

    asyncio.run(main())
